"""
    PythonForPicam is a Python ctypes interface to the Princeton Instruments PICAM Library
    Copyright (C) 2013  Joe Lowney.  The copyright holder can be reached at joelowney@gmail.com

    This program is free software: you can redistribute it and/or modify
    it under the terms of the GNU General Public License as published by
    the Free Software Foundation, either version 3 of the License, or any 
    later version.

    This program is distributed in the hope that it will be useful,
    but WITHOUT ANY WARRANTY; without even the implied warranty of
    MERCHANTABILITY or FITNESS FOR A PARTICULAR PURPOSE.  See the
    GNU General Public License for more details.

    You should have received a copy of the GNU General Public License
    along with this program.  If not, see <http://www.gnu.org/licenses/>.
"""


import ctypes

################################
##### PicamParameterLookup #####
################################
def PI_V(PicamValueType, PicamConstraintType, n):
	if(PicamConstraintType == "None"):
		c = 1
	if(PicamConstraintType == "Range"):
		c = 2
	if(PicamConstraintType == "Collection"):
		c = 3
	if(PicamConstraintType == "Rois"):
		c = 4
	if(PicamConstraintType == "Pulse"):
		c = 5
	if(PicamConstraintType == "Modulations"):
		c = 6
	
	if(PicamValueType == "Integer"):
		v = 1
	if(PicamValueType == "FloatingPoint"):
		v = 2
	if(PicamValueType == "Boolean"):
		v = 3
	if(PicamValueType == "Enumeration"):
		v = 4
	if(PicamValueType == "Rois"):
		v = 5
	if(PicamValueType == "LargeInteger"):
		v = 6
	if(PicamValueType == "Pulse"):
		v = 7
	if(PicamValueType == "Modulations"):
		v = 8
		
	returnval = c * 16777216 + v * 65536 + n
	return returnval

"""
/*-------------------------------------------------------------------------------------*/
/* Shutter Timing ---------------------------------------------------------------------*/
/*-------------------------------------------------------------------------------------*/
"""
PicamParameter_ExposureTime                      = PI_V("FloatingPoint", "Range",        23)
PicamParameter_ShutterTimingMode                 = PI_V("Enumeration",   "Collection",   24)
PicamParameter_ShutterOpeningDelay               = PI_V("FloatingPoint", "Range",        46)
PicamParameter_ShutterClosingDelay               = PI_V("FloatingPoint", "Range",        25)
PicamParameter_ShutterDelayResolution            = PI_V("FloatingPoint", "Collection",   47)
"""
/*-------------------------------------------------------------------------------------*/
/* Intensifier ------------------------------------------------------------------------*/
/*-------------------------------------------------------------------------------------*/
"""
PicamParameter_EnableIntensifier                 = PI_V("Boolean",       "Collection",   86)
PicamParameter_IntensifierStatus                 = PI_V("Enumeration",   "None",         87)
PicamParameter_IntensifierGain                   = PI_V("Integer",       "Range",        88)
PicamParameter_EMIccdGainControlMode             = PI_V("Enumeration",   "Collection",  123)
PicamParameter_EMIccdGain                        = PI_V("Integer",       "Range",       124)
PicamParameter_PhosphorDecayDelay                = PI_V("FloatingPoint", "Range",        89)
PicamParameter_PhosphorDecayDelayResolution      = PI_V("FloatingPoint", "Collection",   90)
PicamParameter_GatingMode                        = PI_V("Enumeration",   "Collection",   93)
PicamParameter_RepetitiveGate                    = PI_V("Pulse",         "Pulse",        94)
PicamParameter_SequentialStartingGate            = PI_V("Pulse",         "Pulse",        95)
PicamParameter_SequentialEndingGate              = PI_V("Pulse",         "Pulse",        96)
PicamParameter_SequentialGateStepCount           = PI_V("LargeInteger",  "Range",        97)
PicamParameter_SequentialGateStepIterations      = PI_V("LargeInteger",  "Range",        98)
PicamParameter_DifStartingGate                   = PI_V("Pulse",         "Pulse",       102)
PicamParameter_DifEndingGate                     = PI_V("Pulse",         "Pulse",       103)
PicamParameter_BracketGating                     = PI_V("Boolean",       "Collection",  100)
PicamParameter_IntensifierOptions                = PI_V("Enumeration",   "None",        101)
PicamParameter_EnableModulation                  = PI_V("Boolean",       "Collection",  111)
PicamParameter_ModulationDuration                = PI_V("FloatingPoint", "Range",       118)
PicamParameter_ModulationFrequency               = PI_V("FloatingPoint", "Range",       112)
PicamParameter_RepetitiveModulationPhase         = PI_V("FloatingPoint", "Range",       113)
PicamParameter_SequentialStartingModulationPhase = PI_V("FloatingPoint", "Range",       114)
PicamParameter_SequentialEndingModulationPhase   = PI_V("FloatingPoint", "Range",       115)
PicamParameter_CustomModulationSequence          = PI_V("Modulations",   "Modulations", 119)
PicamParameter_PhotocathodeSensitivity           = PI_V("Enumeration",   "None",        107)
PicamParameter_GatingSpeed                       = PI_V("Enumeration",   "None",        108)
PicamParameter_PhosphorType                      = PI_V("Enumeration",   "None",        109)
PicamParameter_IntensifierDiameter               = PI_V("FloatingPoint", "None",        110)
"""
/*-------------------------------------------------------------------------------------*/
/* Analog to Digital Conversion -------------------------------------------------------*/
/*-------------------------------------------------------------------------------------*/
"""
PicamParameter_AdcSpeed                          = PI_V("FloatingPoint", "Collection",   33)
PicamParameter_AdcBitDepth                       = PI_V("Integer",       "Collection",   34)
PicamParameter_AdcAnalogGain                     = PI_V("Enumeration",   "Collection",   35)
PicamParameter_AdcQuality                        = PI_V("Enumeration",   "Collection",   36)
PicamParameter_AdcEMGain                         = PI_V("Integer",       "Range",        53)
PicamParameter_CorrectPixelBias                  = PI_V("Boolean",       "Collection",  106)
"""
/*-------------------------------------------------------------------------------------*/
/* Hardware I/O -----------------------------------------------------------------------*/
/*-------------------------------------------------------------------------------------*/
"""
PicamParameter_TriggerSource                     = PI_V("Enumeration",   "Collection",   79)
PicamParameter_TriggerResponse                   = PI_V("Enumeration",   "Collection",   30)
PicamParameter_TriggerDetermination              = PI_V("Enumeration",   "Collection",   31)
PicamParameter_TriggerFrequency                  = PI_V("FloatingPoint", "Range",        80)
PicamParameter_TriggerTermination                = PI_V("Enumeration",   "Collection",   81)
PicamParameter_TriggerCoupling                   = PI_V("Enumeration",   "Collection",   82)
PicamParameter_TriggerThreshold                  = PI_V("FloatingPoint", "Range",        83)
PicamParameter_OutputSignal                      = PI_V("Enumeration",   "Collection",   32)
PicamParameter_InvertOutputSignal                = PI_V("Boolean",       "Collection",   52)
PicamParameter_AuxOutput                         = PI_V("Pulse",         "Pulse",        91)
PicamParameter_EnableSyncMaster                  = PI_V("Boolean",       "Collection",   84)
PicamParameter_SyncMaster2Delay                  = PI_V("FloatingPoint", "Range",        85)
PicamParameter_EnableModulationOutputSignal      = PI_V("Boolean",       "Collection",  116)
PicamParameter_ModulationOutputSignalFrequency   = PI_V("FloatingPoint", "Range",       117)
PicamParameter_ModulationOutputSignalAmplitude   = PI_V("FloatingPoint", "Range",       120)
"""
/*-------------------------------------------------------------------------------------*/
/* Readout Control --------------------------------------------------------------------*/
/*-------------------------------------------------------------------------------------*/
"""
PicamParameter_ReadoutControlMode                = PI_V("Enumeration",   "Collection",   26)
PicamParameter_ReadoutTimeCalculation            = PI_V("FloatingPoint", "None",         27)
PicamParameter_ReadoutPortCount                  = PI_V("Integer",       "Collection",   28)
PicamParameter_ReadoutOrientation                = PI_V("Enumeration",   "None",         54)
PicamParameter_KineticsWindowHeight              = PI_V("Integer",       "Range",        56)
PicamParameter_VerticalShiftRate                 = PI_V("FloatingPoint", "Collection",   13)
PicamParameter_Accumulations                     = PI_V("LargeInteger",  "Range",        92)
"""
/*-------------------------------------------------------------------------------------*/
/* Data Acquisition -------------------------------------------------------------------*/
/*-------------------------------------------------------------------------------------*/
"""
PicamParameter_Rois                              = PI_V("Rois",          "Rois",         37)
PicamParameter_NormalizeOrientation              = PI_V("Boolean",       "Collection",   39)
PicamParameter_DisableDataFormatting             = PI_V("Boolean",       "Collection",   55)
PicamParameter_ReadoutCount                      = PI_V("LargeInteger",  "Range",        40)
PicamParameter_ExactReadoutCountMaximum          = PI_V("LargeInteger",  "None",         77)
PicamParameter_PhotonDetectionMode               = PI_V("Enumeration",   "Collection",  125)
PicamParameter_PhotonDetectionThreshold          = PI_V("FloatingPoint", "Range",       126)
PicamParameter_PixelFormat                       = PI_V("Enumeration",   "Collection",   41)
PicamParameter_FrameSize                         = PI_V("Integer",       "None",         42)
PicamParameter_FrameStride                       = PI_V("Integer",       "None",         43)
PicamParameter_FramesPerReadout                  = PI_V("Integer",       "None",         44)
PicamParameter_ReadoutStride                     = PI_V("Integer",       "None",         45)
PicamParameter_PixelBitDepth                     = PI_V("Integer",       "None",         48)
PicamParameter_ReadoutRateCalculation            = PI_V("FloatingPoint", "None",         50)
PicamParameter_OnlineReadoutRateCalculation      = PI_V("FloatingPoint", "None",         99)
PicamParameter_FrameRateCalculation              = PI_V("FloatingPoint", "None",         51)
PicamParameter_Orientation                       = PI_V("Enumeration",   "None",         38)
PicamParameter_TimeStamps                        = PI_V("Enumeration",   "Collection",   68)
PicamParameter_TimeStampResolution               = PI_V("LargeInteger",  "Collection",   69)
PicamParameter_TimeStampBitDepth                 = PI_V("Integer",       "Collection",   70)
PicamParameter_TrackFrames                       = PI_V("Boolean",       "Collection",   71)
PicamParameter_FrameTrackingBitDepth             = PI_V("Integer",       "Collection",   72)
PicamParameter_GateTracking                      = PI_V("Enumeration",   "Collection",  104)
PicamParameter_GateTrackingBitDepth              = PI_V("Integer",       "Collection",  105)
PicamParameter_ModulationTracking                = PI_V("Enumeration",   "Collection",  121)
PicamParameter_ModulationTrackingBitDepth        = PI_V("Integer",       "Collection",  122)
"""
/*-------------------------------------------------------------------------------------*/
/* Sensor Information -----------------------------------------------------------------*/
/*-------------------------------------------------------------------------------------*/
"""
PicamParameter_SensorType                        = PI_V("Enumeration",   "None",         57)
PicamParameter_CcdCharacteristics                = PI_V("Enumeration",   "None",         58)
PicamParameter_SensorActiveWidth                 = PI_V("Integer",       "None",         59)
PicamParameter_SensorActiveHeight                = PI_V("Integer",       "None",         60)
PicamParameter_SensorActiveLeftMargin            = PI_V("Integer",       "None",         61)
PicamParameter_SensorActiveTopMargin             = PI_V("Integer",       "None",         62)
PicamParameter_SensorActiveRightMargin           = PI_V("Integer",       "None",         63)
PicamParameter_SensorActiveBottomMargin          = PI_V("Integer",       "None",         64)
PicamParameter_SensorMaskedHeight                = PI_V("Integer",       "None",         65)
PicamParameter_SensorMaskedTopMargin             = PI_V("Integer",       "None",         66)
PicamParameter_SensorMaskedBottomMargin          = PI_V("Integer",       "None",         67)
PicamParameter_SensorSecondaryMaskedHeight       = PI_V("Integer",       "None",         49)
PicamParameter_SensorSecondaryActiveHeight       = PI_V("Integer",       "None",         74)
PicamParameter_PixelWidth                        = PI_V("FloatingPoint", "None",          9)
PicamParameter_PixelHeight                       = PI_V("FloatingPoint", "None",         10)
PicamParameter_PixelGapWidth                     = PI_V("FloatingPoint", "None",         11)
PicamParameter_PixelGapHeight                    = PI_V("FloatingPoint", "None",         12)
"""
/*-------------------------------------------------------------------------------------*/
/* Sensor Layout ----------------------------------------------------------------------*/
/*-------------------------------------------------------------------------------------*/
"""
PicamParameter_ActiveWidth                       = PI_V("Integer",       "Range",         1)
PicamParameter_ActiveHeight                      = PI_V("Integer",       "Range",         2)
PicamParameter_ActiveLeftMargin                  = PI_V("Integer",       "Range",         3)
PicamParameter_ActiveTopMargin                   = PI_V("Integer",       "Range",         4)
PicamParameter_ActiveRightMargin                 = PI_V("Integer",       "Range",         5)
PicamParameter_ActiveBottomMargin                = PI_V("Integer",       "Range",         6)
PicamParameter_MaskedHeight                      = PI_V("Integer",       "Range",         7)
PicamParameter_MaskedTopMargin                   = PI_V("Integer",       "Range",         8)
PicamParameter_MaskedBottomMargin                = PI_V("Integer",       "Range",        73)
PicamParameter_SecondaryMaskedHeight             = PI_V("Integer",       "Range",        75)
PicamParameter_SecondaryActiveHeight             = PI_V("Integer",       "Range",        76)
"""
/*-------------------------------------------------------------------------------------*/
/* Sensor Cleaning --------------------------------------------------------------------*/
/*-------------------------------------------------------------------------------------*/
"""
PicamParameter_CleanSectionFinalHeight           = PI_V("Integer",       "Range",        17)
PicamParameter_CleanSectionFinalHeightCount      = PI_V("Integer",       "Range",        18)
PicamParameter_CleanSerialRegister               = PI_V("Boolean",       "Collection",   19)
PicamParameter_CleanCycleCount                   = PI_V("Integer",       "Range",        20)
PicamParameter_CleanCycleHeight                  = PI_V("Integer",       "Range",        21)
PicamParameter_CleanBeforeExposure               = PI_V("Boolean",       "Collection",   78)
PicamParameter_CleanUntilTrigger                 = PI_V("Boolean",       "Collection",   22)
"""
/*-------------------------------------------------------------------------------------*/
/* Sensor Temperature -----------------------------------------------------------------*/
/*-------------------------------------------------------------------------------------*/
"""
PicamParameter_SensorTemperatureSetPoint         = PI_V("FloatingPoint", "Range",        14)
PicamParameter_SensorTemperatureReading          = PI_V("FloatingPoint", "None",         15)
PicamParameter_SensorTemperatureStatus           = PI_V("Enumeration",   "None",         16)
PicamParameter_DisableCoolingFan                 = PI_V("Boolean",       "Collection",   29)
"""
/*-------------------------------------------------------------------------------------*/
"""

PicamParamDict = {'23': ' PicamParameter_ExposureTime', '24': ' PicamParameter_ShutterTimingMode', '46': ' PicamParameter_ShutterOpeningDelay', '25': ' PicamParameter_ShutterClosingDelay', '47': ' PicamParameter_ShutterDelayResolution', '86': ' PicamParameter_EnableIntensifier', '87': ' PicamParameter_IntensifierStatus', '88': ' PicamParameter_IntensifierGain', '123': ' PicamParameter_EMIccdGainControlMode', '124': ' PicamParameter_EMIccdGain', '89': ' PicamParameter_PhosphorDecayDelay', '90': ' PicamParameter_PhosphorDecayDelayResolution', '93': ' PicamParameter_GatingMode', '94': ' PicamParameter_RepetitiveGate', '95': ' PicamParameter_SequentialStartingGate', '96': ' PicamParameter_SequentialEndingGate', '97': ' PicamParameter_SequentialGateStepCount', '98': ' PicamParameter_SequentialGateStepIterations', '102': ' PicamParameter_DifStartingGate', '103': ' PicamParameter_DifEndingGate', '100': ' PicamParameter_BracketGating', '101': ' PicamParameter_IntensifierOptions', '111': ' PicamParameter_EnableModulation', '118': ' PicamParameter_ModulationDuration', '112': ' PicamParameter_ModulationFrequency', '113': ' PicamParameter_RepetitiveModulationPhase', '114': ' PicamParameter_SequentialStartingModulationPhase', '115': ' PicamParameter_SequentialEndingModulationPhase', '119': ' PicamParameter_CustomModulationSequence', '107': ' PicamParameter_PhotocathodeSensitivity', '108': ' PicamParameter_GatingSpeed', '109': ' PicamParameter_PhosphorType', '110': ' PicamParameter_IntensifierDiameter', '33': ' PicamParameter_AdcSpeed', '34': ' PicamParameter_AdcBitDepth', '35': ' PicamParameter_AdcAnalogGain', '36': ' PicamParameter_AdcQuality', '53': ' PicamParameter_AdcEMGain', '106': ' PicamParameter_CorrectPixelBias', '79': ' PicamParameter_TriggerSource', '30': ' PicamParameter_TriggerResponse', '31': ' PicamParameter_TriggerDetermination', '80': ' PicamParameter_TriggerFrequency', '81': ' PicamParameter_TriggerTermination', '82': ' PicamParameter_TriggerCoupling', '83': ' PicamParameter_TriggerThreshold', '32': ' PicamParameter_OutputSignal', '52': ' PicamParameter_InvertOutputSignal', '91': ' PicamParameter_AuxOutput', '84': ' PicamParameter_EnableSyncMaster', '2': ' PicamParameter_SyncMaster', '116': ' PicamParameter_EnableModulationOutputSignal', '117': ' PicamParameter_ModulationOutputSignalFrequency', '120': ' PicamParameter_ModulationOutputSignalAmplitude', '26': ' PicamParameter_ReadoutControlMode', '27': ' PicamParameter_ReadoutTimeCalculation', '28': ' PicamParameter_ReadoutPortCount', '54': ' PicamParameter_ReadoutOrientation', '56': ' PicamParameter_KineticsWindowHeight', '13': ' PicamParameter_VerticalShiftRate', '92': ' PicamParameter_Accumulations', '37': ' PicamParameter_Rois', '39': ' PicamParameter_NormalizeOrientation', '55': ' PicamParameter_DisableDataFormatting', '40': ' PicamParameter_ReadoutCount', '77': ' PicamParameter_ExactReadoutCountMaximum', '125': ' PicamParameter_PhotonDetectionMode', '126': ' PicamParameter_PhotonDetectionThreshold', '41': ' PicamParameter_PixelFormat', '42': ' PicamParameter_FrameSize', '43': ' PicamParameter_FrameStride', '44': ' PicamParameter_FramesPerReadout', '45': ' PicamParameter_ReadoutStride', '48': ' PicamParameter_PixelBitDepth', '50': ' PicamParameter_ReadoutRateCalculation', '99': ' PicamParameter_OnlineReadoutRateCalculation', '51': ' PicamParameter_FrameRateCalculation', '38': ' PicamParameter_Orientation', '68': ' PicamParameter_TimeStamps', '69': ' PicamParameter_TimeStampResolution', '70': ' PicamParameter_TimeStampBitDepth', '71': ' PicamParameter_TrackFrames', '72': ' PicamParameter_FrameTrackingBitDepth', '104': ' PicamParameter_GateTracking', '105': ' PicamParameter_GateTrackingBitDepth', '121': ' PicamParameter_ModulationTracking', '122': ' PicamParameter_ModulationTrackingBitDepth', '57': ' PicamParameter_SensorType', '58': ' PicamParameter_CcdCharacteristics', '59': ' PicamParameter_SensorActiveWidth', '60': ' PicamParameter_SensorActiveHeight', '61': ' PicamParameter_SensorActiveLeftMargin', '62': ' PicamParameter_SensorActiveTopMargin', '63': ' PicamParameter_SensorActiveRightMargin', '64': ' PicamParameter_SensorActiveBottomMargin', '65': ' PicamParameter_SensorMaskedHeight', '66': ' PicamParameter_SensorMaskedTopMargin', '67': ' PicamParameter_SensorMaskedBottomMargin', '49': ' PicamParameter_SensorSecondaryMaskedHeight', '74': ' PicamParameter_SensorSecondaryActiveHeight', '9': ' PicamParameter_PixelWidth', '10': ' PicamParameter_PixelHeight', '11': ' PicamParameter_PixelGapWidth', '12': ' PicamParameter_PixelGapHeight', '1': ' PicamParameter_ActiveWidth', '2': ' PicamParameter_ActiveHeight', '3': ' PicamParameter_ActiveLeftMargin', '4': ' PicamParameter_ActiveTopMargin', '5': ' PicamParameter_ActiveRightMargin', '6': ' PicamParameter_ActiveBottomMargin', '7': ' PicamParameter_MaskedHeight', '8': ' PicamParameter_MaskedTopMargin', '73': ' PicamParameter_MaskedBottomMargin', '75': ' PicamParameter_SecondaryMaskedHeight', '76': ' PicamParameter_SecondaryActiveHeight', '17': ' PicamParameter_CleanSectionFinalHeight', '18': ' PicamParameter_CleanSectionFinalHeightCount', '19': ' PicamParameter_CleanSerialRegister', '20': ' PicamParameter_CleanCycleCount', '21': ' PicamParameter_CleanCycleHeight', '78': ' PicamParameter_CleanBeforeExposure', '22': ' PicamParameter_CleanUntilTrigger', '14': ' PicamParameter_SensorTemperatureSetPoint', '15': ' PicamParameter_SensorTemperatureReading', '16': ' PicamParameter_SensorTemperatureStatus', '29': ' PicamParameter_DisableCoolingFan'};
