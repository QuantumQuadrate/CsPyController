'''AnalogOutput.py
Part of the AQuA Cesium Controller software package

author=Martin Lichtman
created=2013-10-24
modified>=2013-10-24

This file holds everything needed to model the analog output from a National Instruments HSDIO card.  It communicates to LabView via the higher up LabView(Instrument) class.
'''

from atom.api import Bool, Typed, Member, Coerced #, Array
from enthought.chaco.api import VPlotContainer, ArrayPlotData, Plot
from enthought.enable.api import Component
from instrument_property import BoolProp, FloatProp, StrProp, ListProp, EvalProp
import cs_evaluate
from cs_instruments import Instrument
#from cs_errors import PauseError
#import experiments
import numpy, logging
logger = logging.getLogger(__name__)

#borrowed from traits_enaml package
class Array(Coerced):
    """ A value of type `np.ndarray`

    Values are coerced to ndarrays using np.array.
    
    """
    __slots__ = ()
    
    def __init__(self, default=None, factory=None, kwargs=None):
        import numpy as np
        if default:
            kwargs = kwargs or {}
            factory = lambda: np.array(default, **kwargs)
        else:
            factory = lambda: ()
        super(Array, self).__init__(
                np.ndarray, factory=factory, coercer=np.array)

class AOEquation(EvalProp):
    value=Array()
    plot=Typed(Component)
    AO=Member()
    plotdata=Member()
    #myArrayHolder=Typed(arrayHolder)
    #properties will already include 'function' from EvalProp, which is what holds our equation string
    
    def __init__(self,name,experiment,description='',kwargs={}):
        self.AO=kwargs['AO']
        
        #create an empty plot
        self.plotdata = ArrayPlotData(t=numpy.arange(2),y=numpy.zeros(2))
        self.plot = Plot(self.plotdata)
        self.plot.plot(("t", "y"), type="line", color="blue")
        self.plot.title = self.description
        
        super(AOEquation,self).__init__(name,experiment)
    
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
    enable=Bool()
    physicalChannels=Typed(StrProp)
    minimum=Typed(FloatProp)
    maximum=Typed(FloatProp)
    clockRate=Typed(FloatProp)
    totalAOTime=Typed(FloatProp)
    units=Typed(FloatProp)
    waitForStartTrigger=Typed(BoolProp)
    triggerSource=Typed(StrProp)
    triggerEdge=Typed(StrProp)
    equations=Typed(ListProp)
    
    plot=Typed(Component)
    timesteps=Array()
    version=Member()
    
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
        
        #set up Atom notifications from sub-traits
        self.clockRate.observe('value',self.call_evaluate)
        self.totalAOTime.observe('value',self.call_evaluate)
        self.units.observe('value',self.call_evaluate)
        
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
        