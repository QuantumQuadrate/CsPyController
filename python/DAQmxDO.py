"""
DAQmxDO.py
Part of the AQuA Cesium Controller software package

author=Martin Lichtman
created=2013-10-19
modified>=2015-05-24

This file holds everything to model a National Instruments DAQmx pulse output.  It communicated to LabView via the higher up LabView class.
"""

from __future__ import division
__author__ = 'Martin Lichtman'
import logging
logger = logging.getLogger(__name__)


import numpy as np
from atom.api import Typed, Member, Int

from cs_instruments import Instrument
from instrument_property import Prop, BoolProp, IntProp, FloatProp, StrProp, EnumProp
from digital_waveform import NumpyChannels


class StartTrigger(Prop):
    waitForStartTrigger = Typed(BoolProp)
    source = Typed(StrProp)
    edge = Typed(EnumProp)
    
    def __init__(self, experiment):
        super(StartTrigger, self).__init__('startTrigger', experiment)
        self.waitForStartTrigger = BoolProp('waitForStartTrigger', experiment, 'wait for start trigger', 'False')
        self.source = StrProp('source', experiment, 'start trigger source', '"PFI0"')
        self.edge = EnumProp('edge', experiment, 'start trigger edge', '"rising"', ["rising", "falling"])
        self.properties += ['waitForStartTrigger', 'source', 'edge']


class DAQmxDO(Instrument):
    version = '2015.05.24'
    resourceName = Typed(StrProp)
    clockRate = Typed(FloatProp)
    units = Typed(FloatProp)
    hardwareAlignmentQuantum = Typed(IntProp)
    channels = Member()
    triggers = Member()
    startTrigger = Member()
    numChannels = Int(8)

    # properties for functional waveforms
    transition_list = Member()  # list that will store the transitions as they are added
    states = Member()  # an array of the compiled transition states
    indices = Member()  # an array of the compiled transitions times (in samples indexes)
    times = Member()  # an array of the compiled transition times (in seconds, for plotting)
    time_durations = Member()  # an array of the compiled transition durations (in seconds, for plotting)

    def __init__(self, experiment):
        super(DAQmxDO, self).__init__('DAQmxDO', experiment)
        self.resourceName = StrProp('resourceName', experiment, 'the hardware location of the card', "'Dev1'")
        self.clockRate = FloatProp('clockRate', experiment, 'samples/channel/sec', '1000')
        self.units = FloatProp('units', experiment, 'multiplier for timing values (milli=.001)', '1')
        self.channels = NumpyChannels(experiment, self)
        self.startTrigger = StartTrigger(experiment)
        self.properties += ['version', 'resourceName', 'clockRate', 'units', 'channels', 'startTrigger', 'numChannels']
        # the number of channels is defined by the resourceName (and the waveform which must agree), so
        # channels need not be send to hardware
        self.doNotSendToHardware += ['units', 'channels']
        self.transition_list = []

    def evaluate(self):
        if self.experiment.allow_evaluation:
            logger.debug('DAQmxDO.evaluate()')
            return super(DAQmxDO, self).evaluate()

    def evaluate(self):
        if self.enable and self.experiment.allow_evaluation:
            logger.debug('DAQmxDO.evaluate()')
            super(DAQmxDO, self).evaluate()
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
                    state_list[-1][channels[i]] = state[i]
                else:
                    # If this is a new time, increase the length of time_list and state_list.
                    # Create the new state_list entry by copying the last entry.
                    index_list = np.append(index_list, indices[i])
                    state_list.append(state_list[-1, np.newaxis], axis=0)
                    # then update the last entry
                    state_list[-1, channels[i]] = states[i]

            # find the duration of each segment
            durations = np.empty_like(index_list)
            durations[:-1] = index_list[1:]-index_list[:-1]
            durations[-1] = 1  # add in a 1 sample duration at end for last transition

            # find the real time at each index (used for plotting)
            # leave this in seconds, don't use units so that the plot can apply its own units
            self.times = 1.0*index_list/self.clockRate.value
            self.time_durations = 1.0*durations/self.clockRate.value

            # update the exposed variables
            self.indices = index_list
            self.states = state_list
        else:
            self.times = np.zeros(0, dtype=np.float64)
            self.time_durations = np.zeros(0, dtype=np.float64)
            self.indices = np.zeros(0, dtype=np.uint64)
            self.states = np.zeros((0, self.numChannels), dtype=np.bool)

    def toHardware(self):
        if self.enable:
            waveformXML = ('<waveform>'+
                '<name>'+self.name+'</name>'+
                '<transitions>'+' '.join([str(time) for time in self.indices])+'</transitions>'+
                '<states>'+'\n'.join([' '.join([str(sample) for sample in state]) for state in self.states])+'</states>\n'+
                '</waveform>\n')

            # then upload scriptOut instead of script.toHardware, waveformXML instead of waveforms.toHardware (those toHardware methods will return an empty string and so will not interfere)
            # then process the rest of the properties as usual
            return '<DAQmxDO>{}\n'.format(waveformXML)+super(DAQmxDO, self).toHardware()[9:]  # [9:] removes the <DAQmxDO> on what is returned from super.toHardware
        else:
            # let Instrument.toHardware send <name><enable>False</enable><name>
            return super(DAQmxDO, self).toHardware()
