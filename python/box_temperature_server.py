"""
box_temperature_server.py
Party of the CsPyController package.

A program to talk to the Laird temperature controllers (used for the box coldplates).
This program continuously grabs the temperature data from the controllers and saves it to a file.
It also runs a TCP/IP server that returns the most recent temperature information when polled.  This is used to save
the most recent temperature info into the experiment hdf5 files.

author = 'Martin Lichtman'
created = '2014.09.08'
modified >= '2014.09.08'
"""

__author__ = 'Martin Lichtman'

import serial, os, datetime, time, struct
import numpy as np
import TCP  # import from our package

# define which COM ports have which Laird controllers
ports = np.array([('COM6', 'frontS'),
              ('COM7', 'frontN'),
              ('COM8', 'topS'),
              ('COM9', 'topN'),
              ('COM10', 'bottomS'),
              ('COM11', 'bottomN')],
              dtype = np.dtype([('port', str, 5), ('name', str, 7)]))

# the string to send to the controllers to ask for data
request_string = '$R0?\r$R100?\r$R101?\r$R102?\r$R103?\r$R150?\r$R152?\r$R106?\r'

# label columns of expected data
labels = ['Set point', 'Main sensor', 'Coldplate', 'Extra sensor', 'Controller', 'Current', 'Voltage', 'Power']


class Controller(object):
    """Define an individual channel controller"""

    def __init__(self, name, port):

        # hold the name of this controller
        self.name = name

        # open the serial port to communicate with the controller
        self.ser = serial.Serial(port, 115200, timeout=.02, writeTimeout=.02)

        # open the file to log the results
        filename = r'X:\{}.txt'.format(self.name)

        # check if it already exists
        exists = os.path.exists(filename)

        # open data file in append mode
        self.file = open(filename, 'a')

        # add the header if necessary
        if not exists:
            self.file.write('Date and time\t'+'\t'.join(labels)+'\n')

        # create an array to hold returned data
        self.data = np.zeros(8, dtype=np.float64)

        # load initial data
        self.read_port()

    def read_port(self):
        self.ser.write(request_string)  # send a request for the cold plate controller state
        data1 = self.ser.readlines()  # read the returned data (will wait for 20 ms timeout)
        data2 = [x.strip() for x in data1]  # remove newlines
        # Remove echoed commands, keeping the data which is in every other word.  Cast data to float.
        self.data[:] = map(float, [data2[j] for j in xrange(1, 16, 2)])
        print self.name, ' '.join(*self.data)

        # write data to file
        datestring = datetime.datetime.now().strftime('%Y/%m/%d %H:%M:%S')
        self.file.write(datestring + '\t' + '\t'.join(map((lambda x: '{:.6f}'.format(x)), self.data)) + '\n')

    def get_data(self):
        return struct.pack('!8d', *self.data)

class BoxTempServer(TCP.CsServerSock):
    """A subclass of CsServerSock which handles incoming TCP requests for data"""

    def __init__(self, portNumber, controllers):
        self.controllers = controllers
        super(BoxTempServer, self).__init__(portNumber)

    # override parsemsg to define what this CsServerSock will do with incoming messages
    def parsemsg(self, data):
        msg = ''
        if data.startswith('get'):
            for i in self.controllers:
                msg += TCP.makemsg('Laird/'+i.name, i.get_data)
        return msg

if __name__ == '__main__':
    # open all controllers
    controllers = [Controller(i['name'], i['port']) for i in ports]

    # start TCP/IP server in a different thread
    server = BoxTempServer(9001, controllers)

    # enter a loop of continual data taking
    while True:
        time.sleep(300)  # wait 5 minutes between data points
        print ' '.join(labels)
        for controller in controllers:
            controller.read_port()