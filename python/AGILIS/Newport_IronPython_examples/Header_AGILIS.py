#=========================================================================
# Newport Proprietary and Confidential    Newport Corporation 2011
#
# No part of this file in any format, with or without modification 
# shall be used, copied or distributed without the express written 
# consent of Newport Corporation.
# 
#==========================================================================

#==========================================================================
#Initialization Start
#The script within Initialization Start and Initialization End is needed for properly 
#initializing IOPortClientLib and Command Interface DLL for AGILIS instrument.
#The user should copy this code as is and specify correct paths here.
import sys
import time
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

