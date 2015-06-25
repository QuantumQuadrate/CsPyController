"""HSDIO.py
Part of the AQuA Cesium Controller software package

author=Martin Lichtman
created=2013-10-08
modified>=2015-05-24

This file holds everything needed to model the high speed digital output from the National Instruments HSDIO card.  It communicates to LabView via the higher up LabView(Instrument) class.
"""

from __future__ import division
__author__ = 'Martin Lichtman'
import logging
logger = logging.getLogger(__name__)

from cs_errors import PauseError

from atom.api import Typed, Member, Int
import numpy as np

from instrument_property import Prop, BoolProp, IntProp, FloatProp, StrProp, ListProp
from cs_instruments import Instrument
from digital_waveform import NumpyChannels


class ScriptTrigger(Prop):
    id = Typed(StrProp)
    source = Typed(StrProp)
    type = Typed(StrProp)
    edge = Typed(StrProp)
    level = Typed(StrProp)
    
    def __init__(self, name, experiment, description=''):
        super(ScriptTrigger, self).__init__('trigger', experiment, description)
        self.id = StrProp('id', experiment, '', '"ScriptTrigger0"')
        self.source = StrProp('source', experiment, '', '"PFI0"')
        self.type = StrProp('type', experiment, '', '"edge"')
        self.edge = StrProp('edge', experiment, '', '"rising"')
        self.level = StrProp('level', experiment, '', '"high"')
        self.properties += ['id', 'source', 'type', 'edge', 'level']


class StartTrigger(Prop):
    waitForStartTrigger = Typed(BoolProp)
    source = Typed(StrProp)
    edge = Typed(StrProp)
    
    def __init__(self, experiment):
        super(StartTrigger, self).__init__('startTrigger', experiment)
        self.waitForStartTrigger = BoolProp('waitForStartTrigger', experiment, 'HSDIO wait for start trigger', 'False')
        self.source = StrProp('source', experiment, 'start trigger source', '"PFI0"')
        self.edge = StrProp('edge', experiment, 'start trigger edge', '"rising"')
        self.properties += ['waitForStartTrigger', 'source', 'edge']


class HSDIO(Instrument):
    """A version of the HSDIO instrument that uses functionally defined waveforms."""
    version = '2015.05.24'

    numChannels = Int(32)
    resourceName = Member()
    clockRate = Member()
    units = Member()
    hardwareAlignmentQuantum = Member()
    waveforms = Member()
    channels = Member()
    triggers = Member()
    startTrigger = Member()

    # properties for functional waveforms
    transition_list = Member()  # list that will store the transitions as they are added
    states = Member()  # an array of the compiled transition states
    indices = Member()  # an array of the compiled transition indices
    times = Member()  # an array of the compiled transition times
    index_durations = Member()  # an array of the compiled transition durations (in terms of indexes)
    time_durations = Member()  # an array of compiled transition durations (in terms of time)

    def __init__(self, name, experiment):
        super(HSDIO, self).__init__(name, experiment)
        self.resourceName = StrProp('resourceName', experiment, 'the hardware location of the HSDIO card', "'Dev1'")
        self.clockRate = FloatProp('clockRate', experiment, 'samples/channel/sec', '1000')
        self.units = FloatProp('units', experiment, 'multiplier for HSDIO timing values (milli=.001)', '1')
        self.hardwareAlignmentQuantum = IntProp('hardwareAlignmentQuantum', experiment, '(PXI=1,SquareCell=2)', '1')
        self.channels = NumpyChannels(experiment, self)
        self.triggers = ListProp('triggers', self.experiment, listElementType=ScriptTrigger, listElementName='trigger')
        self.startTrigger = StartTrigger(experiment)
        self.properties += ['version', 'resourceName', 'clockRate', 'units', 'hardwareAlignmentQuantum', 'triggers',
                            'channels', 'startTrigger', 'numChannels']
        self.doNotSendToHardware += ['units']  # script and waveforms are handled specially in HSDIO.toHardware()
        self.transition_list=[]  # an empty list to store

    def evaluate(self):
        if self.enable and self.experiment.allow_evaluation:
            logger.debug('HSDIO.evaluate()')
            super(HSDIO, self).evaluate()
            self.parse_transition_list()
            # reset the transition list so it starts empty for the next usage
            self.transition_list = []

    def add_transition(self, time, channel, state):
        """Append a transition to the list of transitions.  The values are not processed until evaluate is called.
        Generally the master functional waveform instrument should evaluate before HSDIO evaluates.
        :param time: float.  Absolute time since the HSDIO was triggered, in the units specified by self.units
        :param channel: int.  The channel number to change.
        :param state: bool.  Should the channel go high  (True) or low (False) at this time?
        :return: Nothing.
        """
        self.transition_list.append((time, channel, state))

    def parse_transition_list(self):
        if self.transition_list:
            # put all the transitions that have been stored together into one big list
            # convert the float time to an integer number of samples
            indices = np.rint(np.array([i[0] for i in self.transition_list], dtype=np.float64)*self.clockRate.value*self.units.value).astype(np.uint64)
            # compile the channels
            channels = np.array([i[1] for i in self.transition_list], dtype=np.uint8)
            # compile the states
            states = np.array([i[2] for i in self.transition_list], dtype=np.bool)

            # Create two arrays to store the compiled times and states.
            # These arrays will be appended to to increase their size as we go along.
            index_list = np.zeros(1, dtype=np.uint64)
            state_list = np.zeros((1, self.numChannels), dtype=np.bool)

            # sort the transitions time.  If there is a tie, preserve the order.
            # mergesort is slower than the default quicksort, but it is 'stable' which means items of the same value are kept in their relative order, which is desired here
            order = np.argsort(indices, kind='mergesort')

            # go through all the transitions, updating the compiled sequence as we go
            for i in order:
                # check to see if the next time is the same as the last one in the time list
                if indices[i] == index_list[-1]:
                    # if this is a duplicate time, the latter entry overrides
                    state_list[-1][channels[i]] = states[i]
                else:
                    # If this is a new time, increase the length of time_list and state_list.
                    # Create the new state_list entry by copying the last entry.
                    index_list = np.append(index_list, indices[i])
                    state_list = np.append(state_list, state_list[-1, np.newaxis], axis=0)
                    # then update the last entry
                    state_list[-1, channels[i]] = states[i]

            # find the duration of each segment
            durations = np.empty_like(index_list)
            durations[:-1] = index_list[1:]-index_list[:-1]
            durations[-1] = 1  # add in a 1 sample duration at end for last transition

            # find the real time at each index (used for plotting)
            # send values in seconds, do not use units, so that the plot can apply its own units
            self.times = 1.0*index_list/self.clockRate.value
            self.time_durations = 1.0*durations/self.clockRate.value

            #update the exposed variables
            self.indices = index_list
            self.states = state_list
            self.index_durations = durations
        else:
            self.times = np.zeros(0, dtype=np.float64)
            self.time_durations = np.zeros(0, dtype=np.float64)
            self.indices = np.zeros(0, dtype=np.uint64)
            self.states = np.zeros((0, self.numChannels), dtype=np.bool)
            self.index_durations = np.zeros_like(self.indices)

    def toHardware(self):
        """
        This overrides Instrument.toHardware() in order to accommodate the compiled way that scripts are specified
        (a la the former 'compressedGenerate').  The script is created based on self.times and self.states.
        A waveform is created for every transition.  These waveforms are only 1 sample long (or as long as necessary to
        satisfy hardwareAlignmentQuantum).  The timing is specified by placing 'wait' commands between these 1 sample
        waveforms.
        Only the necessary waveforms are created and passed to the HSDIO hardware.
        """

        if self.enable:
            #build dictionary of waveforms keyed on waveform name
            waveformsInUse = []

            script = 'script script1\n'
            waveformXML=''

            #go through each transition
            for i in xrange(len(self.indices)):
                # for each transition, replace with a sequence of generate wXXXXXXXX, if wXXXXXXXX not in list, add wXXXXXXXX to list of necessary waveforms, create waveform and add it to waveform XML
                singleSampleWaveformName = 'w'+''.join([str(int(j)) for j in self.states[i]])  # make a name for the waveform.  the name is w followed by the binary expression of the state
                script += 'generate '+singleSampleWaveformName+'\n'
                waitTime = self.index_durations[i]-self.hardwareAlignmentQuantum.value
                if waitTime > 0:  # if we need to wait after this sample to get the correct time delay
                    if waitTime % self.hardwareAlignmentQuantum.value != 0:  # if the wait time is not a multiple of the hardwareAlignmentQuantum
                        waitTime = (int(waitTime/self.hardwareAlignmentQuantum.value)+1)*self.hardwareAlignmentQuantum.value  # round up
                        script += int(waitTime/536870912)*'wait 536870912\n'  # the HSDIO card cannot handle a wait value longer than this, so we repeat it as many times as necessary
                        script += 'wait '+str(int(waitTime % 536870912))+'\n'  # add the remaining wait
                if not singleSampleWaveformName in waveformsInUse:
                    # add waveform to those to be transferred to LabView
                    waveformsInUse += [singleSampleWaveformName]
                    # don't create a real waveform object, just its toHardware signature
                    waveformXML += ('<waveform>'+
                        '<name>'+singleSampleWaveformName+'</name>' +
                        '<transitions>'+' '.join([str(time) for time in range(self.hardwareAlignmentQuantum.value)])+'</transitions>'+  # make as many time points as the minimum necessary for hardware
                        '<states>'+'\n'.join([' '.join([str(sample) for sample in self.states[i]]) for time in range(self.hardwareAlignmentQuantum.value)])+'</states>\n' +
                        '</waveform>\n')
            script += 'end script\n'

            # then upload scriptOut instead of script.toHardware, waveformXML instead of waveforms.toHardware (those toHardware methods will return an empty string and so will not interfere)
            # then process the rest of the properties as usual
            return '<HSDIO><script>{}</script>\n<waveforms>{}</waveforms>\n'.format(script, waveformXML)+super(HSDIO, self).toHardware()[7:]  # [7:] removes the <HSDIO> on what is returned from super.toHardware
        else:
            # let Instrument.toHardware send <name><enable>False</enable><name>
            return super(HSDIO, self).toHardware()