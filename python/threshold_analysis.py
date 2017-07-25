import logging
import numpy as np
import time

from atom.api import Bool, Str, Member

from analysis import ROIAnalysis

from colors import green_cmap

logger = logging.getLogger(__name__)


class ThresholdROIAnalysis(ROIAnalysis):
    '''Compares the raw ROI from the selected source to a simple threshold cut to
    determine atom number
    '''

    version = '2017.05.09'
    ROI_source = Member()
    threshold_array = Member()
    loading_array = Member()
    meas_analysis_path = Str()
    iter_analysis_path = Str()
    enable = Bool()
    cutoffs_from_which_experiment = Member()

    def __init__(self, experiment):
        super(ThresholdROIAnalysis, self).__init__(
            'ThresholdROIAnalysis',
            experiment,
            'Simple threshold digitization'
        )
        # initialize arrays
        dtype = [
            ('1', np.int32)  # add more atom number cuts later
        ]
        self.threshold_array = np.zeros(
            (experiment.ROI_rows * experiment.ROI_columns),
            dtype=dtype
        )
        # set up rois
        self.set_rois()

        # point analysis at the roi sum source
        self.ROI_source = getattr(
            self.experiment,
            self.experiment.Config.config.get('CAMERA', 'ThresholdROISource')
        )
        self.meas_analysis_path = 'analysis/ROIThresholds'
        self.iter_analysis_path = 'analysis/ROI_Thresholds/cuts'
        self.properties += ['version', 'ROI_source', 'threshold_array']
        self.properties += ['enable']

        # threading stuff
        self.queueAfterMeasurement = True
        self.measurementDependencies += [self.ROI_source]

    def set_rois(self):
        """Initialize the ROI Call when number of ROIs changes"""
        roi_rows = self.experiment.ROI_rows
        roi_columns = self.experiment.ROI_columns

        self.loading_array = np.zeros((0, roi_rows, roi_columns), dtype=np.bool_)
        
        if len(self.threshold_array) != roi_rows*roi_columns:
            msg = 'The ROI definitions do not agree. Check relevant analyses. '
            msg += '\nthreshold array len: `{}`, ROI rows(columns) `{}({})`'
            msg = msg.format(len(self.threshold_array), roi_rows, roi_columns)
            logger.warning(msg)
            # make a new ROIs object from the old one as best as we can
            dtype = [
                ('1', np.int32) # add more atom number cuts later
            ]
            ta = np.zeros(roi_rows*roi_columns, dtype=dtype)
            for i in range(min(len(ta), len(self.threshold_array))):
                ta[i] = self.threshold_array[i]
            self.threshold_array = ta
            logger.warning('new thresholds: {}'.format(self.threshold_array))


    def analyzeMeasurement(self, measurementResults, iterationResults, experimentResults):
        if self.enable:
            shot_array = measurementResults[self.ROI_source.meas_analysis_path][()]
            numShots = len(shot_array)
            numROIs = len(self.ROI_source.ROIs)
            # temporary 2D threshold array, ROIs are 1D
            threshold_array = np.zeros((numShots, numROIs), dtype=np.bool_)

            for i, shot in enumerate(shot_array):
                # TODO: more complicated threshold
                # (per shot threshold & 2+ atom threshold)
                threshold_array[i] = shot >= self.threshold_array['1']

            self.loading_array = threshold_array.reshape((
                numShots, 
                self.experiment.ROI_rows, 
                self.experiment.ROI_columns
            ))
            measurementResults[self.meas_analysis_path] = threshold_array
            self.updateFigure()


    def analyzeIteration(self, iterationResults, experimentResults):
        """Consoladates loading cuts."""
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


    def updateFigure(self):
        if self.draw_fig:
            fig = self.backFigure
            fig.clf()
            if self.loading_array.size > 0:
                n = len(self.loading_array)
                for i in range(n):
                    ax = fig.add_subplot(n, 1, i+1)
                    # make the digital plot here
                    ax.matshow(self.loading_array[i], cmap=green_cmap)
                    ax.set_title('shot '+str(i))
            super(ThresholdROIAnalysis, self).updateFigure()

