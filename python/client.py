import TCP
c=TCP.CsClientSock('localhost',10000)

def redo():
    c.close()
    reload(TCP)
    c=TCP.CsClientSock('localhost',10000)
