"""
This file is for analyses that are specific to the FNODE experiment and which
would not be expected to function for other experiments due to assumptions about
where data is stored, how to process it, and how to save it.
"""
import logging
import numpy as np
from analysis import Analysis
from atom.api import Str, Bool, Member


class AIAnalysisFNODE(Analysis):
    """
    Perform pre-processing on raw analog input data before sending to origin
    server. Depending on the outcome of the processing, we may choose to filter
    the measurement results.
    """
    logger = Member()
    enable = Bool(True)

    def __init__(self, experiment):
        super(AIAnalysisFNODE, self).__init__(
            name='AIAnalysisFNODE',
            experiment=experiment,
            description='Does pre-analysis on Analog Inputs for Origin Server'
        )
        self.logger = logging.getLogger(str(self.__class__))

    def analyzeMeasurement(self, measResults, iterationResults,
                           experimentResults):
        raw_data = measResults['data/AI/data'].value

        # Background due to the repumper beams
        z_repumper = np.nanmean(raw_data[1, 37:])
        xy_repumper = np.nanmean(raw_data[0, 37:])

        # Background corrected values for each axis and wavelength
        z_780 = np.nanmean(raw_data[1, 0:16]) - z_repumper
        xy_780 = np.nanmean(raw_data[0, 0:16]) - xy_repumper
        z_852 = np.nanmean(raw_data[1, 18:36]) - z_repumper
        xy_852 = np.nanmean(raw_data[0, 18:36]) - xy_repumper

        # Processed data
        fort = np.nanmean(raw_data[2])
        t_780 = z_780 + xy_780
        d_780 = z_780 - xy_780
        t_852 = z_852 + xy_852
        d_852 = z_852 - xy_852

        # Setpoints and tolerances
        # Hard coded for testing purposes, will make cleaner Soon TM

        t_852_setpoint = 0.75
        t_852_tolerance = 0.02

        d_852_setpoint = 0.08
        d_852_tolerance = 0.02

        t_780_setpoint = 0.75
        t_780_tolerance = 0.03

        d_780_setpoint = 0.04
        d_780_tolerance = 0.02

        fort_setpoint = 0.15
        fort_tolerance = 0.02

        failed = False
        if abs(t_780-t_780_setpoint) > t_780_tolerance:
            failed = True
            self.logger.info('T780 is out of spec:\n'
                             'setpoint: {}\tvalue: {}'.format(t_780_setpoint,
                                                              t_780)
                             )
        if abs(d_780-d_780_setpoint) > d_780_tolerance:
            failed = True
            self.logger.info('D780 is out of spec:\n'
                             'setpoint: {}\tvalue: {}'.format(d_780_setpoint,
                                                              d_780)
                             )
        if abs(d_852-d_852_setpoint) > d_852_tolerance:
            failed = True
            self.logger.info('D852 is out of spec:\n'
                             'setpoint: {}\tvalue: {}'.format(d_852_setpoint,
                                                              d_852)
                             )
        if abs(t_852-t_852_setpoint) > t_852_tolerance:
            failed = True
            self.logger.info('T852 is out of spec:\n'
                             'setpoint: {}\tvalue {}'.format(t_852_setpoint,
                                                              t_852)
                             )
        if abs(fort-fort_setpoint) > fort_tolerance:
            failed = True
            self.logger.info('FORT is out of spec:\n'
                             'setpoint: {}\tvalue: {}'.format(fort_setpoint,
                                                              fort)
                             )
        processed_data = [t_852, d_852, d_780, t_780, fort]
        measResults['analysis/processed_AI/data'] = processed_data
        if failed:
            return 2
        return 0


