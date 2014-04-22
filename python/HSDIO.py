"""HSDIO.py
Part of the AQuA Cesium Controller software package

author=Martin Lichtman
created=2013-10-08
modified>=2013-10-08

This file holds everything needed to model the high speed digital output from the National Instruments HSDIO card.  It communicates to LabView via the higher up LabView(Instrument) class.
"""

from __future__ import division
import logging
logger = logging.getLogger(__name__)

from cs_errors import PauseError

from atom.api import Typed, Member
from instrument_property import Prop, BoolProp, IntProp, FloatProp, StrProp, ListProp
from cs_instruments import Instrument

from digital_waveform import NumpyWaveform, Channels, NumpyChannels

#---- HSDIO properties ----


class ScriptTrigger(Prop):
    id = Typed(StrProp)
    source = Typed(StrProp)
    type = Typed(StrProp)
    edge = Typed(StrProp)
    level = Typed(StrProp)
    
    def __init__(self, name, experiment, description=''):
        super(ScriptTrigger, self).__init__('trigger', experiment, description)
        self.id = StrProp('id', experiment, '', '"ScriptTrigger0"')
        self.source = StrProp('source', experiment, '', '"PFI0"')
        self.type = StrProp('type', experiment, '', '"edge"')
        self.edge = StrProp('edge', experiment, '', '"rising"')
        self.level = StrProp('level', experiment, '', '"high"')
        self.properties += ['id', 'source', 'type', 'edge', 'level']

class Waveforms(ListProp):
    #digitalout=Member()
    #refreshButton=Member()
    '''We can't use an unmodified ListProp for this because the added children must be passed waveforms=self, which is not possible to describe in a one-line definintion.'''
    def __init__(self, experiment, digitalout):
        super(Waveforms, self).__init__('waveforms', experiment, description='Holds all the digitalout waveforms', listElementType=NumpyWaveform, listElementName='waveform', listElementKwargs={'digitalout': digitalout, 'waveforms': self})
        #self.digitalout=digitalout
        
    #def fromXML(self,xmlNode):
    #    self.listProperty=[Waveform(child.tag,self.experiment,digitalout=self.digitalout,waveforms=self).fromXML(child) for i,child in enumerate(xmlNode)]
    #    self.refresh()
    #    return self
    #
    #def refresh(self):
    #    if hasattr(self,'refreshButton') and (self.refreshButton is not None): #prevents trying to do this before GUI is active
    #        self.refreshButton.clicked()  #refresh the GUI
    
class StartTrigger(Prop):
    waitForStartTrigger = Typed(BoolProp)
    source = Typed(StrProp)
    edge = Typed(StrProp)
    
    def __init__(self, experiment):
        super(StartTrigger, self).__init__('startTrigger', experiment)
        self.waitForStartTrigger = BoolProp('waitForStartTrigger', experiment, 'HSDIO wait for start trigger', 'False')
        self.source = StrProp('source', experiment, 'start trigger source', '"PFI0"')
        self.edge = StrProp('edge', experiment, 'start trigger edge', '"rising"')
        self.properties += ['waitForStartTrigger', 'source', 'edge']

#---- HSDIO instrument ----


class HSDIO(Instrument):
    version = '2014.01.22'
    enable = Typed(BoolProp)
    script = Typed(StrProp)
    resourceName = Typed(StrProp)
    clockRate = Typed(FloatProp)
    units = Typed(FloatProp)
    hardwareAlignmentQuantum = Typed(IntProp)
    waveforms = Typed(Waveforms)
    channels = Typed(Channels)
    triggers = Typed(ListProp)
    startTrigger = Typed(StartTrigger)
    numChannels = 32
    
    def __init__(self, name, experiment):
        super(HSDIO, self).__init__(name, experiment)
        self.enable = BoolProp('enable', experiment, 'enable HSDIO output', 'False')
        self.script = StrProp('script', experiment, 'HSDIO script that says what waveforms to generate', "'script script1\\n  wait 1\\nend script'")
        self.resourceName = StrProp('resourceName', experiment, 'the hardware location of the HSDIO card', "'Dev1'")
        self.clockRate = FloatProp('clockRate', experiment, 'samples/channel/sec', '1000')
        self.units = FloatProp('units', experiment, 'multiplier for HSDIO timing values (milli=.001)', '1')
        self.hardwareAlignmentQuantum = IntProp('hardwareAlignmentQuantum', experiment, '(PXI=1,SquareCell=2)', '1')
        self.waveforms = Waveforms(experiment, self)
        self.channels = Channels(experiment, self)
        self.triggers = ListProp('triggers', self.experiment, listElementType=ScriptTrigger, listElementName='trigger')
        self.startTrigger = StartTrigger(experiment)
        self.properties += ['version', 'enable', 'resourceName', 'clockRate', 'units', 'hardwareAlignmentQuantum',
                            'startTrigger', 'triggers', 'channels', 'waveforms', 'script']
        self.doNotSendToHardware += ['units', 'script', 'waveforms']  # script and waveforms are handled specially in HSDIO.toHardware()
    
    def toHardware(self):
        """override to accommodate compressedGenerate, and to only upload necessary waveforms
        toHardware for HSDIO.waveforms and HSDIO.script will be overridden and return blank so they do not append conflicting results
        no need to evaluate, that will already be done by this point"""
        
        #build dictionary of waveforms keyed on waveform name
        definedWaveforms = {i.name:i for i in self.waveforms}
        
        #keep track of which waveforms are to be uploaded
        waveformsInUse = []
        
        scriptOut = ''
        waveformXML = ''
        
        #go through script line by line
        for row in self.script.value.split('\n'):
            words=row.strip().split()
            if len(words)>1:
                command=words[0].lower()
                waveformName=words[1]
                if command=='generate':
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
                    if waveformName not in definedWaveforms:
                        logger.warning('HSDIO script says: {}, but waveform {} does not exist.'.format(row,words[1]))
                        raise PauseError
                    waveform=definedWaveforms[waveformName]
                    for state,duration in zip(waveform.stateList,waveform.duration): #iterates over first index in stateList, which is time points
                        singleSampleWaveformName='w'+''.join([str(i) for i in state]) #make a name for the waveform.  the name is w followed by the binary expression of the state
                        newString+='generate '+singleSampleWaveformName+'\n'
                        waitTime=duration-self.hardwareAlignmentQuantum.value
                        if waitTime > 0: #if we need to wait after this sample to get the correct time delay
                            if waitTime%self.hardwareAlignmentQuantum.value!=0: #if the wait time is not a multiple of the hardwareAlignmentQuantum
                                waitTime=(int(waitTime/self.hardwareAlignmentQuantum.value)+1)*self.hardwareAlignmentQuantum.value #round up
                            newString+=int(waitTime/536870912)*'wait 536870912\n' #the HSDIO card cannot handle a wait value longer than this, so we repeat it as many times as necessary
                            newString+='wait '+str(int(waitTime%536870912))+'\n' #add the remaining wait
                        if not singleSampleWaveformName in waveformsInUse:
                            #add waveform to those to be transferred to LabView
                            waveformsInUse+=[singleSampleWaveformName]
                            #don't create a real waveform object, just its toHardware signature
                            waveformXML+=('<waveform>'+
                                '<name>'+singleSampleWaveformName+'</name>'+
                                '<transitions>'+' '.join([str(time) for time in range(self.hardwareAlignmentQuantum.value)])+'</transitions>'+ #make as many time points as the minimum necessary for hardware
                                '<states>'+'\n'.join([' '.join([str(sample) for sample in state]) for time in range(self.hardwareAlignmentQuantum.value)])+'</states>\n'+
                                '</waveform>\n')
                    scriptOut+=newString
                    continue #don't do the scriptOut+=row+'\n'
            scriptOut+=row+'\n'
        
        #then upload scriptOut instead of script.toHardware, waveformXML instead of waveforms.toHardware (those toHardware methods will return an empty string and so will not interfere)
        #then process the rest of the properties as usual
        return '<HSDIO><script>{}</script>\n<waveforms>{}</waveforms>\n'.format(scriptOut,waveformXML)+super(HSDIO,self).toHardware()[7:] #[7:] removes the <HSDIO> on what is returned from super.toHardware

class npHSDIO(Instrument):
    """version of HSDIO that uses numpy based waveforms"""
    version = '2014.04.05'
    numChannels = 32

    enable = Member()
    script = Member()
    resourceName = Member()
    clockRate = Member()
    units = Member()
    hardwareAlignmentQuantum = Member()
    waveforms = Member()
    channels = Member()
    triggers = Member()
    startTrigger = Member()
    import_path = Member()

    def __init__(self, name, experiment):
        super(npHSDIO, self).__init__(name, experiment)
        self.enable = BoolProp('enable', experiment, 'enable HSDIO output', 'False')
        self.script = StrProp('script', experiment, 'HSDIO script that says what waveforms to generate', "'script script1\\n  wait 1\\nend script'")
        self.resourceName = StrProp('resourceName', experiment, 'the hardware location of the HSDIO card', "'Dev1'")
        self.clockRate = FloatProp('clockRate', experiment, 'samples/channel/sec', '1000')
        self.units = FloatProp('units', experiment, 'multiplier for HSDIO timing values (milli=.001)', '1')
        self.hardwareAlignmentQuantum = IntProp('hardwareAlignmentQuantum', experiment, '(PXI=1,SquareCell=2)', '1')
        self.waveforms = Waveforms(experiment, self)
        self.channels = NumpyChannels(experiment, self)
        self.triggers = ListProp('triggers', self.experiment, listElementType=ScriptTrigger, listElementName='trigger')
        self.startTrigger = StartTrigger(experiment)
        self.properties += ['version', 'enable', 'resourceName', 'clockRate', 'units', 'hardwareAlignmentQuantum', 'waveforms', 'triggers', 'channels', 'startTrigger', 'script']
        self.doNotSendToHardware += ['units', 'script', 'waveforms']  # script and waveforms are handled specially in HSDIO.toHardware()

    def import_waveform(self, path):
        #set path as default
        self.import_path = os.path.dirname(path)
        raise NotImplementedError

    def toHardware(self):
        """override to accommodate compressedGenerate, and to only upload necessary waveforms
        toHardware for HSDIO.waveforms and HSDIO.script will be overridden and return blank so they do not append conflicting results
        no need to evaluate, that will already be done by this point"""
        
        #build dictionary of waveforms keyed on waveform name
        definedWaveforms = {i.name:i for i in self.waveforms}
        
        #keep track of which waveforms are to be uploaded
        waveformsInUse = []
        
        scriptOut=''
        waveformXML=''
        
        #go through script line by line
        for row in self.script.value.split('\n'):
            words = row.strip().split()
            if len(words) > 1:
                command = words[0].lower()
                waveformName = words[1]
                if command == 'generate':
                    # for each generate, if waveformName not in list:
                    #  add waveform to list of necessary waveforms
                    #  add waveform to waveform XML (if it does not exist give error)
                    if waveformName not in definedWaveforms:
                        logger.warning('HSDIO script says: {}, but waveform {} does not exist.'.format(row, words[1]))
                        raise PauseError
                    elif waveformName not in waveformsInUse:
                        # add waveform to those to be transferred to LabView
                        waveformsInUse += [waveformName]
                        waveformXML += definedWaveforms[waveformName].toHardware()
                elif command == 'compressedgenerate':
                    # for each compressedGenerate, replace with a sequence of generate wXXXXXXXX, if wXXXXXXXX not in list, add wXXXXXXXX to list of necessary waveforms, create waveform and add it to waveform XML
                    newString = ''  # this will replace the current line
                    if waveformName not in definedWaveforms:
                        logger.warning('HSDIO script says: {}, but waveform {} does not exist.'.format(row, words[1]))
                        raise PauseError
                    waveform = definedWaveforms[waveformName]
                    for state, duration in zip(waveform.stateList, waveform.duration):  # iterates over first index in stateList, which is time points
                        singleSampleWaveformName = 'w'+''.join([str(i) for i in state])  # make a name for the waveform.  the name is w followed by the binary expression of the state
                        newString += 'generate '+singleSampleWaveformName+'\n'
                        waitTime = duration-self.hardwareAlignmentQuantum.value
                        if waitTime > 0:  # if we need to wait after this sample to get the correct time delay
                            if waitTime % self.hardwareAlignmentQuantum.value != 0:  # if the wait time is not a multiple of the hardwareAlignmentQuantum
                                waitTime = (int(waitTime/self.hardwareAlignmentQuantum.value)+1)*self.hardwareAlignmentQuantum.value  # round up
                            newString += int(waitTime/536870912)*'wait 536870912\n'  # the HSDIO card cannot handle a wait value longer than this, so we repeat it as many times as necessary
                            newString += 'wait '+str(int(waitTime % 536870912))+'\n'  # add the remaining wait
                        if not singleSampleWaveformName in waveformsInUse:
                            # add waveform to those to be transferred to LabView
                            waveformsInUse += [singleSampleWaveformName]
                            # don't create a real waveform object, just its toHardware signature
                            waveformXML += ('<waveform>'+
                                '<name>'+singleSampleWaveformName+'</name>' +
                                '<transitions>'+' '.join([str(time) for time in range(self.hardwareAlignmentQuantum.value)])+'</transitions>'+  # make as many time points as the minimum necessary for hardware
                                '<states>'+'\n'.join([' '.join([str(sample) for sample in state]) for time in range(self.hardwareAlignmentQuantum.value)])+'</states>\n' +
                                '</waveform>\n')
                    scriptOut += newString
                    continue  # don't do the scriptOut+=row+'\n'
            scriptOut += row + '\n'
        
        # then upload scriptOut instead of script.toHardware, waveformXML instead of waveforms.toHardware (those toHardware methods will return an empty string and so will not interfere)
        # then process the rest of the properties as usual
        return '<HSDIO><script>{}</script>\n<waveforms>{}</waveforms>\n'.format(scriptOut, waveformXML)+super(npHSDIO,self).toHardware()[7:]  # [7:] removes the <HSDIO> on what is returned from super.toHardware
