__author__ = 'Martin Lichtman'

import TCP
s=TCP.CsServerSock(10000)

def redo():
    s.closeConnection()
    s.close()
    reload(TCP)
    s=TCP.CsServerSock(10000)
