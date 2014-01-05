# This is the reference implementation for a TCP hardware client for the CsPyController.
# author = Martin Lichtman
# created = 2014-01-05
# modified = 2014-01-05

#started from http://pymotw.com/2/socket/tcp.html

import socket
import sys
import numpy as np
import struct
import pylab
import time
import select

# Create a TCP/IP socket
sock = socket.socket(socket.AF_INET, socket.SOCK_STREAM)

# Connect the socket to the port where the server is listening
#server_address = ('128.104.162.205', 6340)
server_address = ('localhost', 9000)
print 'connecting to {} port {}'.format(*server_address)

try:
    sock.connect(server_address)
except:
    print 'error while opening socket'
    sock.close()


try:
    #set up plot window
    pylab.ion() #interactive on
    pylab.ylim([-1,1])
    pylab.show()

    firstloop=True
    time1=time.time()
    fps=0
    print "Press Enter to stop"
    while True:
    
        #ask for data
        sock.sendall('ready')
        
        #the first information passed is the size of the information to follow encoded as a 4-byte signed integer
        datasize=struct.unpack("!l", sock.recv(4))[0]
        #print 'get ready to receive %i floats...' % datasize
        #now get the real data
        rawdata=sock.recv(datasize*8)
        while len(rawdata)<(datasize*8): #repeat until we've got all the data
            #print "len(rawdata) =",len(rawdata)
            rawdata+=sock.recv(datasize*8)
        #print "...received"
        datalen=len(rawdata)
        data=struct.unpack("!{}d".format(datalen/8),rawdata)

        #update the plot
        if firstloop:
            firstloop=False
            line,=pylab.plot(data)
            fps_text=pylab.text(1,0.5,'FPS = {}'.format(fps))
        else:
            line.set_ydata(data)
            fps_text.set_text('FPS = {}'.format(fps))
        pylab.draw()
    
        #calculate run time
        time2=time.time()        
        if time2!=time1: #prevent divide by zero
            fps=1.0/(time2-time1)
        else:
            fps=float('Inf')
        time1=time2

        #check for keyboard press
        keyPressed=select.select([sys.stdin],[],[],0)
        if len(keyPressed[0])>0:
            break

finally:
    #tell the server to stop sending
    sock.sendall('quit')
    print 'closing socket'
    sock.close()
