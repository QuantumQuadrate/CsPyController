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
            msg = msg.format(len(self.threshold_array[0]), roi_rows, roi_columns)
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
            except (IndexError, ValueError):
                dtype = [
                    ('1', np.int32)  # add more atom number cuts later
                ]
                self.threshold_array = np.zeros(
                    (self.shots, size),
                    dtype=dtype
                )
            logger.warning('new thresholds: {}'.format(self.threshold_array))

    def set_thresholds(self, new_thresholds, timestamp, exclude_shot=[]):
        # the same threshold is used for all shots
        for j, shot in enumerate(new_thresholds):
            if j not in exclude_shot:
                for i, t in enumerate(shot):
                    self.threshold_array[j, i] = (t,)
        self.cutoffs_from_which_experiment = timestamp

    def preExperiment(self, experimentResults):
        super(ThresholdROIAnalysis, self).preExperiment(experimentResults)
        # reset the measurement enable flag
        self.meas_enable = True

    def process_measurement(self, shot_array, shape):
        """Process a single sub-measurement. f there are multiple
        sub-measurements, Then call this multiple times.
        Returns a threshold array for single sub-measurement
        """
        # temporary 2D threshold array, ROIs are 1D
        threshold_array = np.zeros(shape, dtype=np.bool_)
        try:
            shots_to_ignore_str = self.experiment.Config.config.get(
                'CAMERA', 'ShotsToIgnore')
            shots_to_ignore=map(int,shots_to_ignore_str.split(","))
        except Exception:
            shots_to_ignore=[]

        to_include = [x for x in range(0,len(shot_array)) if x not in
                      shots_to_ignore]
        for i, shot in enumerate(shot_array):
            # TODO: more complicated threshold
            # (per shot threshold & 2+ atom threshold)
            if i in to_include:
                threshold_array[to_include.index(i)] = (
                        shot.flatten() >=
                        self.threshold_array[to_include.index(i)]['1']
                )

        self.loading_array = threshold_array.reshape((
            shape[0],
            self.experiment.ROI_rows,
            self.experiment.ROI_columns
        ))
        return threshold_array

    def analyzeMeasurement(self, measResults, iterResults, expResults):
        if self.enable and self.meas_enable:
            try:
                data_path = self.ROI_source.meas_analysis_path
                shot_array = measResults[data_path][()]
                #logger.info(shot_array.shape)
            except (KeyError, AttributeError):
                msg = (
                    'No measurement ROI sum data found at `{}`.'
                    'Disabling per measurement threshold analysis.'
                )
                logger.warning(msg.format(data_path))
                self.meas_enable = False
            else:
                # check if the roi source has the sub-measurement dimension
                if len(shot_array.shape) == 3:
                    # if not add it
                    logger.warning('ROI_source for threshold_analysis does not have sub-measurement support.')
                    shot_array = np.array([shot_array])

                n_sub_meas, n_shots, n_rows, n_cols = shot_array.shape
                threshold_array = np.zeros((n_sub_meas, n_shots, n_rows*n_cols), dtype=np.bool_)
                for sm in xrange(n_sub_meas):
                    threshold_array[sm] = self.process_measurement(shot_array[sm], threshold_array[sm].shape)
                try:
                    measResults[self.meas_analysis_path] = threshold_array
                except RuntimeError:
                    del measResults[self.meas_analysis_path]
                    measResults[self.meas_analysis_path] = threshold_array
                else:
                    self.updateFigure()

    def read_meas_results(self, iter_res, meas_path, meas_nums):
        """Read all measurements results and flatten measurements to sub-measurements.

        return a list of sub-measurements
        """
        res = np.array(iter_res[meas_path.format(meas_nums[0])][()])
        for m in meas_nums[1:]:
            res = np.concatenate((res, iter_res[meas_path.format(m)][()]))
        return res

    def analyzeIteration(self, iterationResults, experimentResults):
        """Consoladates loading cuts."""
        if self.enable:
            meas = map(int, iterationResults['measurements'].keys())
            meas.sort()
            #re-analyze loading in case threasholds have changed
            for i in meas:
                meas_results_path = 'measurements/{}'.format(i)
                meas_results = iterationResults[meas_results_path]
                self.analyzeMeasurement(meas_results, iterationResults, experimentResults)

            # if the per measurement threshold analysis is disabled we then
            # need to go fetch the results from elsewhere
            if self.meas_enable:
                path = 'measurements/{}/' + self.meas_analysis_path
            else:
                return 0

            try:
                res = self.read_meas_results(iterationResults, path, meas)
            except KeyError:
                # I was having problem with the file maybe not being ready
                msg = "Issue reading hdf5 file. Waiting then repeating."
                logger.warning(msg)
                time.sleep(0.1)  # try again in a little
                try:
                    res = self.read_meas_results(iterationResults, path, meas)
                except KeyError:
                    logger.exception("Reading from hdf5 file failed.")
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
