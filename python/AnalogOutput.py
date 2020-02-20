"""AnalogOutput.py
Part of the AQuA Cesium Controller software package

author=Martin Lichtman
created=2013-10-24
modified>=2013-10-24

This file holds everything needed to model the analog output from a National Instruments HSDIO card.  It communicates to LabView via the higher up LabView(Instrument) class.
"""

from __future__ import division
__author__ = 'Martin Lichtman'
import logging
logger = logging.getLogger(__name__)

from cs_errors import PauseError

from atom.api import Typed, Member, Int, Str
from instrument_property import BoolProp, FloatProp, StrProp
from cs_instruments import Instrument
import numpy as np


class AnalogOutput(Instrument):
    version = '2015.06.29'

    physicalChannels = Typed(StrProp)
    minimum = Typed(FloatProp)
    maximum = Typed(FloatProp)
    clockRate = Typed(FloatProp)
    units = Typed(FloatProp)
    waitForStartTrigger = Typed(BoolProp)
    triggerSource = Typed(StrProp)
    triggerEdge = Typed(StrProp)
    exportStartTrigger = Typed(BoolProp)
    exportStartTriggerDestination = Typed(StrProp)
    useExternalClock = Typed(BoolProp)
    externalClockSource = Typed(StrProp)
    maxExternalClockRate = Typed(FloatProp)
    channel_descriptions = Str('[]')
    numChannels = Int(6)

    # properties for functional waveforms
    transition_list = Member()  # list that will store the transitions as they are added
    values = Member()  # an array of the compiled transition values
    times = Member()  # an array of the compiled transition times
    transitions = Member()

    def __init__(self, experiment):
        super(AnalogOutput, self).__init__('AnalogOutput', experiment)
        self.enable = False
        self.physicalChannels = StrProp('physicalChannels', self.experiment, '', '"PXI1Slot2/ao0:7"')
        self.minimum = FloatProp('minimum', self.experiment, '', '-10')
        self.maximum = FloatProp('maximum', self.experiment, '', '10')
        self.clockRate = FloatProp('clockRate', self.experiment, '', '1000.0')
        self.units = FloatProp('units', self.experiment, 'equations entered in ms', '.001')
        self.waitForStartTrigger = BoolProp('waitForStartTrigger', self.experiment, '', 'True')
        self.triggerSource = StrProp('triggerSource', self.experiment, '', '"/PXI1Slot2/PFI0"')
        self.triggerEdge = StrProp('triggerEdge', self.experiment, '', '"Rising"')
        self.exportStartTrigger = BoolProp('exportStartTrigger', self.experiment, 'Should we trigger all other cards off the AO card?','True')
        self.exportStartTriggerDestination = StrProp('exportStartTriggerDestination', self.experiment, 'What line to send the AO StartTrigger out to?', '"/PXISlot2/PXI_Trig0"')
        self.useExternalClock = BoolProp('useExternalClock', self.experiment, 'True for external clock, false for default clock.', 'False')
        self.externalClockSource = StrProp('externalClockSource', self.experiment, 'Where does the external clock come in?','"/PXISlot2/PFI9"')
        self.maxExternalClockRate = FloatProp('maxExternalClockRate', self.experiment, 'Upper limit on the external clock. Does not have to be exact.', '2000000')

        self.properties += ['version', 'physicalChannels', 'numChannels', 'minimum', 'maximum', 'clockRate', 'units',
                            'waitForStartTrigger', 'triggerSource', 'triggerEdge', 'exportStartTrigger',
                            'exportStartTriggerDestination', 'useExternalClock', 'externalClockSource',
                            'maxExternalClockRate', 'channel_descriptions']
        self.doNotSendToHardware += ['numChannels', 'units', 'channel_descriptions']
        self.transition_list = []  # an empty list to store

    def add_transition(self, time, channel, value):
        """Append a transition to the list of transitions.  The values are not processed until evaluate is called.
        Generally the master functional waveform instrument should evaluate before AO evaluates.
        :param time: float.  Absolute time since the HSDIO was triggered, in the units specified by self.units
        :param channel: int.  The channel number to change.
        :param value: bool.  Voltage value of the channel at this time.
        :return: Nothing.
        """
        self.transition_list.append((time, channel, value))

    def parse_transition_list(self):
        if self.transition_list:
            # put all the transitions that have been stored together into one big list
            # keep the times as floats for now, they will be converted to integer samples after the sample rate is applied
            times = np.array([i[0] for i in self.transition_list], dtype=np.float64)
            # compile the channels
            channels = np.array([i[1] for i in self.transition_list], dtype=np.uint8)
            # compile the values
            values = np.array([i[2] for i in self.transition_list], dtype=np.float32)

            # sort the transitions time.  If there is a tie, preserve the order.
            # mergesort is slower than the default quicksort, but it is 'stable'
            # which means items of the same value are kept in their relative order, which is desired here
            order = np.argsort(times, kind='mergesort')

            # Create an array to store the compiled sample values
            total_samples = int(np.rint(times[order[-1]]*self.clockRate.value*self.units.value)+1)
            time_list = 1.0*np.arange(total_samples)/self.clockRate.value
            value_list = np.zeros((total_samples, self.numChannels), dtype=np.float32)

            # go through all the transitions, updating the compiled sequence as we go
            # duplicate times are okay.  We want to allow that to allow sharp steps.
            for i in order:
                # evaluate the sample index equivalent to the transition time
                index = np.rint(times[i]*self.clockRate.value*self.units.value).astype(np.uint64)
                # for all samples >= index set it to the new value
                try:
                    value_list[index:, channels[i]] = values[i]
                except Exception as e:
                    print "probably invalid slice....... Exception: {}".format(e)
                    print "index={}".format(index)
                    raise PauseError

            # update the exposed variables
            self.times = time_list
            self.values = value_list
            self.transitions = times[order]*self.units.value  # used for plot xticks
        else:
            # there are no stored transitions
            self.times = np.zeros(0, dtype=np.float64)
            self.values = np.zeros((0, self.numChannels), dtype=np.float32)
            self.transitions = np.zeros(0, dtype=np.float64)  # used for plot xticks

    def evaluate(self):
        if self.enable and self.experiment.allow_evaluation:
            logger.debug('AnalogOutput.evaluate()')
            super(AnalogOutput, self).evaluate()
            self.parse_transition_list()
            # reset the transition list so it starts empty for the next usage
            self.transition_list = []

    def toHardware(self):
        """This overwrites Instrument.toHardware in order to add in the <waveform> which is not stored as a property.
        We transpose self.values because Labview expects the waveform with shape (channels, times)."""
        if self.enable:
            waveformXML = ('<waveform>'+
                '\n'.join([' '.join([str(sample) for sample in channel]) for channel in self.values.T])+
                '</waveform>\n')

            # then insert waveformXML into the output sent to LabView, in addition to the other properites
            # [14:] removes the <AnalogOutput> on what is returned from super.toHardware
            return '<AnalogOutput>{}\n'.format(waveformXML)+super(AnalogOutput, self).toHardware()[14:]
        else:
            # let Instrument.toHardware send <name><enable>False</enable><name>
            return super(AnalogOutput, self).toHardware()