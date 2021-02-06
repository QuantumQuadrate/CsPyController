from __future__ import division
import logging

from cs_errors import PauseError
from atom.api import Member, Int

# Bring in other files in this package
import functional_waveforms
from functional_waveforms import FunctionalWaveformGraph
import analysis
import TTL
import LabView
import DDS
import andor
import AnalogInput
import Counter
import nidaq_ai
logger = logging.getLogger(__name__)
import origin_interface
import FakeInstrument  # for testing


# analyses
from threshold_analysis import ThresholdROIAnalysis
from retention_analysis import RetentionAnalysis, RetentionGraph
from histogram_analysis import HistogramAnalysis, HistogramGrid

from experiments import Experiment


class FNODE(Experiment):
    """A subclass of Experiment which knows about all our particular hardware"""

    window_dict = Member()

    Andors = Member()
    DAQmxAI = Member()
    LabView = Member()
    DDS = Member()
    Embezzletron = Member()

    functional_waveforms_graph = Member()
    TTL_filters = Member()
    AI_graph = Member()
    AI_filter = Member()
    thresholdROIAnalysis = Member()
    loading_filters = Member()
    error_filters = Member()
    first_measurements_filter = Member()
    histogramAnalysis = Member()
    measurements_graph = Member()
    retention_graph = Member()
    retention_analysis = Member()
    counter_graph = Member()
    counter_hist = Member()
    origin = Member()
    ROI_rows = Int(3)
    ROI_columns = Int(1)
    ROI_bg_rows = Int(1)
    ROI_bg_columns = Int(1)
    Ramsey = Member()

    def __init__(self,
                 config_instrument=None,
                 cache_location=None,
                 settings_location=None,
                 temp_location=None):

        super(FNODE, self).__init__(config_instrument=config_instrument,
                                    cache_location=cache_location,
                                    settings_location=settings_location,
                                    temp_location=temp_location)
        self.Andors = andor.Andors(
            name='Andors',
            experiment=self,
            description='Andor Luca measurementResults')
        self.DAQmxAI = nidaq_ai.NIDAQmxAI(
            name='DAQmxAI',
            experiment=self,
            description='NI-DAQmx Analog Input')
        self.LabView = LabView.LabView(self)
        self.DDS = DDS.DDS(name='DDS',
                           experiment=self,
                           description='server for homemade DDS boxes')
        self.Embezzletron = FakeInstrument.Embezzletron(
            name='Embezzletron',
            experiment=self,
            description='Fake instrument that reports random data for testing')
        # do not include functional_waveforms in self.instruments because it
        # need not start/stop
        self.instruments += [
            self.Andors, self.DDS, self.Embezzletron,
        ]
        # Labview must be last at least until someone fixes the start command
        self.instruments += [self.LabView]

        # analyses
        self.functional_waveforms_graph = FunctionalWaveformGraph(
            name='functional_waveform_graph',
            experiment=self,
            description='Graph the HSDIO, DAQmx DO, and DAQmx AO settings')
        self.TTL_filters = TTL.TTL_filters(name='TTL_filters', experiment=self)
        self.AI_graph = AnalogInput.AI_Graph(
            name='AI_graph',
            experiment=self,
            description='Analog Input Graph')
        self.AI_filter = AnalogInput.AI_Filter(
            name='AI_filter',
            experiment=self,
            description='Analog Input filter')
        self.first_measurements_filter = analysis.DropFirstMeasurementsFilter(
            name='first_measurements_filter',
            experiment=self,
            description='drop the first N measurements')
        self.counter_graph = Counter.CounterAnalysis(
            name='counter_graph',
            experiment=self,
            description='Graphs the counter data after each measurement.')
        self.thresholdROIAnalysis = ThresholdROIAnalysis(self)
        self.loading_filters = analysis.LoadingFilters(
            name='loading_filters',
            experiment=self,
            description='drop measurements with no atom loaded')
        self.error_filters = analysis.LoadingFilters(
            name='error_filters',
            experiment=self,
            description='drop measurements with errors using roi input')
        self.histogramAnalysis = HistogramAnalysis(
            name='histogramAnalysis',
            experiment=self,
            description='plot the histogram of any shot and roi')
        self.measurements_graph = analysis.MeasurementsGraph(
            name='measurements_graph',
            experiment=self,
            description='plot the ROI sum vs all measurements')
        self.retention_graph = RetentionGraph(
            name='retention_graph',
            experiment=self,
            description='plot occurence of binary result (i.e. whether or not'
                        ' atoms are there in the 2nd shot)')
        self.Ramsey = analysis.Ramsey(
            name='Ramsey',
            experiment=self,
            description='Fit a cosine to retention results')
        self.retention_analysis = RetentionAnalysis(
            name='retention_analysis',
            experiment=self,
            description='calculate the loading and retention')
        self.counter_hist = Counter.CounterHistogramAnalysis(
            name='counter_hist',
            experiment=self,
            description='Fits histograms of counter data and plots hist and '
                        'fits.')
        self.origin = origin_interface.Origin(
            name='origin',
            experiment=self,
            description='saves selected data to the origin data server')

        # do not include functional_waveforms_graph in self.analyses because it
        # need not update on iterations, etc.
        # origin needs to be the last analysis always
        self.analyses += [
            self.TTL_filters, self.AI_graph, self.AI_filter,
            # ROI analyses go here ------------------------------------------
            self.counter_graph,  self.thresholdROIAnalysis,
            # ---------------------------------------------------------------
            self.histogramAnalysis,
            self.loading_filters, self.error_filters,
            self.first_measurements_filter,
            self.measurements_graph,
            self.Andors,
            self.Ramsey, self.DAQmxAI,
            self.retention_analysis, self.retention_graph,
            self.counter_hist,
            self.origin  # origin has to be last
        ]

        self.properties += [
            'Config', 'functional_waveforms', 'LabView',
            'functional_waveforms_graph', 'DDS',
            'Andors',
            'DAQmxAI',
            'thresholdROIAnalysis',
            'TTL_filters', 'AI_graph',
            'AI_filter', 'loading_filters', 'error_filters',
            'first_measurements_filter', 'histogramAnalysis',
            'retention_analysis', 'measurements_graph',
            'retention_graph',
            'Ramsey', 'counter_graph', 'counter_hist',
            'ROI_rows', 'ROI_columns', 'ROI_bg_rows', 'ROI_bg_columns',
            'origin'
        ]

        # You can specify your own combo box menu by taking the default
        # dictionary from cs_GUI.enaml and pasting it here, removing undesired
        # entries.
        self.window_dict = {
            '': '',
            'Experiment': 'ExperimentPage(experiment = main.experiment, creator = main, name = "Experiment")',
            'Independent Variables': 'IndependentVariables(independentVariables = main.experiment.independentVariables, creator = main, name = "Independent Variables")',
            'Constants and Dependent Vars': 'Variables(experiment = main.experiment, creator = main, name = "Constants and Dependent Vars")',
            'PXI Communication': 'LabViewPage(LabView = main.experiment.LabView, creator = main, name = "PXI Communication")',
            'HSDIO': 'HSDIO_DigitalOutPage(HSDIO = main.experiment.LabView.HSDIO, creator = main, name = "HSDIO")',
            'DAQmx': 'DAQmxDigitalOutPage(DAQmx = main.experiment.LabView.DAQmxDO, creator = main, name = "DAQmx")',
            'DAQmxAI': 'DAQmxAI(NIDAQmxAI = main.experiment.DAQmxAI, creator = main, name = "DAQmxAI")',
            'DDS': 'DDS_Page(DDS = main.experiment.DDS, creator = main, name = "DDS")',
            'RF Generators': 'RFGenPage(LabView = main.experiment.LabView, creator = main, name = "RF Generators")',
            'Andor Cameras': 'Andors(andors = main.experiment.Andors, creator = main, name = "Andor Cameras")',
            'Analog Output': 'AnalogOutput(AO = main.experiment.LabView.AnalogOutput, creator = main, name = "Analog Output")',
            'Analog Input': 'AnalogInput(AI = main.experiment.LabView.AnalogInput, filters = main.experiment.AI_filter, analysis = main.experiment.AI_graph, creator = main, name = "Analog Input")',
            'Threshold ROI': 'ThresholdROIContainer(experiment = main.experiment, analysis = main.experiment.thresholdROIAnalysis, creator = main, name = "Threshold ROI")',
            'Histogram': 'Histogram(experiment = main.experiment, analysis = main.experiment.histogramAnalysis, creator = main, name = "Histogram")',
            'Measurements Graph': 'MeasurementsGraph(experiment = main.experiment, analysis = main.experiment.measurements_graph, creator = main, name = "Measurements Graph")',
            'Retention Graph': 'RetentionGraph(experiment = main.experiment, analysis = main.experiment.retention_graph, creator = main, name = "Retention Graph")',
            'Filters': 'Filters(experiment = main.experiment, creator = main, name = "Filters")',
            'Optimization': 'Optimizer(experiment = main.experiment, analysis = main.experiment.optimizer, creator = main, name = "Optimization")',
            'Ramsey': 'Ramsey(analysis = main.experiment.Ramsey, creator = main, name = "Ramsey")',
            'Retention Analysis': 'RetentionAnalysis(analysis = main.experiment.retention_analysis, creator = main, name = "Retention Analysis")',
            'Counters': 'Counters(counters = main.experiment.LabView.Counters, creator = main, name = "Counters")',
            'Functional Waveforms': 'FunctionalWaveforms(waveforms = main.experiment.functional_waveforms, creator = main, name = "Functional Waveforms")',
            'Functional Waveforms Graph': 'FunctionalWaveformsGraph(graph = main.experiment.functional_waveforms_graph, creator = main, name = "Functional Waveforms Graph")',
            'CounterGraph': 'CounterGraph(analysis = main.experiment.counter_graph, creator = main, name = "CounterGraph")',
            'CounterHistAnalysis': 'CounterHistAnalysis(analysis = main.experiment.counter_hist, creator = main, name = "CounterHistAnalysis")',
            'Origin Interface': 'Origin(origin = main.experiment.origin, creator = main, name = "Origin Interface")',
                             }

        try:
            self.allow_evaluation = False
            self.loadDefaultSettings()
            # update variables
            self.allow_evaluation = True
            self.evaluateAll()
        except PauseError:
            logger.warning('Loading default settings aborted in '
                           'FNODE.__init__().  PauseError')
        except Exception:
            logger.exception('Loading default settings aborted in '
                             'FNODE.__init__().')

        # make sure evaluation is allowed now
        self.allow_evaluation = True

    def exiting(self):
        """
        Clean-up that should be performed whenever CsPy closes.
        """
        self.Andors.__del__()
        return
