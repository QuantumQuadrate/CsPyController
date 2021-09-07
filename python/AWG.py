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

    def __init__(self, name, experiment, description):
        super(AWG, self).__init__(name, experiment, description)

        self.slot = IntProp('slot', self.experiment, 'The PXI crate slot number')
        self.clockFrequency = IntProp('clockFrequency', self.experiment, 'Hz')
        self.channels = ListProp('channels', self.experiment,
                                 listProperty=[AWGchannel('channel {}'.format(i), self.experiment) for i in range(4)],
                                 listElementType=AWGchannel, listElementName='channel')
        self.properties += ['slot', 'clockFrequency', 'channels']

        # logger.info("Instantiating AWG")
        # logger.info(",".join(["{}".format(chan) for chan in self.channels]))


class AWGchannel(Prop):

    # props
    number = Typed(IntProp)
    amplitude = Typed(FloatProp)
    frequency = Typed(IntProp)

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
        self.modulationFunction = 0 # amplitude by default

        # lists

        self.trigger = ExternalTrigger()

        # logger.info("Instantiated AWG channel {}".format(self.name))

    def __repr__(self):
        return "AWGchannel({},{},{})".format(self.name, self.experiment, self.description)


# AWG_channel spits out "NoneType object has no attribute triggerBehavior" and so forth
class ExternalTrigger:

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


class AI_Filter(Analysis):
    """
    This analysis monitors the Analog Inputs and does either hard or soft cuts of the data accordingly.
    The filters are specified by the what_to_filter string, which is a list in the form:
    [(channel,sample_list,low,high), (channel,sample_list,low,high)]
    The samples in sample_list will be averaged.
    """

    enable = Bool()
    what_to_filter = Str()  # string representing a list of [(channel,low,high), (channel,low,high)]
    text = Str()
    filter_level = Int()

    def __init__(self, name, experiment, description=''):
        super(AI_Filter, self).__init__(name, experiment, description)
        self.properties += ['enable', 'what_to_filter', 'filter_level']

    def analyzeMeasurement(self, measurement_results, iteration_results, experiment_results):
        text = ''
        if self.enable and ('AI' in measurement_results['data']):
            failed = False  # keep track of if any of the filters fail
            # read the AI results
            data = measurement_results['data/AI/data']

            # parse the "what_to_filter" string
            try:
                filter_list = eval(self.what_to_filter)
            except Exception as e:
                logger.warning('Could not eval what_to_filter in AI_Filter:\n{}\n'.format(e))
                raise PauseError
            for i in filter_list:
                # read the data for the channel
                d = numpy.float(numpy.average(data[i[0], i[1]]))
                trysecondpath=False
                try:
                    measurement_results['data/AI/BinAve/channel'+ numpy.str(i[0])] = d
                except:
                    trysecondpath = True
                    logger.info("Unable to find data in first path. Trying second")

                if trysecondpath:
                    try:
                        measurement_results['data/AI/BinAve/channel'+ numpy.str(i[0])+'2'] = d
                    except:
                        logger.error("Unable to find AI data in either of the paths")
                if d > i[3]:
                    # data is above the high limit
                    text += 'Analog Input filter failed for channel {}.  Value was {}, above high limit {}.\n'.format(i[0], d, i[3])
                    failed = True
                elif d < i[2]:
                    # data is below the low limit
                    text += 'Analog Input filter failed for channel {}.  Value was {}, below low limit {}.\n'.format(i[0], d, i[2])
                    failed = True

            # check to see if any of the filters failed
            if failed:
                # record to the log and screen
                logger.warning(text)
                self.set_gui({'text': text})
                # User chooses whether or not to delete data.
                # max takes care of ComboBox returning -1 for no selection
                return max(0, self.filter_level)
            else:
                text = 'okay'
        self.set_gui({'text': text})
