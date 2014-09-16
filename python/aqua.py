from __future__ import division
__author__ = 'Martin Lichtman'
import logging
logger = logging.getLogger(__name__)
from cs_errors import PauseError

import traceback
from atom.api import Member

# Bring in other files in this package
import analysis, save2013style, TTL, LabView, roi_fitting, picomotors, andor, DCNoiseEater, Laird_temperature
from experiments import Experiment


class AQuA(Experiment):
    """A subclass of Experiment which knows about all our particular hardware"""

    picomotors = Member()
    Andor = Member()
    LabView = Member()
    DC_noise_eaters = Member()
    box_temperature = Member()

    TTL_filters = Member()
    squareROIAnalysis = Member()
    gaussian_roi = Member()
    loading_filters = Member()
    first_measurements_filter = Member()
    text_analysis = Member()
    recent_shot_analysis = Member()
    shotBrowserAnalysis = Member()
    imageSumAnalysis = Member()
    imageWithROIAnalysis = Member()
    histogramAnalysis = Member()
    histogram_grid = Member()
    measurements_graph = Member()
    iterations_graph = Member()
    retention_graph = Member()
    andor_viewer = Member()
    DC_noise_eater_graph = Member()
    DC_noise_eater_filter = Member()
    save2013Analysis = Member()
    ROI_rows = 7
    ROI_columns = 7

    def __init__(self):
        super(AQuA, self).__init__()

        #add instruments
        self.picomotors = picomotors.Picomotors('picomotors', self, 'Newport Picomotors')
        self.Andor = andor.Andor('Andor', self, 'Andor Luca Camera')
        self.LabView = LabView.LabView(experiment=self)
        self.DC_noise_eaters = DCNoiseEater.DCNoiseEaters('DC_noise_eaters', self)
        self.box_temperature = Laird_temperature.LairdTemperature('box_temperature', self)
        self.instruments += [self.box_temperature, self.picomotors, self.Andor, self.DC_noise_eaters, self.LabView]

        #analyses
        self.TTL_filters = TTL.TTL_filters('TTL_filters', self)
        self.loading_filters = analysis.LoadingFilters('loading_filters', self, 'drop measurements with no atom loaded')
        self.first_measurements_filter = analysis.DropFirstMeasurementsFilter('first_measurements_filter', self, 'drop the first N measurements')
        self.squareROIAnalysis = analysis.SquareROIAnalysis(self, ROI_rows=self.ROI_rows, ROI_columns=self.ROI_columns)
        self.gaussian_roi = roi_fitting.GaussianROI('gaussian_roi', self, rows=self.ROI_rows, columns=self.ROI_columns)
        self.text_analysis = analysis.TextAnalysis('text_analysis', self, 'text results from the measurement')
        self.imageSumAnalysis = analysis.ImageSumAnalysis(self)
        self.recent_shot_analysis = analysis.RecentShotAnalysis('recent_shot_analysis', self, description='just show the most recent shot')
        self.shotBrowserAnalysis = analysis.ShotsBrowserAnalysis(self)
        self.histogramAnalysis = analysis.HistogramAnalysis('histogramAnalysis', self, 'plot the histogram of any shot and roi')
        self.histogram_grid = analysis.HistogramGrid('histogram_grid', self, 'all 49 histograms for shot 0 at the same time')
        self.measurements_graph = analysis.MeasurementsGraph('measurements_graph', self, 'plot the ROI sum vs all measurements')
        self.iterations_graph = analysis.IterationsGraph('iterations_graph', self, 'plot the average of ROI sums vs iterations')
        self.retention_graph = analysis.RetentionGraph('retention_graph', self, 'plot occurence of binary result (i.e. whether or not atoms are there in the 2nd shot)')
        self.andor_viewer = andor.AndorViewer('andor_viewer', self, 'show the most recent Andor image')
        self.DC_noise_eater_graph = DCNoiseEater.DCNoiseEaterGraph('DC_noise_eater_graph', self, 'DC Noise Eater graph')
        self.DC_noise_eater_filter = DCNoiseEater.DCNoiseEaterFilter('DC_noise_eater_filter', self, 'DC Noise Eater Filter')
        self.save2013Analysis = save2013style.Save2013Analysis(self)
        self.analyses += [self.TTL_filters, self.squareROIAnalysis, self.gaussian_roi, self.loading_filters,
                          self.first_measurements_filter, self.text_analysis, self.imageSumAnalysis,
                          self.recent_shot_analysis, self.shotBrowserAnalysis, self.histogramAnalysis,
                          self.histogram_grid, self.measurements_graph, self.iterations_graph, self.retention_graph,
                          self.andor_viewer, self.DC_noise_eater_graph, self.DC_noise_eater_filter,
                          self.save2013Analysis]

        self.properties += ['LabView', 'picomotors', 'Andor', 'DC_noise_eaters', 'box_temperature',
                            'squareROIAnalysis', 'gaussian_roi', 'TTL_filters', 'loading_filters',
                            'first_measurements_filter', 'imageSumAnalysis', 'recent_shot_analysis',
                            'shotBrowserAnalysis', 'histogramAnalysis', 'histogram_grid', 'measurements_graph',
                            'iterations_graph', 'retention_graph', 'andor_viewer', 'DC_noise_eater_graph',
                            'DC_noise_eater_filter']

        try:
            self.allow_evaluation = False
            self.loadDefaultSettings()

            #update variables
            self.allow_evaluation = True
            self.evaluateAll()
        except PauseError:
            logger.warning('Loading default settings aborted in AQuA.__init__().  PauseError')
        except Exception as e:
            logger.warning('Loading default settings aborted in AQuA.__init__().\n{}\n{}\n'.format(e, traceback.format_exc()))

        #make sure evaluation is allowed now
        self.allow_evaluation = True
