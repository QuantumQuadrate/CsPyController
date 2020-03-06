"""
SquareROIAnalysis.py
Part of the CsPyController package.

This analysis integrates the signal in rectangular signal ROIs, substracts the
average background per pixel measured in the background ROIs and saves the data
to the HDF5 file

author = 'Martin Lichtman'
created = '2014.09.08'
modified >= '2014.09.08'
modified >= '2017.05.04'
"""

import logging

import numpy as np
from analysis import Analysis
from atom.api import Str, Bool

logger = logging.getLogger(__name__)


class AQuAAIAnalysis(Analysis):
    """Perform preprocessing on raw analog input data before sending to origin server."""

    version = '2018.02.01'
    enable = Bool()
    list_of_what_to_save = Str()

    def __init__(self, experiment):
        super(AQuAAIAnalysis, self).__init__(
            'AQuAAIAnalysis',
            experiment,
            'Does pre-analysis on Analog Inputs for Origin Server'
        )
        if self.experiment.Config.config.get('EXPERIMENT', 'Name') == 'AQUA':
            self.enable = True
        else:
            self.enable = False

    def analyzeMeasurement(self, measResults, iterationResults, experimentResults):
        if self.enable:
            raw_data = measResults['data/AI/data'].value
            Bx = np.nanmean(raw_data[0])
            By = np.nanmean(raw_data[1])
            Bz = np.nanmean(raw_data[2])
            MOT1 = np.nanmean(raw_data[3,1:2])
            MOT2 = np.nanmean(raw_data[4,1:2])
            MOT3 = np.nanmean(raw_data[5,1:2])
            MOT4 = np.nanmean(raw_data[6,1:2])
            MOT5 = np.nanmean(raw_data[7,1:2])
            Stark459 = np.nanmean(raw_data[8,13:15])
            RydA = np.nanmean(raw_data[0,1:14])
            Ryd1038 = np.nanmean(raw_data[1,1:14])
            trap_TA1 = np.nanmean(raw_data[10,13:15])
            trap_TA2 = np.nanmean(raw_data[10,16:17])
            trap_Sprout = np.nanmean(raw_data[10,18:19])
            trap_Verdi = np.nanmean(raw_data[10,20:21])
            repump_895 = np.nanmean(raw_data[3,20:21])
            processed_data = [Bx, By, Bz, MOT1, MOT2, MOT3, MOT4, MOT5, Stark459, RydA, Ryd1038, trap_TA1, trap_TA2, trap_Sprout, trap_Verdi, repump_895]
            measResults['analysis/processed_AI/data'] = processed_data
