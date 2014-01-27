'''LabView.py
This file holds everything needed to talk to the PXI crate known as HEXQC2, running LabView.  It can be modified in the future for other LabView systems.
On the LabView end, server.vi must be running, part of this package in the labview directory.

Part of the AQuA Cesium Controller software package

author=Martin Lichtman
created=2013-10-08
modified>=2013-10-08
'''

import TCP, HSDIO, piezo, DDS, RF_generators, AnalogOutput, DAQmxPulse, Camera
from atom.api import Bool, Int, Str, Member, Typed
from instrument_property import FloatProp
from cs_instruments import Instrument
import numpy, struct
import logging
from cs_errors import PauseError
logger = logging.getLogger(__name__)

class LabView(Instrument):
    enabled=Bool()
    port=Int()
    IP=Str()
    connected=Bool()
    msg=Str()
    HSDIO=Member()
    DDS=Member()
    piezo=Member()
    RF_generators=Member()
    AnalogOutput=Member()
    DAQmxPulse=Member()
    results=Member()
    sock=Member()
    camera=Member()
    timeout=Typed(FloatProp)
    error=Bool()
    log=Str()

    
    '''This is a meta instrument which encapsulates the capability of the HEXQC2 PXI system. It knows about several subsystems (HSDIO, DAQmx, Counters, Camera), and can send settings and commands to a corresponding Labview client.'''
    def __init__(self,experiment):
        super(LabView,self).__init__('LabView',experiment,'for communicating with a LabView system')
        self.HSDIO=HSDIO.HSDIO(experiment)
        self.DDS=DDS.DDS(experiment)
        self.piezo=piezo.Piezo(experiment)
        self.RF_generators=RF_generators.RF_generators(experiment)
        self.AnalogOutput=AnalogOutput.AnalogOutput(experiment)
        self.DAQmxPulse=DAQmxPulse.DAQmxPulse(experiment)
        self.camera=Camera.HamamatsuC9100_13(experiment)
        self.results={}
        #self.Counter=Counter.Counter(experiment)
        
        self.instruments=[self.HSDIO,self.DDS,self.piezo,self.RF_generators,self.AnalogOutput,self.DAQmxPulse,self.camera] #,self.Counter]
        
        self.sock=None
        self.connected=False
        
        self.timeout=FloatProp('timeout',experiment,'how long before LabView gives up and returns [s]','0.5')
        
        self.properties+=['IP','port','enabled','connected','timeout','HSDIO','DDS','piezo','RF_generators','AnalogOutput','DAQmxPulse','camera']
    
    def initialize(self):
        if self.enabled:
            #check for an old socket and delete it
            if self.sock is not None:
                print 'debug LabView.initialize() closing sock'
                self.sock.close()
                del self.sock
            # Create a TCP/IP socket
            try:
                print 'debug LabView.initialize() opening sock'
                self.sock=TCP.CsClientSock(self.IP,self.port,parent=self)
            except:
                logger.warning('Failed to open TCP socket in LabView.initialize()')
            else:
                print 'LabView.initialize sock opened'
                self.connected=True
            for i in self.instruments:
                i.initialize()
            self.isInitialized=True
        
    def close(self):
        if self.sock:
            self.sock.close()
        self.connected=False
        self.isInitialized=False
    
    def update(self):
        super(LabView,self).update()
        self.msg=self.toHardware()
        if self.enabled:
            if self.isInitialized:
                if self.connected:
                    self.sock.settimeout(self.timeout.value)
                    self.sock.sendmsg(self.msg)
                    #wait for response
                    try:
                        rawdata=self.sock.receive()
                    except IOError:
                        logger.warning('Timeout while waiting for LabView to return data in LabView.update()')
                        raise PauseError
                    else:
                        self.results=self.sock.parsemsg(rawdata)
                        for key,value in self.results.iteritems():
                            #print 'key: {} value: {}'.format(key,str(value)[:40])
                            if key=='error':
                                self.error=bool(value)
                            elif key=='log':
                                self.log+=value
                else:
                    logger.warning('LabView instrument claims to be initialized, but is not connected in LabView.update()')
                    raise PauseError
            else:
                logger.warning('LabView instrument should be initialized already, but is not, in LabView.update()')
                raise PauseError
    
    def start(self):
        if self.enabled:
            if self.isInitialized:
                if self.connected:
                    #tell the LabView instruments to measure
                    self.msg='<LabView><command>measure</command></LabView>'
                    self.sock.sendmsg(self.msg)
                    #wait for response
                    while not self.experiment.timeOutExpired:
                        try:
                            rawdata=self.sock.receive()
                        except IOError:
                            print 'Waiting for data'
                        if rawdata is not None:
                            self.results=self.sock.parsemsg(rawdata)
                            break
                else:
                    logger.warning('LabView instrument claims to be initialized, but is not connected in LabView.start()')
                    raise PauseError
            else:
                logger.warning('LabView instrument should be initialized already, but is not, in LabView.start()')
                raise PauseError
            
        self.isDone=True
    
    def writeResults(self,hdf5):
        '''Write the previously obtained results to the experiment hdf5 file.
        hdf5 is an hdf5 group, typically the data group in the appropriate part of the
        hierarchy for the current measurement.'''
        for key,value in self.results.iteritems():
            #print 'key: {} value: {}'.format(key,str(value)[:40])
            if key.startswith('Hamamatsu/shots/'):
                #specific protocol for images: turn them into 2D numpy arrays
                
                #unpack the image in 2 byte chunks
                array=numpy.array(struct.unpack('!'+str(int(len(value)/2))+'H',value))
                
                #the dictionary is unpacked alphabetically, so if width and height were
                #transmitted they should be loaded already
                try: #if ('Hamamatsu/rows' in hdf5) and ('Hamamtsu/columns' in hdf5):
                    array.resize((int(hdf5['Hamamatsu/rows'].value),int(hdf5['Hamamatsu/columns'].value)))
                except Exception as e:
                    print 'no resize:'+str(e)
                hdf5[key]=array
            elif key=='error':
                self.error=bool(value)
                hdf5[key]=self.error
            elif key=='log':
                self.log+=value
                hdf5[key]=value
            else:
                # no special protocol
                hdf5[key]=value
        if ('error' in hdf5) and (hdf5['error'].value):
            if ('log' in hdf5):
                logger.warning('LabView error.  Log:\n'+hdf5['log'].value)
            else:
                logger.warning('LabView error.  No log available.')
            raise PauseError
    
    def initializeDDS(self):
        raise NotImplementedError
    
    def loadDDS(self):
        raise NotImplementedError