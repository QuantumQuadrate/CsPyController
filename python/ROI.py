"""
ROI.py
Part of the CsPyController experiment control software
author = Martin Lichtman
created = 2015.02.24
modified >= 2015.02.26

This file handles the storage of regions of interest, their display, and calculation of ROI sums.
Finding of regions of interest is handled in other files, such as roi_fitting.py.

"""

from __future__ import division
__author__ = 'Martin Lichtman'
import logging
logger = logging.getLogger(__name__)

import numpy as np
from analysis import AnalysisWithFigure

class ROI_framework(AnalysisWithFigure):
    """This is a general framework for region of interest calculations.
    This analysis calculates the region of interest sums.  ROIs are stored as 2D floating point arrays, which should
    be the same size as the camera images.  The bright pixels in these arrays represent the pixels to use in the ROI,
    and fractional values are acceptable.  ROIs can be set by several other analyses to give ROIs of different shapes,
    such as square boxes, gaussian blobs, and amorphous ICA selected blobs.
    """

    version = '2015.02.26'
    enable = Bool()
    enable_post_measurement = Bool()
    enable_post_iteration = Bool()
    enable_show_rois = Bool()
    calculate_sums = Bool()
    subtract_background = Bool()
    display_individual_rois = Bool()
    display_roi_summation = Bool()
    display_contours = Bool()
    display_numbers = Bool()
    multiply_sums_by_photoelectron_scaling = Bool()
    image_source = Str()


    ROIs = Member()  # an array of size (num shots, num rois, image rows, image columns)
    contours = Member()  # a list of the matplotlib path veritces that will be used to draw the contours around the ROIs


    def __init__(self, name, experiment):
        super(ROI_framework, self).__init__(name, experiment, "ROI framework")
        self.properties += ['version', 'enable', 'enable_post_measurement', 'enable_post_iteration',
                            'enable_show_rois', 'calculate_sums', 'subtract_background', 'display_individual_rois',
                            'display_roi_summation', 'display_contours', 'display_numbers',
                            'multiply_sums_by_photoelectron_scaling', 'image_source', 'ROIs']

    def analyzeIteration(self, iterationResults, experimentResults):
        """After each iteration, the sums are compiled and saved into an array."""
        if self.enable_post_iteration:
            # list and sort the measurements
            measurements = map(int, iterationResults['measurements'].keys())
            measurements.sort()
            # compile all the sums into one array, which makes it a lot easier to use in later analysis
            # file the results under self.name, in case this analysis is used for multiple cameras
            iterationResults['analysis/{}/sums'.format(self.name)] = np.array([iterationResults['measurements/{}/analysis/roi/sums'.format(m)].value for m in measurements])

    def analyzeMeasurement(self, measurementResults, iterationResults, experimentResults):
        """After each measurement, the region of interest sums are calculated.
        The image_source variable is used so that this analysis can point to any camera.
        image_source must be an array of shape (shots, image rows, image columns)"""

        if self.enable:
            self.calculate_sums(measurementResults[self.image_source].value)
            self.drawstuff(self.backFigure)
            super(ROI_framework, self).updateFigure()

    def drawstuff(self, fig):
        # draw individual rois
        # draw summation image individual image
        pass

    def set_ROIs(self, ROIs, contours=None):
        self.ROIs = ROIs
        self.contours = contours

        # update roi images
        # draw individual rois
        # draw roi summation
        # draw contour summation


    def calculate_sums(self, images):
        if self.subtract_background:
            images = images - self.experiment.imageSumAnalysis.background_array
        if self.multiply_sums_by_photoelectron_scaling:
            images = images * self.experiment.LabView.camera.photoelectronScaling.value
        # turn each image into a 1D array to make the multiplication simpler
        a = images.reshape(images.shape[0], images.shape[1]*images.shape[2])
        data = np.dot(a, self.rois)
        return data
