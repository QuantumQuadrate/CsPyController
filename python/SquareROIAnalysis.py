"""
SquareROIAnalysis.py
Part of the CsPyController package.

This analysis integrates the signal in rectangular signal ROIs, substracts the average
background per pixel measured in the background ROIs and saves the data to the
HDF5 file

author = 'Martin Lichtman'
created = '2014.09.08'
modified >= '2014.09.08'
modified >= '2017.05.04'
"""

import logging
from colors import my_cmap, green_cmap

import numpy as np
from atom.api import Bool, Str, Member, Int
import time

from analysis import ROIAnalysis

logger = logging.getLogger(__name__)

def roi_sum(roi, shot):
    '''Sum over a single ROI'''
    return np.sum(shot[roi['top']:roi['bottom'], roi['left']:roi['right']])

def roi_sums(rois, shot):
    '''Sum over a list of ROIs'''
    return np.array([roi_sum(roi, shot) for roi in rois], dtype=np.uint32)

def roi_pixels(roi):
    '''return the number of pixels in the roi'''
    return abs((roi[2]-roi[0])*(roi[3]-roi[1]))

def roi_pixel_cnt(rois):
    '''List of pixels in each ROI'''
    return np.array([roi_pixels(roi) for roi in rois], dtype=np.uint32)


class SquareROIAnalysis(ROIAnalysis):
    """Add up the sums of pixels in a region, and evaluate whether or not an
    atom is present based on the totals.
    """

    version = '2017.05.04'
    # signal ROIs
    ROI_rows = Int()
    ROI_columns = Int()
    ROIs = Member()  # a numpy array holding an ROI in each row
    # background ROIs
    ROI_bg_rows = Int()
    ROI_bg_columns = Int()
    ROIs_bg = Member()  # a numpy array holding an ROI in each row

    enable = Bool()
    sum_array = Member()
    camera = Member()
    shots_path = Member()
    meas_analysis_path = Member()
    iter_analysis_path = Member()


    def __init__(self, experiment):
        super(SquareROIAnalysis, self).__init__(
            'SquareROIAnalysis',
            experiment,
            'Does analysis on square regions of interest'
        )
        # initialize with blank arrays, will be filled in from settings if there
        dtype = [
            ('left', np.uint16),
            ('top', np.uint16),
            ('right', np.uint16),
            ('bottom', np.uint16)
        ]
        self.ROIs = np.zeros(
            experiment.ROI_rows*experiment.ROI_columns,
            dtype=dtype
        )
        self.ROIs_bg = np.zeros(
            experiment.ROI_bg_rows*experiment.ROI_bg_columns,
            dtype=dtype
        )
        # set up ROIs
        self.set_rois()
        # HDF5 data paths
        # where the camera data is expected to be stored
        self.shots_path = 'data/' + self.experiment.Config.config.get('CAMERA', 'DataGroup') + '/shots'
        # where we are going to dump data after analysis
        self.meas_analysis_path = 'analysis/squareROIsums'
        # self.iter_analysis_path = 'analysis/squareROI/sums'
        self.iter_analysis_path = 'analysis/square_roi/sums'

        # analyze in a separate thread
        self.queueAfterMeasurement = True

        self.properties += ['version', 'enable', 'ROIs', 'ROIs_bg']


    def set_rois(self):
        """Initialize the ROI Call when number of ROIs changes"""

        self.ROI_rows = self.experiment.ROI_rows
        self.ROI_columns = self.experiment.ROI_columns
        self.ROI_bg_rows = self.experiment.ROI_bg_rows
        self.ROI_bg_columns = self.experiment.ROI_bg_columns
        # create sum_array in the shot, row, column format
        # will be resized to the expected number of shots later
        self.sum_array = np.zeros((0, self.ROI_rows, self.ROI_columns), dtype=np.int32)
        
        warn = False
        msg = 'The ROI definitions do not agree. Check relevant analyses. '
        if len(self.ROIs) != self.ROI_rows*self.ROI_columns:
            warn = True
            msg += '\nROI definitions: `{}`, ROI rows(columns) `{}({})`'
            msg = msg.format(len(self.ROIs), self.ROI_rows, self.ROI_columns)
        if len(self.ROIs_bg) != self.ROI_bg_rows*self.ROI_bg_columns:
            warn = True
            msg += '\nROI bg definitions: `{}`, ROI bg rows(columns): `{}({})`'
            msg = msg.format(len(self.ROIs_bg), self.ROI_bg_rows, self.ROI_bg_columns)

        if warn:
            logger.warning(msg)
            dtype = [
                ('left', np.uint16),
                ('top', np.uint16),
                ('right', np.uint16),
                ('bottom', np.uint16)
            ]
            # make a new ROIs object from the old one as best as we can
            ROIs = np.zeros(self.ROI_rows*self.ROI_columns, dtype=dtype)
            for i in range(min(len(ROIs), len(self.ROIs))):
                ROIs[i] = self.ROIs[i]
            self.ROIs = ROIs
            logger.warning('new ROIs: {}'.format(self.ROIs))
            # make a new ROIs_bg object from the old one as best as we can
            ROIs_bg = np.zeros(self.ROI_bg_rows*self.ROI_bg_columns, dtype=dtype)
            for i in range(min(len(ROIs_bg), len(self.ROIs_bg))):
                ROIs_bg[i] = self.ROIs_bg[i]
            self.ROIs_bg = ROIs_bg
            logger.warning('new ROIs_bg: {}'.format(self.ROIs_bg))


    def find_camera(self):
        """Find camera instrument object in experiment properties tree."""
        # get the property tree path to the camera object from the config file
        prop_tree = self.experiment.Config.config.get('CAMERA', 'CameraObj').split(',')

        camera = self.experiment
        for lvl in prop_tree:
            camera = getattr(camera, lvl)

        # if camera is stored in a ListProp list then use the index function
        # to retreive it
        camera_idx = self.experiment.Config.config.getint('CAMERA', 'CameraIdx')
        if camera_idx >= 0:
            try:
                camera = camera[camera_idx]
            except ValueError:
                logger.warning(
                    'No camera found at index `%d` in camera list: `%s`. Disabling analysis',
                    camera_idx,
                    '.'.join(prop_tree)
                )
                self.enable = False

        self.camera = camera

    def analyzeMeasurement(self, measurementResults, iterationResults, experimentResults):
        if self.enable:
            if self.shots_path in measurementResults:
                # here we want to live update a digital plot of atom loading
                num_shots = len(measurementResults[self.shots_path])
                if self.camera.enable and (num_shots != self.camera.shotsPerMeasurement.value):
                    logger.warning(
                        'Camera expected %s shots, but instead got %s.',
                        self.camera.shotsPerMeasurement.value, num_shots
                    )
                    return 3  # hard fail, delete measurement

                bg_pixel_cnt = np.sum(roi_pixel_cnt(self.ROIs_bg))
                sig_pixel_cnt = roi_pixel_cnt(self.ROIs)

                num_rois = len(self.ROIs)
                sum_array = np.zeros((num_shots, num_rois), dtype=np.int32)

                # for each image
                for i, (name, shot) in enumerate(measurementResults[self.shots_path].items()):
                    # generate background normalized per pixel
                    bg_per_pix = 0
                    if bg_pixel_cnt != 0:
                        bg_per_pix = np.divide(np.sum(roi_sums(self.ROIs_bg, shot)), bg_pixel_cnt, dtype='float32')
                    # subtract the average background signal per pixel from each signal pixel
                    shot_sums = np.subtract(roi_sums(self.ROIs, shot), bg_per_pix*sig_pixel_cnt)
                    # round to nearest integer
                    sum_array[i] = np.rint(shot_sums)

                self.sum_array = sum_array.reshape((num_shots, self.ROI_rows, self.ROI_columns))
                measurementResults[self.meas_analysis_path] = sum_array
                self.updateFigure()

            # check to see if there were supposed to be images
            elif self.camera.enable and (self.camera.shotsPerMeasurement.value > 0):
                logger.warning(
                    'Camera expected %s shots, but did not get any.',
                    self.camera.shotsPerMeasurement.value
                )
                return 3  # hard fail, delete measurement
            else:
                logger.warning("enabled: {}".format(self.camera.enable))
                logger.warning("shots: {}".format(self.camera.shotsPerMeasurement.value))
                return 3

    def analyzeIteration(self, iterationResults, experimentResults):
        """Analyze all measurements taken in the iteration.

        Create a big array of the results from each measurement for convenience
        data is stored in iterationResults['analysis/square_roi/sums']
        as an array of size (measurements x shots x roi) array
        """
        if self.enable:
            meas = map(int, iterationResults['measurements'].keys())
            meas.sort()
            path = 'measurements/{}/' + self.meas_analysis_path
            try:
                res = np.array([iterationResults[path.format(m)] for m in meas])
            except KeyError:
                # I was having problem with the file maybe not being ready
                logger.warning("Issue reading hdf5 file. Waiting then repeating.")
                time.sleep(0.1)  # try again in a little
                try:
                    res = np.array([iterationResults[path.format(m)] for m in meas])
                except KeyError:
                    msg = (
                        "Reading from hdf5 file during measurement `{}`"
                        " failed."
                    ).format(m)
                    logger.exception(msg)
            iterationResults[self.iter_analysis_path] = np.array(res)

    def fromHDF5(self, hdf):
        """Override of the analysis fromHDF5 fcuntion.

        I need to override this so I can call the find camera function after
        the camera has been loaded.
        """
        super(SquareROIAnalysis, self).fromHDF5(hdf)
        # I am here because the camera needs to be setup first
        self.find_camera()

    def updateFigure(self):
        if self.draw_fig:
            fig = self.backFigure
            fig.clf()
            if self.sum_array.size > 0:
                n = len(self.sum_array)
                for i in range(n):
                    ax = fig.add_subplot(n, 1, i+1)
                    #make the digital plot here
                    ax.matshow(self.sum_array[i], cmap=green_cmap)
                    ax.set_title('shot '+str(i))
            super(SquareROIAnalysis, self).updateFigure()
