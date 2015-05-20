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

from atom.api import Typed, Member, Int
from enaml.application import deferred_call
from matplotlib.ticker import NullFormatter
from instrument_property import BoolProp, FloatProp, StrProp
from cs_instruments import Instrument
import numpy as np


class AnalogOutput(Instrument):
    version = '2015.05.19'

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
    numChannels = Int(6)

    # properties for functional waveforms
    transition_list = Member()  # list that will store the transitions as they are added
    values = Member()  # an array of the compiled transition values
    times = Member()  # an array of the compiled transition times

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
                            'maxExternalClockRate']
        self.doNotSendToHardware += ['numChannels', 'units']
        self.transition_list = []  # an empty list to store

    def add_transition(self, time, channel, state):
        """Append a transition to the list of transitions.  The values are not processed until evaluate is called.
        Generally the master functional waveform instrument should evaluate before AO evaluates.
        :param time: float.  Absolute time since the HSDIO was triggered, in the units specified by self.units
        :param channel: int.  The channel number to change.
        :param value: bool.  Voltage value of the channel at this time.
        :return: Nothing.
        """
        self.transition_list.append((time, channel, value))

    def parse_transition_list(self):
        # put all the transitions that have been stored together into one big list
        # keep the times as floats for now, they will be converted to integer samples after the sample rate is applied
        times = np.array([i[0] for i in self.transition_list], dtype=np.float64)
        # compile the channels
        channels = np.array([i[1] for i in self.transition_list], dtype=np.uint8)
        # compile the values
        values = np.array([i[2] for i in self.transition_list], dtype=np.float32)

        # sort the transitions time.  If there is a tie, preserve the order.
        # mergesort is slower than the default quicksort, but it is 'stable' which means items of the same value are kept in their relative order, which is desired here
        order = np.argsort(times, kind='mergesort')
        times = times[order]
        channels = channels[order]
        values = values[order]

        # Create an array to store the compiled sample values
        total_samples = times[order[-1]]*self.clockRate.value*self.units.value+1
        time_list = np.arange(0,total_samples)
        value_list = np.zeros((total_samples, self.numChannels), dtype=np.float32)

        # go through all the transitions, updating the compiled sequence as we go
        # duplicate times are okay.  We want to allow that to allow sharp steps.
        for i in order:
            # evaluate the sample index equivalent to the transition time
            index = np.rint(times[i]*self.clockRate.value*self.units.value).astype(np.uint64)
            # for all samples >= index set it to the new value
            value_list[index:, channels[i]] =  values[i]

        #update the exposed variables
        self.times = time_list
        self.values = value_list

    def drawMPL(self):
        try:
            fig=self.backFigure

            #clear the old graph
            fig.clf()

            #redraw the graph
            n=len(self.equations)
            for i in range(n):
            #for each equation
                ax=fig.add_subplot(n,1,i+1)
                ax.plot(self.timesteps,self.equations[i].value)
                ax.set_ylabel(self.equations[i].description)
                if i<(n-1):
                    #remove tick labels all all except last plot
                    ax.xaxis.set_major_formatter(NullFormatter())
                else:
                    #label only the last (bottom) plot
                    ax.set_xlabel('time')
                    #make sure the tick labels have room

                #make the ylim a little wider than default (otherwise constant levels are sometimes on top of the plot frame)
                ylim=ax.get_ylim()
                yrange=abs(ylim[1]-ylim[0])
                newylim=(ylim[0]-yrange*.05,ylim[1]+yrange*.05)
                ax.set_ylim(newylim)

            #make room for the equation labels
            fig.subplots_adjust(left=.2,right=.95)
        except Exception as e:
            # report the error and continue if drawing the figure fails
            logger.warning('Exception in {}.drawMPL():\n{}\n{}\n'.format(self.name, e, traceback.format_exc()))

    def evaluate(self):
        if self.enable and self.experiment.allow_evaluation:
            logger.debug('AnalogOutput.evaluate()')
            super(AnalogOutput, self).evaluate()
            self.parse_transition_list()
            # reset the transition list so it starts empty for the next usage
            self.transition_list = []
