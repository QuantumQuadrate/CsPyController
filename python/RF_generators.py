'''RF_generators.py
Part of the AQuA Cesium Controller software package

author=Martin Lichtman
created=2013-10-22
modified>=2013-10-22

This file holds everything needed to model the microwave RF generators (HP/Agilient) which are controlled by GPIB.  It communicates to LabView via the higher up HEXQC2 class.
'''


#from cs_errors import PauseError
from atom.api import Bool, Int, Typed, Member
from instrument_property import Prop, BoolProp, FloatProp, ListProp #IntProp, StrProp
from cs_instruments import Instrument
import logging
logger = logging.getLogger(__name__)

class RFGenList(ListProp):
    def __init__(self,name,experiment,description='',listProperty=None,listElementType=None,listElementName='element'):
        super(RFGenList,self).__init__(name,experiment,description,listProperty,listElementType,listElementName)
        self.listProperty=[]
    
    def load(self):
        raise NotImplementedError

class RF_generators(Instrument):
    enable=Typed(BoolProp)
    HP83623A_list=Typed(RFGenList)
    HP8662A_list=Typed(RFGenList)
    HP83712B_list=Typed(RFGenList)
    version=Member()
    
    def __init__(self,experiment):
        super(RF_generators,self).__init__('RF_generators',experiment)
        self.version='2013.10.22'
        self.enable=BoolProp('enable',self.experiment,'enable output','False')
        self.HP83623A_list=RFGenList('HP83623A_list',experiment,listElementType=HP83623A,listElementName='HP83623A')
        self.HP8662A_list=RFGenList('HP8662A_list',experiment,listElementType=RF_generator,listElementName='HP8662A')
        self.HP83712B_list=RFGenList('HP83712B_list',experiment,listElementType=RF_generator,listElementName='HP83712B')
        self.HP83623A_list.add() #TODO: don't add this initial box, but if we don't then the comboBox doesn't update for some reason
        self.HP8662A_list.add()
        self.HP83712B_list.add()
        self.properties+=['version','enable','HP83623A_list','HP8662A_list','HP83712B_list']


class RF_generator(Prop):
    enable=Bool()
    GPIBchannel=Int()
    frequency=Typed(FloatProp)
    power=Typed(FloatProp)
    
    def __init__(self,name,experiment,description='',kwargs=None):
        super(RF_generator,self).__init__(name,experiment,description)
        self.frequency=FloatProp('frequency',self.experiment,'[MHz]','10')
        self.power=FloatProp('power',self.experiment,'[dBm]','0')
        self.properties+=['enable','GPIBchannel','frequency','power']
        
class HP83623A(RF_generator):
    RFoutput=Typed(BoolProp)
    externalTrigger=Typed(BoolProp)
    
    def __init__(self,name,experiment,description='',kwargs=None):
        super(HP83623A,self).__init__(name,experiment,description)
        self.RFoutput=BoolProp('RFoutput',self.experiment,'','False')
        self.externalTrigger=BoolProp('externalTrigger',self.experiment,'','False')
        self.properties+=['RFoutput','externalTrigger']
