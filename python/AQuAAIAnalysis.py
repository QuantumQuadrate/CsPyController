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

logger = logging.getLogger(__name__)




class AQuAAIAnalysis(Analysis):
    """Add up the sums of pixels in a region, and evaluate whether or not an
    atom is present based on the totals.
    """

    version = '2018.02.01'


    def __init__(self, experiment):
        super(AQuAAIAnalysis, self).__init__(
            'AQuAAIAnalysis',
            experiment,
            'Does pre-analysis on Analog Inputs for Origin Server'
        )
        if self.experiment.Config.config.get('EXPERIMENT', 'Name') == 'AQUA':
            self.enable = True


    def analyzeMeasurement(self, measResults, iterationResults, experimentResults):
        raw_data = measResults['data/AI/data'].value
        Bx = np.nanmean(raw_data[0])
        By = np.nanmean(raw_data[1])
        Bz = np.nanmean(raw_data[2])
        processed_data = [Bx,By,Bz]
        measResults['analysis/processed_AI/data'] = processed_data