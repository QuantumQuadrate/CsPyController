__author__ = 'jaisaacs'

###
# Serial interface for control of the Newport Vertical Stage
#
# Joshua A Isaacs 2016/11/3
#
#
###

import serial
import serial.tools.list_ports

import logging
logger = logging.getLogger(__name__)

class Newport():

    #ser_add = '' #'COM6'# Address of serial controller for stage
    #motion_dict = dict(home = 'XH',pos = 'XR', moveAbs = 'XG ', setVel = 'XV ')

    minpos = -13700
    maxpos =  13700

    def __init__(self,comport,axis='X'):
        self.axis = 'X'
        self.setaxis(axis)
        ports = serial.tools.list_ports.comports()
        # print ports

        # Try comport first
        self.comport_bad = False
        self.ser_add = comport
        try:
            self.ser = serial.Serial(self.ser_add)
        except serial.SerialException as e:
            logger.exception(e)
            self.comport_bad = True

        if not self.comport_bad:
            if not self.ser.isOpen():
                try:
                    self.ser.open()
                except Exception as e:
                    logger.exception(e)
            self.ser.timeout = 1
            self.ser.xonxoff = True

            self.WriteThenPrint('COMOPT3')
            self.comport_bad = not self.test_port()

        if self.comport_bad:
            for port in ports:
                #print port[0]
                if port[0] == comport:
                    continue
                try:
                    self.ser = serial.Serial(port[0])
                    logger.info("Opened Port {}".format(port[0]))
                except serial.SerialException as e:
                    logger.exception(e)
                    continue
                if not self.ser.isOpen():
                    try:
                        self.ser.open()
                        logger.info("{} is not open".format(comport))
                    except Exception as e:
                        logger.exception(e)
                self.ser.timeout = 1
                self.ser.xonxoff =True
                self.WriteThenPrint('COMOPT3')
                if self.test_port():
                    logger.info("Port {} is initialized, Axis = {}".format(port[0], self.axis))
                    break
                else:
                    self.ser.close()
                    self.ser = None

    def WriteThenPrint(self,s):
        self.ser.write((s+'\n\r').encode('utf-8'))
        response = self.ser.readlines()
        for i in response:
            logger.info(i.rstrip())

    def WriteThenStore(self,s):
        self.ser.write((s+'\n\r').encode('utf-8'))
        response = self.ser.readlines()
        logger.info(response)
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
            logger.info('Status: {}\n'.format(done))
        logger.info('Calibration: Complete!')

    def status(self): return self.WriteThenStore(self.axis+'STAT')[0].rstrip()[-2:]

    def whereAmI(self):
        output = self.WriteThenStore(self.axis+'R')[1].rstrip()[2:]
        c = 0
        while output == '' and c < 20:
            output = self.WriteThenStore(self.axis+'R')[1].rstrip()[2:]
            c += 1
            logger.info("finding location, attempt {}/20".format(c))
        return float(output)

    def findCenter(self,side=-1):
        self.WriteThenStore(self.axis+'F {}'.format(side))
        done = ''
        while done != self.axis+'D':
            done = self.status()
            logger.info('Status: {}\n'.format(done))
        logger.info('Center: Found!')


    def calibrateStage(self):
        self.WriteThenStore(self.axis+'AZ')
        done = ''
        while done != self.axis+'D':
            done = self.status()
            logger.info('Status: {}\n'.format(done))
        logger.info('Calibration: Complete!')
        
    def setaxis(self,axis):
        if axis in ['X','Y','Z']:
            self.axis = axis
            #print 'Axis is {}'.format(self.axis)
        else:
            logger.warning("Invalid axis parameter passed to "
                           "NewportMotionController class. "
                           "Valid values are X, Y, Z. Defaulting to X.")
            self.axis='X'

    def test_port(self):
        '''
        Tests the current COM port to make sure correct device is being addressed. Currently a hacky workaround.

        :return: Good port: Boolean, Is the port the correct port?
        '''
        try:
            self.whereAmI()
        except IndexError:
            logger.info("There was an index Error. Probably wrong COM port")
            return False

        logger.info("No Errors, probably the right port")
        return True





