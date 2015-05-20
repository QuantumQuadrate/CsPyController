"""AnalogInput.py
Part of the AQuA Cesium Controller software package

author=Martin Lichtman
created=2014-08-19
modified>=2014-08-19

This file holds everything needed to set up a finite acquisition of a fixed number of data points during the
experiment from a National Instruments DAQmx card.
It communicates to LabView via the higher up LabView(Instrument) class.
Saving of returned data is handled in the LabView class.
"""

from __future__ import division
__author__ = 'Martin Lichtman'
import logging
logger = logging.getLogger(__name__)

import numpy
from atom.api import Str, Typed, Member, Bool, observe, Int
from instrument_property import BoolProp, FloatProp, StrProp, IntProp, Numpy1DProp
from cs_instruments import Instrument
from analysis import Analysis, AnalysisWithFigure

class AnalogInput(Instrument):
    version = '2014.08.19'
    sample_rate = Typed(FloatProp)
    source = Typed(StrProp)
    samples_per_measurement = Typed(IntProp)
    waitForStartTrigger = Typed(BoolProp)
    triggerSource = Typed(StrProp)
    triggerEdge = Typed(StrProp)
    channels = Member()  # just holds the channel descriptions
    ground_mode = Str('NRSE') = Typed(StrProp)

    def __init__(self, experiment):
        super(AnalogInput, self).__init__('AnalogInput', experiment)
        self.sample_rate = FloatProp('sample_rate', experiment, 'samples per second', '1000.0')
        self.source = StrProp('source', experiment, '', '"PXI1Slot6/ai0:15"')
        self.samples_per_measurement = IntProp('samples_per_measurement', experiment, '', '1')
        self.waitForStartTrigger = BoolProp('waitForStartTrigger', experiment, '', 'True')
        self.triggerSource = StrProp('triggerSource', experiment, '', '"/PXI1Slot6/PFI0"')
        self.triggerEdge = StrProp('triggerEdge', experiment, '"Rising" or "Falling"', '"Rising"')
        self.channels = Numpy1DProp('channels', experiment, 'a list of channel descriptions', dtype=[('description', object)], hdf_dtype=[('description', h5py.special_dtype(vlen=str))], zero=('new'))
        self.ground_mode = StrProp('ground_mode', self.experiment, 'RSE for ungrounded sensors, NRSE for grounded sensors')
        self.properties += ['version', 'sample_rate', 'source', 'samples_per_measurement', 'waitForStartTrigger',
                            'triggerSource', 'triggerEdge', 'channels', 'ground_mode']
        self.doNotSendToHardware += ['channels']

class AI_Graph(AnalysisWithFigure):
    """Plots a region of interest sum after every measurement"""
    version = '2014.10.13'
    enable = Bool()
    data = Member()
    update_lock = Bool(False)
    list_of_what_to_plot = Str()  # a list of tuples of [(channel, samples_list), (channel, samples_list)] where samples in samples_list will be averaged over

    def __init__(self, name, experiment, description=''):
        super(AI_Graph, self).__init__(name, experiment, description)
        self.properties += ['version', 'enable', 'list_of_what_to_plot']
        self.data = None

    def analyzeMeasurement(self, measurementResults, iterationResults, experimentResults):
        if self.enable and ('data/AI' in measurementResults):
            #every measurement, update a big array of all the AI data on all channels
            d = measurementResults['data/AI/data']
            if self.data is None:
                self.data = numpy.array([d])
            else:
                self.data = numpy.append(self.data, numpy.array([d]), axis=0)
            self.updateFigure()

    @observe('list_of_what_to_plot')
    def reload(self, change):
        self.updateFigure()

    def clear(self):
        self.data = None
        self.updateFigure()

    def updateFigure(self):
        if self.enable and (not self.update_lock):
            try:
                self.update_lock = True
                fig = self.backFigure
                fig.clf()

                if self.data is not None:
                    #parse the list of what to plot from a string to a list of numbers
                    try:
                        plotlist = eval(self.list_of_what_to_plot)
                    except Exception as e:
                        logger.warning('Could not eval plotlist in AIGraph:\n{}\n'.format(e))
                        return
                    #make one plot
                    ax = fig.add_subplot(111)
                    for i in plotlist:
                        try:
                            data = numpy.average(self.data[:, i[0], i[1]], axis=1)  # All measurements. Selected channel, saverage over sampels.
                        except:
                            logger.warning('Trying to plot data that does not exist in AIGraph: channel {} samples {}-{}'.format(i[0], min(i[1]), max(i[1])))
                            continue
                        label = 'ch.{}'.format(i[0])
                        ax.plot(data, 'o', label=label)
                    #add legend using the labels assigned during ax.plot()
                    ax.legend()
                super(AI_Graph, self).updateFigure()
            except Exception as e:
                logger.warning('Problem in AIGraph.updateFigure()\n:{}'.format(e))
            finally:
                self.update_lock = False


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

    def analyzeMeasurement(self, measurementResults, iterationResults, experimentResults):
        text = ''
        if self.enable and ('AI' in measurementResults['data']):
            failed = False  # keep track of if any of the filters fail
            # read the AI results
            data = measurementResults['data/AI/data']

            # parse the "what_to_filter" string
            try:
                filter_list = eval(self.what_to_filter)
            except Exception as e:
                logger.warning('Could not eval what_to_filter in AI_Filter:\n{}\n'.format(e))
                raise PauseError
            for i in filter_list:
                # read the data for the channel
                d = numpy.average(data[i[0], i[1]])
                if d > i[3]:
                    # data is above the high limit
                    text += 'Analog Input filter failed for channel {}.  Value was {}, above high limit {}.\n'.format(i[0], d, i[3])
                    failed = True
                elif d < i[2]:
                    # data is below the low limit
                    text += 'Analog Input filter failed for channel {}.  Value was {}, below low limit {}.\n'.format(i[0], d, i[2])
                    failed = True

            #check to see if any of the filters failed
            if failed:
                #record to the log and screen
                logger.warning(text)
                self.set_gui({'text': text})
                # User chooses whether or not to delete data.
                # max takes care of ComboBox returning -1 for no selection
                return max(0, self.filter_level)
            else:
                text = 'okay'
        self.set_gui({'text': text})
