'''LabView.py
This file holds everything needed to talk to the PXI crate known as HEXQC2, running LabView.  It can be modified in the future for other LabView systems.
On the LabView end, server.vi must be running, part of this package in the labview directory.

Part of the AQuA Cesium Controller software package

author=Martin Lichtman
created=2013-10-08
modified>=2013-10-08
'''

import TCP, HSDIO, piezo, DDS, RF_generators, AnalogOutput
from traits.api import Bool, Int, Str
from cs_instruments import Instrument
import logging
logger = logging.getLogger(__name__)

class LabView(Instrument):
    enabled=Bool
    port=Int
    IP=Str
    connected=Bool
    msg=Str('')
    
    '''This is a meta instrument which encapsulates the capability of the HEXQC2 PXI system. It knows about several subsystems (HSDIO, DAQmx, Counters, Camera), and can send settings and commands to a corresponding Labview client.'''
    def __init__(self,experiment):
        super(LabView,self).__init__('LabView',experiment,'for communicating with a LabView system')
        self.HSDIO=HSDIO.HSDIO(experiment)
        self.DDS=DDS.DDS(experiment)
        self.piezo=piezo.Piezo(experiment)
        self.RF_generators=RF_generators.RF_generators(experiment)
        self.AnalogOutput=AnalogOutput.AnalogOutput(experiment)
        #self.DAQmxPulse=DAQmxPulse()
        #self.Counter=Counter()
        #self.Camera=HamamatsuC9100_13
        
        self.instruments=[self.HSDIO,self.DDS,self.piezo,self.RF_generators,self.AnalogOutput] #self.DAQmxPulse,self.Counter,self.Camera]
        
        self.sock=None
        self.connected=False
        
        self.properties+=['IP','port','enabled','connected','HSDIO','DDS','piezo','RF_generators','AnalogOutput']
    
    def initialize(self):
        print "LabView.initialize()"
        if self.enabled:
            #check for an old socket and delete it
            if self.sock is not None:
                self.sock.close()
                del self.sock
            # Create a TCP/IP socket
            try:
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
            try:
                #tell the server to stop sending
                self.sock.sendall('quit')
                print 'closing socket'
            finally:
                self.sock.close()
        self.connected=False
        self.isInitialized=False
    
    def update(self):
        super(LabView,self).update()
        self.msg=self.toHardware()
        #print '---start XML---\n'+msg+'---end XML---\n'
        if self.enabled:
            if self.connected:
                if self.sock is not None:
                    self.sock.sendmsg(self.msg)
                else:
                    print "LabView TCP says self.connected=True, but has no sock"
            else:
                print "LabView TCP enabled but not connected"
    
    def start(self):
        #tell the LabView instruments to measure
        self.msg='<LabView><command>measure</command></LabView>'
        self.sock.sendmsg(self.msg)
        
        #wait for response
        while not self.experiment.timeOutExpired:
            rawdata=self.sock.receive()
            if rawdata is not None:
                self.results=self.sock.parsemsg(rawdata)
        
        self.isDone=True
    
    def writeResults(self,hdf5):
        '''Write the previously obtained results to the experiment hdf5 file.
        hdf5 is an hdf5 group, typically the data group in the appropriate part of the
        hierarchy for the current measurement.'''
        
        for key,value in self.results.iteritems():
            if key.startswith('Hamamatsu/shots/'):
                #specific protocol for images: turn them into 2D numpy arrays
                
                #unpack the image in 2 byte chunks
                array=numpy.array(struct.unpack('!'+str(int(len(value)/2))+'H',value))
                
                #the dictionary is unpacked alphabetically, so if width and height were
                #transmitted they should be loaded already
                if ('Hamamatsu/rows' in hdf5) and ('Hamamtsu/columns' in hdf5):
                    array.resize((hdf5['Hamamatsu/rows'].value,hdf5['Hamamatsu/columns'].value))
                hdf5[key]=array
            else:
                #no special protocol
                hdf5[key]=value
    
    def initializeDDS(self):
        raise NotImplementedError
    
    def loadDDS(self):
        raise NotImplementedError