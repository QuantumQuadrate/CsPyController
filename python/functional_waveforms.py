"""functional_waveforms.py
Part of the AQuA Cesium Controller software package

author=Martin Lichtman
created=2015-05-19
modified>=2015-05-24

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

import traceback
import numpy as np
from atom.api import Str, Member, Float, Bool, Int, observe

import cs_evaluate
from analysis import AnalysisWithFigure
from cs_instruments import Instrument


class FunctionalWaveforms(Instrument):
    """A virtual instrument that specifies the timing for HSDIO, DAQmx DIO, and DAQmx AO."""
    version = '2015.05.24'

    text = Str()  # a text string that holds all the waveforms

    def __init__(self, name, experiment, description=''):
        super(FunctionalWaveforms, self).__init__(name, experiment, description)
        self.properties += ['version', 'text']

    def evaluate(self):
        if self.enable and self.experiment.allow_evaluation:
            logger.debug('FunctionalWaveforms.evaluate()')

            #localvars = self.experiment.vars.copy()
            cs_evaluate.execWithGlobalDict(self.text) #, localvars)

            super(FunctionalWaveforms, self).evaluate()

class FunctionalWaveformGraph(AnalysisWithFigure):
    """
    This analysis is not set up to be called after measurements or iterations.  It is set up to update on evaluate().
    """

    labels = Member()
    saved_labels = Member()
    spans = Member()
    saved_spans = Member()
    enable = Bool()
    plotmin_str = Str()
    plotmax_str = Str()
    units = Float(.001)
    HSDIO_channels_to_plot = Str()
    AO_channels_to_plot = Str()
    DO_channels_to_plot = Str()
    AO_scale = Float(1)
    update_lock = Bool(False)
    draw_HSDIO_ticks = Bool()
    draw_AO_ticks = Bool()
    draw_DO_ticks = Bool()
    draw_label_ticks = Bool()

    def __init__(self, name, experiment, description=''):
        super(FunctionalWaveformGraph, self).__init__(name, experiment, description)
        self.properties += ['enable', 'plotmin_str', 'plotmax_str', 'units', 'HSDIO_channels_to_plot',
                            'AO_channels_to_plot', 'DO_channels_to_plot', 'AO_scale', 'draw_HSDIO_ticks',
                            'draw_AO_ticks', 'draw_DO_ticks', 'draw_label_ticks']
        self.labels = []
        self.spans = []

    def label(self, time, text):
        self.labels += [(time, text)]

    def span(self, t1, t2, text):
        self.spans += [(t1, t2, text)]

    def evaluate(self):
        if self.enable and self.experiment.allow_evaluation:

            # save the labels for plotting
            self.saved_labels = self.labels
            self.saved_spans = self.spans

            # clear the label lists so they are empty for next time the functional waveforms are evaluated
            self.labels = []
            self.spans = []

            self.updateFigure()

    @observe('plotmin_str', 'plotmax_str', 'units', 'HSDIO_channels_to_plot', 'AO_channels_to_plot',
             'DAQmxDO_channels_to_plot', 'AO_scale', 'draw_HSDIO_ticks', 'draw_AO_ticks', 'draw_DO_ticks',
             'draw_label_ticks')
    def reload(self, change):
        self.updateFigure()

    def updateFigure(self):
        """Update the plot"""
        if self.enable and self.experiment.allow_evaluation and (not self.update_lock):
            try:
                self.update_lock = True
                # draw on the inactive figure
                fig = self.backFigure
                # clear figure
                fig.clf()

                # sources
                HSDIO = self.experiment.LabView.HSDIO
                AO = self.experiment.LabView.AnalogOutput
                DO = self.experiment.LabView.DAQmxDO

                # channels to plot
                if self.HSDIO_channels_to_plot:
                    HSDIO_channels = eval(self.HSDIO_channels_to_plot)
                else:
                    HSDIO_channels = []
                if self.AO_channels_to_plot:
                    AO_channels = eval(self.AO_channels_to_plot)
                else:
                    AO_channels = []
                if self.DO_channels_to_plot:
                    DO_channels = eval(self.DO_channels_to_plot)
                else:
                    DO_channels = []
                total_channels = len(HSDIO_channels)+len(AO_channels)+len(DO_channels)

                # new axes
                ax = fig.add_subplot(111)
                # create axis
                ax.set_xlabel('time [{}*s]'.format(self.units))
                # make horizontal grid lines
                ax.grid(True)

                # set plot limits
                # y
                ax.set_ylim(0, total_channels)
                # x
                if self.plotmin_str == '':
                    plotmin = 0
                    if HSDIO_channels and (len(HSDIO.times) > 0):
                        plotmin = min(plotmin, HSDIO.times[0]/self.units)
                    if AO_channels and (len(AO.times) > 0):
                        plotmin = min(plotmin, AO.times[0]/self.units)
                    if DO_channels and (len(DO.times) > 0):
                        plotmin = min(plotmin, DO.times[0]/self.units)
                else:
                    plotmin = float(self.plotmin_str)
                if self.plotmax_str == '':
                    plotmax = 0
                    if HSDIO_channels and (len(HSDIO.times) > 0):
                        plotmax = max(plotmax, HSDIO.times[-1]/self.units)
                    if AO_channels and (len(AO.times) > 0):
                        plotmax = max(plotmax, AO.times[-1]/self.units)
                    if DO_channels and (len(DO.times) > 0):
                        plotmax = max(plotmax, DO.times[-1]/self.units)
                else:
                    plotmax = float(self.plotmax_str)
                if plotmin == plotmax:
                    # avoid divide by zeros
                    plotmax += 1

                # HSDIO plots
                if HSDIO_channels:
                    self.draw_digital(ax, HSDIO, HSDIO_channels, plotmin, plotmax, 0)

                # AO plots
                if AO_channels:
                    self.draw_analog(ax, AO, AO_channels, self.AO_scale, len(HSDIO_channels))

                # DAQmxDO plots
                if DO_channels:
                    self.draw_digital(ax, DO, DO_channels, plotmin, plotmax, len(HSDIO_channels)+len(AO_channels))

                # setup the x-ticks
                xticks = []
                if self.draw_HSDIO_ticks:
                    a = (HSDIO.times/self.units).tolist()
                    xticks += a
                if self.draw_DO_ticks:
                    a = (DO.times/self.units).tolist()
                    xticks += a
                if self.draw_AO_ticks:
                    a = (AO.transitions/self.units).tolist()
                    xticks += a
                # set the plot ticks
                ax.set_xticks(xticks)

                # labels
                if self.draw_label_ticks:
                    # get the plot ticks so for
                    xticks = ax.get_xticks().tolist()
                    xtick_labels = map(lambda x: x.get_text(), ax.get_xticklabels())
                    for i in self.saved_labels:
                        xticks += [i[0]]
                        xtick_labels += [i[1]]
                    # set the plot ticks again
                    ax.set_xticks(xticks)
                    ax.set_xticklabels(xtick_labels)

                # make the xtick labels vertical
                for label in ax.xaxis.get_ticklabels():
                    label.set_rotation(90)

                ax.set_xlim(plotmin, plotmax)

                # setup y-axis ticks
                ax.set_yticks(np.arange(total_channels)+0.5)
                #HSDIO
                yticklabels = ['{}: {}'.format(i, HSDIO.channels.array['description'][i]) for i in HSDIO_channels]
                #AO
                AO_yticks = eval(AO.channel_descriptions)
                yticklabels += [AO_yticks[i] for i in AO_channels]
                #DO
                yticklabels += [x for x in DO.channels.array['description'][DO_channels]]
                ax.set_yticklabels(yticklabels)

                #make sure the tick labels have room
                fig.subplots_adjust(left=.3, right=.95, bottom=.2)

                # TODO:draw the horizontal spans

                # call super to update the figure to the GUI
                super(FunctionalWaveformGraph, self).updateFigure()

            except Exception as e:
                logger.warning('Problem in FunctionalWaveformGraph.updateFigure()\n{}\n{}\n'.format(e, traceback.format_exc()))
            finally:
                self.update_lock = False

    def draw_digital(self, ax, source, channels, plotmin, plotmax, offset):
        try:
            states = source.states[:, channels]
            times = 1.0*source.times/self.units
            durations = 1.0*source.time_durations/self.units

            # get plot info
            numTransitions, numChannels = states.shape

            # create a timeList on the scale 0 to 1
            relativeTimeList = 1.0*(times-plotmin)/(plotmax-plotmin)
            relativeDuration = 1.0*durations/(plotmax-plotmin)

            # Make a broken horizontal bar plot, i.e. one with gaps
            for i in xrange(numChannels):
                # reverse plot order of channels
                yhigh = i+.9+offset
                ylow = i+.1+offset
                for j in xrange(numTransitions):
                    if states[j, i]:
                        ax.axhspan(ylow, yhigh, relativeTimeList[j], relativeTimeList[j]+relativeDuration[j], color='gray')
                    # if value is False, plot nothing

        except Exception as e:
            # report the error and continue if drawing the figure fails
            logger.warning('Exception in {}.draw_digital():\n{}\n{}\n'.format(self.name, e, traceback.format_exc()))
            # return no new xticks
            return [], []

    def draw_analog(self, ax, AO, channels, scale, offset):
        try:
            # scale the x-axis
            times = 1.0*AO.times/self.units

            n = len(channels)
            for i, x in enumerate(channels):
                # plot the values with a vertical offset to separate them
                ax.step(times, 1.0*AO.values[:, x]/scale+i+.5+offset, where='post')
        except Exception as e:
            # report the error and continue if drawing the figure fails
            logger.warning('Exception in {}.drawAO():\n{}\n{}\n'.format(self.name, e, traceback.format_exc()))
