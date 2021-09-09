"""AWG.py
Part of the CsPy experiment controller

author=PrestonHuft
created=2021-09-06

Defines object for representing a Signadyne AWG and exposing the required parameters to the CsPy interface.
Params set in the AWG window are then sent to the Instrument Server over TCP/IP.
"""

from __future__ import division
__author__ = 'Martin Lichtman'
import logging
logger = logging.getLogger(__name__)

import numpy
import h5py
from atom.api import Str, Typed, Member, Bool, observe, Int, List

from instrument_property import Prop, BoolProp, FloatProp, StrProp, IntProp, Numpy1DProp, ListProp
from cs_instruments import Instrument
from analysis import Analysis, AnalysisWithFigure

class AWG(Instrument):

    slot = Typed(IntProp)
    clockFrequency = Typed(IntProp)
    clockIOconfig = Int()
    channels = Typed(ListProp)
    clockIOconfigList = ['0: Disable external CLK connector',
                         '1: CLK connector outputs copy of reference clock']
    waveformList = Typed(StrProp)
    waveformQueueStr = ("String representing list of waveforms to be stored in RAM, implicitly numbered"
                        + "with 0-based indexing. Each channel's waveformQueue will be built from this list"
                        + "\nby referring to a waveform by its index in the list here."
                        + "Functions used in waveforms must belong to the numpy package, e.g. sin refers to numpy.sin")
    prescalerNoteStr = ('Note about waveformQueue params:'
                        + '\n - Prescaler: used to set rate at which RAM steps are deployed. Calculate based on the '
                        + 'desired waveform duration tau: prescaler = int(tau*clockFrequency/(5*waveform_pts)).'
                        + '\n - Cycles: 0 if waveform should repeat with every trigger received, n > 0 to playback '
                        + 'for only the first n triggers')

    def __init__(self, experiment, name='AWG', description='Signadyne AWG Card'):
        super(AWG, self).__init__(name, experiment, description)

        self.slot = IntProp('slot', self.experiment, 'The PXI crate slot number')
        self.clockFrequency = IntProp('clockFrequency', self.experiment, 'Hz')
        self.channels = ListProp('channels', self.experiment,
                                 listProperty=[AWGchannel('channel {}'.format(i), self.experiment) for i in range(4)],
                                 listElementType=AWGchannel, listElementName='channel')
        self.waveformList = StrProp('waveformList', self.experiment,
                                     'e.g.: [[exp(-x**2) for x in linspace(-5,5,100)],[x for x in linspace(0,1,20)]]')
        self.properties += ['slot', 'clockFrequency', 'channels', 'waveformList']


class AWGchannel(Prop):

    # props
    number = Typed(IntProp)
    amplitude = Typed(FloatProp)
    frequency = Typed(IntProp)
    waveformQueue = Typed(StrProp)

    # combobox stuff
    waveshape = Int() # get combobox index
    modulationFunction = Int() # get combobox index; amplitude, freq(phase) or none
    modulationType = Int() # get combobox index
    triggerBehavior = Int() # get combobox index
    deviationGain = Int()

    # other
    trigger = Member()

    # use lists to populate comboboxes, from which to choose defined parameter options
    # waveshapeList = Typed(list)
    waveshapeList = ['AOU_OFF', 'AOU_SINUSOIDAL', 'AOU_TRIANGULAR', 'AOU_SQUARE', 'AOU_DC', 'AOU_AWG',
                          'AOU_PARTNER']
    modulationFunctionList = ['amplitude','angle']
    modulationTypeDescriptions = {'amplitude': ['Modulation off','Amplitude','Offset'],
                          'angle': ['Modulation off','Frequency','Phase']}
    modulationTypeDict = {'amplitude': ['AOU_MOD_OFF','AOU_MOD_AM','AOU_MOD_OFFSET'],
                          'angle': ['AOU_MOD_OFF','AOU_MOD_FM','AOU_MOD_PM']}

    def __init__(self, name, experiment, description=''):
        super(AWGchannel, self).__init__(name, experiment, description)
        self.number = IntProp('number', self.experiment, '0-indexed chan. num')
        self.amplitude = FloatProp('amplitude', self.experiment, 'Volts')
        self.frequency = IntProp('frequency', self.experiment, 'Hz')
        self.waveformQueue = StrProp('waveformQueue', self.experiment, 'e.g.: [(0,0,0,1),(1,0,0,1)]')
        self.modulationFunction = 0 # amplitude by default

        # lists

        self.trigger = ExternalTrigger()

        # logger.info("Instantiated AWG channel {}".format(self.name))

    def __repr__(self):
        return "AWGchannel({},{},{})".format(self.name, self.experiment, self.description)


# AWG_channel spits out "NoneType object has no attribute triggerBehavior" and so forth
class ExternalTrigger(Prop):

    triggerBehavior = Int()
    triggerBehaviorList = ['1: Trigger active when high',
                           '2: Trigger active when low',
                           '3: Trigger active on rising edge',
                           '4: Trigger active on falling edge']

    externalSourceList = ['0: External', 'PXI trigger. Not currently supported']
    externalSource = Int()

    def __init__(self):
        self.externalSource = 0


# make this the waveform plot
# class AI_Graph(AnalysisWithFigure):
#     """Plots a region of interest sum after every measurement"""
#     enable = Bool()
#     data = Member()
#     update_lock = Bool(False)
#     list_of_what_to_plot = Str()  # a list of tuples of [(channel, samples_list), (channel, samples_list)] where samples in samples_list will be averaged over
#
#     def __init__(self, name, experiment, description=''):
#         super(AI_Graph, self).__init__(name, experiment, description)
#         self.properties += ['version', 'enable', 'list_of_what_to_plot']
#         self.data = None
#s
#     def analyzeMeasurement(self, measurementResults, iterationResults, experimentResults):
#         if self.enable and ('data/AI' in measurementResults):
#             #every measurement, update a big array of all the AI data on all channels
#             d = measurementResults['data/AI/data']
#             if self.data is None:
#                 self.data = numpy.array([d])
#             else:
#                 self.data = numpy.append(self.data, numpy.array([d]), axis=0)
#             self.updateFigure()
#
#     @observe('list_of_what_to_plot')
#     def reload(self, change):
#         self.updateFigure()
#
#     def clear(self):
#         self.data = None
#         self.updateFigure()
#
#     def updateFigure(self):
#         if self.draw_fig:
#             if self.enable and (not self.update_lock):
#                 try:
#                     self.update_lock = True
#                     fig = self.backFigure
#                     fig.clf()
#
#                     if self.data is not None:
#                         # parse the list of what to plot from a string to a list of numbers
#                         try:
#                             plotlist = eval(self.list_of_what_to_plot)
#                         except Exception as e:
#                             logger.warning('Could not eval plotlist in AIGraph:\n{}\n'.format(e))
#                             return
#                         # make one plot
#                         ax = fig.add_subplot(111)
#                         for i in plotlist:
#                             try:
#                                 data = numpy.average(self.data[:, i[0], i[1]], axis=1)  # All measurements. Selected channel, saverage over sampels.
#                                 # data=numpy.average(self.data[:, i[0], i[1]], axis=1) # Show only the latest
#                             except:
#                                 logger.warning('Trying to plot data that does not exist in AIGraph: channel {} samples {}-{}'.format(i[0], min(i[1]), max(i[1])))
#                                 continue
#                             label = 'ch.{}'.format(i[0])
#                             ax.plot(data, 'o', label=label)
#                         # add legend using the labels assigned during ax.plot()
#                         ax.legend(bbox_to_anchor=(0., 1.02, 1., .102), loc=2, borderaxespad=0.0)
#                         ax.grid('on')
#                     super(AI_Graph, self).updateFigure()
#                 except Exception as e:
#                     logger.warning('Problem in AIGraph.updateFigure()\n:{}'.format(e))
#                 finally:
#                     self.update_lock = False ##
