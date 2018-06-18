import logging
import numpy
import time
import requests

from atom.api import Bool, Str, Member, Int, Float
from instrument_property import Prop, IntProp, ListProp, FloatProp
from cs_instruments import Instrument
from colors import green_cmap

logger = logging.getLogger(__name__)


class Rearrange_settings(Prop):
    # must keep track of voltage changes
    frequency_increment = Float()
    jump_time = Float()
    desired_occupation = Member()
    xfrequencies = Member()
    yfrequencies = Member()
    laser_ramp_on_time = Float()
    

    def __init__(self, name, experiment):
        super(Rearrange_settings, self).__init__(name, experiment, description)
        self.xfrequencies = ListProp('xfrequencies', experiment, 'A list of frequency values for scanner axis1', listElementType=Rearrange,
                               listElementName='xfrequency')
        self.yfrequencies = ListProp('yfrequencies', experiment, 'A list of frequency values for scanner axis2', listElementType=Rearrange,
                               listElementName='yfrequency')
        self.desired_occupation = ListProp('desired_occupation', experiment, 'A list of sites which should have atoms loaded into them', listElementType=Rearrange,
                               listElementName='site_bool')
        self.properties += ['frequency_increment', 'jump_time', 'desired_occupation', 'xfrequencies', 'yfrequencies', 'laser_ramp_time']
        
                # where we are going to dump data after analysis
        self.iter_analysis_base_path = 'analysis'
        
        self.frequency_array = np.zeros(
            (2, experiment.ROI_rows * experiment.ROI_columns)
        )

        
    def postIteration(self, iterationResults, experimentResults):
        if self.enable:
            # --- save analysis ---
            data_path = self.iter_analysis_base_path + 'rearrange/site_frequencies'
            frequency_array = numpy.array[self.xfrequencies,self.yfrequencies]
            iterationResults[data_path] = frequency_array
            data_path = self.iter_analysis_base_path + 'rearranger/occupation_matrix'
            iterationResults[data_path] = self.desired_occupation
            data_path = self.iter_analysis_base_path + 'rearranger/laser_ramp_params'
            iterationResults[data_path] = [self.frequency_increment, self.jump_time, self.laser_ramp_on_time]
            
    def update(self):
        # return the new voltage value
        gaussian_roi_params = self.iter_analysis_base_path + 'gaussian_roi/fit_params'
        s0_thresholds = self.iter_analysis_base_path + 'threasholds/s0'
        return self.xfrequencies, self.yfrequencies, self.desired_occupation; self.frequency_increment, self.jump_time, self.laser_ramp_on_time gaussian_roi_params, s0_thresholds

class Rearrange(Instrument):
    '''Send data to atom rearranger on PXI crate
    '''

    version = '2018.06.18'
    enable = Bool()
    IP = Str()
    port = Int()

    def __init__(self, name, experiment, description=''):
        super(Rearrange, self).__init__(name, experiment, description)
        self.properties += ['version', 'IP', 'port','enable']

    def initialize(self):
        if self.enable:
            self.isInitialized = True

    def start(self):
        self.isDone = True

    def update(self):
        """
        Every iteration, send settings to rearranger program updated positions.
        """
        python_address = 'http://{}:{}/python_settings'.format(self.IP, self.port)
        arduino_address = 'http://{}:{}/arduino_settings'.format(self.IP, self.port)
        if self.enable:

            xfrequencies, yfrequencies, desired_occupation, frequency_increment, jump_time, laser_ramp_on_time, gaussian_roi_params, s0_thresholds = i.update()
            
            arduino_dict = {'xfrequencies': xfrequencies, 'yfrequencies': yfrequencies, 'frequency_increment': frequency_increment, 
            'jump_time': jump_time, 'laser_ramp_on_time': laser_ramp_on_time}
            
            python_dict = {'desired_occupation': desired_occupation, 'gaussian_roi_params': gaussian_roi_params, 's0_thresholds': s0_thresholds}
            
            requests.post(python_address, json=python_dict)
            requests.post(arduino_address, json=arduino_dict)
        else:
            xfrequencies, yfrequencies, desired_occupation, frequency_increment, jump_time, laser_ramp_on_time, gaussian_roi_params, s0_thresholds = i.update()
            
            desired_occupation = zeros(121)            
            python_dict = {'desired_occupation': desired_occupation} 
            requests.post(python_address, json=python_dict)

