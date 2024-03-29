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
modified >= '2021.01.21' CY
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
        self.properties += ['version']
        if self.experiment.Config.config.get('EXPERIMENT', 'Name') == 'Rb':
            self.enable = True
        else:
            self.enable = False


    def analyzeMeasurement(self, measResults, iterationResults, experimentResults):
        if self.enable:

            try:
                raw_data = measResults['data/AI/data'].value

                # to get data: raw_data[AI_channel_idx_on_the_card, range_of_sample_indices]

                # 3D MOT arms powers from I2V curves
                Y1 = (13.0538+1.07403*(np.nanmean(raw_data[3,1:10])*1000))
                Y2 = (15.2633+1.03056*(np.nanmean(raw_data[4,1:10])*1000))
                X1 = (-5.48042+1.25244*(np.nanmean(raw_data[5,1:10])*1000))
                #X2 = (-67.3664+1.3473*(np.nanmean(raw_data[6,1:10])*1000)) #old
                X2 = (3.39254 + 0.887009 * (np.nanmean(raw_data[6, 1:10])*1000))
                Z1 = (-3.03318+0.162235*(np.nanmean(raw_data[7,1:10])*1000))
                Z2 = (-10.8903+1.01039*(np.nanmean(raw_data[8,1:10])*1000))
                MOTtot = Y1+Y2+X1+X2+Z1+Z2
                MOTX = X1/X2 # x1-x2
                MOTY = Y1/Y2 # y1-y2
                MOTZ = Z1/Z2 # z1-z2"

                # Sensor for B-fields in the Box
                SBX = np.nanmean(raw_data[13,1:10])
                SBY = np.nanmean(raw_data[14,1:10])
                SBZ = np.nanmean(raw_data[15,1:10])
                # 2D MOT monitors
                I2V_2DX1 = (np.nanmean(raw_data[10, 1:10]))
                I2V_2DX2 = (np.nanmean(raw_data[9, 1:10]))
                I2V_2DY1 = (np.nanmean(raw_data[11, 1:10]))
                I2V_2DY2 = (np.nanmean(raw_data[12, 1:10]))

                MOT2DX1A = (0.0653098 + 3.9974 * I2V_2DX1)
                MOT2DX2A = (-0.19505 + 19.5512 * I2V_2DX2)
                MOT2DY1A = (-0.312174 + 28.816 * I2V_2DY1)
                MOT2DY2A = (-0.140666 + 21.6126 * I2V_2DY2)

                # MOT2DX1Cross = (-0.00255145 + 0.00449123 * MOT2DX2A)
                # MOT2DX2Cross = (-0.0015141 + 0.0068935 * I2V_2DX2)
                # MOT2DY1Cross = (-0.000700941 + 0.00549701 * I2V_2DY1)
                # MOT2DY2Cross = (-0.0000259972 + 0.000414435 * I2V_2DY2)

                # MOT2DX1 = MOT2DX1A - (0.0653098 + 3.9974 * MOT2DX1Cross)
                # MOT2DX2 = MOT2DX2A - (-0.19505 + 19.5512 * MOT2DX2Cross)
                # MOT2DY1 = MOT2DY1A - (-0.312174 + 28.816 * MOT2DY1Cross)
                # MOT2DY2 = MOT2DY2A - (-0.140666 + 21.6126 * MOT2DY2Cross)

                MOT2DX1 = MOT2DX1A
                MOT2DX2 = MOT2DX2A
                MOT2DY1 = MOT2DY1A
                MOT2DY2 = MOT2DY2A

                # MOT2DX1 = MOT2DX1A - (0.568097+222.656*MOT2DX2A)
                # MOT2DX2 = MOT2DX2A - (0.219641+145.064*MOT2DX1A)
                # MOT2DY1 =  MOT2DY1A - (0.127513+181.917*MOT2DY2A)
                # MOT2DY2 = MOT2DY2A - (0.0627294+2412.93* MOT2DY1A)

                MOT2Dtot = MOT2DX1 + MOT2DX2 + MOT2DY1 + MOT2DY2
                MOT2DX = MOT2DX1 / MOT2DX2  # x1-x2
                MOT2DY = MOT2DY1 / MOT2DY2  # y1-y2

                logger.info('X1/X2 = {} Total X Power: {}'.format(MOTX, X1 + X2))
                logger.info('Y1/Y2 = {} Total Y Power: {}'.format(MOTY, Y1 + Y2))
                logger.info('Z1/Z2 = {} Total Z Power: {}'.format(MOTZ, Z1 + Z2))
                logger.info('TOTAL = %s uW' % MOTtot)
                # print " X1 voltage is ", np.nanmean(raw_data[5,1:10])*1000
                # print " X1 is ", X1
                # print " X2 voltage is ", np.nanmean(raw_data[6,1:10])*1000
                # print " X2 is ", X2
                # print "MOTX is ",MOTX
                # MOTtot = np.nanmean(raw_data[9,1:10])

                # testing
                logger.info('2D mot X1 = {} 2D mot X2 = {}'.format(MOT2DX1, MOT2DX2))
                logger.info('2D mot Y1 = {} 2D mot Y2 = {}'.format(MOT2DY1, MOT2DY2))
                logger.info('2D mot X Arm Ratio: {}  2D mot Y Arm Ratio: {}'.format(MOT2DX, MOT2DY))
                logger.info('TOTAL = %s mW' % MOT2Dtot)
                processed_data = [MOTX, MOTY, MOTZ, MOTtot]
                processed_data2 = [MOT2DX, MOT2DY, MOT2Dtot]

                # add measurements to the measurement results
                measResults['analysis/processed_AI/data'] = processed_data
                # measResults['analysis/processed_AI/data2DMOT'] = processed_data2
                measResults['analysis/AI_magnetic_sensor_3axis'] = [SBX, SBY, SBZ]
                # hdf5['AI/test'] = 11.0
            except KeyError as e:
                logger.warning("No AI data found. This might be expected if AnalogInput is disabled, \n or if the NI instrument server is down. \n {}".format(e))


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
