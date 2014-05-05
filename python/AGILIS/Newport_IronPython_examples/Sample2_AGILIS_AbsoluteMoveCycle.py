#===============================================================================================#
# Caroline Samyn from Newport
# 4 November 2011
# Add the "WaitEndOfMotion" procedure
# Call this new procedure after each motion command (MV, PR, ...)
# Corrections
#===============================================================================================#
import time
#Initialization Start
import sys
#import time
#IOPortClientLib and Command Interface DLL are found here.
print "Adding location of IOPortClientLib.dll & Newport.AGILISUC.CommandInterface.DLL to sys.path"
sys.path.append(r'C:\Program Files\Newport\Instrument Manager\NSTRUCT\Instruments\AG-UC2-UC8\Bin')

# The CLR module provide functions for interacting with the underlying 
# .NET runtime
import clr
# Add reference to assembly and import names from namespace
clr.AddReferenceToFile("Newport.AGILISUC.CommandInterface.dll")
from CommandInterfaceAgilisUC import *

import System

#*************************************************
# Procedure to get the controller version
#*************************************************
def GetControllerVersion (componentID, flag):
	result, version, errString = AGILIS.VE(componentID) 
	if flag == 1:	
		if result == 0:
			print 'Controller version => ',version
		else:
			print 'Error=>',errString
	return result, version

#*************************************************
# Procedure to get the controller state and error
#*************************************************
def GetControllerState (componentID, axis, flag):
	# Get controller state
	result, controllerState, errString = AGILIS.TS(componentID, axis) 			
	if flag==1:	
		if result!=0:
			print 'Error => ',errString, ' result = ', result
			controllerState=0
			
		if controllerState == 0:
			print 'Controller state: ', controllerState, ' => Ready (not moving)'
		else:
			if controllerState == 1:
				print 'Controller state: ', controllerState, ' => Stepping (currently executing a PR command)'	
			else:
				if controllerState == 2:
					print 'Controller state: ', controllerState, ' => Jogging (currently executing a JA command with command parameter different than 0).'			
				else:
					if controllerState == 3:
						print 'Controller state: ', controllerState, ' => Moving to limit (currently executing MV, MA, PA commands)'						
			
	return result, controllerState
	
#*************************************************
# Procedure to get the error code
#*************************************************
def GetControllerError (componentID, flag):
	result, controllerError, errString = AGILIS.TE(componentID) 
	if flag == 1:	
		if result != 0:
			print 'GetControllerError error =>', errString
			
		if controllerError!=0:
			if controllerError == -6:
				print 'Controller error: ', controllerError, ' => Not allowed in current state'
			else:
				if controllerError == -5:
					print 'Controller error: ', controllerError, ' => Not allowed in local mode'	
				else: 
					if controllerError == -4:
						print 'Controller error: ', controllerError, ' => Parameter nn out of range'			
					else:
						if controllerError == -3:
							print 'Controller error: ', controllerError, ' => Wrong format for parameter nn (or must not be specified)'				
						else:
							if controllerError == -2:
								print 'Controller error: ', controllerError, ' => Axis out of range (must be 1 or 2, or must not be specified)'
							else:
								if controllerError == -1:
									print 'Controller error: ', controllerError, ' => Unknown command'					
			
	return result, controllerError
	
#*************************************************
# Procedure to wait the end of current motion
# Author: Newport
#*************************************************
def WaitEndOfMotion (componentID, axis):
	print "WaitEndOfMotion ..."
	#time.sleep(40)
	time.sleep(1)
	
	# Get controller status
	result, ControllerState = GetControllerState (componentID, axis, 1)		
	while ControllerState != 0 & result == 0:
		time.sleep(TEMPO)
		# Get controller status
		result, ControllerState = GetControllerState (componentID, axis, 1)
		
	if result!=0:
		print 'ERROR=', result

	return result

#*************************************************
# Procedure to perform a relative motion
#*************************************************
def RelativeMove (componentID, axis, NumberSteps, flag):
	if (flag == 1):
		print 'Moving ' , NumberSteps, ' steps ...'
	
	# Execute a relative motion	
	result, errStringMove = AGILIS.PR(componentID, axis, NumberSteps)
	return result
	
#*************************************************
# Procedure to perform an absolute motion
#*************************************************
def AbsoluteMove (componentID, axis, position, flag):
	if (flag == 1):
		print 'Moving to ' , position
		
	# Execute an absolute motion	
	result, errStringMove = AGILIS.PA_Set(componentID, axis, position)
	return result
	
#*************************************************
# Procedure to set the channel number
# Only for AG-UC8 controllers
#*************************************************
def SetChannel (componentID, channelNumber, flag):
	result, errString = AGILIS.CC_Set(componentID, channelNumber)
	return result
	
#*************************************************
# Procedure to set the step amplitude
#*************************************************
def SetStepAmplitude (componentID, axis, direction, StepAmplitude, flag):
	result, errString = AGILIS.SU_Set(componentID, axis, direction, StepAmplitude)
	return result
	
#*************************************************
# Procedure to go to remote mode
#*************************************************
def RemoteMode (componentID, flag):
	if (flag == 1):
		print 'Remote mode '
		
	# Execute a relative motion	
	result, errString = AGILIS.MR(componentID) 
	
	return result
	
#*************************************************
# Procedure to go to local mode
#*************************************************
def LocalMode (componentID, flag):
	if (flag == 1):
		print 'Local mode '
		
	# Execute a relative motion	
	result, errString = AGILIS.ML(componentID) 
	
	return result
	
	
#*************************************************
# Procedure to execute motion cycle(s)
#*************************************************	
def ExecuteMotionOnChannel (componentID, channel, pos, displayFlag):
	# Initialization
	controllerError=0
	result=0
	
	# Set channel number
	result = SetChannel(componentID, channel, displayFlag);
	if result != 0:
		print 'SetChannel error => ',result
	else:
		for i in range(2): 	
			if result==0 & controllerError==0:
				axis = i+1
				print '------------- Channel ',channel,' => Axis #', axis, ' --------------'		
				
				# Displacement
				result = AbsoluteMove (componentID, axis, pos, displayFlag)
				if result != 0 :
					print 'AbsoluteMove error => ',result		
				else:	
					# Get controller error
					result, controllerError = GetControllerError(componentID, 1)
					if result != 0 :
						print 'GetControllerError error => ',result		
					else:
						if controllerError==0:
							# Wait the end of motion	
							result=WaitEndOfMotion(componentID, axis)	
							time.sleep(1)
					
	return result, controllerError		
	
#*************************************************
# Procedure to execute motion cycle(s)
#*************************************************	
def ExecuteMotionCycle(componentID, nbloops, nbChannels, pos, displayFlag):
	controllerError=0
	result=0
	
	for count in range(nbloops):
		if result==0 & controllerError==0:
			print '----- CYCLE #',count+1,' -----'		
			for i in range(nbChannels): 
				if result==0 & controllerError==0:
					channel = i+1	
					result, controllerError = ExecuteMotionOnChannel (componentID, channel, pos, displayFlag)		

	if result!=0:
		print 'Error=', result
		
	print '----- End of cycle -----'		

	
#*************************************************
# Main program
#*************************************************
# Instrument Initialization
# The key should have double slashes since
# (one of them is escape character)
instrumentKey="Agilis (FTTNQ45S)"
print 'Instrument Key=>', instrumentKey

# Agilis interface
AGILIS = AGILISUC()

# Agilis parameter's definition
TEMPO=0.1
NB_CYCLES = 1
NB_CHANNELS = 1
displayFlag = 1
axis = 1
target=100

# register to server, componentID needs to be used in all commands
componentID = AGILIS.RegisterComponent(instrumentKey);
print 'componentID=>', componentID

# Remote mode
result = RemoteMode(componentID, displayFlag) 
	
# Get controller revision information
result, version = GetControllerVersion(componentID, displayFlag) 

# Get current controller state and error
result, state = GetControllerState(componentID, axis, displayFlag) 
	
# Get controller error
result, controllerError = GetControllerError(componentID, displayFlag)

# cycle of motions
result = ExecuteMotionCycle(componentID, NB_CYCLES, NB_CHANNELS, target, 0)	
	
print 'End of script'

# unregister server	
AGILIS.UnregisterComponent(componentID);
