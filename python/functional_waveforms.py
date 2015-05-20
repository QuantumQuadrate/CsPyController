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
    DO_channels_to_plot = Str()
    AO_scale = Float(1)

    def __init__(self, name, experiment, description=''):
        super(FunctionalWaveformGraph, self).__init__(name, experiment, description)
        self.properties += ['enable', 'plotmin', 'plotmax', 'units', 'HSDIO_channels_to_plot', 'AO_channels_to_plot',
                            'DAQmxDO_channels_to_plot', 'AO_scale']

    def __init__(self):
        self.labels = []

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

        # channels to plot
        HSDIO_channels = eval(self.HSDIO_channels_to_plot)
        AO_channels = eval(self.AO_channels_to_plot)
        DO_channels = eval(self.DO_channels_to_plot)
        total_channels = len(HSDIO_channels)+len(AO_channels)+len(DO_channels)

        # draw on the inactive figure
        fig = self.backFigure
        # clear figure
        fig.clf()
        # new axes
        ax = fig.add_subplot(111)

        # HSDIO plots
        self.drawHSDIO(ax, HSDIO, HSDIO_channels)

        # AO plots
        self.drawAO(ax, AO, AO_channels, len(HSDIO_channels))

        # DAQmxDO plots
        self.drawDO(ax, DO, DO_channels, len(HSDIO_channels)+len(AO_channels))

        # set plot limits
        # y
        ax.set_ylim(0, total_channels)
        # x
        if self.plotmin == '':
            plotmin = min(HSDIO.times[0], AO.times[0], DO.times[0])
        else:
            plotmin = float(self.plotmin)
        if self.plotmax == '':
            plotmax = max(HSDIO.times[-1], AO.times[-1], DO.times[-1])
        else:
            plotmax = float(self.plotmax)
        if plotmin == plotmax:
            # avoid divide by zeros
            plotmax += 1
        ax.set_xlim(plotmin, plotmax)

        # setup y-axis ticks
        ax.set_yticks(numpy.arange(numChannels)+0.5)
        #HSDIO
        yticklabels = [x for x in HSDIO.channels.array['description'][HSDIO_channels]]
        #AO
        yticklabels += eval(AO.channel_descriptions)
        #DO
        yticklabels += [x for x in DO.channels.array['description'][HSDIO_channels]]
        ax.set_yticklabels(yticklabels)

        #make sure the tick labels have room
        fig.subplots_adjust(left=.3, right=.95, bottom=.2)

        # draw the vertical labels

        # draw the horizontal spans

        # clear the label lists
        self.labels = []
        self.spans = []

    def drawHSDIO(self, ax, HSDIO, channels):
        try:
            #create axis
            ax.set_xlabel('time [ms]')

            # make horizontal grid lines
            ax.grid(True)

            states = HSDIO.states[:, channels]
            times = HSDIO.times/self.units
            durations = HSDIO.durations/self.units

            # get plot info
            numTransitions, numChannels = states.shape



            # set up plot ticks
            ax.set_xticks(times)
            ax.set_xticklabels(map(lambda x: str.format('{:.3g}', x), times))
            # make vertical tick labels on the bottom
            for label in ax.xaxis.get_ticklabels():
                label.set_rotation(90)

            # create a timeList on the scale 0 to 1
            relativeTimeList = (times-plotmin)/(plotmax-plotmin)
            relativeDuration = durations/(plotmax-plotmin)

            # Make a broken horizontal bar plot, i.e. one with gaps
            for i in xrange(numChannels):
                # reverse plot order of channels
                yhigh = i+.9
                ylow = i+.1
                for j in xrange(numTransitions):
                    if states[j, i]:
                        ax.axhspan(ylow, yhigh, relativeTimeList[j], relativeTimeList[j]+relativeDuration[j], color='black', alpha=0.5)
                    # if value is False, plot nothing

        except Exception as e:
            # report the error and continue if drawing the figure fails
            logger.warning('Exception in {}.drawHSDIO():\n{}\n{}\n'.format(self.name, e, traceback.format_exc()))

    def drawAO(self, ax, AO, channels, scale, offset):
        try:
            # select the channels
            values = AO.values[:, channels]
            times = AO.times/self.units

            #redraw the graph
            n=len(channels)
            for i in range(n):
                # plot the values with a vertical offset to separate them
                ax.plot(AO.times, AO.values[:,i]/scale+i+offset)
        except Exception as e:
            # report the error and continue if drawing the figure fails
            logger.warning('Exception in {}.drawAO():\n{}\n{}\n'.format(self.name, e, traceback.format_exc()))

    def drawDO(self, ax, DO, channels, offset):
        try:
            #create axis
            ax.set_xlabel('time [ms]')

            # make horizontal grid lines
            ax.grid(True)

            states = HSDIO.states[:, channels]
            times = HSDIO.times/self.units
            durations = HSDIO.durations/self.units

            # get plot info
            numTransitions, numChannels = states.shape



            # set up plot ticks
            ax.set_xticks(times)
            ax.set_xticklabels(map(lambda x: str.format('{:.3g}', x), times))
            # make vertical tick labels on the bottom
            for label in ax.xaxis.get_ticklabels():
                label.set_rotation(90)

            # create a timeList on the scale 0 to 1
            relativeTimeList = (times-plotmin)/(plotmax-plotmin)
            relativeDuration = durations/(plotmax-plotmin)

            # Make a broken horizontal bar plot, i.e. one with gaps
            for i in xrange(numChannels):
                # reverse plot order of channels
                yhigh = i+.9
                ylow = i+.1
                for j in xrange(numTransitions):
                    if states[j, i]:
                        ax.axhspan(ylow, yhigh, relativeTimeList[j], relativeTimeList[j]+relativeDuration[j], color='black', alpha=0.5)
                    # if value is False, plot nothing

        except Exception as e:
            # report the error and continue if drawing the figure fails
            logger.warning('Exception in {}.drawHSDIO():\n{}\n{}\n'.format(self.name, e, traceback.format_exc()))
