from __future__ import division

"""
nidaq_ai.py

part of the CsPyController package for AQuA experiment control by Martin Lichtman

Handles reading analog data from an NI-DAQmx interface.

created = 2015.06.22
modified >= 2015.06.22
"""

__author__ = 'Martin Lichtman'
import logging
logger = logging.getLogger(__name__)

from atom.api import Bool, Str, Member, Int
from instrument_property import FloatProp, IntProp, StrProp, BoolProp
from cs_instruments import Instrument
from analysis import Analysis
from cs_errors import PauseError
from ctypes import *
import numpy



class NIDAQmxAI(Instrument,Analysis):
    version = '2016.12.21'

    allow_evaluation = Bool(True)
    gui = Member()
    enable = Bool(False)
    nidaq = Member()
    DeviceName = Member()
    DAQmx_Val_Cfg_Default = Member()
    DAQmx_Val_RSE = Int(10083)
    DAQmx_Val_NRSE = Int(10078)
    DAQmx_Val_Diff = Int(10106)
    DAQmx_Val_PseudoDiff = Int(12529)
    DAQmx_Val_Volts = Int(10348)
    DAQmx_Val_Rising = Int(10280)
    DAQmx_Val_Falling = Int(10171)
    DAQmx_Val_FiniteSamps = Int(10178)
    DAQmx_Val_GroupByChannel = Int(0)
    DAQmx_Val_GroupByScanNumber = Int(1)
    DAQmx_Val_ChanPerLine = Int(0)
    taskHandle = Member()
    samples_per_measurement = Member()
    sample_rate = Member()
    waitForStartTrigger = Member()
    triggerSource = Member()
    triggerEdge = Member()
    data = Member()
    chanList=Member()
    channellist = Member()
    outputstring = Str()
    applyFormula = Bool(False)
    formula = Str()

    def __init__(self, name, experiment, description=''):
        super(NIDAQmxAI, self).__init__(name, experiment, description)
        self.DeviceName = StrProp('DeviceName',experiment,'Device Name','Dev1')
        self.chanList = StrProp('chanList',experiment,'Channel List','[\'ai0\']')
        self.samples_per_measurement = IntProp('samples_per_measurement',experiment,'Samples per Measurement','1')
        self.sample_rate = FloatProp('sample_rate',experiment,'Sample Rate','1000')
        self.waitForStartTrigger = BoolProp('waitForStartTrigger',experiment,'Wait For Start Trigger','True')
        self.triggerSource = StrProp('triggerSource',experiment,'Trigger Source','Dev1/PFI0')
        self.triggerEdge = StrProp('triggerEdge',experiment,'Trigger Edge (\"Rising\" or \"Falling\")','Rising')
        self.properties += ['enable','DeviceName','chanList','samples_per_measurement',
                            'sample_rate','waitForStartTrigger','triggerSource','triggerEdge',
                            'applyFormula','formula']

    def preExperiment(self,hdf5):
        if self.enable and not self.isInitialized:
            self.nidaq = windll.nicaiu
            self.DAQmx_Val_Cfg_Default = c_long(-1)
            self.taskHandle = c_ulong(0)
            self.isInitialized = True

    def CHK(self,err,func):
        if err<0:
            buf_size = 1000
            buf = create_string_buffer('\000'*buf_size)
            self.nidaq.DAQmxGetErrorString(err,byref(buf),buf_size)
            logger.error('nidaq call %s failed with error %d: %s'%(func,err,repr(buf.value)))
            raise PauseError

    def preIteration(self, iterationresults, hdf5):
        if self.enable:
            if self.taskHandle.value != 0:
                self.nidaq.DAQmxStopTask(self.taskHandle)
                self.nidaq.DAQmxClearTask(self.taskHandle)
            self.CHK(self.nidaq.DAQmxCreateTask("",byref(self.taskHandle)),"CreateTask")
            try:
                self.channellist = self.chanList.value.split(',')
            except Exception as e:
                logger.error("Failed to eval DAQmx channel list (did you remember quotes?): {}".format(e))
                raise PauseError
            print self.channellist
            self.data = numpy.zeros((self.samples_per_measurement.value*len(self.channellist),),dtype=numpy.float64)
            print self.data.shape
            mychans = ""
            for i,chan in enumerate(self.channellist):
                if i<len(self.channellist)-1:
                    mychans+=self.DeviceName.value+"/"+chan+", "
                else:
                    mychans+=self.DeviceName.value+"/"+chan
            print mychans
            self.CHK(self.nidaq.DAQmxCreateAIVoltageChan(self.taskHandle,c_char_p(mychans),"",
                                                    self.DAQmx_Val_RSE,c_double(-5.0),c_double(5.0),
                                                    self.DAQmx_Val_Volts,None),"CreateAIVoltageChan")
            self.CHK(self.nidaq.DAQmxCfgSampClkTiming(self.taskHandle,"",c_double(self.sample_rate.value),self.DAQmx_Val_Rising,
                                                self.DAQmx_Val_FiniteSamps,c_uint64(self.samples_per_measurement.value)),"CfgSampClkTiming")


            if self.waitForStartTrigger.value:
                #self.CHK(self.nidaq.DAQmxCreateDIChan(self.taskHandle,self.triggerSource.value,"",self.DAQmx_Val_ChanPerLine),"CreateDIChan")
                #self.CHK(self.nidaq.DAQmxCreateAIVoltageChan(self.taskHandle,self.triggerSource.value,"",
                #                                    self.DAQmx_Val_Cfg_Default,c_double(-10.0),c_double(10.0),
                #                                    self.DAQmx_Val_Volts,None),"CreateAIVoltageChan_PFI0")
                if self.triggerEdge.value=="Rising":
                    self.CHK(self.nidaq.DAQmxCfgDigEdgeStartTrig(self.taskHandle,c_char_p(self.triggerSource.value),
                                                                  c_int32(self.DAQmx_Val_Rising)),"CfgDigEdgeStartTrig_Rising")
                else:
                    self.CHK(self.nidaq.DAQmxCfgDigEdgeStartTrig(self.taskHandle,c_char_p(self.triggerSource.value),
                                                                  c_int32(self.DAQmx_Val_Falling)),"CfgDigEdgeStartTrig_Falling")

            self.CHK(self.nidaq.DAQmxStartTask(self.taskHandle),"StartTask")
        return


    def analyzeMeasurement(self, measurementresults, iterationresults, hdf5):
        if self.enable:
            read = c_int32()
            self.CHK(self.nidaq.DAQmxReadAnalogF64(self.taskHandle,self.samples_per_measurement.value,c_double(10.0),
                                                   self.DAQmx_Val_GroupByScanNumber,self.data.ctypes.data,
                                                   len(self.data),byref(read),None),"ReadAnalogF64")
            if self.nidaq.DAQmxWaitUntilTaskDone(self.taskHandle, c_double(4.0)) < 0:
                logger.error("DAQ task took too long (> 4 seconds). Stopping task.")
            self.nidaq.DAQmxStopTask(self.taskHandle)
            self.CHK(self.nidaq.DAQmxStartTask(self.taskHandle),"(Re)StartTask")
            measurementresults['NIDAQmx_AI'] = self.data
            self.outputstring = ""
            if self.applyFormula:
                func = eval(self.formula)
            for i,chan in enumerate(self.channellist):
                if not self.applyFormula:
                    self.outputstring += "{}: {}\n".format(chan,self.data[i])
                else:
                    self.outputstring += "{}: {}\n".format(chan,func[i](self.data[i]))
        return

    def analyzeIteration(self, iterationresults, hdf5):
        if self.enable:
            if self.taskHandle.value != 0:
                self.nidaq.DAQmxStopTask(self.taskHandle)
                self.nidaq.DAQmxClearTask(self.taskHandle)
        return

    def postExperiment(self, hdf5):
        return

    def finalize(self,hdf5):
        return

