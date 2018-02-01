"""
roi_fitting.py
Part of the CsPyController experiment control software
author = Martin Lichtman
housekeeper =  Y.S.@AQuA
created = 2014.07.01
modified >= 2015.10.19

This file contains an analysis which tries to fit 49 gaussians to the atom
array.

"""

from __future__ import division
import logging

import numpy as np
from matplotlib.patches import Ellipse
from matplotlib.gridspec import GridSpec
from sklearn.decomposition import FastICA
from scipy.optimize import curve_fit
from atom.api import Bool, Float, Member, Int, Str
from analysis import ROIAnalysis

__author__ = 'Martin Lichtman'
logger = logging.getLogger(__name__)


class GaussianROI(ROIAnalysis):
    version = '2017.07.24'
    enable = Bool()  # whether or not to activate this optimization
    useICA = Bool()  # whether or not to clean up the image
    shot = Int()
    top = Float(7)
    left = Float(21)
    bottom = Float(47)
    right = Float(58)
    ROIs = Member()
    rows = Int()
    columns = Int()
    fitParams = Member()
    fitCovariances = Member()
    image_shape = Member()
    rois = Member()
    enable_grid_fit = Bool()
    automatically_use_rois = Bool()
    enable_calculate_sums = Bool()
    subtract_background = Bool()
    cutoffs = Member()
    subtract_background_from_sums = Bool()
    multiply_sums_by_photoelectron_scaling = Bool()
    cutoffs_from_which_experiment = Str()
    shots_path = Str()
    meas_analysis_path = Str()
    iter_analysis_path = Str()

    def __init__(self, name, experiment):
        super(GaussianROI, self).__init__(
            name,
            experiment,
            "a gaussian fit to the regions of interest"
        )
        self.ROIs = np.zeros(
            experiment.ROI_rows * experiment.ROI_columns,
        )

        self.set_rois()
        # HDF5 data paths
        # where the camera data is expected to be stored
        self.shots_path = 'data/{}/shots'.format(
            self.experiment.Config.config.get('CAMERA', 'DataGroup')
        )
        # where we are going to dump data after analysis
        self.meas_analysis_path = 'analysis/gaussianROI'
        self.iter_analysis_path = 'analysis/gaussian_roi'

        # analyze in a separate thread
        self.queueAfterMeasurement = True

        self.properties += [
            'version', 'enable', 'useICA', 'shot', 'top', 'left', 'bottom',
            'right', 'fitParams', 'fitCovariances', 'image_shape', 'rois',
            'enable_grid_fit', 'automatically_use_rois',
            'enable_calculate_sums', 'subtract_background', 'cutoffs',
            'subtract_background_from_sums',
            'multiply_sums_by_photoelectron_scaling',
            'cutoffs_from_which_experiment'
        ]

    def set_rois(self):
        self.rows = self.experiment.ROI_rows
        self.columns = self.experiment.ROI_columns

        warn = False
        msg = 'The ROI definitions do not agree. Check relevant analyses. '
        if len(self.ROIs) != self.rows * self.columns:
            warn = True
            msg += '\nROI definitions: `{}`, ROI rows(columns) `{}({})`'
            msg = msg.format(len(self.ROIs), self.rows, self.columns)

        if warn:
            logger.warning(msg)
            # make a new ROIs object from the old one as best as we can
            ROIs = np.zeros(self.rows * self.columns)
            for i in range(min(len(ROIs), len(self.ROIs))):
                ROIs[i] = self.ROIs[i]
            self.ROIs = ROIs
            logger.warning('new ROIs: {}'.format(self.ROIs))

    def fromHDF5(self, hdf):
        """Override of the analysis fromHDF5 fcuntion.

        I need to override this so I can call the find camera function after
        the camera has been loaded.
        """
        super(GaussianROI, self).fromHDF5(hdf)
        # I am here because the camera needs to be setup first
        self.find_camera()

    # define functions for a gaussian with various degrees of freedom

    def normal_gaussian(self, a, xy):
        return a * np.exp(-0.5 * (np.sum(xy**2, axis=0)))

    def elliptical_gaussian(self, a, w, xy):
        return self.normal_gaussian(a, xy / w)

    def rotation(self, angle):
        return np.array([
            [np.cos(angle), -np.sin(angle)],
            [np.sin(angle), np.cos(angle)]
        ])

    def rotated_gaussian(self, a, w, rotation, xy):
        # xy is (2,len(x),len(y)) as such returned by np.indices((x,y))
        xy = np.tensordot(self.rotation(rotation), xy, axes=1)
        return self.elliptical_gaussian(a, w, xy)

    def gaussian(self, a, w, rotation, xy0, xy):
        return self.rotated_gaussian(a, w, rotation, xy - xy0)

    def fitFunc(self, xy, x0, y0, spacing, grid_angle, amplitude, wx, wy,
                spot_angle, blacklevel):
        """Find the best fit to a square grid of gaussians of all the same
        height, equal spacing in x and y, allow for rotation of array, allow
        for different wx and wy, allow for uniform rotation of spots
        """

        # sum up the contribution of each gaussian to the total
        xy0 = np.array([[[x0]], [[y0]]])
        xy_offset = np.array([[[row_offset_x]], [[row_offset_y]]])
        width = np.array([[[wx]], [[wy]]])
        spots = []
        for r in xrange(self.rows):
            for c in xrange(self.columns):
                xy0i = xy0 + np.tensordot(
                    self.rotation(grid_angle),
                    np.array([[[r]], [[c]]]),
                    axes=1
                ) * spacing

                spots.append(self.gaussian(
                    amplitude,
                    width,
                    spot_angle,
                    xy0i,
                    xy
                ))
        out = np.sum(spots, axis=0) + blacklevel
        return out.ravel()

    def get_rois(self, image_shape, x0, y0, spacing, grid_angle, amplitude,
                 wx, wy, spot_angle, blacklevel):
        """Create a set of ROI masks from the fit parameters.
        Use 1 for all the amplitudes so they are weighted the same."""

        xy = np.indices(image_shape)

        # sum up the contribution of each gaussian to the total
        xy0 = np.array([[[x0]], [[y0]]])
        xy_offset = np.array([[[row_offset_x]], [[row_offset_y]]])
        width = np.array([[[wx]], [[wy]]])
        spots = np.empty((
            self.rows * self.columns,
            image_shape[0] * image_shape[1]
        ))
        i = 0
        for r in xrange(self.rows):
            for c in xrange(self.columns):
                xy0i = xy0 + np.tensordot(
                    self.rotation(grid_angle),
                    np.array([[[r]], [[c]]]),
                    axes=1
                ) * spacing

                spots[i] = self.gaussian(
                    1,
                    width,
                    spot_angle,
                    xy0i,
                    xy
                ).flatten()
                i += 1
        return spots.T

    def use_current_rois(self):
        self.rois = self.get_rois(self.image_shape, *self.fitParams)

    def analyzeMeasurement(self, measRes, iterRes, expRes):
        if self.enable and self.enable_calculate_sums:
            all_images = np.array([[
                s.value for s in measRes[self.shots_path].itervalues()
            ]])
            res = self.calculate_sums(all_images)[0]
            data_path = self.meas_analysis_path
            measRes[data_path] = res

    def postIteration(self, iterationResults, experimentResults):
        if self.enable:
            # compile all images from the chosen shot over the whole iteration
            all_images = np.array([
                [s.value for s in m[self.shots_path].itervalues()]
                for m in iterationResults['measurements'].itervalues()
            ])
            images = all_images[:, self.shot]
            self.image_shape = (images.shape[1], images.shape[2])
            if self.subtract_background:
                images -= self.experiment.imageSumAnalysis.background_array
            if self.enable_grid_fit:
                # we use a big try block, and if there are any errors, just set
                # the amplitude to 0 and move on
                try:
                    self.fitParams, self.fitCovariances = self.fit_grid(
                        images,
                        self.backFigure,
                        self.useICA,
                        self.rows,
                        self.columns,
                        self.bottom,
                        self.top,
                        self.right,
                        self.left
                    )
                    if self.automatically_use_rois:
                        self.use_current_rois()
                except Exception:
                    # note the error, set the amplitude to 0 and move on:
                    logger.exception("Exception in GaussianROI.postIteration")
                    # set the amplitude to 0 and move on
                    self.fitParams = (0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0)
                    self.fitCovariances = np.zeros(1)
                # --- save analysis ---
                data_path = self.iter_analysis_path + '/fit_params'
                iterationResults[data_path] = self.fitParams
                data_path = self.iter_analysis_path + '/covariance_matrix'
                iterationResults[data_path] = self.fitCovariances

            if self.enable_calculate_sums:
                data_path = self.iter_analysis_path + '/sums'
                iterationResults[data_path] = self.calculate_sums(all_images)

    def calculate_sums(self, images):
        if self.subtract_background_from_sums:
            images = images - self.experiment.imageSumAnalysis.background_array
        if self.multiply_sums_by_photoelectron_scaling:
            images *= self.experiment.LabView.camera.photoelectronScaling.value
        a = images.reshape(
            images.shape[0],
            images.shape[1],
            images.shape[2] * images.shape[3]
        )
        data = np.dot(a, self.rois)
        return data

    def fit_grid(self, images, fig, useICA, rows, columns, bottom, top, right,
                 left):
        """Expects images to be of shape (measurements x width x height)"""

        raw_sum = np.sum(images, axis=0)

        if useICA:
            # Only use ICA if we have enough pictures:
            if images.shape[0] > rows * columns:
                try:
                    # clean up using independent component analysis
                    X = images.reshape(
                        images.shape[0],
                        images.shape[1] * images.shape[2]
                    ).astype(float)
                    ica = FastICA(n_components=rows * columns, max_iter=2000)
                    ica.fit(X)
                    A_ica = ica.components_  # Get estimated mixing matrix
                    image_sum = np.sum(
                        np.abs(A_ica),
                        axis=0
                    ).reshape(images.shape[1], images.shape[2])
                except:
                    # ICA failed, but just note the error in the log and move
                    # on
                    logger.exception("ICA failed")
                    image_sum = raw_sum
            else:
                image_sum = raw_sum
        else:
            image_sum = raw_sum

        # --- initial guess ---

        # guess the top-left and bottom-right corners of the array as
        # (row,column) = (top,left), (bottom,right)
        # use the input from the GUI

        # find the width and height of the whole array
        span = np.array([bottom - top, right - left])
        # find the proper diagonal angle for the array
        proper_angle = np.arctan2(columns - 1, rows - 1)

        # find the tilt angle deviation
        angle = np.arctan2(span[1], span[0]) - proper_angle

        # find the spacing by using the diagonal distance
        diagonal_distance = np.sqrt(np.sum(span**2))
        diagonal_units = np.sqrt((rows - 1)**2 + (columns - 1)**2)
        spacing = diagonal_distance / diagonal_units

        # guess the gaussian width
        width = spacing / 4

        # find the noise level, and the height of the gaussians.  This could be
        # improved using a fit to the histogram
        amplitude = np.amax(image_sum)
        blacklevel = np.amin(image_sum)

        initial_guess = (
            top,
            left,
            spacing,
            angle,
            amplitude,
            width,
            width,
            0,
            blacklevel
        )

        # --- curve fit ---

        # create the (x,y) values for each point on the image
        xy = np.indices(image_sum.shape)

        # use the image_sum as our real data
        y = image_sum.ravel()

        # specifically catch errors in the fit function
        try:
            fitParams, fitCovariances = curve_fit(
                self.fitFunc,
                xy,
                y,
                p0=initial_guess
            )
        except:
            # set the amplitude to 0 and move on
            logger.exception("Fit failed in GaussianROI")
            fitParams = (0, 0, 0, 0, 0, 0, 0, 0, 0)
            fitCovariances = np.zeros((9, 9))
            # --- save analysis ---
            return fitParams, fitCovariances

        # --- update figure ---

        fig.clf()

        gs = GridSpec(
            2,
            3,
            left=0.02,
            bottom=0.02,
            top=.98,
            right=.98,
            hspace=0.2
        )

        # plot the original data
        ax = fig.add_subplot(gs[0, 0])
        ax.matshow(raw_sum)
        ax.set_title('raw data')

        if self.useICA:
            # plot the ICA cleaned up version
            ax = fig.add_subplot(gs[0, 1])
            ax.set_title('cleaned up with ICA')

        # plot the guess
        ax = fig.add_subplot(gs[0, 2])
        ax.matshow(
            self.fitFunc(xy, *initial_guess).reshape(
                image_sum.shape[0],
                image_sum.shape[1]
            ),
            vmin=np.amin(image_sum),
            vmax=np.amax(image_sum)
        )
        ax.set_title('guess')

        # plot the fit
        ax = fig.add_subplot(gs[1, 0])
        ax.matshow(
            self.fitFunc(xy, *fitParams).reshape(
                image_sum.shape[0],
                image_sum.shape[1]
            ),
            vmin=np.amin(image_sum),
            vmax=np.amax(image_sum)
        )
        ax.set_title('fit')

        # plot the 1 sigma gaussian ellipses
        x0 = fitParams[0]
        y0 = fitParams[1]
        spacing = fitParams[2]
        grid_angle = fitParams[3]
        amplitude = fitParams[4]
        wx = fitParams[5]
        wy = fitParams[6]
        spot_angle = fitParams[7]
        blacklevel = fitParams[8]

        xy0 = np.array([[[x0]], [[y0]]])
        xy_offset = np.array([[[row_offset_x]], [[row_offset_y]]])
        width = np.array([[[wx]], [[wy]]])
        ax = fig.add_subplot(gs[1, 1])
        ax.matshow(image_sum)
        ax.set_title('1 sigma contour on data')
        for r in xrange(rows):
            for c in xrange(columns):
                xy0i = xy0 + np.tensordot(
                    self.rotation(grid_angle),
                    np.array([[[r]], [[c]]]),
                    axes=1
                ) * spacing
                patch = Ellipse(
                    xy0i[::-1],
                    width=2 * wx,
                    height=2 * wy,
                    angle=-spot_angle,
                    edgecolor='white',
                    facecolor='none',
                    lw=1
                )
                ax.add_patch(patch)
                ax.text(xy0i[1], xy0i[0], str(self.rows * r + c))

        super(GaussianROI, self).updateFigure()

        return fitParams, fitCovariances
