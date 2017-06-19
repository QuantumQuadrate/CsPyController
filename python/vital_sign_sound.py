import logging
import numpy as np
import threading
from atom.api import Bool, Str, Member, Int, observe

from analysis import Analysis
import winsound

# get the config file
from __init__ import import_config
config = import_config()

logger = logging.getLogger(__name__)

class Vitalsign(Analysis):
    '''Beeps when atoms are loaded
    '''

    version = '2017.05.30'
    threshold_array = Member()
    enable = Bool()
    meas_analysis_path = Member()
    queueAfterMeasurement=True

    def __init__(self, experiment, roi_rows=1, roi_columns=1):
        super(Vitalsign, self).__init__('Vitalsign', experiment, 'Atom heartbeat')
        self.threshold_array = np.zeros(10)
        self.properties += ['version', 'threshold_array', 'enable']
        self.enable=True
        self.meas_analysis_path = 'analysis/ROIThresholds'

    def analyzeMeasurement(self, measurementResults, iterationResults, experimentResults):
        if self.enable:
            #threshold_array = np.random.choice([0, 1], size=(10,), p=[1./2, 1./2])
            threshold_array=measurementResults[self.meas_analysis_path][()]
            threshold_array.astype(int)
            if np.sum(threshold_array)>0:
                winsound.Beep(2000,200)
