'''HSDIO.py
Part of the AQuA Cesium Controller software package

author=Martin Lichtman
created=2013-10-08
modified>=2013-10-08

This file holds everything needed to model the high speed digital output from the National Instruments HSDIO card.  It communicates to LabView via the higher up LabView(Instrument) class.
'''

from cs_errors import PauseError
from atom.api import Bool, Typed, Str, Int, Member
#from enthought.chaco.api import ArrayPlotData, Plot #for chaco plot
from instrument_property import Prop, BoolProp, IntProp, FloatProp, StrProp, ListProp
from cs_instruments import Instrument
import matplotlib.pyplot as plt
import numpy, logging
logger = logging.getLogger(__name__)

from digital_waveform import Waveform, Channels
#import digital_waveform #my helper class for making Chaco plots of waveforms

#---- HSDIO properties ----
class ScriptTrigger(Prop):
    id=Typed(StrProp)
    source=Typed(StrProp)
    type=Typed(StrProp)
    edge=Typed(StrProp)
    level=Typed(StrProp)
    
    def __init__(self,name,experiment,description='',kwargs={}):
        super(ScriptTrigger,self).__init__('trigger',experiment,description)
        self.id=StrProp('id',experiment,'','"ScriptTrigger0"')
        self.source=StrProp('source',experiment,'','"PFI0"')
        self.type=StrProp('type',experiment,'','"edge"')
        self.edge=StrProp('edge',experiment,'','"rising"')
        self.level=StrProp('level',experiment,'','"high"')
        self.properties+=['id','source','type','edge','level']

class Waveforms(ListProp):
    digitalout=Member()
    refreshButton=Member()

    def __init__(self,experiment,digitalout):
        super(Waveforms,self).__init__('waveforms',experiment,description='Holds all the digitalout waveforms',listElementType=Waveform)
        self.digitalout=digitalout
        self.add()
        #self.refresh()
    
    def getNextAvailableName(self):
        #figure out unique name for a new waveform
        count=int(0)
        names=[i.name for i in self.listProperty]
        while True:
            name='wfm'+str(count)
            if not name in names:
                return name
            count+=1
    
    def add(self):
        name=self.getNextAvailableName()
        waveform=Waveform(name,self.experiment,self.digitalout,waveforms=self)
        self.listProperty.append(waveform)
        return waveform
    
    def fromXML(self,xmlNode):
        while self.listProperty: #go until the list is empty
            self.listProperty.pop()
        self.listProperty+=[Waveform(self.getNextAvailableName(),self.experiment,self.digitalout,waveforms=self).fromXML(child) for child in xmlNode]
        self.refresh()
        return self
    
    def refresh(self):
        if hasattr(self,'refreshButton') and (self.refreshButton is not None): #prevents trying to do this before GUI is active
            self.refreshButton.clicked()  #refresh the GUI
    
    def toHardware(self):
        '''This returns an empty string, because this is handled in HSDIO.toHardware()'''
        return ''

class StartTrigger(Prop):
    waitForStartTrigger=Typed(BoolProp)
    source=Typed(StrProp)
    edge=Typed(StrProp)
    
    def __init__(self,experiment):
        super(StartTrigger,self).__init__('startTrigger',experiment)
        self.waitForStartTrigger=BoolProp('waitForStartTrigger',experiment,'HSDIO wait for start trigger','False')
        self.source=StrProp('source',experiment,'start trigger source','"PFI0"')
        self.edge=StrProp('edge',experiment,'start trigger edge','"rising"')
        self.properties+=['waitForStartTrigger','source','edge']

class Script(StrProp):

    def toHardware(self):
        '''This returns an empty string, because the script is handled in HSDIO.toHardware()'''
        return ''

#---- HSDIO instrument ----

class HSDIO(Instrument):
    enable=Typed(BoolProp)
    script=Typed(StrProp)
    resourceName=Typed(StrProp)
    clockRate=Typed(FloatProp)
    units=Typed(FloatProp)
    hardwareAlignmentQuantum=Typed(IntProp)
    waveforms=Typed(Waveforms)
    channels=Typed(Channels)
    triggers=Typed(ListProp)
    startTrigger=Typed(StartTrigger)
    version=Str()
    numChannels=Int()
    
    def __init__(self,experiment):
        super(HSDIO,self).__init__('HSDIO',experiment)
        self.version='2014.01.22'
        self.numChannels=32
        self.enable=BoolProp('enable',experiment,'enable HSDIO output','False')
        self.script=StrProp('script',experiment,'HSDIO script that says what waveforms to generate',"'script script1\\n  generate waveform1\\n  idle\\nend script'")
        self.resourceName=StrProp('resourceName',experiment,'the hardware location of the HSDIO card',"'Dev1'")
        self.clockRate=FloatProp('clockRate',experiment,'samples/channel/sec','1000')
        self.units=FloatProp('units',experiment,'multiplier for HSDIO timing values (milli=.001)','1')
        self.hardwareAlignmentQuantum=IntProp('hardwareAlignmentQuantum',experiment,'(PXI=1,SquareCell=2)','1')
        self.waveforms=Waveforms(experiment,self)
        self.channels=Channels(experiment,self)
        self.triggers=ListProp('triggers',self.experiment,listElementType=ScriptTrigger,listElementName='trigger')
        self.startTrigger=StartTrigger(experiment)
        self.properties+=['version','enable','resourceName','clockRate','units','hardwareAlignmentQuantum','waveforms','triggers','channels','startTrigger','script']
    
    def initialize(self):
        self.isInitialized=True
    
    def toHardware(self):
        '''override to accommodate compressedGenerate, and to only upload necessary waveforms
        toHardware for HSDIO.waveforms and HSDIO.script will be overridden and return blank so they do not append conflicting results
        no need to evaluate, that will already be done by this point'''
        
        #build dictionary of waveforms keyed on waveform name
        definedWaveforms={i.name:i for i in HSDIO.waveforms}
        
        #keep track of which waveforms are to be uploaded
        waveformsInUse=[]
        
        scriptOut=''
        waveformXML=''
        
        #go through script line by line
        for row in self.script.value.split('\n'):
            words=row.strip().split()
            if len(words)>1:
                command=words[0].lower()
                waveformName=words[1]
                if command='generate':
                    #for each generate, if waveformName not in list, add waveform to list of necessary waveforms,add waveform to waveform XML (if it does not exist give error
                    if waveformName not in definedWaveforms:
                        logger.warning('HSDIO script says: {}, but waveform {} does not exist.'.format(row,words[1]))
                        raise PauseError
                    elif waveformName not in waveformsInUse:
                        #add waveform to those to be transferred to LabView
                        waveformsInUse+=[waveformName]
                        waveformXML+=definedWaveforms[waveformName].toHardware()
                elif command=='compressedgenerate':
                    #for each compressedGenerate, replace with a sequence of generate wXXXXXXXX, if wXXXXXXXX not in list, add wXXXXXXXX to list of necessary waveforms, create waveform and add it to waveform XML
                    newString='' #this will replace the current line
                    if waveformName not in waveformNames:
                        logger.warning('HSDIO script says: {}, but waveform {} does not exist.'.format(row,words[1]))
                        raise PauseError
                    for state,duration in zip(waveform.stateList,waveform.duration): #iterates over first index in stateList, which is time points
                        singleSampleWaveformName='w'+hex(int(''.join([str(i) for i in state])))[2:] #make a hexadecimal name for the waveform.  the [2:] drops the leading 0x on the hexadecimal
                        newString+='generate '+singleSampleWaveformName+'\n'
                        waitTime=duration-self.hardwareAlignmentQuantum.value
                        if waitTime > 0: #if we need to wait after this sample to get the correct time delay
                            if waitTime%self.hardwareAlignmentQuantum.value!=0: #if the wait time is not a multiple of the hardwareAlignmentQuantum
                                waitTime=(int(waitTime/self.hardwareAlignmentQuantum.value)+1)*self.hardwareAlignmentQuantum.value #round up
                            newString+=int(waitTime/536870912)*'wait 536870912\n' #the HSDIO card cannot handle a wait value longer than this, so we repeat it as many times as necessary
                            newString+='wait '+str(waitTime%536870912)+'\n' #add the remaining wait
                        if not singleSampleWaveformName in waveformsInUse:
                            #add waveform to those to be transferred to LabView
                            waveformsInUse+=[singleSampleWaveformName]
                            #don't create a real waveform object, just its toHardware signature
                            waveformXML+=('<waveform>'+
                                '<name>'+singleSampleWaveformName+'</name>'+
                                '<transitions>'+' '.join([str(time) for time in range(self.hardwareAlignmentQuantum)])+'</transitions>'+ #make as many time points as the minimum necessary for hardware
                                '<states>'+'\n'.join([' '.join([str(sample) for sample in state]) for time in range(self.hardwareAlignmentQuantum)])+'</states>\n'+
                                '</waveform>\n')
                    scriptOut+=newString
                    continue #don't do the scriptOut+=row+'\n'
            scriptOut+=row+'\n'
        
        #then upload scriptOut instead of script.toHardware, waveformXML instead of waveforms.toHardware (those toHardware methods will return an empty string and so will not interfere)
        #then process the rest of the properties as usual
        return '<HSDIO><script>{}</script>\n<waveforms>{}</waveforms>\n'.format(scriptOut,waveformXML)+super(HSDIO,self).toHardware()
