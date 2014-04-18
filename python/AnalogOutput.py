"""AnalogOutput.py
Part of the AQuA Cesium Controller software package

author=Martin Lichtman
created=2013-10-24
modified>=2013-10-24

This file holds everything needed to model the analog output from a National Instruments HSDIO card.  It communicates to LabView via the higher up LabView(Instrument) class.
"""

from __future__ import division

import logging
logger = logging.getLogger(__name__)

from cs_errors import PauseError

from atom.api import Bool, Typed, Member
from enaml.application import deferred_call
from matplotlib.figure import Figure
from matplotlib.ticker import NullFormatter
from instrument_property import BoolProp, FloatProp, StrProp, ListProp, EvalProp
import cs_evaluate
from cs_instruments import Instrument
import numpy


class AOEquation(EvalProp):
    value = Member()
    AO = Member()
    #properties will already include 'function' from EvalProp, which is what holds our equation string
    placeholder = 'AO equation'
    
    def __init__(self, name, experiment, description='', AO=None):
        self.AO = AO
        super(AOEquation, self).__init__(name, experiment, function='0*t')
    
    #update the plot titles when the description changes
    #Atom will recognize this function name and set up an observer
    def _observe_description(self, change):
        self.AO.update_plot()
    
    def evaluate(self):
        if self.experiment.allow_evaluation:
            #evaluate the 'function' and store it in 'value'
            #but first add the variable 't' into the variables dictionary for timesteps.
            #This will overwrite any previous value, so we make a copy of the dictionary
            vars = self.experiment.vars.copy()
            vars['t'] = self.AO.timesteps
            self.value = cs_evaluate.evalWithDict(self.function, varDict=vars,
                                                      errStr='AO equation.evaluate: {}, {}, {}\n'.format(self.name, self.description, self.function))
            self.AO.update_plot()

    def toHardware(self):
        try:
            valueStr = ' '.join(map(str, self.value.tolist()))
        except Exception as e:
            logger.warning('Exception in ' '.join(map(str,self.value.tolist())) in AnalogOutput.AOEquation.toHardware() in ' + self.name + ' .\n' + str(e))
            raise PauseError
        return '<{}>{}</{}>\n'.format(self.name, valueStr, self.name)


class AnalogOutput(Instrument):
    enable = Member()
    physicalChannels = Typed(StrProp)
    minimum = Typed(FloatProp)
    maximum = Typed(FloatProp)
    clockRate = Typed(FloatProp)
    totalAOTime = Typed(FloatProp)
    units = Typed(FloatProp)
    waitForStartTrigger = Typed(BoolProp)
    triggerSource = Typed(StrProp)
    triggerEdge = Typed(StrProp)
    equations = Typed(ListProp)
    exportStartTrigger = Typed(BoolProp)
    exportStartTriggerDestination = Typed(StrProp)
    
    timesteps = Member()
    version = '2014.02.27'
    
    figure = Typed(Figure)
    backFigure = Typed(Figure)
    figure1 = Typed(Figure)
    figure2 = Typed(Figure)
    
    enable_refresh = Bool(False)  # makes it so that sub-equations won't redraw graph until full evaluation is done
    
    def __init__(self, experiment):
        super(AnalogOutput, self).__init__('AnalogOutput', experiment)
        self.enable = False
        self.physicalChannels = StrProp('physicalChannels', self.experiment, '', '"PXI1Slot2/ao0:7"')
        self.minimum = FloatProp('minimum', self.experiment, '', '-10')
        self.maximum = FloatProp('maximum', self.experiment, '', '10')
        self.clockRate = FloatProp('clockRate', self.experiment, '', '1000.0')
        self.totalAOTime = FloatProp('totalAOTime', self.experiment, '', '5.0')
        self.units = FloatProp('units', self.experiment, 'equations entered in ms', '.001')
        self.waitForStartTrigger = BoolProp('waitForStartTrigger', self.experiment, '', 'True')
        self.triggerSource = StrProp('triggerSource', self.experiment, '', '"/PXI1Slot2/PFI0"')
        self.triggerEdge = StrProp('triggerEdge',self.experiment,'','"Rising"')
        self.equations = ListProp('equations', self.experiment, listElementType=AOEquation,
                            listElementName='equation',listElementKwargs={'AO':self})
        self.exportStartTrigger=BoolProp('exportStartTrigger',self.experiment,'Should we trigger all other cards off the AO card?','True')
        self.exportStartTriggerDestination=StrProp('exportStartTriggerDestination',self.experiment,'What line to send the AO StartTrigger out to?','"/PXISlot2/PXI_Trig0"')
        self.properties+=['version','enable','physicalChannels','minimum','maximum','clockRate','totalAOTime','units','waitForStartTrigger','triggerSource','triggerEdge','exportStartTrigger','exportStartTriggerDestination','equations'] #make sure equations are evaluated last
        self.doNotSendToHardware+=['units','totalAOTime']
        
        self.figure1=Figure()
        self.figure2=Figure()
        self.backFigure=self.figure2
        self.figure=self.figure1
        ##self.update_plot()
        
        #set up Atom notifications from sub-traits
        self.clockRate.observe('value',self.call_evaluate)
        self.totalAOTime.observe('value',self.call_evaluate)
        self.units.observe('value',self.call_evaluate)
        
        self.enable_refresh=True
        
    def drawMPL(self):
        fig=self.backFigure
        
        #clear the old graph
        fig.clf()

        #redraw the graph
        n=len(self.equations)
        for i in range(n):
        #for each equation
            ax=fig.add_subplot(n,1,i+1)
            ax.plot(self.timesteps,self.equations[i].value)
            ax.set_ylabel(self.equations[i].description)
            if i<(n-1):
                #remove tick labels all all except last plot
                ax.xaxis.set_major_formatter(NullFormatter())
            else:
                #label only the last (bottom) plot
                ax.set_xlabel('time')
                #make sure the tick labels have room
        
            #make the ylim a little wider than default (otherwise constant levels are sometimes on top of the plot frame)
            ylim=ax.get_ylim()
            yrange=abs(ylim[1]-ylim[0])
            newylim=(ylim[0]-yrange*.05,ylim[1]+yrange*.05)
            ax.set_ylim(newylim)
            
        #make room for the equation labels
        fig.subplots_adjust(left=.2,right=.95)
        
    def swapFigures(self):
        temp=self.backFigure
        self.backFigure=self.figure
        self.figure=temp
    
    def update_plot(self):
        if self.enable_refresh:
            self.drawMPL()
            try:
                deferred_call(self.swapFigures)
            except RuntimeError: #application not started yet
                self.swapFigures()
    
    def evaluate(self):
        if self.experiment.allow_evaluation:

            self.enable_refresh=False
            #explicitly evaluate totalAOTime and clockRate and units first, so that we can calculate the time steps
            self.units.evaluate()
            self.clockRate.evaluate()
            self.totalAOTime.evaluate()
            #evaluate the time steps
            self.timesteps=numpy.arange(0.0,self.totalAOTime.value,1.0/(self.clockRate.value*self.units.value))
            #evaluate the rest of the properties, including equations
            super(AnalogOutput,self).evaluate()
            
            # plots will update automatically on every AOequation.evaluate()
            
            self.enable_refresh=True
            self.update_plot()
