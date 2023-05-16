from __future__ import division
import logging

from cs_errors import PauseError
from atom.api import Member, Int

# Bring in other files in this package
import functional_waveforms, analysis, save2013style, TTL, LabView
import DDS
import andor, AnalogInput

import Counter, unlock_pause, newportstage, nidaq_ai, HPSignalGenerator, HVcontroller, hybrid_auto_aligner, AWG
logger = logging.getLogger(__name__)
import origin_interface
import FakeInstrument  # for testing

# analyses

from SquareROIAnalysis import SquareROIAnalysis
from recent_shot_analysis import RecentShotAnalysis
from image_sum_analysis import ImageSumAnalysis
from threshold_analysis import ThresholdROIAnalysis
from retention_analysis import RetentionAnalysis, RetentionGraph
from histogram_analysis import HistogramAnalysis, HistogramGrid

from experiments import Experiment

__author__ = 'Martin Lichtman'



class Hybrid(Experiment):
    """A subclass of Experiment which knows about all our particular hardware"""


    aerotechs = Member()
    conexes = Member()
    Andors = Member()
    blackfly_client = Member()
    NewportStage = Member()
    DAQmxAI = Member()
    LabView = Member()
    DDS = Member()
    unlock_pause = Member()
    Embezzletron = Member()
    HPGenerators = Member()
    HVcontrol = Member()
    AutoAligner = Member()
    AWG = Member()


    thresholdROIAnalysis = Member()
    functional_waveforms_graph = Member()
    TTL_filters = Member()
    AI_graph = Member()
    AI_filter = Member()
    loading_filters = Member()
    error_filters = Member()
    first_measurements_filter = Member()
    text_analysis = Member()
    recent_shot_analysis = Member()
    imageSumAnalysis = Member()
    histogramAnalysis = Member()
    histogram_grid = Member()
    measurements_graph = Member()
    iterations_graph = Member()
    retention_graph = Member()
    retention_analysis = Member()
    counter_graph = Member()
    counter_hist = Member()
    save_notes = Member()
    origin = Member()
    ROI_rows = Int(1)
    ROI_columns = Int(1)
    ROI_bg_rows = Int(0)
    ROI_bg_columns = Int(0)
    Ramsey = Member()
    squareROIAnalysis = Member()
    window_dict = Member()
    beam_alignment_filter = Member()

    def __init__(self,
                 config_instrument=None,
                 cache_location=None,
                 settings_location=None,
                 temp_location=None):

        super(Hybrid, self).__init__(config_instrument=config_instrument,
                                   cache_location=cache_location,
                                   settings_location=settings_location,
                                   temp_location=temp_location)
        try:
            import conex
            self.conexes = conex.Conexes('conexes', self, 'CONEX-CC')
            self.instruments += [self.conexes]
            self.properties += ['conexes']
        except Exception as e:
            logger.exception(e,exc_info=True)
            logger.warning("Conex could not be instantiated."
                           "Conex translation stages will not work.")
        try:
            import aerotech
            self.aerotechs = aerotech.Aerotechs('aerotechs', self,
                                                'Aerotech Ensemble')
            self.instruments += [self.aerotechs]
            self.properties += ['aerotechs']
        except:
            logger.warning("Aerotech could not be instantiated. If it is needed"
                           ", check that pythonnet and pywin32 are installed.")
        try:
            # communicates with Blackfly camera server
            from blackfly import BlackflyClient
            self.blackfly_client = BlackflyClient('BlackflyClient', self)
            self.instruments += [self.blackfly_client]
            self.properties += ['blackfly_client']
        except:
            logger.warning("Blackfly client disabled,"
                           "install PyCapture2 module to enable")

        self.Andors = andor.Andors('Andors', self, 'Andor Luca measurementResults')
        self.DAQmxAI = nidaq_ai.NIDAQmxAI('DAQmxAI', self, 'NI-DAQmx Analog Input')
        self.NewportStage = newportstage.NewportStage('NewportStage', self, 'Newport Translation Stage')
        self.LabView = LabView.LabView(self)
        self.DDS = DDS.DDS('DDS', self, 'server for homemade DDS boxes')
        self.unlock_pause = unlock_pause.UnlockMonitor('unlock_pause', self, 'Monitor for pausing when laser unlocks')
        self.Embezzletron = FakeInstrument.Embezzletron('Embezzletron', self, 'Fake instrument that generates random data for testing')
        self.HPGenerators = HPSignalGenerator.HPGenerators('HPGenerators', self, 'controls HP8648B signal generator')
        self.HVcontrol = HVcontroller.HighVoltageController('HVcontrol', self, 'Controls Hybrid HV DACs')
        self.AutoAligner = hybrid_auto_aligner.AutoAligner('AutoAligner', self, 'Maintains the 595nm alignment')
        self.AWG = AWG.AWG(name='AWG', experiment=self, description="testing 1 2")
        # do not include functional_waveforms in self.instruments because it
        # need not start/stop
        self.instruments += [
            self.Andors, self.DDS, self.unlock_pause,
            self.Embezzletron, self.NewportStage, self.HPGenerators, self.HVcontrol, self.AutoAligner, self.AWG
        ]
        # Labview must be last at least until someone fixes the start command
        self.instruments += [self.LabView]

        # analyses
        self.functional_waveforms_graph = functional_waveforms.FunctionalWaveformGraph('functional_waveform_graph', self, 'Graph the HSDIO, DAQmx DO, and DAQmx AO settings')
        self.TTL_filters = TTL.TTL_filters('TTL_filters', self)
        self.AI_graph = AnalogInput.AI_Graph('AI_graph', self, 'Analog Input Graph')
        self.AI_filter = AnalogInput.AI_Filter('AI_filter', self, 'Analog Input filter')
        self.first_measurements_filter = analysis.DropFirstMeasurementsFilter('first_measurements_filter', self, 'drop the first N measurements')
        self.squareROIAnalysis = SquareROIAnalysis(self)
        self.counter_graph = Counter.CounterAnalysis('counter_graph', self, 'Graphs the counter data after each measurement.')
        self.thresholdROIAnalysis = ThresholdROIAnalysis(self)
        self.loading_filters = analysis.LoadingFilters('loading_filters', self, 'drop measurements with no atom loaded')
        self.error_filters = analysis.LoadingFilters('error_filters', self, 'drop measurements with errors using roi input')
        self.text_analysis = analysis.TextAnalysis('text_analysis', self, 'text results from the measurement')
        self.imageSumAnalysis = ImageSumAnalysis(self)
        self.recent_shot_analysis = RecentShotAnalysis('recent_shot_analysis', self, description='just show the most recent shot')
        self.histogramAnalysis = HistogramAnalysis('histogramAnalysis', self, 'plot the histogram of any shot and roi')
        self.histogram_grid = HistogramGrid('histogram_grid', self, 'all 121 histograms for shot 0 or 1 at the same time')
        self.measurements_graph = analysis.MeasurementsGraph('measurements_graph', self, 'plot the ROI sum vs all measurements')
        self.iterations_graph = analysis.IterationsGraph('iterations_graph', self, 'plot the average of ROI sums vs iterations')
        self.retention_graph = RetentionGraph('retention_graph', self, 'plot occurence of binary result (i.e. whether or not atoms are there in the 2nd shot)')
        self.Ramsey = analysis.Ramsey('Ramsey', self,
                                      'Fit a cosine to retention results')
        self.retention_analysis = RetentionAnalysis('retention_analysis', self, 'calculate the loading and retention')
        self.counter_hist = Counter.CounterHistogramAnalysis('counter_hist', self, 'Fits histograms of counter data and plots hist and fits.')
        self.save_notes = save2013style.SaveNotes('save_notes', self, 'save a separate notes.txt')
        self.origin = origin_interface.Origin('origin', self, 'saves selected data to the origin data server')
        self.beam_alignment_filter = hybrid_auto_aligner.BeamAlignmentFilter('beam_alignment_filter', self, 'drop measurements where beam isn\'t aligned')


        # do not include functional_waveforms_graph in self.analyses because it
        # need not update on iterations, etc.
        # origin needs to be the last analysis always
        self.analyses += [
            self.TTL_filters, self.AI_graph, self.AI_filter,
            # ROI analyses go here ------------------------------------------
            self.counter_graph, self.squareROIAnalysis,
            # ---------------------------------------------------------------
            self.histogram_grid,self.histogramAnalysis, self.thresholdROIAnalysis,
            self.loading_filters, self.error_filters,
            self.first_measurements_filter, self.text_analysis,
            self.imageSumAnalysis, self.recent_shot_analysis,
            self.measurements_graph,
            self.iterations_graph, self.Andors,
            self.Ramsey, self.DAQmxAI, self.unlock_pause,
            self.retention_analysis, self.retention_graph,
            self.save_notes, self.counter_hist, self.origin,
            self.beam_alignment_filter
        ]

        self.properties += [
            'Config', 'functional_waveforms', 'LabView',
            'functional_waveforms_graph', 'DDS',
            'Andors', 'DAQmxAI', 'histogram_grid', 'TTL_filters', 'AI_graph',
            'AI_filter', 'NewportStage', 'loading_filters', 'error_filters',
            'first_measurements_filter', 'imageSumAnalysis',
            'recent_shot_analysis', 'histogramAnalysis',
            'retention_analysis', 'measurements_graph', 'iterations_graph',
            'retention_graph', 'Ramsey', 'counter_graph', 'counter_hist',
            'unlock_pause', 'ROI_rows', 'ROI_columns',
            'ROI_bg_rows', 'ROI_bg_columns',
            'origin', 'HPGenerators', 'thresholdROIAnalysis', 'squareROIAnalysis', 'HVcontrol', 'AutoAligner',
            'AWG', 'beam_alignment_filter'
        ]

        self.window_dict = {
            '': '',
            'Experiment': 'ExperimentPage(experiment = main.experiment, creator=main, name ="Experiment")',
            'Independent Variables': 'IndependentVariables(independentVariables = main.experiment.independentVariables, creator=main, name="Independent Variables")',
            'Constants and Dependent Vars': 'Variables(experiment = main.experiment, creator=main, name="Constants and Dependent Vars")',
            'PXI Communication': 'LabViewPage(LabView = main.experiment.LabView, creator=main, name="PXI Communication")',
            'HSDIO': 'HSDIO_DigitalOutPage(HSDIO = main.experiment.LabView.HSDIO, creator=main, name="HSDIO")',
            'DAQmx': 'DAQmxDigitalOutPage(DAQmx = main.experiment.LabView.DAQmxDO, creator=main, name="DAQmx")',
            'DAQmxAI': 'DAQmxAI(NIDAQmxAI = main.experiment.DAQmxAI, creator=main, name="DAQmxAI")',
            'DDS': 'DDS_Page(DDS = main.experiment.DDS, creator=main, name="DDS")',
            'Hamamatsu': 'CameraPage(camera = main.experiment.LabView.camera, creator=main, name="Hamamatsu")',
            'Andor Cameras': 'Andors(andors = main.experiment.Andors, creator=main, name="Andor Cameras")',
            'Blackfly Client': 'BlackflyClient(blackfly_client = main.experiment.blackfly_client, creator=main, name="Blackfly Client")',
            'Newport Translation Stage': 'NewportStage(newportstage = main.experiment.NewportStage, creator=main, name="Newport Translation Stage")',
            'Analog Output': 'AnalogOutput(AO = main.experiment.LabView.AnalogOutput, creator=main, name="Analog Output")',
            'Analog Input': 'AnalogInput(AI = main.experiment.LabView.AnalogInput, filters = main.experiment.AI_filter, analysis = main.experiment.AI_graph, creator=main, name="Analog Input")',
            'Aerotech': 'Aerotechs(aerotechs = main.experiment.aerotechs, creator=main, name="Aerotech")',
            'CONEX-CC': 'Conexes(conexes = main.experiment.conexes, creator=main, name="CONEX-CC")',
            'Live Images': 'MultiImage(experiment = main.experiment, analysis0 = main.experiment.recent_shot_analysis, analysis2 = main.experiment.imageSumAnalysis, analysis3 = main.experiment.text_analysis, creator=main, name="Live Images")',
            'Histogram Grid': 'HistogramGrid(experiment = main.experiment, analysis = main.experiment.histogram_grid, creator=main, name="Histogram Grid")',
            'Measurements Graph': 'MeasurementsGraph(experiment = main.experiment, analysis = main.experiment.measurements_graph, creator=main, name="Measurements Graph")',
            'Iterations Graph': 'IterationsGraph(experiment = main.experiment, analysis = main.experiment.iterations_graph, creator=main, name="Iterations Graph")',
            'Filters': 'Filters(experiment = main.experiment, creator=main, name="Filters")',
            'Optimization': 'Optimizer(experiment = main.experiment, analysis = main.experiment.optimizer, creator=main, name="Optimization")',
            'Counters': 'Counters(counters = main.experiment.LabView.Counters, creator=main, name="Counters")',
            'Functional Waveforms': 'FunctionalWaveforms(waveforms = main.experiment.functional_waveforms, creator=main, name="Functional Waveforms")',
            'Functional Waveforms Graph': 'FunctionalWaveformsGraph(graph = main.experiment.functional_waveforms_graph, creator=main, name="Functional Waveforms Graph")',
            'Origin Interface': 'Origin(origin = main.experiment.origin, creator=main, name="Origin Interface")',
            'HP Signal Generators': 'HPGenerators(hps = main.experiment.HPGenerators, creator=main, name="HP Signal Generators")',
            'High Voltage Controller': 'HVcontrol(ctrl = main.experiment.HVcontrol, creator=main, name="High Voltage Controller")',
            'CounterGraph': 'CounterGraph(analysis = main.experiment.counter_graph, creator=main, name="CounterGraph")',
            'CounterHistAnalysis': 'CounterHistAnalysis(analysis = main.experiment.counter_hist, creator=main, name="CounterHistAnalysis")',
            'Hybrid Auto Aligner': 'AutoAligner(ctrl = main.experiment.AutoAligner, creator=main, name="Hybrid Auto Aligner")',
            'AWG': 'AWG_Page(AWG = main.experiment.AWG, creator=main, name="AWG")'
        }

        try:
            self.allow_evaluation = False
            self.loadDefaultSettings()
            # update variables
            self.allow_evaluation = True
            self.evaluateAll()
        except PauseError:
            logger.warning('Loading default settings aborted in Hybrid.__init__().  PauseError')
        except:
            logger.exception('Loading default settings aborted in Hybrid.__init__().')

        # make sure evaluation is allowed now
        self.allow_evaluation = True

    def exiting(self):
        self.Andors.__del__()
        return
