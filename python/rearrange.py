import logging
import numpy
import h5py
import requests

from atom.api import Bool, Str, Member, Int
from instrument_property import Prop, ListProp, FloatProp
from cs_instruments import Instrument

from time import sleep

logger = logging.getLogger(__name__)


class Fit_Sites(Prop):
    # must keep track of position changes and send only difference
    Fit_site = Int() #site to apply offsets
    Fit_Frequency_x = Member() #x frequency for fit
    Fit_Frequency_y = Member() #y frequency for fit

    def __init__(self, name, experiment, description=''):
        super(Fit_Sites, self).__init__(name, experiment, description)
        self.Fit_Frequency_x = FloatProp('Fit_Frequency_x', experiment, 'the fit for the x frequency','0')
        self.Fit_Frequency_y = FloatProp('Fit_Frequency_y', experiment, 'the fit for the y frequency','0')
        self.properties += ['Fit_site', 'Fit_Frequency_x', 'Fit_Frequency_y']

    def update(self):
        # calculate relative move necessary
        return self.Fit_site, self.Fit_Frequency_x.value, self.Fit_Frequency_y.value

class Force_Sites(Prop):
    # must keep track of position changes and send only difference
    Force_site = Int() #site to apply offsets
    Force_Frequency_x = Member() #force x frequency
    Force_Frequency_y = Member() #force y frequency

    def __init__(self, name, experiment, description=''):
        super(Force_Sites, self).__init__(name, experiment, description)
        self.Force_Frequency_x = FloatProp('Force_Frequency_x', experiment, 'force the x frequency','0')
        self.Force_Frequency_y = FloatProp('Force_Frequency_y', experiment, 'force the y frequency','0')
        self.properties += ['Force_site', 'Force_Frequency_x', 'Force_Frequency_y']

    def update(self):
        # calculate relative move necessary
        return self.Force_site, self.Force_Frequency_x.value, self.Force_Frequency_y.value

class Pattern_Sites(Prop):
    # must keep track of position changes and send only difference
    occupation_site = Int() #site to apply offsets
    pattern_num = Int() #force x frequency

    def __init__(self, name, experiment, description=''):
        super(Pattern_Sites, self).__init__(name, experiment, description)
        self.properties += ['occupation_site', 'pattern_num']

    def update(self):
        # calculate relative move necessary
        return self.occupation_site, self.pattern_num


class Rearrange(Instrument):
    '''Send data to atom rearranger on PXI crate
    '''
    version = '2018.06.18'
    IP = Str()
    port = Int()
    enable = Bool()
    iter_analysis_base_path = Str()

# Arduino Dictionary Settings
    frequency_increment = Member()
    jump_time = Member()
    laser_ramp_on_time = Member()
    fit_freq_sites = Member()
    force_freq_sites = Member()

# Python Dictionary Settings    
    rows = Int()
    columns = Int()
    sub_array_left = Int()
    sub_array_top = Int()
    sub_array_width = Int()
    sub_array_height = Int()
    gaussian_roi_params = Member()
    site_pattern = Member()  # a numpy array holding and occupation status in each row
    s0_thresholds = Member()


    def __init__(self, name, experiment, description=''):
        super(Rearrange, self).__init__(name, experiment, description='') 
        self.properties += ['version', 'IP', 'port','enable', 'sub_array_left', 'sub_array_top', 'sub_array_width', 'sub_array_height']
        
        self.frequency_increment = FloatProp('frequency_increment', experiment, 'the target power 1 percentage','100')
        self.jump_time = FloatProp('jump_time', experiment, 'the target power 1 percentage','100')
        self.laser_ramp_on_time = FloatProp('laser_ramp_on_time', experiment, 'the target power 1 percentage','100')
        self.fit_freq_sites = ListProp('fit_freq_sites', experiment, 'A of sites fequency offsets which can take variable inputs', listElementType=Fit_Sites,listElementName='fit_site_freq')   
        self.force_freq_sites = ListProp('force_freq_sites', experiment, 'A of sites fequency offsets which can take variable inputs', listElementType=Force_Sites,listElementName='force_site_freq')
        self.site_pattern = ListProp('site_pattern', experiment, 'A of sites fequency offsets which can take variable inputs', listElementType=Pattern_Sites,listElementName='site_occupation')
                
        #self.site_pattern = List('site_pattern', experiment, 'occupation', listElementType=Site_Offset,listElementName='occupation signature')         
        self.properties += ['jump_time', 'frequency_increment', 'laser_ramp_on_time','enable', 'version','fit_freq_sites','force_freq_sites','site_pattern']

        # where we are going to dump data after analysis
        self.iter_analysis_base_path = 'analysis'
        
        # open settings file
        settings = h5py.File('settings.hdf5','r')
        
        # get rows and columns
        self.rows = settings['settings/experiment/ROI_rows'].value
        self.columns = settings['settings/experiment/ROI_columns'].value
        
        # get gaussian roi parameters and append image rows and columns to front of list 
        bottom = eval(settings['settings/experiment/LabView/camera/frameGrabberAcquisitionRegionBottom/function'].value)
        top =  eval(settings['settings/experiment/LabView/camera/frameGrabberAcquisitionRegionTop/function'].value)
        image_rows = bottom - top
        right = eval(settings['settings/experiment/LabView/camera/frameGrabberAcquisitionRegionRight/function'].value)
        left =  eval(settings['settings/experiment/LabView/camera/frameGrabberAcquisitionRegionLeft/function'].value)
        image_columns = right - left
        
        self.gaussian_roi_params = settings['settings/experiment/gaussian_roi/fitParams'].value
        self.gaussian_roi_params = [(image_rows,image_columns)]+list(self.gaussian_roi_params)
        
        # get cutoffs to send to rearranger
        barecutoff = settings['settings/experiment/thresholdROIAnalysis/threshold_array'].value[0]
        self.s0_thresholds = numpy.zeros(self.rows*self.columns)
        if len(barecutoff) != len(self.s0_thresholds):
            logger.warning('ROI number change detected, thresholds for rearrangement are invalid.')
            barecutoff = numpy.resize(barecutoff, len(self.s0_thresholds))
        for i in range(self.rows * self.columns):
            self.s0_thresholds[i] = barecutoff[i][0]
        self.s0_thresholds[i] = self.s0_thresholds[i]
        
        #close hdf5 file
        settings.close()


    def update_values(self):
        # return the new voltage value'

        fit_sites = []
        Fit_Frequencies_x = []
        Fit_Frequencies_y = []
        force_sites = []
        Force_Frequencies_x = []
        Force_Frequencies_y = []
        pattern = numpy.full(self.rows*self.columns,2)
        for i in self.fit_freq_sites:
            Fit_site, Fit_Frequency_x, Fit_Frequency_y = i.update()
            fit_sites = numpy.append(fit_sites, Fit_site)
            Fit_Frequencies_x = numpy.append(Fit_Frequencies_x, Fit_Frequency_x)
            Fit_Frequencies_y = numpy.append(Fit_Frequencies_y, Fit_Frequency_y)
        fit_site_array = zip(fit_sites, Fit_Frequencies_x, Fit_Frequencies_y)
        
        for i in self.force_freq_sites:
            Force_site, Force_Frequency_x, Force_Frequency_y = i.update()
            force_sites = numpy.append(force_sites, Force_site)
            Force_Frequencies_x = numpy.append(Force_Frequencies_x, Force_Frequency_x)
            Force_Frequencies_y = numpy.append(Force_Frequencies_y, Force_Frequency_y)
        force_site_array = zip(force_sites, Force_Frequencies_x, Force_Frequencies_y)
        
        for i in self.site_pattern:
            occupation_site, pattern_num = i.update()
            pattern[occupation_site] = pattern_num  
            
        arduino_dict = {'frequency_increment': self.frequency_increment.value, 'jump_time': self.jump_time.value, 'laser_ramp_on_time': self.laser_ramp_on_time.value, 
            'fitfrequencies': list(fit_site_array), 'forcefrequencies': list(force_site_array)}
        python_dict = {'doRearrangement': self.enable, 'columns': self.columns, 'rows': self.rows, 'gaussian_roi_params': self.gaussian_roi_params, 'left': self.sub_array_left, 
            'top': self.sub_array_top, 'width': self.sub_array_width, 'height': self.sub_array_height, 'pattern': list(pattern), 's0_thresholds': list(self.s0_thresholds)}
        #arduino_dict = {'frequency_increment': self.frequency_increment.value}
        #python_dict = {'columns': self.columns, 'rows': self.rows}  
            
        return python_dict, arduino_dict
        
        
        
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
        if True:
            if True:

                python_dict, arduino_dict= self.update_values()
                #print python_dict
                requests.post(python_address, json=python_dict)
                sleep(0.005)
                requests.post(arduino_address, json=arduino_dict)
                logger.info('updating atom rearranger')
            else:
            
                desired_occupation = numpy.zeros(121)            
                python_dict = {'pattern': pattern} 
                requests.post(python_address, json=python_dict)