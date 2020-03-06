from __future__ import division
import logging

from cs_errors import PauseError
from atom.api import Member

# Bring in other files in this package
import functional_waveforms, LabView
import DDS
import andor, picampython, AnalogInput
import unlock_pause, nidaq_ai
import analysis
logger = logging.getLogger(__name__)

from experiments import Experiment


class HOLMIUM(Experiment):
    """A subclass of Experiment which knows about all our particular hardware"""

    Andors = Member()
    DAQmxAI = Member()
    PICams = Member()
    LabView = Member()
    DDS = Member()
    unlock_pause = Member()

    functional_waveforms = Member()
    functional_waveforms_graph = Member()
    AI_graph = Member()
    AI_filter = Member()
    picam_viewer = Member()
    Ramsey = Member()
    window_dict = Member()

    def __init__(self,
                 config_instrument=None,
                 cache_location=None,
                 settings_location=None,
                 temp_location=None):

        super(HOLMIUM, self).__init__(config_instrument=config_instrument,
                                   cache_location=cache_location,
                                   settings_location=settings_location,
                                   temp_location=temp_location)

        self.functional_waveforms = functional_waveforms.FunctionalWaveforms('functional_waveforms', self, 'Waveforms for HSDIO, DAQmx DIO, and DAQmx AO; defined as functions')
        self.Andors = andor.Andors('Andors', self, 'Andor Luca measurementResults')
        self.PICams = picampython.PICams('PICams', self, 'Princeton Instruments Cameras')
        self.DAQmxAI = nidaq_ai.NIDAQmxAI('DAQmxAI', self, 'NI-DAQmx Analog Input')
        self.LabView = LabView.LabView(self)
        self.DDS = DDS.DDS('DDS', self, 'server for homemade DDS boxes')
        self.unlock_pause = unlock_pause.UnlockMonitor('unlock_pause', self, 'Monitor for pausing when laser unlocks')
        # do not include functional_waveforms in self.instruments because it
        # need not start/stop
        self.instruments += [
            self.Andors, self.PICams, self.DDS, self.unlock_pause
        ]
        # Labview must be last at least until someone fixes the start command
        self.instruments += [self.LabView]

        # analyses
        self.functional_waveforms_graph = functional_waveforms.FunctionalWaveformGraph('functional_waveform_graph', self, 'Graph the HSDIO, DAQmx DO, and DAQmx AO settings')
        self.AI_graph = AnalogInput.AI_Graph('AI_graph', self, 'Analog Input Graph')
        self.AI_filter = AnalogInput.AI_Filter('AI_filter', self, 'Analog Input filter')
        self.Ramsey = analysis.Ramsey('Ramsey', self,
                                      'Fit a cosine to retention results')

        # do not include functional_waveforms_graph in self.analyses because it
        # need not update on iterations, etc.
        # origin needs to be the last analysis always
        self.analyses += [
            self.AI_graph, self.AI_filter, self.Ramsey
        ]

        self.properties += [
            'Config', 'functional_waveforms', 'LabView',
            'functional_waveforms_graph', 'DDS', 'Andors', 'PICams', 'DAQmxAI',
            'unlock_pause', 'AI_graph', 'AI_filter', 'Ramsey'
        ]

        self.window_dict = {
            '':'',
            'Experiment': 'ExperimentPage(experiment = main.experiment, creator=main, name ="Experiment")',
            'Independent Variables': 'IndependentVariables(independentVariables = main.experiment.independentVariables, creator=main, name="Independent Variables")',
            'Constants and Dependent Vars': 'Variables(experiment = main.experiment, creator=main, name="Constants and Dependent Vars")',
            'PXI Communication': 'LabViewPage(LabView = main.experiment.LabView, creator=main, name="PXI Communication")',
            'HSDIO': 'HSDIO_DigitalOutPage(HSDIO = main.experiment.LabView.HSDIO, creator=main, name="HSDIO")',
            'DAQmx': 'DAQmxDigitalOutPage(DAQmx = main.experiment.LabView.DAQmxDO, creator=main, name="DAQmx")',
            'DAQmxAI': 'DAQmxAI(NIDAQmxAI = main.experiment.DAQmxAI, creator=main, name="DAQmxAI")',
            'DDS': 'DDS_Page(DDS = main.experiment.DDS, creator=main, name="DDS")',
            'Andor Cameras': 'Andors(andors = main.experiment.Andors, creator=main, name="Andor Cameras")',
            'Princeton Instruments Camera': 'PICams(picams = main.experiment.PICams, creator=main, name="Princeton Instruments Camera")',
            'Analog Output': 'AnalogOutput(AO = main.experiment.LabView.AnalogOutput, creator=main, name="Analog Output")',
            'Analog Input': 'AnalogInput(AI = main.experiment.LabView.AnalogInput, filters = main.experiment.AI_filter, analysis = main.experiment.AI_graph, creator=main, name="Analog Input")',
            'Optimization': 'Optimizer(experiment = main.experiment, analysis = main.experiment.optimizer, creator=main, name="Optimization")',
            'Functional Waveforms': 'FunctionalWaveforms(waveforms = main.experiment.functional_waveforms, creator=main, name="Functional Waveforms")',
            'Functional Waveforms Graph': 'FunctionalWaveformsGraph(graph = main.experiment.functional_waveforms_graph, creator=main, name="Functional Waveforms Graph")',
            'Pi Lock Monitor': 'Unlock_Pause(unlock_pause = main.experiment.unlock_pause, creator=main, name="Pi Lock Monitor")',
        }

        try:
            self.allow_evaluation = False
            self.loadDefaultSettings()
            # update variables
            self.allow_evaluation = True
            self.evaluateAll()
        except PauseError:
            logger.warning('Loading default settings aborted in AQuA.__init__().  PauseError')
        except:
            logger.exception('Loading default settings aborted in AQuA.__init__().')

        # make sure evaluation is allowed now
        self.allow_evaluation = True

    def exiting(self):
        self.PICams.__del__()
        self.Andors.__del__()
        return
