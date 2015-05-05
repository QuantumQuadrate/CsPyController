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
    enable = Bool()  # whether or not to activate this optimization
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

#TODO:
# calculated data must be filed under self.name, in case of multiple cameras
# there should be an input box for which camera data to use

    def __init__(self, name, experiment):
        super(ROI_framework, self).__init__(name, experiment, "ROI framework")
        self.properties += ['version', 'enable', 'enable_post_measurement', 'enable_post_iteration',
                            'enable_show_rois', 'calculate_sums', 'subtract_background', 'display_individual_rois',
                            'display_roi_summation', 'display_contours', 'display_numbers',
                            'multiply_sums_by_photoelectron_scaling', 'image_source', 'ROIs']

    def analyzeIteration(self, iterationResults, experimentResults):
        # draw summation image
        if self.enable_post_iteration:
            pass

    def analyzeMeasurement(self, measurementResults, iterationResults, experimentResults):
        """This is called after each measurement.
        The parameters (measurementResults, iterationResults, experimentResults)
        reference the HDF5 nodes for this measurement.
        Subclass this to update the analysis appropriately."""

        self.calculate_sums(measurementResults[image_source])
        if self.enable_post_measurement:

            measurementResults

        self.drawstuff(self.backFigure)

        super(ROI_framework, self).updateFigure()

    def drawstuff(self, fig):
        # draw individual rois
        # draw summation image individual image
        # draw
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
        a = images.reshape(images.shape[0], images.shape[1], images.shape[2]*images.shape[3])
        data = np.dot(a, self.rois)
        return data
