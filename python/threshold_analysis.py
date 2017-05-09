import logging
import numpy as np
from atom.api import Bool, Str, Member, Int, observe

from analysis import AnalysisWithFigure

from colors import my_cmap, green_cmap

# get the config file
from __init__ import import_config
config = import_config()

logger = logging.getLogger(__name__)

class ThresholdROIAnalysis(AnalysisWithFigure):
    '''Compares the raw ROI from the selected source to a simple threshold cut to 
    determine atom number
    '''

    version = '2017.05.09'
    ROI_rows = Int()
    ROI_columns = Int()
    ROI_source = Member()
    threshold_array = Member()
    loading_array = Member()
    meas_analysis_path = Member()
    enable = Bool()

    def __init__(self, experiment, roi_rows=1, roi_columns=1):
        super(ThresholdROIAnalysis, self).__init__('ThresholdROIAnalysis', experiment, 'Simple threshold digitization')
        self.loading_array = np.zeros((0, roi_rows, roi_columns), dtype=np.bool_)
        dtype = [
            ('1', np.int32) # add more atom number cuts later
        ]
        self.threshold_array = np.zeros((roi_rows*roi_columns), dtype=dtype)
        self.ROI_rows = roi_rows
        self.ROI_columns = roi_columns
        self.ROI_source = getattr(self.experiment, config.get('CAMERA', 'ThresholdROISource'))
        self.meas_analysis_path = 'analysis/ROIThresholds'
        self.properties += ['version', 'ROI_source', 'threshold_array', 'enable']

    def analyzeMeasurement(self, measurementResults, iterationResults, experimentResults):
        if self.enable:
            shot_array = measurementResults[self.ROI_source.meas_analysis_path][()]
            numShots = len(shot_array)
            numROIs = len(self.ROI_source.ROIs)
            # temporary 2D threshold array, ROIs are 1D
            threshold_array = np.zeros((numShots, numROIs), dtype=np.bool_)

            for i, shot in enumerate(shot_array):
                #TODO: more complicated threshold (per shot threshold & 2+ atom threshold)
                threshold_array[i] = shot >= self.threshold_array['1']

            self.loading_array = threshold_array.reshape((numShots, self.ROI_rows, self.ROI_columns))
            measurementResults[self.meas_analysis_path] = threshold_array
            self.updateFigure()

    def analyzeIteration(self, iterationResults, experimentResults):
        '''Calculate loading rates'''
        pass

    def updateFigure(self):
        fig = self.backFigure
        fig.clf()
        if self.loading_array.size > 0:
            n = len(self.loading_array)
            for i in range(n):
                ax = fig.add_subplot(n, 1, i+1)
                #make the digital plot here
                ax.matshow(self.loading_array[i], cmap=green_cmap)
                ax.set_title('shot '+str(i))
        super(ThresholdROIAnalysis, self).updateFigure()
