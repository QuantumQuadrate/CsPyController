__author__ = 'jaisaacs'

###
# Serial interface for control of the Newport Vertical Stage
#
# Joshua A Isaacs 2016/11/3
#
#
###

import serial

class Newport():

    #ser_add = '' #'COM6'# Address of serial controller for stage
    #motion_dict = dict(home = 'XH',pos = 'XR', moveAbs = 'XG ', setVel = 'XV ')

    minpos = -13700
    maxpos =  13700

    def __init__(self,comport,axis='X'):
        self.axis = 'X'
        self.setaxis(axis)
        self.ser_add = comport
        self.ser = serial.Serial(self.ser_add)
        if self.ser.isOpen() == False:
            try:
                print("{} is not open".format(comport))
                ser.open()
            except Exception as e:
                print e

            #Communication options
        self.ser.timeout = 1
        self.ser.xonxoff = True

        self.WriteThenPrint('COMOPT3')


    def WriteThenPrint(self,s):
        self.ser.write((s+'\n\r').encode('utf-8'))
        response = self.ser.readlines()
        for i in response:
            print i.rstrip()

    def WriteThenStore(self,s):
        self.ser.write((s+'\n\r').encode('utf-8'))
        response = self.ser.readlines()
        print(response)
        return response

    def home(self): self.WriteThenStore(self.axis+'H')

    def setVelocity(self,vel): self.WriteThenStore(self.axis+'V {}'.format(vel))

    def moveAbs(self,pos): self.WriteThenStore(self.axis+'G {}'.format(pos))

    def moveAbsCheck(self,pos):
        '''
        Moves stage to position "pos" and acknowledges arrival with message
        :param pos:
        :return:
        '''
        output = self.WriteThenStore(self.axis+'G {}'.format(pos))
        done = ''
        while done != self.axis+'D':
            done = self.status()
            print('Status: {}\n'.format(done))
        print('Calibration: Complete!')

    def status(self): return self.WriteThenStore(self.axis+'STAT')[0].rstrip()[-2:]

    def whereAmI(self):
        output = self.WriteThenStore(self.axis+'R')[1].rstrip()[2:]
        while output == '':
            output = self.WriteThenStore(self.axis+'R')[1].rstrip()[2:]
        return float(output)

    def findCenter(self,side=-1):
        self.WriteThenStore(self.axis+'F {}'.format(side))
        done = ''
        while done != self.axis+'D':
            done = self.status()
            print('Status: {}\n'.format(done))
        print('Center: Found!')


    def calibrateStage(self):
        self.WriteThenStore(self.axis+'AZ')
        done = ''
        while done != self.axis+'D':
            done = self.status()
            print('Status: {}\n'.format(done))
        print('Calibration: Complete!')
        
    def setaxis(self,axis):
        if axis in ['X','Y','Z']:
            self.axis = axis
            #print 'Axis is {}'.format(self.axis)
        else:
            print "Invalid axis parameter passed to NewportMotionController class. Valid values are X, Y, Z. Defaulting to X."
            self.axis='X'

    def test_port(self):
        '''
        Tests the current COM port to make sure correct device is being addressed. Currently a hacky workaround.

        :return: Good port: Boolean, Is the port the correct port?
        '''
        try:
            self.whereAmI()
        except IndexError:
            print "There was an index Error. Probably wrong COM port"
            return False

        print "No Errors, probably the right port"
        return True





