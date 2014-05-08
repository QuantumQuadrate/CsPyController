#Communications functions for working with analog input, and Newport AGILIS piezo motors

#Martin Lichtman
# created  =  2013-04-22
# modified >= 2013-04-22

import logging
logging.basicConfig(stream=sys.stderr, level=logging.DEBUG)

import sys
import numpy as np
import pylab
import time
import select
import os
import socket

buffersize=128 #messages are at most 128 bytes
timeout=5 #set 5 second tcp timeouts

#number of free variables
axes=4
datalist=[]

def getSock(name,address,port):
    #setup tcp connection to a server
    try:
        sock = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
        sock.settimeout(timeout) #make it so the socket will not block forever
        sock.connect((address,port))
    except socket.timeout as exception:
        logging.debug('timeout while trying to connect to {} socket: '.format(name,exception))
        sock.close()
    except as exception:
        logging.debug('error while trying to connect to {} socket: '.format(name,exception))
        sock.close()
    else:
        return sock

def getAIsock():
    return getSock('Analog Input','localhost',10000)

def getAGILISsock():
#setup tcp connection to agilis server
    return getSock('AGILIS','128.104.162.212',10001)

def message(sock,message):
    for tries in range(3): #try 3 times
        logging.debug('sending: '+message')
        AIsock.sendall(message)
        logging.debug('waiting for response')
        try:
            response = sock.recv(buffersize) #wait for response
        except timeout as exception:
            logging.debug('timeout waiting for response: '+str(exception))
            return
        except as exception:
            logging.debug('error waiting for response: '+str(exception))
            return
        logging.debug('response: '+response)
        return response

#make a function to request the current analog input values
def AI_read():
    responsewords=message(AIsock,'read').split(' ')
    if responsewords[0]=='data': #check if we have a good response
        return map(float,responsewords[1:]) #return data portion as numbers
    else:
        print 'ai read failed'

#make a function to move AGILIS a certain relative distance
def AGILIS_move(channel,axis,distance):
    msg='move {} {} {}'.format(channel,axis,distance)
    message(AGILISsock,msg)
    if response=='done' or response=='done limit': #we have a good response (or pretty good
        return response
    else:
        print 'AGILIS move failed'

#make a function to get a datapoint at a certain position
def datapoint(dx):
    #move to position
    for i in range(axes):
        if dx[i]!=0:
            channel = int(i/2)+1 #channels 1,2,3,4
            axis=int(i%2)+1 #axes 1,2
            AGILIS_move(channel,axis,dx[i])
    #read data
    data=AI_read()
    coupling=data[2]
    print 'coupling =',coupling
    return coupling



#take a reading at the initial point
data=datapoint(np.zeros(axes))

def genetic(data):
    delta=1
    #pick an axis
    #axis=np.random.randint(axes)
    dx=np.random.randint(-delta,delta,axes)
    print 'dx={}'.format(dx)
    while True:
        data2=datapoint(dx)
        print 'data={} data2={}'.format(data,data2)
        if data2<data:
            break
        else:
            #repeat the motion
            data=data2
    print "returning"
    #reverse the motion
    data=datapoint(-dx) #measure again to return to previous position
    return dx,data

#set up plot window
pylab.ion() #interactive on
pylab.ylim([-1,1])
pylab.show()

#setup looping
firstloop=True
time1=time.time()
fps=0
print "Press ctrl+C to stop"

while True:
    dx,data = genetic(data)
    
    print 'dx:',dx
    print 'data:',data
    
    datalist.append(data) #add the best point to the plot

    #update the plot
    if firstloop:
        firstloop=False
        line,=pylab.plot(datalist)
        fps_text=pylab.text(1,0.5,'FPS = {}'.format(fps))
    else:
        line.set_xdata(np.arange(len(datalist)))
        pylab.xlim([0,len(datalist)-1])
        line.set_ydata(datalist)
        pylab.ylim([min(datalist),max(datalist)])
        fps_text.set_text('FPS = {}'.format(fps))
    pylab.draw()

    #calculate run time
    time2=time.time()        
    if time2!=time1: #prevent divide by zero
        fps=1.0/(time2-time1)
    else:
        fps=float('Inf')
    time1=time2
    
    #time.sleep(1)

    #check for keyboard press
    if os.name != 'nt':
        keyPressed=select.select([sys.stdin],[],[],0)
        if len(keyPressed[0])>0:
            break