'''echoBox.py
    Part of the AQuA Cesium Controller software package.
    This Instrument sends some fake test data to the LabView server (or python test server), which will then be echoed back for display for test purposes.

    author=Martin Lichtman
    created=2014.02.10
    modified>=2014.02.10
    '''

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
        super(EchoBox,self).__init__('echoBox',experiment)
        self.enable=BoolProp('enable',experiment,'enable echoBox','False')
        self.properties+=['enable']
    
    def initialize(self):
        self.isInitialized=True
    
    def toHardware(self):
        #create some dummy data 16-bit 512x512
        rows=512; columns=512; bytes=1; signed=''; highbit=2**(8*bytes);
        testdata=numpy.random.randint(0,highbit,(rows,columns))
        #turn the image array into a long string composed of 2 bytes for each number
        #first create a struct object, because reusing the same object is more efficient
        myStruct=struct.Struct('!H') #'!H' indicates unsigned short (2 byte) integers
        testdatamsg=''.join([myStruct.pack(t) for t in testdata.flatten()])
        msg=makemsg('Hamamatsu/rows',str(rows))+makemsg('Hamamatsu/columns',str(columns))+makemsg('Hamamatsu/bytes',str(bytes))+makemsg('Hamamatsu/signed',str(signed))+makemsg('Hamamatsu/shots/0',testdatamsg)
        return '<echoBox>'+msg+'</echoBox>'