from traits.api import Bool, Float, Str, Instance
import logging
logger = logging.getLogger(__name__)
#from cs_errors import PauseError
from instrument_property import Prop, BoolProp, FloatProp, ListProp
from cs_instruments import Instrument

class PiezoChannel(Prop):
    setServo=Instance(BoolProp)
    setPosition=Instance(FloatProp)
    readAxis=Str
    readServo=Bool
    readPosition=Float
    
    def __init__(self,name,experiment,description='',kwargs={}):
        super(PiezoChannel,self).__init__(name,experiment,description)
        self.setServo=BoolProp('setServo',self.experiment,'','False')
        self.setPosition=FloatProp('setPosition',self.experiment,'','0')
        self.readAxis=''
        self.readServo=False
        self.readPosition=float('nan')
        self.properties+=['setServo','setPosition','readAxis','readServo','readPosition']

class PiezoController(Prop):
    enable=Bool
    serialNumber=Str
    identificationRead=Str
    serialNumberRead=Str
    channels=Instance(ListProp)
    
    def __init__(self,name,experiment,description='',kwargs={}):
        super(PiezoController,self).__init__(name,experiment,description)
        self.enable=False
        self.serialNumber=''
        self.identificationRead=''
        self.serialNumberRead=''
        self.channels=ListProp('channels',self.experiment,listProperty=[PiezoChannel('channel'+str(i),self.experiment) for i in range(9)],listElementType=PiezoChannel,listElementName='channel')
        self.properties=['enable','serialNumber','identificationRead','serialNumberRead','channels']

class Piezo(Instrument):
    enable=Bool
    channels=Instance(ListProp)
    
    def __init__(self,experiment):
        super(Piezo,self).__init__('piezo',experiment)
        self.version='2013.10.22'
        self.enable=False
        self.controllers=ListProp('controllers',self.experiment,listProperty=[PiezoController('controller'+str(i),self.experiment) for i in range(2)],listElementType=PiezoController,listElementName='controller')
        self.properties+=['version','enable','controllers']