"""
cs_instruments.py
author = Martin Lichtman
created = 2013-07-10
modified >= 2013-07-10

This file is part of the Cesium Control program designed by Martin Lichtman in 2013 for the AQuA project.
It contains classes that represent instruments
"""

from __future__ import division
__author__ = 'Martin Lichtman'
import logging
logger = logging.getLogger(__name__)

from cs_errors import PauseError

from atom.api import Bool, Member, Str, Typed
from instrument_property import Prop, FloatProp
import traceback, threading
import TCP

def toBool(x):
    if (x == 'False') or (x == 'false'):
        return False
    elif (x == 'True') or (x == 'true'):
        return True
    else:
        return bool(x)

class Instrument(Prop):
    enable = Bool(False)
    isInitialized = Bool()
    isDone = Bool()
    instruments = Member()
    data = Member()

    def __init__(self, name, experiment, description=''):
        super(Instrument, self).__init__(name, experiment, description)
        self.instruments = []
        self.isInitialized = False
        self.isDone = True
        self.data = []
        self.properties += ['enable']

    def evaluate(self):
        """Checks to see if the Instrument is enabled, before calling Prop.evaluate()"""
        if self.enable:
            logger.debug('{}.evaluate()'.format(self.name))
            return super(Instrument, self).evaluate()

    def toHardware(self):
        """Checks to see if the Instrument is enabled, before calling Prop.toHardware()"""
        if self.enable:
            return super(Instrument, self).toHardware()
        else:
            return '<{}><enable>False</enable></{}>'.format(self.name, self.name)

    def update(self):
        """Sends current settings to the instrument.  This function is run at the beginning of every new iteration.
        Does not explicitly call evaluate, to avoid duplication of effort.
        All calls to evaluate should already have been accomplished."""

        for i in self.instruments:
            if i.enable:
                #check that the instruments are initialized
                if not i.isInitialized:
                    i.initialize()  # reinitialize
                i.update()  # put the settings to where they should be at this iteration

        #the details of sending to each instrument must be handled in a subclass
        #first call super(subclass,self).update() to call this method
        #then do the hardware update, probably involving sending the toXML string via TCP/IP

    def start(self):
        """Enables the instrument to begin a measurement.  Sent at the beginning of every measurement.
        Actual output or input from the measurement may yet wait for a signal from another device."""
        pass

    def stop(self):
        """Stops output as soon as possible.  This is not run during the course of a normal instrument."""
        pass

    def initialize(self):
        """Sends initialization commands to the instrument"""
        for i in self.instruments:
            i.initialize()
        self.isInitialized = True

    def acquire_data(self):
        """Instruments that are not aware of the experiment timing can not be programmed to acquire
        data during start().  Instead they can be programmed to get data in this method, which is
        called after start() has completed."""

        for i in self.instruments:
            if i.enable:
                i.acquire_data()

    def writeResults(self, hdf5):
        """Write results to the hdf5 file.  Must be overwritten in subclass to do anything."""
        pass

class TCP_Instrument(Instrument):
    """
    This class inherets from Instrument but has the capability to do TCP communication to an instrument server.
    This class is generalized from the LabView class.
    """

    port = Member()
    IP = Str()
    connected = Member()
    msg = Str()
    results = Member()
    sock = Member()
    timeout = Typed(FloatProp)
    error = Bool()
    log = Str()

    def __init__(self, name, experiment, description=''):
        super(TCP_Instrument, self).__init__(name, experiment, description)

        # defaults
        self.port = 0
        self.connected = False
        self.error = False

        self.connected = False
        self.results = {}

        self.sock = None
        self.connected = False

        self.timeout = FloatProp('timeout', experiment, 'how long before TCP gives up [s]', '1.0')

        self.properties += ['IP', 'port', 'timeout']
        self.doNotSendToHardware += ['IP', 'port', 'timeout']

    def openThread(self):
        thread = threading.Thread(target=self.initialize)
        thread.daemon = True
        thread.start()

    def open(self):

        if self.enable:

            logger.debug('Opening {} TCP.'.format(self.name))
            # check for an old socket and delete it
            if self.sock is not None:
                logger.debug('Closing previously open sock.')
                try:
                    self.sock.close()
                except Exception as e:
                    logger.debug('Ignoring exception during sock.close() of previously open sock.\n{}\n'.format(e))
                try:
                    del self.sock
                except Exception as e:
                    logger.debug('Ignoring exception during sock.close() of previously open sock.\n{}\n'.format(e))

            # Create a TCP/IP socket
            logger.debug('{}.open() opening sock'.format(self.name))
            try:
                self.sock = TCP.CsClientSock(self.IP, self.port, parent=self)
            except Exception as e:
                logger.warning('Failed to open TCP socket in {}.open():\n{}\n'.format(self.name, e))
                raise PauseError
            logger.debug('{}.open() sock opened'.format(self.name))
            self.connected = True

    def initialize(self):
        self.open()
        logger.debug('Initializing LabView instruments.')
        super(TCP_Instrument, self).initialize()

    def close(self):
        if self.sock is not None:
            self.sock.close()
        self.connected = False
        self.isInitialized = False

    def update(self):
        """Send the current values to hardware."""

        super(TCP_Instrument, self).update()
        self.send(self.toHardware())

    def start(self):
        self.isDone = True

    def writeResults(self, hdf5):
        """Write the previously obtained results to the experiment hdf5 file.
        hdf5 is an hdf5 group, typically the data group in the appropriate part of the
        hierarchy for the current measurement."""

        for key, value in self.results.iteritems():

            # no special protocol
            try:
                hdf5[key] = value
            except Exception as e:
                logger.error('Exception in {}.writeResults() doing hdf5[key]=value for key={}\n'.format(key, self.name, e))
                raise PauseError

    def send(self, msg):
        results = {}
        if self.enable:
            if not (self.isInitialized and self.connected):
                logger.debug('TCP is not both initialized and connected.  Reinitializing TCP in {}.send().'.format(self.name))
                self.initialize()

            # display message on GUI
            self.set_dict({'msg': msg})

            # send message
            #logger.info('{} sending message ...'.format(self.name))
            #logger.info('msg: `{}`'.format(msg))
            try:
                self.sock.settimeout(self.timeout.value)
                self.sock.sendmsg(msg)
            except IOError as e:
                logger.warning('Timeout while waiting to send data in {}.send():\n{}\n'.format(self.name, e))
                self.connected = False
                raise PauseError
            except Exception as e:
                logger.warning('Exception while sending message in {}.send():\n{}\n{}\n'.format(self.name, e, traceback.format_exc()))
                self.connected = False
                raise PauseError

            # wait for response
            logger.info('{} waiting for response ...'.format(self.name))
            try:
                rawdata = self.sock.receive()
            except IOError as e:
                logger.warning('Timeout while waiting for return data in {}.send():\n{}\n'.format(self.name, e))
                self.connected = False
                raise PauseError
            except Exception:
                logger.exception('Exception in {}.sock.receive.')
                self.connected = False
                raise PauseError

            # parse results
            logger.info('Parsing TCP results ...')
            results = self.sock.parsemsg(rawdata)
            # for key, value in self.results.iteritems():
            #    print 'key: {} value: {}'.format(key,str(value)[:40])

            # report server errors
            log = ''
            if 'log' in results:
                log = results['log']
                self.set_gui({'log': self.log + log})
            if 'error' in results:
                error = toBool(results['error'])
                self.set_gui({'error': error})
                if error:
                    logger.warning('Error returned from {}.send:\n{}\n'.format(self.name, log))
                    raise PauseError

        self.results = results
        self.isDone = True
        return results
