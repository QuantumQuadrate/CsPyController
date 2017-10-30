import logging
import numpy as np
import time

from atom.api import Bool, Str, Member, Int

from analysis import ROIAnalysis

from colors import green_cmap

logger = logging.getLogger(__name__)


class ThresholdROIAnalysis(ROIAnalysis):
    '''Compares the raw ROI from the selected source to a simple threshold cut
    to determine atom number
    '''

    version = '2017.05.09'
    ROI_source = Member()
    threshold_array = Member()
    loading_array = Member()
    meas_analysis_path = Str()
    iter_analysis_path = Str()
    meas_enable = Bool(True)
    cutoffs_from_which_experiment = Member()
    shots = Int(2)

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
            (self.shots, experiment.ROI_rows * experiment.ROI_columns),
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

        self.loading_array = np.zeros(
            (0, roi_rows, roi_columns),
            dtype=np.bool_
        )

        size = roi_rows * roi_columns
        if len(self.threshold_array[0]) != size:
            msg = 'The ROI definitions do not agree. Check relevant analyses. '
            msg += '\nthreshold array len: `{}`, ROI rows(columns) `{}({})`'
            msg = msg.format(len(self.threshold_array), roi_rows, roi_columns)
            logger.warning(msg)
            # make a new ROIs object from the old one as best as we can
            dtype = [
                ('1', np.int32)  # add more atom number cuts later
            ]
            try:
                for s in range(self.shots):
                    ta = np.zeros(size, dtype=dtype)
                    for i in range(min(len(ta), len(self.threshold_array[s]))):
                        ta[i] = self.threshold_array[s, i]
                    self.threshold_array[s] = ta
            except IndexError:
                dtype = [
                    ('1', np.int32)  # add more atom number cuts later
                ]
                self.threshold_array = np.zeros(
                    (self.shots, size),
                    dtype=dtype
                )
            logger.warning('new thresholds: {}'.format(self.threshold_array))

    def set_thresholds(self, new_thresholds, timestamp):
        # the same threshold is used for all shots
        for j, shot in enumerate(new_thresholds):
            for i, t in enumerate(shot):
                self.threshold_array[j, i] = (t,)
        self.cutoffs_from_which_experiment = timestamp

    def preExperiment(self, experimentResults):
        super(ThresholdROIAnalysis, self).preExperiment(experimentResults)
        # reset the measurement enable flag
        self.meas_enable = True

    def analyzeMeasurement(self, measurementResults, iterationResults,
                           experimentResults):
        if self.enable and self.meas_enable:
            try:
                data_path = self.ROI_source.meas_analysis_path
                shot_array = measurementResults[data_path][()]
            except (KeyError, AttributeError):
                msg = (
                    'No measurement ROI sum data found at `{}`.'
                    'Disabling per measurement threshold analysis.'
                )
                logger.warning(msg.format(data_path))
                self.meas_enable = False

            else:
                numShots = len(shot_array)
                numROIs = len(self.ROI_source.ROIs)
                # temporary 2D threshold array, ROIs are 1D
                threshold_array = np.zeros((numShots, numROIs), dtype=np.bool_)

                for i, shot in enumerate(shot_array):
                    # TODO: more complicated threshold
                    # (per shot threshold & 2+ atom threshold)
                    #print self.threshold_array[i]['1']
                    shots_to_ignore = 0
                    try:
                        shots_to_ignore = self.experiment.Config.config.get('CAMERA', 'ShotsToIgnore')
                    except:
                        pass
                    if i <= shots_to_ignore:  # Rubudium uses shot2 for alignment pupose so do not apply threshold for this shot
                        threshold_array[i] = shot >= self.threshold_array[i]['1']

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
            # if the per measurement threshold analysis is disabled we then
            # need to go fetch the results from elsewhere
            if self.meas_enable:
                path = 'measurements/{}/' + self.meas_analysis_path
            else:
                return 0

            try:
                res = np.array(
                    [iterationResults[path.format(m)] for m in meas]
                )
            except KeyError:
                # I was having problem with the file maybe not being ready
                msg = "Issue reading hdf5 file. Waiting then repeating."
                logger.warning(msg)
                time.sleep(0.1)  # try again in a little
                try:
                    res = np.array(
                        [iterationResults[path.format(m)] for m in meas]
                    )
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
                    ax = fig.add_subplot(n, 1, i + 1)
                    # make the digital plot here
                    ax.matshow(self.loading_array[i], cmap=green_cmap)
                    ax.set_title('shot ' + str(i))
            super(ThresholdROIAnalysis, self).updateFigure()
