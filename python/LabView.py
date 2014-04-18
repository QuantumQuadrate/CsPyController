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
import logging
logger = logging.getLogger(__name__)

from cs_errors import PauseError

import TCP, HSDIO, piezo, DDS, RF_generators, AnalogOutput, DAQmxDO, Camera, EchoBox
from atom.api import Bool, Str, Member, Typed
from instrument_property import FloatProp
from cs_instruments import Instrument
import numpy, struct, traceback, threading, sys

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
    enabled = Member()
    port = Member()
    IP = Str()
    connected = Member()
    msg = Str()
    HSDIO = Member()
    DDS = Member()
    piezo = Member()
    RF_generators = Member()
    AnalogOutput = Member()
    DAQmxDO = Member()
    results = Member()
    sock = Member()
    camera = Member()
    timeout = Typed(FloatProp)
    error = Bool()
    log = Str()
    cycleContinuously = Member()

    def __init__(self, experiment):
        super(LabView, self).__init__('LabView', experiment, 'for communicating with a LabView system')

        #defaults
        self.enabled = False
        self.port = 0
        self.connected = False
        self.error = False
        self.cycleContinuously = False

        self.connected = False
        self.HSDIO = HSDIO.npHSDIO('HSDIO', experiment)
        self.DDS = DDS.DDS(experiment, self)
        self.piezo = piezo.Piezo(experiment)
        self.RF_generators = RF_generators.RF_generators(experiment)
        self.AnalogOutput = AnalogOutput.AnalogOutput(experiment)
        self.DAQmxDO = DAQmxDO.DAQmxDO(experiment)
        self.camera = Camera.HamamatsuC9100_13(experiment)
        self.results = {}
        #self.Counter = Counter.Counter(experiment)
        
        self.instruments = [self.HSDIO, self.DDS, self.piezo, self.RF_generators, self.AnalogOutput, self.DAQmxDO,
                            self.camera] #,self.Counter]
        
        self.sock = None
        self.connected = False
        
        self.timeout = FloatProp('timeout', experiment, 'how long before LabView gives up and returns [s]', '1.0')
        
        self.properties += ['IP', 'port', 'enabled', 'connected', 'timeout', 'AnalogOutput', 'HSDIO', 'DDS', 'piezo', 'RF_generators',
                            'DAQmxDO', 'camera', 'cycleContinuously']  # ,'EchoBox']
        self.doNotSendToHardware += ['IP', 'port', 'enabled', 'connected']

    def openThread(self):
        thread = threading.Thread(target=self.initialize)
        thread.daemon = True
        thread.start()

    def open(self):
        if self.enabled:
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
        for key,value in self.results.iteritems():
            #print 'key: {} value: {}'.format(key,str(value)[:40])
            if key.startswith('Hamamatsu/shots/'):
                #specific protocol for images: turn them into 2D numpy arrays
                
                #unpack the image in 2 byte chunks
                #print "len(value)={}".format(len(value))
                array = numpy.array(struct.unpack('!'+str(int(len(value)/2))+'H', value), dtype=numpy.uint16)
                
                #the dictionary is unpacked alphabetically, so if width and height were
                #transmitted they should be loaded already
                try: #if ('Hamamatsu/rows' in hdf5) and ('Hamamtsu/columns' in hdf5):
                    array.resize((int(hdf5['Hamamatsu/rows'].value),int(hdf5['Hamamatsu/columns'].value)))
                except Exception as e:
                    print 'unable to resize image, check for Hamamatsu row/column data:'+str(e)
                    raise PauseError
                try:
                    hdf5[key]=array
                except Exception as e:
                    logger.warning('in LabView.writeResults() doing hdf5[key]=array for key='+key+'\n'+str(e))
                    raise PauseError
            elif key=='error':
                self.error=toBool(value)
                try:
                    hdf5[key]=self.error
                except Exception as e:
                    logger.warning('in LabView.writeResults() doing hdf5[key]=self.error for key='+key+'\n'+str(e))
                    raise PauseError

            elif key=='log':
                self.log+=value
                try:
                    hdf5[key]=value
                except Exception as e:
                    logger.warning('in LabView.writeResults() doing hdf5[key]=value for key='+key+'\n'+str(e))
                    raise PauseError

            else:
                # no special protocol
                try:
                    hdf5[key]=value
                except Exception as e:
                    logger.warning('in LabView.writeResults() doing hdf5[key]=value for key='+key+'\n'+str(e))
                    raise PauseError
        
        try:
            if ('error' in hdf5) and (hdf5['error'].value):
                if ('log' in hdf5):
                    logger.warning('LabView error.  Log:\n'+hdf5['log'].value)
                else:
                    logger.warning('LabView error.  No log available.')
                raise PauseError
        except PauseError:
            raise PauseError
        except Exception as e:
            logger.warning("while getting hdf5['error']\n"+str(e))
            raise PauseError
    
    def send(self, msg):
        results = {}
        if self.enabled:
            if not (self.isInitialized and self.connected):
                logger.debug("TCP is not both initialized and connected.  Reinitializing TCP in LabView.send().")
                self.initialize()

            #display message on GUI
            self.msg = msg

            #send message
            sys.stdout.write('LabView: sending ...')
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

            #wait for response
            sys.stdout.write(' waiting for response ...')
            try:
                rawdata = self.sock.receive()
            except IOError:
                logger.warning('Timeout while waiting for LabView to return data in LabView.send():\n{}\n'.format(e))
                self.connected = False
                raise PauseError
            except Exception as e:
                logger.warning('in LabView.sock.receive:\n{}\n{}\n'.format(e, traceback.format_exc()))
                self.connected = False
                raise PauseError

            #parse results
            sys.stdout.write(' parsing results ...')
            results = self.sock.parsemsg(rawdata)
            #for key, value in self.results.iteritems():
            #    print 'key: {} value: {}'.format(key,str(value)[:40])
            if 'log' in self.results:
                self.log += self.results['log']
            if 'error' in self.results:
                self.error = toBool(self.results['error'])
                if self.error:
                    logger.warning('Error returned from LabView.send:\n{}\n'.format(self.results['log']))
                    raise PauseError
            sys.stdout.write(' done.\n')
        self.results = results
        self.isDone = True
        return results
