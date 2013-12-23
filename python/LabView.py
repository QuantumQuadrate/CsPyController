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
        if self.enabled:
            # Create a TCP/IP socket
            self.sock=TCP.CsSock(self.IP,self.port)
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
    
    def update(self):
        super(LabView,self).update()
        msg=self.toHardware()
        print '---start XML---\n'+msg+'---end XML---\n'
        if self.enabled:
            self.sock.sendmsg(msg)
    
    def start(self):    
        #tell the LabView instruments to measure
        self.isDone=True
        
    def initializeDDS(self):
        raise NotImplementedError
    
    def loadDDS(self):
        raise NotImplementedError