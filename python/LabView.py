'''LabView.py
This file holds everything needed to talk to the PXI crate known as HEXQC2, running LabView.  It can be modified in the future for other LabView systems.
On the LabView end, server.vi must be running, part of this package in the labview directory.

Part of the AQuA Cesium Controller software package

author=Martin Lichtman
created=2013-10-08
modified>=2013-10-08
'''

from cs_errors import PauseError, setupLog
logger=setupLog(__name__)

import TCP, HSDIO, piezo, DDS, RF_generators, AnalogOutput, DAQmxPulse, Camera, EchoBox
from atom.api import Bool, Int, Str, Member, Typed
from instrument_property import FloatProp
from cs_instruments import Instrument
import numpy, struct

def toBool(x):
    if (x=='False') or (x=='false'):
        return False
    elif (x=='True') or (x=='true'):
        return True
    else:
        return bool(x)

class LabView(Instrument):
    enabled=Bool()
    port=Int()
    IP=Str()
    connected=Bool(False)
    msg=Str()
    HSDIO=Member()
    DDS=Member()
    piezo=Member()
    RF_generators=Member()
    AnalogOutput=Member()
    DAQmxPulse=Member()
    EchoBox=Member()
    results=Member()
    sock=Member()
    camera=Member()
    timeout=Typed(FloatProp)
    error=Bool()
    log=Str()
    cycleContinuously=Bool(False)

    
    '''This is a meta instrument which encapsulates the capability of the HEXQC2 PXI system. It knows about several subsystems (HSDIO, DAQmx, Counters, Camera), and can send settings and commands to a corresponding Labview client.'''
    def __init__(self,experiment):
        super(LabView,self).__init__('LabView',experiment,'for communicating with a LabView system')
        self.HSDIO=HSDIO.HSDIO(experiment)
        self.DDS=DDS.DDS(experiment,self)
        self.piezo=piezo.Piezo(experiment)
        self.RF_generators=RF_generators.RF_generators(experiment)
        self.AnalogOutput=AnalogOutput.AnalogOutput(experiment)
        self.DAQmxPulse=DAQmxPulse.DAQmxPulse(experiment)
        self.camera=Camera.HamamatsuC9100_13(experiment)
        self.EchoBox=EchoBox.EchoBox(experiment)
        self.results={}
        #self.Counter=Counter.Counter(experiment)
        
        self.instruments=[self.HSDIO,self.DDS,self.piezo,self.RF_generators,self.AnalogOutput,self.DAQmxPulse,self.camera,self.EchoBox] #,self.Counter]
        
        self.sock=None
        self.connected=False
        
        self.timeout=FloatProp('timeout',experiment,'how long before LabView gives up and returns [s]','1.0')
        
        self.properties+=['IP','port','enabled','connected','timeout','HSDIO','DDS','piezo','RF_generators','AnalogOutput','DAQmxPulse','camera','cycleContinuously']#,'EchoBox']
        self.doNotSendToHardware+=['IP','port','enabled','connected']
    
    def open(self):
        if self.enabled:
            #check for an old socket and delete it
            if self.sock is not None:
                logger.debug('debug LabView.open() closing sock')
                self.sock.close()
                del self.sock
            # Create a TCP/IP socket
            try:
                logger.debug('LabView.open() opening sock')
                self.sock=TCP.CsClientSock(self.IP,self.port,parent=self)
            except:
                logger.warning('Failed to open TCP socket in LabView.open()')
            else:
                logger.debug('LabView.open() sock opened')
                self.connected=True
    
    def initialize(self):
        self.open()
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
                                self.error=toBool(value)
                            elif key=='log':
                                self.log+=value
                else:
                    logger.warning('LabView instrument claims to be initialized, but is not connected in LabView.update()')
                    raise PauseError
            else:
                logger.warning('LabView instrument should be initialized already, but is not, in LabView.update()')
                raise PauseError
    
    def start(self):
        self.send('<measure/>')
    
    def writeResults(self,hdf5):
        '''Write the previously obtained results to the experiment hdf5 file.
        hdf5 is an hdf5 group, typically the data group in the appropriate part of the
        hierarchy for the current measurement.'''
        for key,value in self.results.iteritems():
            #print 'key: {} value: {}'.format(key,str(value)[:40])
            if key.startswith('Hamamatsu/shots/'):
                #specific protocol for images: turn them into 2D numpy arrays
                
                #unpack the image in 2 byte chunks
                #print "len(value)={}".format(len(value))
                array=numpy.array(struct.unpack('!'+str(int(len(value)/2))+'H',value))
                
                #the dictionary is unpacked alphabetically, so if width and height were
                #transmitted they should be loaded already
                try: #if ('Hamamatsu/rows' in hdf5) and ('Hamamtsu/columns' in hdf5):
                    array.resize((int(hdf5['Hamamatsu/rows'].value),int(hdf5['Hamamatsu/columns'].value)))
                except Exception as e:
                    print 'unable to resize image, check for Hamamatsu row/column data:'+str(e)
                    raise PauseError
                #if self.experiment.saveData and self.experiment.save2013styleFiles:
                #    if hasattr(self,'camera') and self.camera.saveAsPNG:
                #            try:
                #                self.savePNG(array,os.path.join(self.experiment.measurementPath,'shot'+key.split('/')[-1]+'.png'))
                #            except Exception as e:
                #                logger.warning('problem saving PNG in LabView.writeResults()\n'+str(e))
                #                raise PauseError
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
    
    def send(self,msg):
        results={}
        if self.enabled:
            if not self.connected:
                logger.info('LabView was not initialized.  Initializing LabView in LabView.send({}...)'.format(msg[:40]))
                self.open()
            if self.connected:
                #tell the LabView instruments to measure
                self.msg='<LabView>'+msg+'</LabView>'
                self.sock.sendmsg(self.msg)
                #wait for response
                while not self.experiment.timeOutExpired:
                    try:
                        rawdata=self.sock.receive()
                    except IOError:
                        print 'Waiting for data'
                    if rawdata is not None:
                        #print 'data received: {}'.format(rawdata[:40])
                        results=self.sock.parsemsg(rawdata)
                        #print 'len(self.results)={}'.format(len(self.results))
                        break
            else:
                logger.warning('LabView instrument is not connected in LabView.send({})'.format(msg))
                raise PauseError
        self.results=results
        self.isDone=True
        return results
        