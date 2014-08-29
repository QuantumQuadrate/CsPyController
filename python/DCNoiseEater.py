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
from atom.api import Str, Typed, Member, Bool
from enaml.application import deferred_call
from instrument_property import ListProp
from cs_instruments import Instrument
from analysis import AnalysisWithFigure


class DCNoiseEaters(Instrument):
    # Communicates with a bunch of DC Noise Eater boxes that are attached directly to the experiment
    # computer via USB-to-serial Parallax Prop Plugs.  These present themselves to python as simple
    # COM ports.

    version = '2014.08.28'
    boxes = Typed(ListProp)
    deviceList = Member()
    deviceListStr = Str()
    boxDescriptionList = Member()

    def __init__(self, experiment):
        super(DCNoiseEater, self).__init__('DCNoiseEater', experiment)
        self.boxes = ListProp('boxes', experiment, listElementType=DCNoiseEater, listElementName='box', listElementKwargs={'DCNoiseEater': self})
        self.properties += ['version', 'boxes', 'deviceList']

    def evaluate(self):
        if self.experiment.allow_evaluation:
            logger.debug('DCNoiseEaters.evaluate()')
            super(DCNoiseEaters, self).evaluate()
            self.updateBoxDescriptionList()

    def getDeviceListThread(self):
        # calls getDeviceList() in a separate thread to leave the GUI free
        thread = threading.Thread(target=self.getDeviceList)
        thread.daemon = True
        thread.start()

    def getDeviceList(self):
        # list the available COM ports.  The port we want is usually:
        # [('COM17', 'USB Serial Port (COM17)', 'FTDIBUS\\VID_0403+PID_6001+A700AC57A\\0000')]
        result = list(serial.tools.list_ports.comports())
        deviceList = [i[0] for i in result]  # a list of the string necessary to connect to each com port
        deviceStrList = ['{}, {}, {}'.format(*i) for i in result]  # a list of all the info about each com port
        deferred_call(setattr, self, 'deviceList', deviceListStr.split('\n'))

    def updateBoxDescriptionList(self):
        #sets the descriptions shown in the combo box in the GUI
        try:
            deferred_call(setattr, self, 'boxDescriptionList', [str(i)+' '+n.description for i, n in enumerate(self.boxes)])
        except RuntimeError:
            #the GUI is not yet active
            self.boxDescriptionList = [str(i)+' '+n.description for i, n in enumerate(self.boxes)]


class channel(object):

    def __init__(self, channelNum):

        self.channelNum = channelNum

        # read/write variables
        self.update = False  # bool
        self.mode = 0  # int8
        self.warnSetting = False  # bool
        self.limitRange = 0  # int16
        self.invert = False  # bool
        self.integrationTime = 100  # int16
        self.trigNum = 0  # int8
        self.measNum = 0  # int8
        self.kp = 2560  # int16
        self.ki = 64  # int16
        self.setpoint = .9823

        # variables from DC noise eater
        # read only
        self.average = 0  # int16
        self.error = 0  # int16
        self.vin = 0  # int16
        self.vout = 0  # int16
        self.warning = False  # bool

    def settings_in_from_hardware(self, data):
        # format the data returned by the noise eater
        # the code 'b?h?hbbhhhhhhh?' specifies b: signed int8, ?: binary stored as 8 bits, h: uint16
        # '<' is because the propeller chip is little-endian
        self.mode, self.warnSetting, self.limitRange, self.invert, self.integrationTime, self.trigNum, self.measNum, self.kp, self.ki, self.setpoint, self.average, self.error, self.vin, self.vout, self.warning = struct.unpack('<b?h?hbbhhhhhhh?', data)

    def settings_out_to_hardware(self):
        # return a 15 byte array that will be what is sent to the hardware for this channel
        # the code 'b?h?hbbhhh' specifies the 15 bytes as b: signed int8, ?: binary stored as 8 bits, h: uint16
        # '<' is because the propeller chip is little-endian
        data = struct.pack('<b?h?hbbhhh', self.mode, self.warnSetting, self.limitRange, self.invert, self.integrationTime, self.trigNum, self.measNum, self.kp, self.ki, self.setpoint)
        return data

    def print_settings(self):
        # print all the settings for this channel

        print 'channel {} mode {} warnSetting {} limitRange {} invert {} integrationTime {} trigNum {} measNum {} kp {} ki {} setpoint {}'.format(
            self.channelNum, self.mode, self.warnSetting, self.limitRange, self.invert, self.integrationTime,
            self.trigNum, self.measNum, self.kp, self.ki, self.setpoint)
        print 'average {} error {} vin {} vout {} warning {}'.format(
            self.average, self.error, self.vin, self.vout, self.warning)
        print '\n'


class DCNoiseEater(Instrument):
    version = '2014.08.28'

    comport = Str()
    data = Member()
    channels = Typed(ListProp)

    def __init__(self, experiment):
        super(DCNoiseEater, self).__init__('DCNoiseEater', experiment, 'DC NoiseEater')
        self.properties += ['version', 'comport', 'channels']

    def initialize(self):
        """Open the serial port"""
        if self.enable:

            # open the serial port
            ser = serial.Serial(comport, 38400, timeout=1, writeTimeout=1)
            logger.debug('opened: {}'.format(ser.name))  # checks which port was really used

            # create a channel object for each noise eater channel
            self.channels = ListProp('channels', experiment, listElementType=channel, listElementName='channel')

            self.isInitialized = True

    def update(self):
        """
        Every iteration, send the motors updated positions.
        """
        if self.enable:
            msg = ''
            try:
                for i in motors:
                    # get the serial number, motor, and position from each motor
                    msg = i.update()
                    # send it to the picomotor server
                    self.socket.sendmsg(msg)
            except Exception as e:
                logger.error('Problem setting Picomotor position, closing socket:\n{}\n{}\n'.format(msg, e))
                self.socket.close()
                self.isInitialized = False
                raise PauseError

    def acquire_data(self):
        """Send a message to the C# program requesting data, and then receive it."""
        if self.enable:
            try:
                self.socket.sendmsg('get')
            except Exception as e:
                logger.error('Problem getting DC Noise Eater data, closing socket:\n{}\n{}\n'.format(msg, e))
                self.socket.close()
                self.isInitialized = False
                raise PauseError

            # TODO: now receive the data, and parse it into self.data

    def writeResults(self, hdf5):
        """Write results to the hdf5 file.  Must be overwritten in subclass to do anything."""
        hdf5['DC_noise_eater'] = self.data

    # specify how to create output data from the channel objects
    def format_output(channels):
        # create a byte which encodes whether or not to update each channel
        data = chr(sum([2**c.channelNum for c in channels if c.update]))

        #turn off future updates until re-enabled
        for c in channels:
            c.update = False

        # append 15 bytes for each channel, encoding the settings
        for c in channels:
            data += c.settings_out_to_hardware()

        return data

class DCNoiseEaterGraph(AnalysisWithFigure):
    """Plots a region of interest sum after every measurement"""
    version = '2014.08.28'
    enable = Bool()
    data = Member()

    def __init__(self, name, experiment, description=''):
        super(DCNoiseEaterGraph, self).__init__(name, experiment, description)
        self.properties += ['enable']
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

    def clear(self):
        self.data = None
        self.updateFigure()

    def updateFigure(self):
        try:
            fig = self.backFigure
            fig.clf()

            if self.data is not None:
                #make one plot
                ax = fig.add_subplot(111)
                ax.plot(self.data)
                #add legend using the labels assigned during ax.plot()
                ax.legend()
            super(DCNoiseEaterGraph, self).updateFigure()
        except Exception as e:
            logger.warning('Problem in DCNoiseEaterGraph.updateFigure()\n:{}'.format(e))
