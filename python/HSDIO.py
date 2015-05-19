"""HSDIO.py
Part of the AQuA Cesium Controller software package

author=Martin Lichtman
created=2013-10-08
modified>=2013-10-08

This file holds everything needed to model the high speed digital output from the National Instruments HSDIO card.  It communicates to LabView via the higher up LabView(Instrument) class.
"""

from __future__ import division
__author__ = 'Martin Lichtman'
import logging
logger = logging.getLogger(__name__)

from cs_errors import PauseError

from atom.api import Typed, Member
import numpy
np=numpy

from instrument_property import Prop, BoolProp, IntProp, FloatProp, StrProp, ListProp
from cs_instruments import Instrument
from digital_waveform import NumpyWaveform, NumpyChannels


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


class Waveforms(ListProp):
    '''We can't use an unmodified ListProp for this because the added children must be passed waveforms=self, which is not possible to describe in a one-line definintion.'''
    def __init__(self, experiment, digitalout):
        super(Waveforms, self).__init__('waveforms', experiment, description='Holds all the digitalout waveforms', listElementType=NumpyWaveform, listElementName='waveform', listElementKwargs={'digitalout': digitalout, 'waveforms': self})


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
    version = '2015.05.19'

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
    times = Member()  # an array of the compiled transition times
    durations = Member()  # an array of the compiled transition durations

    def __init__(self, name, experiment):
        super(HSDIO, self).__init__(name, experiment)
        self.resourceName = StrProp('resourceName', experiment, 'the hardware location of the HSDIO card', "'Dev1'")
        self.clockRate = FloatProp('clockRate', experiment, 'samples/channel/sec', '1000')
        self.units = FloatProp('units', experiment, 'multiplier for HSDIO timing values (milli=.001)', '1')
        self.hardwareAlignmentQuantum = IntProp('hardwareAlignmentQuantum', experiment, '(PXI=1,SquareCell=2)', '1')
        self.channels = NumpyChannels(experiment, self)
        self.triggers = ListProp('triggers', self.experiment, listElementType=ScriptTrigger, listElementName='trigger')
        self.startTrigger = StartTrigger(experiment)
        self.properties += ['version', 'resourceName', 'clockRate', 'units', 'hardwareAlignmentQuantum', 'triggers', 'channels', 'startTrigger']
        self.doNotSendToHardware += ['units']  # script and waveforms are handled specially in HSDIO.toHardware()
        self.transition_list=[]  # an empty list to store

    def evaluate(self):
        if self.enable and self.experiment.allow_evaluation:
            logger.debug('functional_HSDIO.evaluate()')
            self.parse_transition_list()
            # reset the transition list so it starts empty for the next usage
            self.transition_list = []
            return super(HSDIO, self).evaluate()

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
        # put all the transitions that have been stored together into one big list
        # convert the float time to an integer number of samples
        times = numpy.rint(np.array([i[0] for i in self.transition_list], dtype=np.float64)*self.clockRate.value*self.units.value).astype(numpy.uint64)
        # compile the channels
        channels = np.array([i[1] for i in self.transition_list], dtype=uint8)
        # compile the states
        states = np.array([for i in self.transition_list], dtype=np.bool)

        #transitions = np.array([() for i in self.transition_list], dtype=[('time', np.uint64), ('channel', np.uint32), ('state', numpy.bool)])

        # Create two arrays to store the compiled times and states.
        # These arrays will be appended to to increase their size as we go along.
        time_list = np.zeros(1, dtype=np.uint64)
        state_list = np.zeros((1, self.numChannels), dtype=np.bool)

        # sort the transitions time.  If there is a tie, preserve the order.
        # mergesort is slower than the default quicksort, but it is 'stable' which means items of the same value are kept in their relative order, which is desired here
        order = numpy.argsort(times, kind='mergesort')

        # go through all the transitions, updating the compiled sequence as we go
        for i in order:
            # check to see if the next time is the same as the last one in the time list
            if times[i] == time_list[-1]:
                # if this is a duplicate time, the latter entry overrides
                state_list[-1][channels[i]] = state[i]
            else:
                # If this is a new time, increase the length of time_list and state_list.
                # Create the new state_list entry by copying the last entry.
                time_list = np.append(time_list, times[i])
                state_list.append(state_list[-1, np.newaxis], axis=0)
                # then update the last entry
                state_list[-1, channels[i]] = states[i]

        # find the duration of each segment
        durations = np.empty_like(time_list)
        durations[:-1] = time_list[1:]-time_list[:-1]
        durations[-1] = 1  # add in a 1 sample duration at end for last transition

        #update the exposed variables
        self.times = time_list
        self.states = state_list
        self.durations = durations

    def toHardware(self):
        """
        This overrides Instrument.toHardware() in order to accommodate the compiled way that scripts are specified
        (a la the former 'compressedGenerate').  The script is created based on self.times and self.states.
        A waveform is created for every transition.  These waveforms are only 1 sample long (or as long as necessary to
        satisfy hardwareAlignmentQuantum).  The timing is specified by placing 'wait' commands between these 1 sample
        waveforms.
        Only the necessary waveforms are created and passed to the HSDIO hardware.
        """

        #build dictionary of waveforms keyed on waveform name
        waveformsInUse = []

        script = ''
        waveformXML=''

        #go through each transition
        for i in xrange(len(self.times)):
            # for each transition, replace with a sequence of generate wXXXXXXXX, if wXXXXXXXX not in list, add wXXXXXXXX to list of necessary waveforms, create waveform and add it to waveform XML
            singleSampleWaveformName = 'w'+''.join([str(int(j)) for j in self.states[i]])  # make a name for the waveform.  the name is w followed by the binary expression of the state
            script += 'generate '+singleSampleWaveformName+'\n'
            waitTime = self.durations[i]-self.hardwareAlignmentQuantum.value
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

        # then upload scriptOut instead of script.toHardware, waveformXML instead of waveforms.toHardware (those toHardware methods will return an empty string and so will not interfere)
        # then process the rest of the properties as usual
        return '<HSDIO><script>{}</script>\n<waveforms>{}</waveforms>\n'.format(script, waveformXML)+super(npHSDIO,self).toHardware()[7:]  # [7:] removes the <HSDIO> on what is returned from super.toHardware
