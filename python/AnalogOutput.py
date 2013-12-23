'''AnalogOutput.py
Part of the AQuA Cesium Controller software package

author=Martin Lichtman
created=2013-10-24
modified>=2013-10-24

This file holds everything needed to model the analog output from a National Instruments HSDIO card.  It communicates to LabView via the higher up LabView(Instrument) class.
'''

from enthought.traits.api import Bool, Instance, Array, TraitError #, HasTraits, Int, Str, List
from enthought.chaco.api import VPlotContainer, ArrayPlotData, Plot
from enthought.enable.api import Component
from instrument_property import BoolProp, FloatProp, StrProp, ListProp, EvalProp
import cs_evaluate
from cs_instruments import Instrument
#from cs_errors import PauseError
#import experiments
import numpy, logging
logger = logging.getLogger(__name__)

class AOEquation(EvalProp):
    #we subclass from EvalProp so that the 
    datalist=Array
    plot=Instance(Component)
    value=Array
    #properties will already include 'function' from EvalProp, which is what holds our equation string
    
    def __init__(self,name,experiment,description='',kwargs={}):
        super(AOEquation,self).__init__(name,experiment)
        self.AO=kwargs['AO']
        
        #create an empty plot
        self.plotdata = ArrayPlotData(t=numpy.arange(2),y=numpy.zeros(2))
        self.plot = Plot(self.plotdata)
        self.plot.plot(("t", "y"), type="line", color="blue")
        self.plot.title = self.description
        
        
    #update the plot titles when the description changes
    def _description_changed(self,old,new):
        self.plot.title = self.description
    
    def evaluate(self):
        #evaluate the 'function' and store it in 'value'
        #but first add the variable 't' into the variables dictionary for timesteps.
        #This will overwrite any previous value, so we make a copy of the dictionary
        vars=self.experiment.vars.copy()
        vars['t']=self.AO.timesteps
        try:
            self.value=cs_evaluate.evalWithDict(self.function,varDict=vars,errStr='AO equation.evaluate: {}, {}, {}\n'.format(self.name,self.description,self.function))
        except TraitError as e:
            logger.warning('In AOEquation.evaluate(), TraitError while evaluating: '+self.name+'\ndescription: '+self.description+'\nfunction: '+self.function+'\n'+str(e))
            #raise PauseError
        
        self.plotdata.set_data("t",self.AO.timesteps)
        self.plotdata.set_data("y",self.value)
        self.plot.title = self.description
        self.AO.update_plot()

class AnalogOutput(Instrument):
    enable=Bool
    physicalChannels=Instance(StrProp)
    minimum=Instance(FloatProp)
    maximum=Instance(FloatProp)
    clockRate=Instance(FloatProp)
    totalAOTime=Instance(FloatProp)
    units=Instance(FloatProp)
    waitForStartTrigger=Instance(BoolProp)
    triggerSource=Instance(StrProp)
    triggerEdge=Instance(StrProp)
    equations=Instance(ListProp)
    
    plot=Instance(Component)
    timesteps=Array
    
    def __init__(self,experiment):
        super(AnalogOutput,self).__init__('AnalogOutput',experiment)
        self.version='2013.10.24'
        self.enable=False
        self.physicalChannels=StrProp('physicalChannels',self.experiment,'','"PXI1Slot2/ao0:7"')
        self.minimum=FloatProp('minimum',self.experiment,'','-10')
        self.maximum=FloatProp('maximum',self.experiment,'','10')
        self.clockRate=FloatProp('clockRate',self.experiment,'','1000')
        self.totalAOTime=FloatProp('totalAOTime',self.experiment,'','5')
        self.units=FloatProp('units',self.experiment,'equations entered in ms','.001')
        self.waitForStartTrigger=BoolProp('waitForStartTrigger',self.experiment,'','True')
        self.triggerSource=StrProp('triggerSource',self.experiment,'','"/PXI1Slot6/PFI0"')
        self.triggerEdge=StrProp('triggerEdge',self.experiment,'','"Rising"')
        self.equations=ListProp('equations',self.experiment,listElementType=AOEquation,
                            listElementName='equation',listElementKwargs={'AO':self})
        self.properties+=['version','enable','physicalChannels','minimum','maximum','clockRate','totalAOTime','units','waitForStartTrigger','triggerSource','triggerEdge','equations']
        
        #set up trait notifications from sub-traits
        self.clockRate.on_trait_change(self.evaluate,'value')
        self.totalAOTime.on_trait_change(self.evaluate,'value')
        self.units.on_trait_change(self.evaluate,'value')
        
        #create empty plot
        plot = Plot()
        plot.title = "empty"
        self.plot=plot
    
    def update_plot(self):
        #TODO: find out how to change VPlotContainer components list, instead of remaking the whole thing
        self.plot=VPlotContainer(*[i.plot for i in self.equations])
    
    def evaluate(self):
        super(AnalogOutput,self).evaluate()
        # first evaluate the time steps:
        self.timesteps=numpy.arange(0.0,self.totalAOTime.value,1.0/(self.clockRate.value*self.units.value))
        
        if self.equations is not None:
            for eq in self.equations:
                eq.evaluate()
        
        # plots will update automatically on every AOequation.evaluate()
    
    def initialize(self):
        self.isInitialized=True
        