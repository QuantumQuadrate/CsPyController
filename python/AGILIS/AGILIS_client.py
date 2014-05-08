#my first TCP client
#copied from http://pymotw.com/2/socket/tcp.html

import socket
import sys

# Create a TCP/IP socket
sock = socket.socket(socket.AF_INET, socket.SOCK_STREAM)

# Connect the socket to the port where the server is listening
#server_address = ('localhost', 10000)
server_address = ('128.104.162.212', 10001)
print >>sys.stderr, 'connecting to %s port %s' % server_address
sock.connect(server_address)

try:
    
    # Send data
    message = 'move 1 1 100'
    print >>sys.stderr, 'sending "%s"' % message
    sock.sendall(message)

    response = sock.recv(128)
    print "response: ",response

finally:
    print >>sys.stderr, 'closing socket'
    sock.close()
