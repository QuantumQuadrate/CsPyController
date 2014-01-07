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
importy numpy
from cs_errors import PauseError

high16bit=2**16 #the highest value to be returned for test data

def sendmsg(sock,msgtxt):
    #ask for data
    msglength=len(msgtxt)
    if msglength>=4294967296: #2**32
        logger.error('message is too long, size = '+str(msglength)+' bytes')
        return
    message='MESG'+struct.pack("!L",len(msgtxt))+msgtxt
    try:
        sock.sendall(message)
    except Exception as e:
        logger.error('Error sending message: '+str(e))
        return

def receive(sock):
    #every message should start with 'MESG'
    try:
        header = sock.recv(4)
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
            data = sock.recv(4096)
            if not data: break

    #the next part of the message is a 4 byte unsigned long interger that contains the length (in bytes) of the rest of the message
    try:
        datalen=struct.unpack("!L", sock.recv(4))[0]
    except Exception as e:
        logger.error('incorrectly formatted message: does not have 4 byte unsigned long for length. '+str(e))
        return
    
    #now get the real data
    try:
        rawdata=sock.recv(datalen)
        remaining=datalen-len(rawdata)
        while remaining>0: #repeat until we've got all the data
            logger.info('waiting for more data: '+str(len(rawdata))+'/'+str(datalen))
            rawdata+=sock.recv(remaining)
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

class CsSock(socket.socket):
    def __init(self):
        super(CsSock,self).__init__(socket.AF_INET, socket.SOCK_STREAM)
    
        

class CsClientSock(CsSock):
    def __init__(self,addressString,portNumber):
        super(CsClientSock,self).__init__()
        print 'connecting to {} port {}'.format(addressString,portNumber)
        try:
            self.connect((addressString,portNumber))
            self.setblocking(0) #wait until after we are connected, and then set the socket to be non-blocking
        except Exception as e:
            logger.error('Error while opening socket: '+str(e))
            self.close()
            raise PauseError
    
    def sendmsg(self,msgtxt):
        #reference the common message format
        sendmsg(self,msgtxt)
    
    def receive(self):
        #reference the common message format
        receive(self)
        


class CsServerSock(CsSock):
    
    def sendmsg(self,msgtxt):
        #reference the common message format
        sendmsg(self.connection,msgtxt)
    
    def receive(self):
        #reference the common message format
        receive(self.connection)

    def __init__(self,portNumber):
        super(CsClientSock,self).__init__()
        self.portNumber=portNumber
        # Bind the socket to the port given
        server_address = ('', portNumber)
        self.bind(server_address)
        logger.info('server starting up on %s port %s' % self.getsockname())
        self.listen(0) #the 0 means do not listen to any backlogged connections
        
        while True:
            logger.info('waiting for a connection')
            #the sock is blocking so it will wait for a connection
            try:
                self.connection, client_address = self.accept()
                logger.info('client connected: '+str(client_address))
            except:
                logger.info('error in CsServerSock self.accept()')
                continue
            while True:
                data=self.receive()
                print 'received "%s"' % data
                if data.startswith('<measure'):
                    #create some dummy data 16-bit 512x512
                    rows=512; columns=512; bytes=2; signed=''; highbit=2**(8*bytes);
                    testdata=numpy.random.randint(0,highbit,(rows,columns))
                    #turn the image array into a long string composed of 2 bytes for each number
                    #first create a struct object, because reusing the same object is more efficient
                    myStruct=struct.Struct('!H') #'!H' indicates unsigned short (2 byte) integers
                    testdatamsg=''.join([myStruct.pack(t) for t in testdata.flatten()])
                    msg='<image><rows>{}</rows><columns>{}</columns><bytes>{}</bytes><signed>{}</signed><data>{}</data></image>'.format(rows,columns,bytes,signed,testdatamsg)
                    self.sendmsg(msg)
                else:
                    logger.info('bad command received: '+data)
            finally:
                connection.shutdown(socket.SHUT_RDWR)
                connection.close()
