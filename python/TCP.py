#TCP.py
#author: Martin Lichtman
#created = 2013.08.02
#modified >= 2013.08.02

#This module bundles the TCP message passing protocol defined for the Cesium project.

#Messages begin with 'MESG' followed by a 4 byte unsigned long int that gives the length of the remainder of the message.

#The class CsSock inherets from socket.socket, and makes it easier to open up the type of socket we use, and then send or receive
#a message with the correct format.


import socket
import struct
import logging
logger = logging.getLogger(__name__)
from cs_errors import PauseError

class CsSock(socket.socket):
    def __init__(self,addressString,portNumber):
        super(CsSock,self).__init__(socket.AF_INET, socket.SOCK_STREAM)
        #self.setblocking(0) #set the socket to be non-blocking
        print 'connecting to {} port {}'.format(addressString,portNumber)
        try:
            self.connect((addressString,portNumber))
            self.setblocking(0) #set the socket to be non-blocking
        except Exception as e:
            logger.error('Error while opening socket: '+str(e))
            self.close()
            raise PauseError
    
    def sendmsg(self,msgtxt):
        #ask for data
        msglength=len(msgtxt)
        if msglength>=4294967296: #2**32
            logger.error('message is too long, size = '+str(msglength)+' bytes')
            return
        message='MESG'+struct.pack("!L",len(msgtxt))+msgtxt
        try:
            self.sendall(message)
        except Exception as e:
            logger.error('Error sending message: '+str(e))
            return
        
    def receive(self):
        #every message should start with 'MESG'
        try:
            header = self.recv(4)
        except Exception as e:
            logger.error('Error trying to receive message header: '+str(e))
            return
        if not header:
            #buffer is empty, no message yet
            return
        if header!='MESG':
            logger.error('incorrectly formatted message does not being with "MESG".  Draining TCP input buffer')
            #Clear the buffer so we aren't in the middle of a message
            #TODO: There is some risk that this will result in lost messages, if
            #a good one comes into the buffer before the bad one is cleared. We
            #we may not want to do this.
            while 1:
                data = self.recv(4096)
                if not data: break

        #the next part of the message is a 4 byte unsigned long interger that contains the length (in bytes) of the rest of the message
        try:
            datalen=struct.unpack("!L", self.recv(4))[0]
        except Exception as e:
            logger.error('incorrectly formatted message: does not have 4 byte unsigned long for length. '+str(e))
            return
        
        #now get the real data
        try:
            rawdata=self.recv(datalen)
            remaining=datalen-len(rawdata)
            while remaining>0: #repeat until we've got all the data
                logger.info('waiting for more data: '+str(len(rawdata))+'/'+str(datalen))
                rawdata+=self.recv(remaining)
                remaining=datalen-len(rawdata)
        except Exception as e:
            logger.error('error while trying to read message data:'+str(e))
            return
        #check size
        if len(rawdata)!=datalen:
            logger.error('incorrect message size received')
            return
        #if we get here, we have gotten data of the right size
        return rawdata
        #do something like this for data packets, but not here:  data=struct.unpack("!{}d".format(datalen/8),rawdata)