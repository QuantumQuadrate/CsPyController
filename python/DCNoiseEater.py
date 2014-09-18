"""DCNoiseEater.py
Part of the AQuA Cesium Controller software package

author=Martin Lichtman
created=2014-08-22
modified>=2014-08-22

This file creates an instrument that grabs data from the DC Noise Eater.
It does so via TCP to a C# program, which in turn talks to a virtual
serial port, which in turn goes over USB, which goes to the little add-on
chip that is used to program the Propller MCU in on the noise eater board.

This instrument requests the settings every measurement, and stores them into
the hdf5.
"""

from __future__ import division
__author__ = 'Martin Lichtman'
import logging
logger = logging.getLogger(__name__)

import time, struct
import numpy
import serial
import serial.tools.list_ports
from atom.api import Str, Typed, Member, Bool, observe, Int
from enaml.application import deferred_call
from instrument_property import Prop, IntProp, ListProp
from cs_instruments import Instrument
from analysis import Analysis, AnalysisWithFigure


class DCNoiseEaters(Instrument):
    # Communicates with a bunch of DC Noise Eater boxes that are attached directly to the experiment
    # computer via USB-to-serial Parallax Prop Plugs.  These present themselves to python as simple
    # COM ports.

    version = '2014.09.01'
    boxes = Typed(ListProp)
    deviceList = Member()
    deviceListStr = Str()
    boxDescriptionList = Member()

    def __init__(self, name, experiment, description='DC Noise Eaters'):
        super(DCNoiseEaters, self).__init__(name, experiment, description)
        self.boxes = ListProp('boxes', experiment, listElementType=DCNoiseEater, listElementName='box')
        self.properties += ['version', 'boxes', 'deviceList']

    def initialize(self):
        if self.enable:
            for box in self.boxes:
                box.initialize()
            self.isInitialized = True

    def start(self):
        if self.enable:
            for box in self.boxes:
                box.start()
        self.isDone = True

    def writeResults(self, hdf5):
        if self.enable:
            hdf5['DC_noise_eater'] = numpy.array([box.resultsArray() for box in self.boxes], dtype=numpy.int16)

    def evaluate(self):
        if self.experiment.allow_evaluation:
            logger.debug('DCNoiseEaters.evaluate()')
            super(DCNoiseEaters, self).evaluate()
            self.updateBoxDescriptionList()

    # currently unused, this will be for when we want to provide a combo box of the available serial ports
    def getDeviceListThread(self):
        # calls getDeviceList() in a separate thread to leave the GUI free
        thread = threading.Thread(target=self.getDeviceList)
        thread.daemon = True
        thread.start()

    # currently unused, this will be for when we want to provide a combo box of the available serial ports
    def getDeviceList(self):
        # list the available COM ports.  The port we want is usually:
        # [('COM17', 'USB Serial Port (COM17)', 'FTDIBUS\\VID_0403+PID_6001+A700AC57A\\0000')]
        result = list(serial.tools.list_ports.comports())
        deviceList = [i[0] for i in result]  # a list of the string necessary to connect to each com port
        deviceStrList = ['{}, {}, {}'.format(*i) for i in result]  # a list of all the info about each com port
        deferred_call(setattr, self, 'deviceList', deviceListStr.split('\n'))

    # currently unused, this will be for when we want to provide a combo box of the available serial ports
    def updateBoxDescriptionList(self):
        #sets the descriptions shown in the combo box in the GUI
        try:
            deferred_call(setattr, self, 'boxDescriptionList', [str(i)+' '+n.description for i, n in enumerate(self.boxes)])
        except RuntimeError:
            #the GUI is not yet active
            self.boxDescriptionList = [str(i)+' '+n.description for i, n in enumerate(self.boxes)]


class Channel(Prop):

    allow_get = Bool(False)  # enables settings on noise eater to overwrite settings on computer

    # read/write variables
    update = Bool(False)  # bool
    mode = Int(0)  # int8
    warnSetting = Bool(False)  # bool
    limitRange = Int(0)  # int16
    invert = Bool(False)  # bool
    integrationTime = Int(100)  # int16
    trigNum = Int(0)  # int8
    measNum = Int(0)  # int8
    #kp = Int(2560)  # int16
    kp = Typed(IntProp)
    #ki = Int(64)  # int16
    ki = Typed(IntProp)
    setpoint = Int(9823)  # int16

    # variables from DC noise eater
    # read only
    average = Int(0)  # int16
    error = Int(0)  # int16
    vin = Int(0)  # int16
    vout = Int(0)  # int16
    warning = Bool(False)  # bool

    def __init__(self, name, experiment, description='a DC Noise Eater channel'):
        super(Channel, self).__init__(name, experiment, description)
        self.kp = IntProp('kp', self.experiment, 'kp', '2560')
        self.ki = IntProp('ki', self.experiment, 'ki', '64')
        self.properties += ['allow_get', 'update', 'mode', 'warnSetting', 'limitRange', 'invert',
                            'integrationTime', 'trigNum', 'measNum', 'kp', 'ki', 'setpoint', 'average', 'error', 'vin',
                            'vout', 'warning']

    def settings_in_from_hardware(self, data):
        # format the data returned by the noise eater
        # the code 'b?h?hbbhhhhhhh?' specifies b: signed int8, ?: binary stored as 8 bits, h: uint16
        # '<' is because the propeller chip is little-endian
        # status variables are written to immediately, but use intermediate variables for the settings
        mode, warnSetting, limitRange, invert, integrationTime, trigNum, measNum, kp, ki, setpoint, self.average, self.error, self.vin, self.vout, self.warning = struct.unpack('<b?h?hbbhhhhhhh?', data)
        if self.allow_get:
            deferred_call(self.gui_write, mode, warnSetting, limitRange, invert, integrationTime, trigNum, measNum, kp, ki, setpoint)

    def gui_write(self, mode, warnSetting, limitRange, invert, integrationTime, trigNum, measNum, kp, ki, setpoint):
        # This is implemented as a separate method so it can be called from the GUI thread.
        # overwrite the settings on the computer with those loaded from the noise eater
        self.mode = mode
        self.warnSetting = warnSetting
        self.limitRange = limitRange
        self.invert = invert
        self.integrationTime = integrationTime
        self.trigNum = trigNum
        self.measNum = measNum
        self.kp.function = str(kp)
        self.ki.function = str(ki)
        self.setpoint = setpoint

    def settings_out_to_hardware(self):
        # return a 15 byte array that will be what is sent to the hardware for this channel
        # the code 'b?h?hbbhhh' specifies the 15 bytes as b: signed int8, ?: binary stored as 8 bits, h: uint16
        # '<' is because the propeller chip is little-endian
        data = struct.pack('<b?h?hbbhhh', self.mode, self.warnSetting, self.limitRange, self.invert, self.integrationTime, self.trigNum, self.measNum, self.kp.value, self.ki.value, self.setpoint)
        return data

    def print_settings(self):
        # print all the settings for this channel

        print 'channel {} mode {} warnSetting {} limitRange {} invert {} integrationTime {} trigNum {} measNum {} kp {} ki {} setpoint {}'.format(
            self.mode, self.warnSetting, self.limitRange, self.invert, self.integrationTime,
            self.trigNum, self.measNum, self.kp.value, self.ki.value, self.setpoint)
        print 'average {} error {} vin {} vout {} warning {}'.format(
            self.average, self.error, self.vin, self.vout, self.warning)
        print '\n'


class DCNoiseEater(Instrument):
    version = '2014.09.01'

    comport = Str()
    data = Member()
    channels = Typed(ListProp)
    numChannels = 3
    ser = Member()
    num_inits = Int(0)

    def __init__(self, name, experiment, description='DC Noise Eater'):
        super(DCNoiseEater, self).__init__(name, experiment, description)
        # create a channel object for each noise eater channel
        # we won't dynamic add or remove channels, always 3 per box
        # if we did dynamically add, they would need to get the channel number passed to their __init__
        self.channels = ListProp('channels', experiment, listProperty=[Channel('channel'+str(i), self.experiment) for i in xrange(3)],
                                 listElementType=Channel, listElementName='channel', listElementKwargs=None)
        #self.channels = [Channel(i) for i in xrange(3)]  # TODO: make this a ListProp
        self.properties += ['version', 'comport', 'channels']

    def initialize(self):
        """Open the serial port"""
        if self.enable:

            if (self.ser is not None) and self.ser.isOpen():
                self.ser.close()

            # open the serial port
            self.ser = serial.Serial(self.comport, 38400, timeout=1, writeTimeout=1)
            logger.debug('opened: {}'.format(self.ser.name))  # checks which port was really used

            self.isInitialized = True

    # specify how to create output data from the channel objects
    def format_output(self, channels):
        # create a byte which encodes whether or not to update each channel
        data = chr(sum([2**i for i, c in enumerate(channels) if c.update]))

        # TODO: make this happen only on changed flag
        #turn off future updates until re-enabled
        #for c in channels:
        #    c.update = False

        # append 15 bytes for each channel, encoding the settings
        for c in channels:
            data += c.settings_out_to_hardware()

        return data

    def start(self):
        if self.enable:
            # every measurement, we write settings to the Noise Eater, and then read back the setting and vin/vout values

            data = self.format_output(self.channels)

            # clear old data
            self.ser.flushOutput()  # Flush output buffer, discarding all its contents.
            self.ser.flushInput()   # Flush input buffer, discarding all its contents.

            # write
            self.ser.write('!VB\n')  # write a string to the noise eater, which tells it to accept settings and return dat'
            self.ser.write(data)  # follow this with the settings

            # read
            time.sleep(.02)  # wait 20 milliseconds for data to be returned
            header = self.ser.readline()
            #print len(header)
            #print header
            if header == '!P1\n':
                data_in = self.ser.read(96)  # read 96 bits
                # update the settings of each channel
                for i, c in enumerate(self.channels):
                    d = data_in[24*i:24*(i+1)]
                    c.settings_in_from_hardware(d)
                    #c.print_settings()
        self.isDone = True

    def resultsArray(self):
        # return an array of all the variables, with an entry for each channel in this box
        # this function is used to store the info in the hdf5 file
        return [[c.mode, c.warnSetting, c.limitRange, c.invert, c.integrationTime, c.trigNum, c.measNum,
            c.kp.value, c.ki.value, c.setpoint, c.average, c.error, c.vin, c.vout, c.warning] for c in self.channels]


class DCNoiseEaterGraph(AnalysisWithFigure):
    """Plots a region of interest sum after every measurement"""
    version = '2014.09.01'
    enable = Bool()
    data = Member()
    update_lock = Bool(False)
    list_of_what_to_plot = Str()

    def __init__(self, name, experiment, description=''):
        super(DCNoiseEaterGraph, self).__init__(name, experiment, description)
        self.properties += ['version', 'enable', 'list_of_what_to_plot']
        self.data = None

    def analyzeMeasurement(self, measurementResults, iterationResults, experimentResults):
        if self.enable and ('data/DC_noise_eater' in measurementResults):
            #every measurement, update a big array of all the noise eater data on all channels
            d = measurementResults['data/DC_noise_eater']
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
                        logger.warning('Could not eval plotlist in DCNoiseEaterGraph:\n{}\n'.format(e))
                        return
                    #make one plot
                    ax = fig.add_subplot(111)
                    for i in plotlist:
                        try:
                            data = self.data[:, i[0], i[1], i[2]]  # All measurements. Selected box, channel, and var.
                        except:
                            logger.warning('Trying to plot data that does not exist in MeasurementsGraph: box {} channel {} var {}'.format(i[0], i[1], i[2]))
                            continue
                        label = '({},{},{})'.format(i[0], i[1], i[2])
                        ax.plot(data, 'o', label=label)
                    #add legend using the labels assigned during ax.plot()
                    ax.legend()
                super(DCNoiseEaterGraph, self).updateFigure()
            except Exception as e:
                logger.warning('Problem in DCNoiseEaterGraph.updateFigure()\n:{}'.format(e))
            finally:
                self.update_lock = False


class DCNoiseEaterFilter(Analysis):
    """
    This analysis monitors the Noise Eater inputs and does either hard or soft cuts of the data accordingly.
    The filters are specified by the what_to_filter string, which is a list in the form:
    [(box,channel,variable,high,low), (box,channel,variable,low,high)]
    The variable numbers are the indices of the data returned by the DC Noise Eater.  See DCNoiseEater.resultsArray() above.
    Error is variable 11.
    """

    enable = Bool()
    what_to_filter = Str()  # string representing a list of [(box,channel,variable,low,high), (box,channel,variable,low,high)]
    text = Str()
    filter_level = Int()

    def __init__(self, name, experiment, description=''):
        super(DCNoiseEaterFilter, self).__init__(name, experiment, description)
        self.properties += ['enable', 'what_to_filter', 'filter_level']

    def analyzeMeasurement(self, measurementResults, iterationResults, experimentResults):
        text = ''
        if self.enable:
            failed = False  # keep track of if any of the filters fail
            if 'DC_noise_eater' in measurementResults['data']:
                # read the DC Noise Eater results
                data = measurementResults['data/DC_noise_eater']

                # parse the "what_to_filter" string
                try:
                    filter_list = eval(self.what_to_filter)
                except Exception as e:
                    logger.warning('Could not eval what_to_filter in NoiseEaterFilter:\n{}\n'.format(e))
                    return
                for i in filter_list:
                    # read the data for the correct box, channel, variable
                    d = data[i[0], i[1], i[2]]
                    if  d > i[4]:
                        # data is above the high limit
                        text += 'Noise Eater filter failed for box {}, channel {}, variable {}.  Value was {}, above high limit {}.'.format(i[0], i[1], i[2], d, i[4])
                        failed = True
                    elif d < i[3]:
                        # data is below the low limit
                        text += 'Noise Eater filter failed for box {}, channel {}, variable {}.  Value was {}, below low limit {}.'.format(i[0], i[1], i[2], d, i[3])
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
