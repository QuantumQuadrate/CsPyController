"""
LabView.py
This file holds everything needed to talk to the PXI crate known as HEXQC2, running LabView.  It can be modified in the future for other LabView systems.
On the LabView end, server.vi must be running, part of this package in the labview directory.

Part of the AQuA Cesium Controller software package

author=Martin Lichtman
created=2013-10-08
modified>=2014-04-08
"""

from __future__ import division
__author__ = 'Martin Lichtman'
import logging
logger = logging.getLogger(__name__)

from cs_errors import PauseError

import TCP, HSDIO, piezo, RF_generators, AnalogOutput, AnalogInput, DAQmxDO, Camera, TTL, Counter
from atom.api import Bool, Str, Member, Typed
from instrument_property import FloatProp
from cs_instruments import Instrument
import numpy, struct, traceback, threading

def toBool(x):
    if (x == 'False') or (x == 'false'):
        return False
    elif (x == 'True') or (x == 'true'):
        return True
    else:
        return bool(x)

class LabView(Instrument):
    """This is a meta instrument which encapsulates the capability of the HEXQC2 PXI system.
    It knows about several subsystems (HSDIO, DAQmx, Counters, Camera), and can send settings and commands to a
    corresponding Labview client."""
    port = Member()
    IP = Str()
    connected = Member()
    msg = Str()
    HSDIO = Member()
    piezo = Member()
    RF_generators = Member()
    AnalogOutput = Member()
    #AnalogOutput2 = Member() # Secondary analog output instrument.
    AnalogInput = Member()
    DAQmxDO = Member()
    Counters = Member()
    camera = Member()
    TTL = Member()
    results = Member()
    sock = Member()
    timeout = Typed(FloatProp)
    error = Bool()
    log = Str()
    cycleContinuously = Member()

    def __init__(self, experiment):
        super(LabView, self).__init__('LabView', experiment, 'for communicating with a LabView system')

        # defaults
        self.port = 0
        self.connected = False
        self.error = False
        self.cycleContinuously = False

        self.connected = False
        self.HSDIO = HSDIO.HSDIO('HSDIO', experiment)
        self.piezo = piezo.Piezo(experiment)
        self.RF_generators = RF_generators.RF_generators(experiment)
        self.AnalogOutput = AnalogOutput.AnalogOutput(experiment)
        self.AnalogInput = AnalogInput.AnalogInput(experiment)
        self.Counters = Counter.Counters('Counters', experiment)
        self.DAQmxDO = DAQmxDO.DAQmxDO(experiment)
        self.camera = Camera.HamamatsuC9100_13(experiment)
        self.TTL = TTL.TTL(experiment)
        self.results = {}

        self.instruments = [self.HSDIO, self.piezo, self.RF_generators, self.AnalogOutput, self.AnalogInput,
                            self.Counters, self.DAQmxDO, self.camera, self.TTL]

        self.sock = None
        self.connected = False

        self.timeout = FloatProp('timeout', experiment, 'how long before LabView gives up and returns [s]', '1.0')

        self.properties += ['IP', 'port', 'timeout', 'AnalogOutput', 'AnalogInput', 'HSDIO',
                            'piezo', 'RF_generators', 'DAQmxDO', 'camera', 'TTL', 'Counters', 'cycleContinuously']
        self.doNotSendToHardware += ['IP', 'port', 'enable']

    def openThread(self):
        thread = threading.Thread(target=self.initialize)
        thread.daemon = True
        thread.start()

    def open(self):

        if self.enable:

            logger.debug('Opening LabView TCP.')
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
            logger.debug('LabView.open() opening sock')
            try:
                self.sock = TCP.CsClientSock(self.IP, self.port, parent=self)
            except Exception as e:
                logger.warning('Failed to open TCP socket in LabView.open():\n{}\n'.format(e))
                raise PauseError
            logger.debug('LabView.open() sock opened')
            self.connected = True

    def initialize(self):
        self.open()
        logger.debug('Initializing LabView instruments.')
        super(LabView, self).initialize()

    def close(self):
        if self.sock is not None:
            self.sock.close()
        self.connected = False
        self.isInitialized = False

    def update(self):
        """Send the current values to hardware."""

        super(LabView, self).update()
        self.send(self.toHardware())

    def start(self):
        self.send('<LabView><measure/></LabView>')

    def writeResults(self, hdf5):
        """Write the previously obtained results to the experiment hdf5 file.
        hdf5 is an hdf5 group, typically the data group in the appropriate part of the
        hierarchy for the current measurement."""

        for key, value in self.results.iteritems():
            # print 'key: {} value: {}'.format(key,str(value)[:40])
            if key.startswith('Hamamatsu/shots/'):
                # specific protocol for images: turn them into 2D numpy arrays

                # unpack the image in 2 byte chunks
                # print "len(value)={}".format(len(value))
                array = numpy.array(struct.unpack('!'+str(int(len(value)/2))+'H', value), dtype=numpy.uint16)

                # the dictionary is unpacked alphabetically, so if width and height were
                # transmitted they should be loaded already
                try:  # if ('Hamamatsu/rows' in hdf5) and ('Hamamtsu/columns' in hdf5):
                    array.resize((int(hdf5['Hamamatsu/rows'].value), int(hdf5['Hamamatsu/columns'].value)))
                except Exception as e:
                    logger.error('unable to resize image, check for Hamamatsu row/column data:\n'+str(e))
                    raise PauseError
                try:
                    hdf5[key] = array
                except Exception as e:
                    logger.error('in LabView.writeResults() doing hdf5[key]=array for key='+key+'\n'+str(e))
                    raise PauseError

            elif key == 'TTL/data':
                # boolean data was stored as 2 byte signed int
                array = numpy.array(struct.unpack('!'+str(int(len(value)/2))+'h', value), dtype=numpy.bool_)
                try:
                    dims = map(int, self.results['TTL/dimensions'].split(','))
                    array.resize(dims)
                except:
                    logger.exception('unable to resize TTL data, check for TTL/dimensions in returned data.')
                    raise PauseError
                try:
                    hdf5[key] = array
                except:
                    logger.exception('in LabView.writeResults() doing hdf5[{}]'.format(key))
                    raise PauseError

            elif key == 'AI/data':
                # analog data was stored as big-endian (network order) doubles floats (8-bytes)
                array = numpy.array(struct.unpack('!'+str(int(len(value)/8))+'d', value), dtype=numpy.float64)
                try:
                    dims = map(int, self.results['AI/dimensions'].split(','))
                    array.resize(dims)
                except:
                    logger.exception('unable to resize AI data, check for AI/dimensions in returned data.')
                    raise PauseError
                try:
                    hdf5[key] = array
                except:
                    logger.error('in LabView.writeResults() doing hdf5[{}]'.format(key))
                    raise PauseError

            elif key == 'counter/data':
                # counter data was stored as big-endian (network order) unsigned long (4-byte) integers
                array = numpy.array(struct.unpack('!'+str(int(len(value)/4))+'L', value), dtype=numpy.uint32)
                try:
                    dims = map(int, self.results['counter/dimensions'].split(','))
                    array.resize(dims)
                except:
                    logger.exception('unable to resize counter data, check for counter/dimensions in returned data.')
                    raise PauseError

                # take the difference of successive elements.
                # Set the first element always to zero.
                # This is tested to work correctly in case of 32-bit rollover.
                array[:, 0] = 0
                array[:, 1:] = array[:, 1:] - array[:, :-1]
                try:
                    hdf5[key] = array
                except:
                    logger.exception('in LabView.writeResults() doing hdf5[{}]'.format(key))
                    raise PauseError

            else:
                # no special protocol
                try:
                    hdf5[key] = value
                except:
                    logger.error('in LabView.writeResults() doing hdf5[key]=value for key='+key+'\n'+str(e))
                    raise PauseError

    def send(self, msg):
        results = {}
        if self.enable:
            if not (self.isInitialized and self.connected):
                logger.debug("TCP is not both initialized and connected.  Reinitializing TCP in LabView.send().")
                self.initialize()

            #display message on GUI
            self.set_dict({'msg': msg})

            #send message
            logger.debug('LabView sending message ...')
            try:
                self.sock.settimeout(self.timeout.value)
                self.sock.sendmsg(msg)
            except IOError:
                logger.warning('Timeout while waiting for LabView to send data in LabView.send():\n{}\n'.format(e))
                self.connected = False
                raise PauseError
            except Exception as e:
                logger.warning('while sending message in LabView.send():\n{}\n{}\n'.format(e, traceback.format_exc()))
                self.connected = False
                raise PauseError

            # wait for response
            logger.debug('Labview waiting for response ...')
            try:
                rawdata = self.sock.receive()
            except IOError as e:
                logger.warning('Timeout while waiting for LabView to return data in LabView.send():\n{}\n'.format(e))
                self.connected = False
                raise PauseError
            except Exception as e:
                logger.warning('in LabView.sock.receive:\n{}\n{}\n'.format(e, traceback.format_exc()))
                self.connected = False
                raise PauseError

            # parse results
            logger.debug('Parsing TCP results ...')
            results = self.sock.parsemsg(rawdata)
            # for key, value in self.results.iteritems():
            #    print 'key: {} value: {}'.format(key,str(value)[:40])

            # report LabView errors
            log = ''
            if 'log' in results:
                log = results['log']
                self.set_gui({'log': self.log + log})
            if 'error' in results:
                error = toBool(results['error'])
                self.set_gui({'error': error})
                if error:
                    logger.warning('Error returned from LabView.send:\n{}\n'.format(log))
                    raise PauseError

        self.results = results
        self.isDone = True
        return results

    def evaluate(self):
        if self.experiment.allow_evaluation:
            logger.debug('LabView.evaluate()')
            return super(LabView, self).evaluate()
