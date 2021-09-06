from __future__ import division
import logging

from cs_errors import PauseError
from atom.api import Member, Int

# Bring in other files in this package
import functional_waveforms, analysis, save2013style, TTL, LabView
import DDS
import AWG
import andor, AnalogInput
import unlock_pause, nidaq_ai
logger = logging.getLogger(__name__)
import origin_interface
from pypico import PyPicoServer  # for communicating with a picomotor server

# analyses
from SquareROIAnalysis import SquareROIAnalysis
from RbAIAnalysis import RbAIAnalysis
from recent_shot_analysis import RecentShotAnalysis
from image_sum_analysis import ImageSumAnalysis
from threshold_analysis import ThresholdROIAnalysis
from retention_analysis import RetentionAnalysis, RetentionGraph
from histogram_analysis import HistogramAnalysis
from beam_position_analysis import BeamPositionAnalysis
from experiments import Experiment


class Rb(Experiment):
    """A subclass of Experiment which knows about all our particular hardware"""

    window_dict = Member()
    Andors = Member()
    blackfly_client = Member()
    LabView = Member()
    DDS = Member()
    AWG = Member()
    pyPicoServer = Member()
    imageSumAnalysis = Member()
    functional_waveforms_graph = Member()
    DAQmxAI = Member()
    beam_position_analysis = Member()
    beam_position_analysis2 = Member()
    TTL_filters = Member()
    unlock_pause = Member()
    AI_graph = Member()
    AI_filter = Member()
    squareROIAnalysis = Member()
    RbAIAnalysis = Member()
    thresholdROIAnalysis = Member()
    loading_filters = Member()
    error_filters = Member()
    first_measurements_filter = Member()
    text_analysis = Member()
    recent_shot_analysis = Member()
    imageWithROIAnalysis = Member()
    histogramAnalysis = Member()
    measurements_graph = Member()
    iterations_graph = Member()
    retention_graph = Member()
    retention_analysis = Member()
    recent_shot_analysis = Member()
    save_notes = Member()
    TTL_filters = Member()
    origin = Member()
    Ramsey = Member()
    ROI_rows = Int(1)
    ROI_columns = Int(1)
    ROI_bg_rows = Int(0)
    ROI_bg_columns = Int(0)

    def __init__(self,
                 config_instrument=None,
                 cache_location=None,
                 settings_location=None,
                 temp_location=None):

        super(Rb, self).__init__(config_instrument=config_instrument,
                                 cache_location=cache_location,
                                 settings_location=settings_location,
                                 temp_location=temp_location)
        try:
            # communicates with Blackfly camera server
            from blackfly import BlackflyClient
            self.blackfly_client = BlackflyClient('BlackflyClient', self)
            self.instruments += [self.blackfly_client]
            self.properties += ['blackfly_client']
        except:
            logger.warning("Blackfly client disabled,"
                           "install PyCapture2 module to enable")
        # self.functional_waveforms = functional_waveforms.FunctionalWaveforms('functional_waveforms', self, 'Waveforms for HSDIO, DAQmx DIO, and DAQmx AO; defined as functions')

        self.Andors = andor.Andors('Andors', self, 'Andor Luca measurementResults')
        self.LabView = LabView.LabView(self)
        self.DAQmxAI = nidaq_ai.NIDAQmxAI('DAQmxAI', self, 'NI-DAQmx Analog Input')
        self.DDS = DDS.DDS('DDS', self, 'server for homemade DDS boxes')
        self.AWG = AWG.AWG('AWG', self, 'Signadyne AWG Card')
        self.pyPicoServer = PyPicoServer('PyPicomotor', self, 'PyPico server interface for controlling closed loop picomotors')
        self.unlock_pause = unlock_pause.UnlockMonitor('unlock_pause', self, 'Monitor for pausing when laser unlocks')
        self.instruments += [
            self.DAQmxAI,
            self.pyPicoServer,
            self.Andors,
            self.DDS,
            self.AWG,
            self.unlock_pause
        ]
        # Labview must be last at least until someone fixes the start command
        self.instruments += [self.LabView]

        # analyses
        self.squareROIAnalysis = SquareROIAnalysis(self)
        self.ROITypeString = 'squareROIsums'
        self.imageSumAnalysis = ImageSumAnalysis(self)
        self.TTL_filters = TTL.TTL_filters('TTL_filters', self)
        self.functional_waveforms_graph = functional_waveforms.FunctionalWaveformGraph('functional_waveforms_graph', self, 'Graph the HSDIO, DAQmx DO, and DAQmx AO settings')
        self.AI_graph = AnalogInput.AI_Graph('AI_graph', self, 'Analog Input Graph')
        self.AI_filter = AnalogInput.AI_Filter('AI_filter', self, 'Analog Input filter')
        self.first_measurements_filter = analysis.DropFirstMeasurementsFilter('first_measurements_filter', self, 'drop the first N measurements')
        self.RbAIAnalysis = RbAIAnalysis(self)
        self.thresholdROIAnalysis = ThresholdROIAnalysis(self)
        self.loading_filters = analysis.LoadingFilters('loading_filters', self, 'drop measurements with no atom loaded')
        self.error_filters = analysis.LoadingFilters('error_filters', self, 'drop measurements with errors using roi input')
        self.text_analysis = analysis.TextAnalysis('text_analysis', self, 'text results from the measurement')
        self.histogramAnalysis = HistogramAnalysis('histogramAnalysis', self, 'plot the histogram of any shot and roi')
        self.Ramsey = analysis.Ramsey('Ramsey', self, 'Fit a cosine to retention results')
        self.measurements_graph = analysis.MeasurementsGraph('measurements_graph', self, 'plot the ROI sum vs all measurements')
        self.iterations_graph = analysis.IterationsGraph('iterations_graph', self, 'plot the average of ROI sums vs iterations')
        self.retention_graph = RetentionGraph('retention_graph', self, 'plot occurence of binary result (i.e. whether or not atoms are there in the 2nd shot)')
        self.retention_analysis = RetentionAnalysis('retention_analysis', self, 'calculate the loading and retention')
        self.save_notes = save2013style.SaveNotes('save_notes', self, 'save a separate notes.txt')
        self.beam_position_analysis = BeamPositionAnalysis(self)
        self.beam_position_analysis2 = BeamPositionAnalysis(self)
        # setup path for second beam position analysis
        self.beam_position_analysis2.set_position_paths(datagroup='Camera1DataGroup')
        self.recent_shot_analysis = RecentShotAnalysis('recent_shot_analysis', self, description='just show the most recent shot')

        # setup path for second beam position analysis
        # self.vitalsignsound=Vitalsign('vital_sign_sound',self,'beeps when atoms are loaded')
        self.origin = origin_interface.Origin('origin', self, 'saves selected data to the origin data server')

        # do not include functional_waveforms_graph in self.analyses because it
        # need not update on iterations, etc.
        # origin needs to be the last analysis always
        self.analyses += [
            self.AI_graph, self.AI_filter, self.RbAIAnalysis,
            # ROI analyses go here ------------------------------------------
            self.squareROIAnalysis,
            # ---------------------------------------------------------------
            self.imageSumAnalysis,
            self.histogramAnalysis, self.thresholdROIAnalysis,
            self.loading_filters, self.error_filters,
            self.first_measurements_filter, self.text_analysis,
            self.recent_shot_analysis,
            self.measurements_graph,
            self.iterations_graph,
            self.Andors,
            self.retention_analysis, self.retention_graph,
            self.save_notes,
            self.TTL_filters,
            self.functional_waveforms_graph,
            self.Ramsey,
            self.beam_position_analysis,
            self.beam_position_analysis2,
            self.recent_shot_analysis,
            self.origin  # TODO: origin has to be last
        ]

        self.properties += [
            'Config', 'Ramsey', 'TTL_filters', 'beam_position_analysis',
            'beam_position_analysis2', 'functional_waveforms_graph',
            'unlock_pause', 'DAQmxAI', 'imageSumAnalysis',
            'RbAIAnalysis', 'functional_waveforms', 'LabView',
            'DDS','AWG',
            'pyPicoServer', 'Andors',
            'squareROIAnalysis', 'histogram_grid', 'thresholdROIAnalysis',
            'TTL_filters', 'AI_graph',
            'AI_filter', 'loading_filters', 'error_filters',
            'first_measurements_filter',
            'histogramAnalysis',
            'retention_analysis', 'measurements_graph', 'iterations_graph',
            'retention_graph',
            'ROI_rows', 'ROI_columns', 'ROI_bg_rows', 'ROI_bg_columns',
            'recent_shot_analysis',
            'origin'
        ]

        self.window_dict = {
            '':'',
            'Experiment': 'ExperimentPage(experiment = main.experiment, creator=main, name ="Experiment")',
            'Independent Variables': 'IndependentVariables(independentVariables = main.experiment.independentVariables, creator=main, name="Independent Variables")',
            'Constants and Dependent Vars': 'Variables(experiment = main.experiment, creator=main, name="Constants and Dependent Vars")',
            'PXI Communication': 'LabViewPage(LabView = main.experiment.LabView, creator=main, name="PXI Communication")',
            'DAQmx': 'DAQmxDigitalOutPage(DAQmx = main.experiment.LabView.DAQmxDO, creator=main, name="DAQmx")',
            'DAQmxAI': 'DAQmxAI(NIDAQmxAI = main.experiment.DAQmxAI, creator=main, name="DAQmxAI")',
            'HSDIO': 'HSDIO_DigitalOutPage(HSDIO = main.experiment.LabView.HSDIO, creator=main, name="HSDIO")',
            'DDS': 'DDS_Page(DDS = main.experiment.DDS, creator=main, name="DDS")',
            'AWG': 'AWG_Page(AWG = main.experiment.AWG, creator=main, name="AWG")',
            'Andor Cameras': 'Andors(andors = main.experiment.Andors, creator=main, name="Andor Cameras")',
            'Blackfly Client': 'BlackflyClient(blackfly_client = main.experiment.blackfly_client, creator=main, name="Blackfly Client")',
            'Analog Output': 'AnalogOutput(AO = main.experiment.LabView.AnalogOutput, creator=main, name="Analog Output")',
            'Analog Input': 'AnalogInput(AI = main.experiment.LabView.AnalogInput, filters = main.experiment.AI_filter, analysis = main.experiment.AI_graph, creator=main, name="Analog Input")',
            'PyPico': 'PyPico(pypico = main.experiment.pyPicoServer, creator=main, name="PyPico")',
            'AAS': 'AAS(aas = main.experiment.beam_position_analysis, creator=main, name="AAS")',
            'AAS2': 'AAS(aas = main.experiment.beam_position_analysis2, creator=main, name="AAS2")',
            'Live Images': 'MultiImage(experiment = main.experiment, analysis0 = main.experiment.recent_shot_analysis, analysis2 = main.experiment.imageSumAnalysis, analysis3 = main.experiment.text_analysis, creator=main, name="Live Images")',
            'Square ROI':  'SquareROIContainer(experiment = main.experiment, analysis = main.experiment.squareROIAnalysis, creator=main, name="Square ROI")',
            'Threshold ROI':  'ThresholdROIContainer(experiment = main.experiment, analysis = main.experiment.thresholdROIAnalysis, creator=main, name="Threshold ROI")',
            'Histogram': 'Histogram(experiment = main.experiment, analysis = main.experiment.histogramAnalysis, creator=main, name="Histogram")',
            'Measurements Graph': 'MeasurementsGraph(experiment = main.experiment, analysis = main.experiment.measurements_graph, creator=main, name="Measurements Graph")',
            'Iterations Graph': 'IterationsGraph(experiment = main.experiment, analysis = main.experiment.iterations_graph, creator=main, name="Iterations Graph")',
            'Retention Graph': 'RetentionGraph(experiment = main.experiment, analysis = main.experiment.retention_graph, creator=main, name="Retention Graph")',
            'Filters': 'Filters(experiment = main.experiment, creator=main, name="Filters")',
            'Functional Waveforms Graph': 'FunctionalWaveformsGraph(graph = main.experiment.functional_waveforms_graph, creator=main, name="Functional Waveforms Graph")',
            'Optimization': 'Optimizer(experiment = main.experiment, analysis = main.experiment.optimizer, creator=main, name="Optimization")',
            'Pi Lock Monitor': 'Unlock_Pause(unlock_pause = main.experiment.unlock_pause, creator=main, name="Pi Lock Monitor")',
            'Retention Analysis': 'RetentionAnalysis(analysis = main.experiment.retention_analysis, creator=main, name="Retention Analysis")',
            'Functional Waveforms': 'FunctionalWaveforms(waveforms = main.experiment.functional_waveforms, creator=main, name="Functional Waveforms")',
            'Origin Interface': 'Origin(origin = main.experiment.origin, creator=main, name="Origin Interface")',
                                }
# window_keys = window_dictionary.keys()
# window_keys.sort()

        try:
            self.allow_evaluation = False
            self.loadDefaultSettings()
            # update variables
            self.allow_evaluation = True
            self.evaluateAll()
        except PauseError:
            logger.warning('Loading default settings aborted in Rb.__init__().  PauseError')
        except:
            logger.exception('Loading default settings aborted in Rb.__init__().')

        # make sure evaluation is allowed now
        self.allow_evaluation = True

    def exiting(self):
        self.Andors.__del__()
        return
