"""functional_waveforms.py
Part of the AQuA Cesium Controller software package

author=Martin Lichtman
created=2015-05-19
modified>=2015-05-019

This file holds text files which specify the waveform timing for HSDIO, DAQmx DIO, and DAQmx AO.
Waveforms are specified as python functions.  Every waveform function must take in the absolute time
for the waveform to begin, and must return the absolute time when the waveform ends.  In this way, the length of each
waveform can easily be used to synchronize all three of these instruments.

In practice the functionality of this instrument is exactly the same as the dependent variables,
except that the resulting definitions will not be saved into the HDF5 file.
"""

from __future__ import division
__author__ = 'Martin Lichtman'
import logging
logger = logging.getLogger(__name__)

from cs_errors import PauseError
import cs_evaluate
from analysis import AnalysisWithFigure
from instrument_property import Prop
from atom.api import Str,Member,Float,Typed


class FunctionalWaveforms(Prop):
    """A virtual instrument that specifies the timing for HSDIO, DAQmx DIO, and DAQmx AO."""
    version = '2015.05.19'

    text = Str()  # a text string that holds all the waveforms

    def __init__(self, name, experiment, description=''):
        super(FunctionalWaveforms, self).__init__(name, experiment, description)
        self.properties += ['version', 'text']

    def evaluate(self):
        if self.enable and self.experiment.allow_evaluation:
            logger.debug('FunctionalWaveforms.evaluate()')

            localvars = self.experiment.vars.copy()
            cs_evaluate.execWithDict(self.text, localvars)

            return super(FunctionalWaveforms, self).evaluate()

class FunctionalWaveformGraph(AnalysisWithFigure):
    """
    This analysis is not set up to be called after measurements or iterations.  It is set up to update on evaluate().
    """

    labels = Member()
    spans = Member()
    plotmin = Str()
    plotmax = Str()
    units = Float(.001)
    HSDIO_channels_to_plot = Str()
    AO_channels_to_plot = Str()
    DAQmxDO_channels_to_plot = Str()

    def __init__(self, name, experiment, description=''):
        super(FunctionalWaveformGraph, self).__init__(name, experiment, description)
        self.properties += ['enable', 'plotmin', 'plotmax', 'units', 'HSDIO_channels_to_plot', 'AO_channels_to_plot',
                            'DAQmxDO_channels_to_plot']
        self.labels = []
        self.spans = []

    def label(self, time, text):
        self.labels += [(time, text)]

    def span(self, t1, t2, text):
        self.spans += [(t1, t2, text)]

    def evaluate(self):
        """Update the plot"""

        # sources
        HSDIO = self.experiment.LabView.HSDIO
        AO = self.experiment.LabView.AnalogOutput
        DO = self.experiment.LabView.DAQmxDO

        #draw on the inactive figure
        fig=self.backFigure

        #clear figure
        fig.clf()

        ### HSDIO plots ###

        #create axis
        ax = fig.add_subplot(111)
        ax.set_xlabel('time [ms]')

        # make horizontal grid lines
        ax.grid(True)

        channels = eval(self.HSDIO_channels_to_plot)
        states = HSDIO.states[:, channels]
        times = HSDIO.times/self.units
        durations = HSDIO.durations/self.units

        # get plot info
        numTransitions, numChannels = states.shape

        # set plot limits
        # y
        ax.set_ylim(0, numChannels)
        # x
        if self.plotmin == '':
            plotmin = times[0]
        else:
            plotmin = float(self.plotmin)
        if self.plotmax == '':
            plotmax = times[-1]
        else:
            plotmax = float(self.plotmax)
        if plotmin == plotmax:
            # avoid divide by zeros
            plotmax += 1
        ax.set_xlim(plotmin, plotmax)

        # set up plot ticks
        ax.set_xticks(times)
        ax.set_xticklabels(map(lambda x: str.format('{:.3g}', x), times))
        # make vertical tick labels on the bottom
        for label in ax.xaxis.get_ticklabels():
            label.set_rotation(90)

        # create a timeList on the scale 0 to 1
        relativeTimeList=(times-plotmin)/(plotmax-plotmin)
        relativeDuration=durations/(plotmax-plotmin)

        # Make a broken horizontal bar plot, i.e. one with gaps
        for i in xrange(numChannels):
            # reverse plot order of channels
            yhigh=numChannels-1-i+.9
            ylow=numChannels-1-i+.1
            for j in xrange(numTransitions):
                if states[j,i]:
                    ax.axhspan(ylow, yhigh, relativeTimeList[j], relativeTimeList[j]+relativeDuration[j], color='black', alpha=0.5)
                # if value is False, plot nothing

        # setup y-axis ticks
        ax.set_yticks(numpy.arange(numChannels)+0.5)
        yticklabels=[x+(' : ' if x else ' ')+str(i) for i,x in enumerate(HSDIO.channels.array['description'][channels])]
        yticklabels.reverse()  # reverse plot order of channels
        ax.set_yticklabels(yticklabels)

        #make sure the tick labels have room
        fig.subplots_adjust(left=.2, right=.95, bottom=.2)

        # make the analog plots

        # clear the label lists
        self.labels = []
        self.spans = []
