'''EchoBox.py
    Part of the AQuA Cesium Controller software package.
    This Instrument sends some fake test data to the LabView server (or python test server), which will then be echoed back for display for test purposes.

    author=Martin Lichtman
    created=2014.02.10
    modified>=2014.02.10
    '''

from __future__ import division
from atom.api import Bool, Typed, Str, Int, Member
from instrument_property import BoolProp
from cs_instruments import Instrument
import numpy, logging, struct
logger = logging.getLogger(__name__)
from TCP import makemsg
from digital_waveform import Waveform, Channels

#---- instrument ----

class EchoBox(Instrument):
    enable=Typed(BoolProp)
    
    def __init__(self,experiment):
        super(EchoBox,self).__init__('EchoBox',experiment,'creates fake test data to be parroted back to the client')
        self.enable=BoolProp('enable',experiment,'enable fake EchoBox data','False')
        self.properties+=['enable']
    
    def initialize(self):
        self.isInitialized=True
    
    #intensity, for incoherent beams
    def gaussian(self,A,w,x,y):
        return A*numpy.exp(-(x**2+y**2)/(2*(w**2)))
    
    def positionNoise(self):
        return 10*(2*numpy.random.random()-1)
    
    def randomLoading(self,rows,columns,bytes,highbit):
        #print 'creating echoBox data'
        noise=int(highbit/50)
        testdata=numpy.random.randint(0,noise,(rows,columns))
        x=numpy.arange(rows,dtype=float)
        y=numpy.arange(columns,dtype=float)
        X,Y=numpy.meshgrid(x,y)
        A=highbit/2
        for i in range(7):
            for j in range(7):
                if numpy.random.random_integers(0,1)==1:
                    testdata+=self.gaussian(A,3,X-(i+.5)*(rows/7)-self.positionNoise(),Y-(j+.5)*(rows/7)-self.positionNoise())
        return testdata
    
    def toHardware(self):
        #create some dummy data 16-bit 512x512
        rows=512; columns=512; bytes=1; signed=''; highbit=2**(8*bytes);
        testdata=self.randomLoading(rows,columns,bytes,highbit)
        #turn the image array into a long string composed of 2 bytes for each number
        #first create a struct object, because reusing the same object is more efficient
        myStruct=struct.Struct('!H') #'!H' indicates unsigned short (2 byte) integers
        testdatamsg=''.join([myStruct.pack(t) for t in testdata.flatten()])
        msg=makemsg('Hamamatsu/rows',str(rows))+makemsg('Hamamatsu/columns',str(columns))+makemsg('Hamamatsu/bytes',str(bytes))+makemsg('Hamamatsu/signed',str(signed))+makemsg('Hamamatsu/shots/0',testdatamsg)
        return '<EchoBox>'+msg+'</EchoBox>'