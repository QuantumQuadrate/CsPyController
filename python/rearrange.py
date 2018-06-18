import logging
import numpy as np
import time

from atom.api import Bool, Str, Member, Int, Float
from instrument_property import Prop, IntProp, ListProp, FloatProp

from colors import green_cmap

logger = logging.getLogger(__name__)


class Rearrange(Instrument):
    '''Compares the raw ROI from the selected source to a simple threshold cut
    to determine atom number
    '''

    version = '2018.06.14'
    enable = Bool()
    frequency_increment = Float()
    iter_analysis_base_path = Str()
    desired_occupation = Member()
    xfrequencies = Member()
    yfrequencies = Member()
    laser_ramp_time = Float()
    IP = Str()
    port = Int()

    def __init__(self, name, experiment, description=''):
        super(Rearrange, self).__init__(name, experiment, description)
        self.xfrequencies = ListProp('xfrequencies', experiment, 'A list of frequency values for scanner axis1', listElementType=Rearrange,
                               listElementName='xfrequency')
        self.yfrequencies = ListProp('yfrequencies', experiment, 'A list of frequency values for scanner axis2', listElementType=Rearrange,
                               listElementName='yfrequency')
        self.desired_occupation = ListProp('desired_occupation', experiment, 'A list of sites which should have atoms loaded into them', listElementType=Rearrange,
                               listElementName='site_bool')
        self.properties += ['version', 'IP', 'port','enable','frequency_increment', 'desired_occupation', 'xfrequencies', 'yfrequencies', 'laser_ramp_time']

    def initialize(self):
        """Open the TCP socket"""
        if self.enable:
            self.isInitialized = True

    def start(self):
        self.update()
        self.isDone = True

    def update(self):
        """
        Every iteration, send the motors updated positions.
        """
        self.resultsArray = numpy.delete(numpy.empty([1,4]), (0), axis=0)
        
        for i in self.pis:
            if self.enable:
                #arr = update()
                #arr2 = [1,2,3,4]
                #IP2 = '10.141.210.242' # ip of raspberry pi 
                #port2 = 12345
                IP, port, settings_array = i.update()
                self.s = socket.socket()
                settings_array = [ d.value for d in settings_array ]
                #print(settings_array)
                data_string = pickle.dumps(settings_array)
                self.s.connect((IP, port))
                self.s.send(data_string)
                self.resultsArray = numpy.append(self.resultsArray, [pickle.loads(self.s.recv(1024))], axis = 0)
                self.s.close()

    def writeResults(self, hdf5):
        if self.enable:
            hdf5['noise_eater'] = self.resultsArray
