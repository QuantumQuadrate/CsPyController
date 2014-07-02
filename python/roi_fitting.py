"""
roi_fitting.py
Part of the CsPyController experiment control software
author = Martin Lichtman
created = 2014.07.01
modified >= 2014.07.01

This file contains an analysis which tries to fit 49 gaussians to the atom array.

"""

from __future__ import division
__author__ = 'Martin Lichtman'
import logging
logger = logging.getLogger(__name__)

import numpy as np
from matplotlib.patches import Ellipse
from matplotlib.gridspec import GridSpec
from sklearn.decomposition import FastICA
from scipy.optimize import curve_fit
from atom.api import Bool, Float, Member, Int
from analysis import AnalysisWithFigure

class GaussianROI(AnalysisWithFigure):
    version = '2014.07.01'
    enable = Bool()  # whether or not to activate this optimization
    shot = Int()
    top = Float(7)
    left = Float(21)
    bottom = Float(47)
    right = Float(58)
    rows = Int(7)
    columns = Int(7)

    def __init__(self, name, experiment, rows=7, columns=7):
        super(GaussianROI, self).__init__(name, experiment, "a gaussian fit to the regions of interest")
        self.rows = rows
        self.columns = columns
        self.properties += ['version', 'enable', 'shot', 'top', 'left', 'bottom', 'right']

    # define functions for a gaussian with various degrees of freedom

    def normal_gaussian(self, a, xy):
        return a*np.exp(-0.5*(np.sum(xy**2, axis=0)))

    def elliptical_gaussian(self, a, w, xy):
        return self.normal_gaussian(a, xy/w)

    def rotation(self, angle):
        return np.array([[np.cos(angle), -np.sin(angle)], [np.sin(angle), np.cos(angle)]])

    def rotated_gaussian(self, a, w, rotation, xy):
        #xy is (2,len(x),len(y)) as such returned by np.indices((x,y))
        r = np.array([[np.cos(rotation), -np.sin(rotation)], [np.sin(rotation), np.cos(rotation)]])
        xy = np.tensordot(r, xy, axes=1)
        return self.elliptical_gaussian(a, w, xy)

    def gaussian(self, a, w, rotation, xy0, xy):
        return self.rotated_gaussian(a, w, rotation, xy-xy0)

    def fitFunc(self, xy, x0, y0, spacing, grid_angle, amplitude, wx, wy, spot_angle, blacklevel):
        """
        find the best fit to a square grid of gaussians of all the same height, equal spacing in x and y,
        allow for rotation of array, allow for different wx and wy, allow for uniform rotation of spots
        """

        # sum up the contribution of each gaussian to the total
        xy0 = np.array([[[x0]], [[y0]]])
        width = np.array([[[wx]], [[wy]]])
        spots = []
        for r in xrange(self.rows):
            for c in xrange(self.columns):
                xy0i = xy0 + np.tensordot(self.rotation(grid_angle), np.array([[[r]], [[c]]]), axes=1)*spacing
                spots.append(self.gaussian(amplitude, width, spot_angle, xy0i, xy))
        out = np.sum(spots, axis=0)+blacklevel
        return out.ravel()

    def postIteration(self, iterationResults, experimentResults):
        if self.enable:
            # we use a big try block, and if there are any errors, just set the amplitude to 0 and move on
            try:
                # --- image cleanup ---

                # compile all shot 1 images from iteration
                images = np.array([m['data/Hamamatsu/shots/'+str(self.shot)] for m in iterationResults['measurements'].itervalues()])
                raw_sum = np.sum(images, axis=0)

                # Use ICA if we have enough pictures:
                if images.shape[0] > self.rows*self.columns:
                    try:
                        # clean up using independent component analysis
                        X = images.reshape(images.shape[0], images.shape[1]*images.shape[2]).astype(float)
                        ica = FastICA(n_components=self.rows*self.columns, max_iter=2000)
                        ica.fit(X)
                        A_ica = ica.components_  # Get estimated mixing matrix
                        image_sum = np.sum(np.abs(A_ica), axis=0).reshape(images.shape[1], images.shape[2])
                    except Exception as e:
                        # ICA failed, but just note the error in the log and move on
                        logger.warning("ICA failed with exception:\n{}\n".format(e))
                        image_sum = raw_sum
                else:
                    image_sum = raw_sum

                # --- initial guess ---

                # guess the top-left and bottom-right corners of the array as (row,column) = (top,left), (bottom,right)
                #use the input from the GUI

                #find the width and height of the whole array
                span = np.array([self.bottom-self.top, self.right-self.left])
                #find the proper diagonal angle for the array
                proper_angle = np.arctan2(self.columns-1, self.rows-1)

                # find the tilt angle deviation
                angle = np.arctan2(span[1], span[0]) - proper_angle

                # find the spacing by using the diagonal distance
                diagonal_distance = np.sqrt(np.sum(span**2))
                diagonal_units = np.sqrt((self.rows-1)**2+(self.columns-1)**2)
                spacing = diagonal_distance / diagonal_units

                #guess the gaussian width
                width = spacing/4

                #find the noise level, and the height of the gaussians.  This could be improved using a fit to the histogram
                amplitude = np.amax(image_sum)
                blacklevel = np.amin(image_sum)

                initial_guess = (self.top, self.left, spacing, angle, amplitude, width, width, 0, blacklevel)

                # --- curve fit ---

                #create the (x,y) values for each point on the image
                xy = np.indices(image_sum.shape)

                #use the image_sum as our real data
                y = image_sum.ravel()

                #specifically catch errors in the fit function
                try:
                    fitParams, fitCovariances = curve_fit(self.fitFunc, xy, y, p0=initial_guess)
                    #print ' initial guess: top {}, left {}, spacing {}, angle {}, amplitude {}, width {}, blacklevel {}\n'.format(*initial_guess)
                    #print ' fit coefficients: top {}, left {}, spacing {}, angle {}, amplitude {}, width {}, blacklevel {}\n'.format(*fitParams)
                    #print ' Covariance matrix:\n', fitCovariances
                except Exception as e:
                    # set the amplitude to 0 and move on
                    logger.warning("Fit failed in GaussianROI:\n{}\n".format(e))
                    fitParams = (0, 0, 0, 0, 0, 0, 0, 0, 0)
                    fitCovariances = np.zeros(1)
                    # --- save analysis ---
                    iterationResults['analysis/gaussian_roi/fit_params'] = fitParams
                    iterationResults['analysis/gaussian_roi/covariance_matrix'] = fitCovariances
                    return

                # --- save analysis ---
                iterationResults['analysis/gaussian_roi/fit_params'] = fitParams
                iterationResults['analysis/gaussian_roi/covariance_matrix'] = fitCovariances

                # --- update figure ---

                fig = self.backFigure
                fig.clf()

                gs = GridSpec(2, 3, left=0.02, bottom=0.02, top=.98, right=.98, hspace=0.2)

                # plot the original data
                ax = fig.add_subplot(gs[0, 0])
                ax.matshow(raw_sum)
                ax.set_title('raw data')

                # plot the ICA cleaned up version
                ax = fig.add_subplot(gs[0, 1])
                p1 = ax.matshow(image_sum)
                #fig.colorbar(p1)
                ax.set_title('cleaned up with ICA')

                #plot the guess
                ax = fig.add_subplot(gs[0, 2])
                ax.matshow(self.fitFunc(xy, *initial_guess).reshape(image_sum.shape[0], image_sum.shape[1]),
                           vmin=np.amin(image_sum), vmax=np.amax(image_sum))
                ax.set_title('guess')

                #plot the fit
                ax = fig.add_subplot(gs[1, 0])
                ax.matshow(self.fitFunc(xy, *fitParams).reshape(image_sum.shape[0], image_sum.shape[1]),
                           vmin=np.amin(image_sum), vmax=np.amax(image_sum))
                ax.set_title('fit')

                #plot the 1 sigma gaussian ellipses
                x0, y0, spacing, grid_angle, amplitude, wx, wy, spot_angle, blacklevel = fitParams
                xy0 = np.array([[[x0]], [[y0]]])
                width = np.array([[[wx]], [[wy]]])
                ax = fig.add_subplot(gs[1, 1])
                ax.matshow(image_sum)
                ax.set_title('1 sigma contour on data')
                for r in xrange(self.rows):
                    for c in xrange(self.columns):
                        xy0i = xy0 + np.tensordot(self.rotation(grid_angle), np.array([[[r]], [[c]]]), axes=1)*spacing
                        patch = Ellipse(xy0i[::-1], width=2*wx, height=2*wy, angle=-spot_angle, edgecolor='white',
                                        facecolor='none', lw=1)
                        ax.add_patch(patch)
                        ax.text(xy0i[1], xy0i[0], str(self.rows*r+c))

                super(GaussianROI, self).updateFigure()
            except Exception as e:
                # note the error, set the amplitude to 0 and move on:
                logger.warning("Exception in GaussianROI.postIteration:\n{}\n".format(e))
                # set the amplitude to 0 and move on
                fitParams = (0, 0, 0, 0, 0, 0, 0, 0, 0)
                fitCovariances = np.zeros(1)
                # --- save analysis ---
                iterationResults['analysis/gaussian_roi/fit_params'] = fitParams
                iterationResults['analysis/gaussian_roi/covariance_matrix'] = fitCovariances
