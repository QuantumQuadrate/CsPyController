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
modified >= '2018.10.22' CY
"""

import logging

import numpy as np
from analysis import Analysis
from atom.api import Str, Bool

logger = logging.getLogger(__name__)


class RbAIAnalysis(Analysis):
    """Perform preprocessing on raw analog input data before sending to origin server."""

    version = '2018.02.01'
    enable = Bool()
    list_of_what_to_save = Str()

    def __init__(self, experiment):
        super(RbAIAnalysis, self).__init__(
            'RbAIAnalysis',
            experiment,
            'Does pre-analysis on Analog Inputs for Origin Server'
        )
        if self.experiment.Config.config.get('EXPERIMENT', 'Name') == 'Rb':
            self.enable = True
        else:
            self.enable = False


    def analyzeMeasurement(self, measResults, iterationResults, experimentResults):
        if self.enable:
            raw_data = measResults['data/AI/data'].value
            Y1 = (13.0538+1.07403*(np.nanmean(raw_data[3,1:10])*1000))
            Y2 = (15.2633+1.03056*(np.nanmean(raw_data[4,1:10])*1000))
            X1 = (-5.48042+1.25244*(np.nanmean(raw_data[5,1:10])*1000))
            X2 = (-67.3664+1.3473*(np.nanmean(raw_data[6,1:10])*1000))
            Z1 = (-3.03318+0.162235*(np.nanmean(raw_data[7,1:10])*1000))
            Z2 = (-10.8903+1.01039*(np.nanmean(raw_data[8,1:10])*1000))
            MOTtot = Y1+Y2+X1+X2+Z1+Z2
            MOTX = X1/X2 # x1-x2
            MOTY = Y1/Y2 # y1-y2
            MOTZ = Z1/Z2 # z1-z2
            logger.info('X1/X2 = ', MOTX," Total X Power: ", X1+X2 )
            logger.info('Y1/Y2 = ', MOTY," Total Y Power: ", Y1+Y2 )
            logger.info('Z1/Z2 = ', MOTZ," Total Z Power: ", Z1+Z2 )
            logger.info('TOTAL = %s uW' % MOTtot)
            # print " X1 voltage is ", np.nanmean(raw_data[5,1:10])*1000
            # print " X1 is ", X1
            # print " X2 voltage is ", np.nanmean(raw_data[6,1:10])*1000
            # print " X2 is ", X2
            # print "MOTX is ",MOTX
            # MOTtot = np.nanmean(raw_data[9,1:10])

            processed_data = [MOTX,MOTY,MOTZ,MOTtot]
            measResults['analysis/processed_AI/data'] = processed_data
            # hdf5['AI/test'] = 11.0


#old analyses from AQuA#Ryd780A = np.nanmean(raw_data[0,22:26])
# Bx = np.nanmean(raw_data[0])
# By = np.nanmean(raw_data[1])
# Bz = np.nanmean(raw_data[2])
# MOT1 = np.nanmean(raw_data[3,1:2])
# MOT2 = np.nanmean(raw_data[4,1:2])
# MOT3 = np.nanmean(raw_data[5,1:2])
# MOT4 = np.nanmean(raw_data[6,1:2])
# MOT5 = np.nanmean(raw_data[7,1:2])
# Stark459 = np.nanmean(raw_data[8,13:15])
# RydA = np.nanmean(raw_data[0,1:14])
# Ryd1038 = np.nanmean(raw_data[1,1:14])
# trap_TA1 = np.nanmean(raw_data[10,13:15])
# trap_TA2 = np.nanmean(raw_data[10,16:17])
# trap_Sprout = np.nanmean(raw_data[10,18:19])
# trap_Verdi = np.nanmean(raw_data[10,20:21])
# repump_895 = np.nanmean(raw_data[3,20:21])
