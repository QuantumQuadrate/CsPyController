#=========================================================================
# Newport Proprietary and Confidential    Newport Corporation 2011
#
# No part of this file in any format, with or without modification 
# shall be used, copied or distributed without the express written 
# consent of Newport Corporation.
# 
# Description: This is a sample Python Script to illustrate how to execute 
# following AGILIS commands:
# VE, TS, TE, SU
#==========================================================================

#==========================================================================
#Initialization Start
#The script within Initialization Start and Initialization End is needed for properly 
#initializing IOPortClientLib and Command Interface DLL for AGILIS instrument.
#The user should copy this code as is and specify correct paths here.
import sys
# import time
#IOPortClientLib and Command Interface DLL can be found here.
print "Adding location of IOPortClientLib.dll & Newport.AGILISUC.CommandInterface.dll to sys.path"
sys.path.append(r'C:\Program Files\Newport\Instrument Manager\NStruct\Instruments\AG-UC2-UC8\Bin')

# The CLR module provide functions for interacting with the underlying 
# .NET runtime
import clr
# Add reference to assembly and import names from namespace
clr.AddReferenceToFile("Newport.AGILISUC.CommandInterface.dll")
from CommandInterfaceAgilisUC import *

import System
#==========================================================================

# Instrument Initialization
# The key should have double slashes since
# (one of them is escape character)
instrument="Agilis (FTTNQ45S)"
print 'Instrument Key=>', instrument

# Agilis interface
AGILIS = AGILISUC()

# register to server, componentID needs to be used in all commands
componentID = AGILIS.RegisterComponent(instrument);
print 'componentID=>', componentID

# Remote mode
result, errString = AGILIS.MR(componentID) 
if result != 0 :
	print 'MR Error=>',errString
	
# Get controller revision information
result, response, errString = AGILIS.VE(componentID) 
if result == 0 :
	print 'controller revision=>', response
else:
	print 'VE Error=>',errString

# Get controller status
axis = 1
result, response, errString = AGILIS.TS(componentID, axis) 
if result == 0 :
	print 'axis status=>', response
else:
	print 'TS Error=>',errString
	
# Get controller error
result, response, errString = AGILIS.TE(componentID) 
if result == 0 :
	print 'controller error=>', response
else:
	print 'TE Error=>',errString

# Get step amplitude in positive direction for axis #1
axis = 1
direction = '+'
result, StepAmplitude, errString = AGILIS.SU_Get(componentID, axis, direction) 
if result == 0 :
	print 'step amplitude (+) for axis #1=>', StepAmplitude
else:
	print 'SU_Get Error=>',errString	
	
# Get step amplitude in negative direction
direction = '-'
result, StepAmplitude, errString = AGILIS.SU_Get(componentID, axis, direction) 
if result == 0 :
	print 'step amplitude (-) for axis #1=>', StepAmplitude
else:
	print 'SU_Get Error=>',errString

# Get step amplitude in positive direction for axis #2
axis = 2
direction = '+'
result, StepAmplitude, errString = AGILIS.SU_Get(componentID, axis, direction) 
if result == 0 :
	print 'step amplitude (+) for axis #2=>', StepAmplitude
else:
	print 'SU_Get Error=>',errString	
	
# Get step amplitude in negative direction
direction = '-'
result, StepAmplitude, errString = AGILIS.SU_Get(componentID, axis, direction) 
if result == 0 :
	print 'step amplitude (-) for axis #2=>', StepAmplitude
else:
	print 'SU_Get Error=>',errString
	
# Local mode
result, errString = AGILIS.ML(componentID) 
if result == 0 :
	print 'controller error=>', response
else:
	print 'ML Error=>',errString
	
print 'End of script'

# unregister server	
AGILIS.UnregisterComponent(componentID);