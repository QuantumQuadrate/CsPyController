#set up logging module to do our debug printouts
import sys
import logging
logging.basicConfig(stream=sys.stderr, level=logging.DEBUG)
logging.debug('logging setup')

#==========================================================================
#initializing IOPortClientLib and Command Interface DLL for AGILIS instrument.

logging.debug('Adding location of IOPortClientLib.dll & Newport.AGILISUC.CommandInterface.dll to sys.path')
sys.path.append(r'C:\Program Files\Newport\Instrument Manager\NStruct\Instruments\AG-UC2-UC8\Bin')

# The CLR module provide functions for interacting with the underlying .NET runtime
logging.debug('adding .NET modules')
import clr
# Add reference to assembly and import names from namespace
logging.debug('adding AGILIS dll')
clr.AddReferenceToFile("Newport.AGILISUC.CommandInterface.dll")
from CommandInterfaceAgilisUC import *

# import Windows .NET stuff
import System
#==========================================================================

# Agilis interface constructor
logging.debug('AGILIS constructor')
AGILIS = AGILISUC()

result=AGILIS.ConnectAndDiscover()
logging.debug('ConnectAndDiscover=%s'%result)

logging.debug('import time')
import time
logging.debug('sleep(5)')
time.sleep(5) #wait so that the server has time to discover

#instrument="Agilis (FTV8ZX9J)"
#This should be the instrument key, but let's ask the server
 
print "GetInstrumentKeys()"
keys=AGILIS.GetInstrumentKeys()
print "Instrument Keys=",keys

instrument=keys[0]
print 'instrument=',instrument

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

#------------setup TCP server------------
import socket
import select

buffersize=128 #messages are at most 128 bytes
timeout=5 #set 5 second tcp timeouts

# Create a TCP/IP socket
sock = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
sock.settimeout(timeout) #make it so the socket will not block forever
    
#may or may not need to put current IP address of AGILIS server in here
server_address = ('', 10001)
sock.bind(server_address)
logging.debug('starting up on %s port %s' % sock.getsockname())
sock.listen(1)

def move(channel,axis,distance):
    #set the channel
    logging.debug('CC_Set()')
    result,errstring=AGILIS.CC_Set(componentID, channel)
    logging.debug('result='+str(result))
    if result !=0:
        logging.debug('errstring='+errstring)
        return "change channel failed: "+errstring
    #try a relative move
    logging.debug('PR()')
    result,errstring=AGILIS.PR(componentID,axis,distance)
    if result!=0:
        logging.debug('errstring='+errstring)
        return "move failed: "+errstring
    else:
        timeout=time.time()+5 #timeout if move is longer than 5 seconds
        while time.time()<timeout: #loop until we reach the set position
            #check limit status
            result,limitStatus,errstring=AGILIS.PH(componentID)
            if result==0:
                if limitStatus!=0:
                    logging.debug('limit reached, result: {}, errstring: {}'.format(result,errstring))
                    return 'done limit'
            else:
                logging.debug('error while checking limit status: '+errstring)
            #check movement status
            result,status,errstring=AGILIS.TS(componentID,axis)
            if result==0:
                if status==0: #movement has stopped
                    return 'done'
            else:
                logging.debug('error getting axis status:'+errstring)
                return errstring
        logging.debug('timeout reached while moving')
        return 'timeout'

def doCommand(command):
    commandwords=command.split(' ')
    print commandwords
    if commandwords[0]=='move':
        channel,axis,distance=map(int,commandwords[1:4]) #floor to integers
        return move(channel,axis,distance)
    return "not a valid command"

while True:
    logging.debug('waiting for a connection')
    #the following command blocks until a connection is made
    try:
        connection, client_address = sock.accept()
    except:
        logging.debug('error waiting for client connection')
        continue #return to waiting for connection
    logging.debug('client connected:'+str(client_address))
    #loop until connection is broken
    logging.debug('starting command loop')
    while True:
        logging.debug('waiting for command')
        try:
            #ready = select.select([AIsock], [], [], timeout)
            #if not ready[0]:
            #    print 'timeout while waiting for AI response'
            #    break #go back to accepting connections
            command = connection.recv(buffersize)
        except timeout:
            logging.debug('timeout while waiting for command')
            continue
        except:
            logging.debug('error in recv()')
            break #go back to accepting connections
        if command:
            logging.debug('received command: '+command)
            response=doCommand(command)
            try:
                logging.debug('sending response')
                connection.sendall(response)
            except:
                print 'error sending response'
                break #go back to accepting connections
    logging.debug('closing connection')
    connection.close()

# Local mode
logging.debug('returning to local mode')
result, errString = AGILIS.ML(componentID) 
if result == 0 :
	print 'controller error=>', response
else:
	print 'ML Error=>',errString

# unregister server	
print 'unregistering...'
AGILIS.UnregisterComponent(componentID);
print 'unregistered'
print 'End of script'
