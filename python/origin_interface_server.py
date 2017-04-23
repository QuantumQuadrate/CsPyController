"""
origin_interface_server.py
Part of the CsPyController package.

A server that waits for events from a controller program, and then transfers the selected 
contents of the passed hdf5 file to the origin data server.

author = 'Matthew Ebert'
created = '2017.04.21'
"""

__author__ = 'Matthew Ebert'

import logging
#get the root logger
logger = logging.getLogger()
logger.setLevel(logging.DEBUG)

#set up logging to console for INFO and worse
sh = logging.StreamHandler()
sh.setLevel(logging.INFO)
sh_formatter = logging.Formatter(fmt='%(asctime)s\n%(message)s\n\n', datefmt='%H:%M:%S')
sh.setFormatter(sh_formatter)

#put the handlers to use
logger.addHandler(sh)

import os, datetime, time, struct
import numpy as np
import TCP  # import from our package
import h5py

import sys, traceback

class OriginInterfaceServer(TCP.CsServerSock):
    """A subclass of CsServerSock which handles incoming TCP requests for data"""

    def __init__(self, portNumber):
        super(OriginInterfaceServer, self).__init__(portNumber)

    # override parsemsg to define what this CsServerSock will do with incoming messages
    def parsemsg(self, data):
        result = super(OriginInterfaceServer, self).parsemsg(data)
        try:
            self.openFile(result)
        except Exception as e:
            print "Exception in user code:"
            print '-'*60
            traceback.print_exc(file=sys.stdout)
            print '-'*60 
        msg=TCP.makemsg('success', '0')
        return msg

    def openFile(self, data):
        self.filepath = data['file']
        print 'path: ', self.filepath
        print(os.path.isfile(self.filepath))
        f = h5py.File(self.filepath, 'r')
        print(f.name)
        print(f.keys())

if __name__ == '__main__':
    # start TCP/IP server in a different thread
    server = OriginInterfaceServer(9003)
    try:
        while True:
            time.sleep(0.1)
    except Exception as e:
        print('stopping thread')
        server.closeConnection()