"""Laird_temperature.py
Part of the AQuA Cesium Controller software package

author=Martin Lichtman
created=2014-09-08
modified>=2014-09-08

This file creates an instrument that grabs data from the Laird temperature server,
which reads the box coldplate temperatures and sensors.

For this to work, the box_temperature_server.py must be running separately.
"""

from __future__ import division
__author__ = 'Martin Lichtman'
import logging
logger = logging.getLogger(__name__)
from cs_errors import PauseError

import threading, struct, traceback
import numpy
from atom.api import Int, Str, Bool, Member

from cs_instruments import Instrument
import TCP


class LairdTemperature(Instrument):
    # Communicates with a bunch of Laird temperature controllers via a separately running box_temperature_server.py

    version = '2014.09.08'
    IP = Str()
    port = Int()
    results = Member()
    sock = Member()
    connected = Bool()
    timeout = .1

    def __init__(self, name, experiment, description='Laird temperature controllers'):
        super(LairdTemperature, self).__init__(name, experiment, description)
        self.sock = None
        self.properties += ['version', 'IP', 'port']

    def start(self):
        if self.enable:
            self.send('get')
        self.isDone = True

    def open_thread(self):
        thread = threading.Thread(target=self.initialize)
        thread.daemon = True
        thread.start()

    def open(self):

        if self.enable:

            logger.debug('Opening TCP.')
            #check for an old socket and delete it
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
            logger.debug('opening sock')
            try:
                self.sock = TCP.CsClientSock(self.IP, self.port, parent=self)
            except Exception as e:
                logger.warning('Failed to open TCP socket in Laird.open():\n{}\n'.format(e))
                raise PauseError
            logger.debug('sock opened')
            self.connected = True

    def initialize(self):
        self.open()
        logger.debug('Initializing Laird instrument.')
        super(LairdTemperature, self).initialize()

    def close(self):
        if self.sock is not None:
            self.sock.close()
        self.connected = False
        self.isInitialized = False

    def writeResults(self, hdf5):
        """Write the previously obtained results to the experiment hdf5 file.
        hdf5 is an hdf5 group, typically the data group in the appropriate part of the
        hierarchy for the current measurement."""

        if self.enable:
            for key, value in self.results.iteritems():

                if key.startswith('Laird'):
                    # data was stored as 8 byte doubles
                    array = numpy.array(struct.unpack('!'+str(int(len(value)/8))+'d', value), dtype=numpy.float64)
                    try:
                        hdf5[key] = array
                    except Exception as e:
                        logger.error('in LairdTemperature.writeResults() doing hdf5[{}]\n{}'.format(key, e))
                        raise PauseError

    def send(self, msg):
        results = {}
        if self.enable:
            if not (self.isInitialized and self.connected):
                logger.debug("TCP is not both initialized and connected.  Reinitializing TCP in LairdTemperature.send().")
                self.initialize()

            #send message
            logger.debug('Laird sending message ...')
            try:
                self.sock.settimeout(self.timeout)
                self.sock.sendmsg(msg)
            except IOError as e:
                logger.warning('Timeout while waiting to send data in LairdTemperature.send():\n{}\n'.format(e))
                self.connected = False
                raise PauseError
            except Exception as e:
                logger.warning('while sending message in LairdTemperature.send():\n{}\n{}\n'.format(e, traceback.format_exc()))
                self.connected = False
                raise PauseError

            #wait for response
            logger.debug('Laird waiting for response ...')
            try:
                rawdata = self.sock.receive()
            except IOError as e:
                logger.warning('Timeout while waiting for Laird to return data in LairdTemperature.send():\n{}\n'.format(e))
                self.connected = False
                raise PauseError
            except Exception as e:
                logger.warning('in LairdTemperature.sock.receive:\n{}\n{}\n'.format(e, traceback.format_exc()))
                self.connected = False
                raise PauseError

            #parse results
            logger.debug('Parsing TCP results ...')
            results = self.sock.parsemsg(rawdata)

        self.results = results
        return results
