import datetime
import numpy as np
import logging
import os
# MPL plotting
import matplotlib as mpl
import matplotlib.pyplot as plt
from matplotlib.gridspec import GridSpec
import matplotlib.patches as patches
from scipy.special import erf, gammainc, gammaincc, gamma
from scipy import optimize
from sklearn import mixture
from scipy.stats import poisson

from atom.api import Bool, Member, Str, observe, Int, Float

from analysis import AnalysisWithFigure, ROIAnalysis

logger = logging.getLogger(__name__)
mpl.use('PDF')


def intersection(ftype, fparams):
    """Returns the intersection of two distributions"""
    if ftype == 'gaussian':
        A1, m0, m1, s0, s1 = fparams
        return (m1*s0**2-m0*s1**2-np.sqrt(s0**2*s1**2*(m0**2-2*m0*m1+m1**2+2*np.log((1-A1)/A1)*(s1**2-s0**2))))/(s0**2-s1**2)
    if ftype == 'poisson':
        A1, m0, m1 = fparams
        A1_min = 0.1  # set cuts assuming at least 10 percent loading
        if A1 < A1_min:
            A1 = A1_min
        for s in range(int(m1)):
            if (1-A1)*poisson.pmf(s, m0) < A1*poisson.pmf(s, m1):
                return s


def overlap(ftype, fparams, cutoff):
    """Calculate the overlap intergral of two distributions, at cutoff (x >= cutoff is high)"""
    if ftype == 'gaussian':
        # intersection over union, see MTL thesis for motovation
        overlap1 = 0.5*(1 + erf((fparams[1]-cutoff)/(fparams[3]*np.sqrt(2))))
        overlap2 = 0.5*(1 + erf((cutoff-fparams[2])/(fparams[4]*np.sqrt(2))))
        return (overlap1*(1-fparams[0]) + overlap2*fparams[0]) / min(fparams[0], 1-fparams[0])
    if ftype == 'poisson':
        # use imcomplete regularized gamma functions to get type 1 and 2 error rates
        # do the calculation at p = 0.5, and not the actual loading rate
        # return fparams[0]*gammainc(fparams[2], cutoff) + (1-fparams[0])*gammaincc(fparams[1], cutoff)
        return 0.5*(gammainc(fparams[2], cutoff) + gammaincc(fparams[1], cutoff))


def frac(fparams):
    'Relative Fraction in 1'
    return fparams[0]


def dblgauss(x, A1, m0, m1, s0, s1):
    return (1-A1)*np.exp(-(x-m0)**2 / (2*s0**2))/np.sqrt(2*np.pi*s0**2) + A1*np.exp(-(x-m1)**2 / (2*s1**2))/np.sqrt(2*np.pi*s1**2)


def poisson_pdf(x, mu):
    """Continuous approximmation of the Poisson PMF to prevent failures from non-integer bin edges"""
    result = np.power(float(mu), x)*np.exp(-float(mu))/gamma(x+1)
    # large values of x will cause overflow, so use gaussian instead
    nans = np.argwhere(np.logical_or(np.isnan(result), np.isinf(result)))
    result[nans] = np.exp(-(x[nans]-mu)**2 / (2*np.sqrt(mu)**2))/np.sqrt(2*np.pi*np.sqrt(mu)**2)
    return result


def dblpoisson(x, A1, m0, m1):
    return (1-A1)*poisson_pdf(x, m0) + A1*poisson_pdf(x, m1)


class HistogramAnalysis(AnalysisWithFigure):
    """This class live updates a histogram as data comes in."""
    enable = Bool()
    all_shots_array = Member()
    update_lock = Bool(False)
    list_of_what_to_plot = Str()
    ROI_source = Member()

    def __init__(self, name, experiment, description=''):
        super(HistogramAnalysis, self).__init__(name, experiment, description)

        # point analysis at the roi sum source
        self.ROI_source = getattr(
            self.experiment,
            self.experiment.Config.config.get('CAMERA', 'HistogramROISource')
        )

        self.properties += ['enable', 'list_of_what_to_plot', 'ROI_source']
        self.queueAfterMeasurement = True
        self.measurementDependencies += [self.ROI_source]

    def preIteration(self, iterationResults, experimentResults):
        # reset the histogram data
        self.all_shots_array = None

    def analyzeMeasurement(self, measurementResults, iterationResults,
                           experimentResults):
        if self.enable:
            # every measurement, update a big array of all the ROI sums, then
            # histogram only the requested shot/site
            d = measurementResults[self.ROI_source.meas_analysis_path]
            if self.all_shots_array is None:
                self.all_shots_array = np.array([d])
            else:
                self.all_shots_array = np.append(
                    self.all_shots_array,
                    np.array([d]),
                    axis=0
                )
            self.updateFigure()

    @observe('list_of_what_to_plot')
    def reload(self, change):
        if self.enable:
            self.updateFigure()

    def updateFigure(self):
        if self.draw_fig:
            if not self.update_lock:
                try:
                    self.update_lock = True
                    fig = self.backFigure
                    fig.clf()

                    if ((self.all_shots_array is not None) and
                            (len(self.all_shots_array) > 1)):

                        # parse the list of what to plot from a string to a
                        # list of numbers
                        try:
                            plotlist = eval(self.list_of_what_to_plot)
                        except Exception:
                            msg = 'Couldnt eval plotlist in HistogramAnalysis'
                            logger.exception(msg)
                            return

                        ax = fig.add_subplot(111)
                        shots = [i[0] for i in plotlist]
                        rois = [i[1] for i in plotlist]
                        data = self.all_shots_array[:, shots, rois]
                        bins = int(1.5 * np.rint(np.sqrt(len(data))))
                        # if the number of bins is not great then just do every bin
                        if 2*np.nanmax(data) < bins:
                            bins = np.arange(np.nanmax(data)+1)
                        labels = [
                            '({},{})'.format(i[0], i[1]) for i in plotlist
                        ]
                        ax.hist(
                            data,
                            bins,
                            histtype='step',
                            label=labels
                        )
                        ax.legend()
                    super(HistogramAnalysis, self).updateFigure()
                except Exception:
                    msg = 'Problem in HistogramAnalysis.updateFigure()'
                    logger.exception(msg)
                finally:
                    self.update_lock = False


class HistogramGrid(ROIAnalysis):
    """This class gives a big histogram grid with 0 and 1 atom cutoffs after
    every iteration.
    """
    enable = Bool()
    all_shots_array = Member()
    histogram_results = Member()
    shot = Int()
    pdf_path = Member()
    bins = Member()
    x_min = Float()
    x_max = Float()
    y_max = Float()
    y_min = Float()
    calculate_new_cutoffs = Bool()
    automatically_use_cutoffs = Bool()
    cutoff_shot_mapping = Str()
    cutoffs_from_which_experiment = Str()
    ROI_source = Member()

    def __init__(self, name, experiment, description=''):
        super(HistogramGrid, self).__init__(name, experiment, description)
        # point analysis at the roi sum source
        self.ROI_source = getattr(
            self.experiment,
            self.experiment.Config.config.get('CAMERA', 'HistogramROISource')
        )
        self.properties += [
            'enable', 'shot', 'calculate_new_cutoffs', 'camera',
            'automatically_use_cutoffs', 'cutoff_shot_mapping', 'ROI_source'
        ]
        self.queueAfterMeasurement = True
        self.measurementDependencies += [self.ROI_source]

    def set_rois(self):
        pass

    def fromHDF5(self, hdf):
        super(HistogramGrid, self).fromHDF5(hdf)
        self.find_camera()

    def preExperiment(self, experimentResults):
        # call therading setup code
        super(HistogramGrid, self).preExperiment(experimentResults)

        if self.enable and self.experiment.saveData:
            # create the nearly complete path name to save pdfs to.
            # The iteration and .pdf will be appended.
            pdf_path = os.path.join(self.experiment.path, 'pdf')
            if not os.path.exists(pdf_path):
                os.mkdir(pdf_path)
            self.pdf_path = os.path.join(
                pdf_path,
                '{}_histogram_grid'.format(self.experiment.experimentPath)
            )

    def analyzeIteration(self, iterationResults, experimentResults):
        if self.enable:
            # all_shots_array will be shape (measurements,shots,rois)
            # or (measurements, sub-measurements shots, rois)
            data_path = self.ROI_source.iter_analysis_path
            all_shots_array = iterationResults[data_path].value
            # flatten sub-measurements
            if len(all_shots_array.shape) == 4:
                all_shots_array = all_shots_array.reshape(-1, *all_shots_array.shape[2:])

            # perform histogram calculations and fits on all shots and regions
            self.calculate_all_histograms(all_shots_array)

            if self.automatically_use_cutoffs:
                self.use_cutoffs()

            # save data to hdf5
            # TODO: convert histogram results back to custom numpy dataset
            data_path = 'analysis/histogram_results'
            iterationResults[data_path] = self.convert_histogram_results()

            self.savefig(iterationResults.attrs['iteration'])

            # update the figure to show the histograms for the selected shot
            self.updateFigure()

    def convert_histogram_results(self):
        """Rework new histogram data format so it doesn't break dependent analyses."""
        hist_dtype = np.dtype([
            ('histogram', str(self.bins) + 'i4'),
            ('bin_edges', str(self.bins+1) + 'f8'),
            ('error', 'f8'),
            ('mean1', 'f8'),
            ('mean2', 'f8'),
            ('width1', 'f8'),
            ('width2', 'f8'),
            ('amplitude1', 'f8'),
            ('amplitude2', 'f8'),
            ('cutoff', 'f8'),
            ('loading', 'f8'),
            ('overlap', 'f8'),
            ('poisson', 'bool_')  # length 25 string for specifying the type of fit (new 5/2018)
        ])
        shots = len(self.histogram_results)
        rois = len(self.histogram_results[0])
        results = np.empty((shots, rois), dtype=hist_dtype)
        results.fill(0)
        for s, shot in enumerate(self.histogram_results):
            for r, roi in enumerate(shot):
                a2, m1, m2 = roi['fit_params'][:3]
                a1 = 1.0 - a2
                if roi['method'] == "poisson":
                    w1 = np.sqrt(m1)
                    w2 = np.sqrt(m2)
                    poisson = True
                else:
                    w1, w2 = roi['fit_params'][3:5]
                    poisson = False
                results[s, r] = (
                    roi['hist_y'],
                    roi['hist_x'],
                    np.nan,  # I haven't calculated the fit residuals yet
                    m1,
                    m2,
                    w1,
                    w2,
                    a1,
                    a2,
                    roi['cuts'][0],
                    roi['loading'],
                    roi['overlap'],
                    poisson
                )
        return results

    @observe('shot')
    def refresh(self, change):
        if self.enable:
            self.updateFigure()

    def savefig(self, iteration):
        try:
            # save to PDF
            if self.experiment.saveData:
                try:
                    pe = self.ROI_source.photoelectronScaling.value
                    ex = self.ROI_source.exposureTime.value
                except AttributeError:
                    pe = None
                    ex = None
                for shot in xrange(len(self.histogram_results)):
                    fig = plt.figure(figsize=(23.6, 12.3))
                    dpi = 80
                    fig.set_dpi(dpi)
                    title = '{} iteration {} shot {}'.format(
                        self.experiment.experimentPath,
                        iteration,
                        shot
                    )
                    fig.suptitle(title)
                    self.histogram_grid_plot(
                        fig,
                        shot,
                        photoelectronScaling=pe,
                        exposure_time=ex
                    )
                    plt.savefig(
                        '{}_{}_{}.pdf'.format(
                            self.pdf_path,
                            iteration,
                            shot
                        ),
                        format='pdf',
                        dpi=dpi,
                        transparent=True,
                        bbox_inches='tight',
                        pad_inches=.25,
                        frameon=False
                    )
                    plt.close(fig)
        except Exception:
            logger.exception('Problem in HistogramGrid.savefig()')

    def updateFigure(self):
        if self.draw_fig:
            try:
                fig = self.backFigure
                fig.clf()

                if self.histogram_results is not None:
                    fig.suptitle('shot {}'.format(self.shot))
                    if self.experiment.gaussian_roi.multiply_sums_by_photoelectron_scaling:
                        pe = self.ROI_source.photoelectronScaling.value
                    else:
                        pe = None
                    try:
                        ex = self.ROI_source.exposureTime.value
                    except AttributeError:
                        ex = None
                    self.histogram_grid_plot(
                        fig,
                        self.shot,
                        photoelectronScaling=pe,
                        exposure_time=ex
                    )

                super(HistogramGrid, self).updateFigure()

            except Exception:
                logger.exception('Problem in HistogramGrid.updateFigure()')

    def use_cutoffs(self):
        """Set the cutoffs.

        Because they are stored in a np field, but we need to set them using
        a deferred_call, the whole ROI array is first copied, then updated,
        then written back to the squareROIAnalysis or gaussian_roi.
        """

        experiment_timestamp = datetime.datetime.fromtimestamp(
            self.experiment.timeStarted
        ).strftime('%Y_%m_%d_%H_%M_%S')

        # register the new cutoffs with threshold analysis
        shots = len(self.histogram_results)
        rois = len(self.histogram_results[0])
        cuts = np.zeros((shots, rois), dtype='int')
        for s in range(shots):
            for r in xrange(rois):
                cuts[s, r] = self.histogram_results[s][r]['cuts'][0]
        self.experiment.thresholdROIAnalysis.set_thresholds(cuts, experiment_timestamp, exclude_shot=[1])

    def calculate_all_histograms(self, all_shots_array):
        measurements, shots, rois = all_shots_array.shape

        # Since the number of measurements is the same for each shot and roi,
        # we can compute the number of bins here:
        # choose 1.5*sqrt(N) as the number of bins
        self.bins = int(np.rint(1.5 * np.sqrt(measurements)))
        self.histogram_results = []
        self.y_max = 0
        self.y_min = 1

        # go through each shot and roi and calculate the histograms and
        # gaussian fits
        for shot in xrange(shots):
            self.histogram_results.append([])
            for roi in xrange(rois):
                roidata = all_shots_array[:, shot, roi]

                # get old cutoffs
                cutoff = self.experiment.thresholdROIAnalysis.threshold_array[shot][roi]['1']
                backup_cut = None
                if self.calculate_new_cutoffs:
                    backup_cut = cutoff
                    cutoff = None

                try:
                    # need to fill a place holder in case of error or there will be misalignment
                    result = self.calculate_histogram(roidata, self.bins, cutoff=cutoff, backup_cut=backup_cut)
                except:
                    logger.exception('Probelm fitting histogram for (s,r): ({},{})'.format(shot, roi))
                    result = None
                self.histogram_results[-1].append(result)

        # make a note of which cutoffs were used
        if self.calculate_new_cutoffs:
            exp_time = datetime.datetime.fromtimestamp(
                self.experiment.timeStarted
            )
            fmt = '%Y_%m_%d_%H_%M_%S'
            self.cutoffs_from_which_experiment = exp_time.strftime(fmt)
        else:
            try:
                self.cutoffs_from_which_experiment = self.ROI_source.cutoffs_from_which_experiment
            except AttributeError:
                logger.warning('Unknown cutoff source')

    def gaussian1D(self, x, x0, a, w):
        """returns the height of a gaussian (with mean x0, amplitude, a and
        width w) at the value(s) x
        """
        # normalize
        g = a/(w*np.sqrt(2*np.pi))*np.exp(-0.5*(x-x0)**2/w**2)
        g[np.isnan(g)] = 0  # eliminate bad elements
        return g

    def two_gaussians(self, x, x0, a0, w0, x1, a1, w1):
        return self.gaussian1D(x, x0, a0, w0) + self.gaussian1D(x, x1, a1, w1)

    def calculate_histogram(self, ROI_sums, bins, cutoff=None, backup_cut=None):
        """Takes in ROI_sums which is size (measurements) and contains the
        data to be histogrammed.
        """

        # first numerically take histograms
        result = self.fit_distribution(ROI_sums, hbins=bins)
        # use new or old cutoff?
        # cuts is a list to later enable support for multiatom cuts
        if cutoff is None:
            cut = result['cuts'][0]
            if cut is None or np.isnan(cut):
                # if failed fall back on previous cut
                cutoff = backup_cut
                result['cuts'] = [cutoff]
            else:
                cutoff = cut
        else:
            result['cuts'] = [cutoff]

        # calculate the loading based on the cuts (updated if specified) and
        # the actual atom data
        total = len(ROI_sums)
        # make a boolean array of loading
        atoms = ROI_sums >= cutoff
        # find the loading for each roi
        loaded = np.sum(atoms)
        result['loading'] = loaded/total

        # calculalate the overlap
        result['overlap'] = overlap(result['method'], result['fit_params'], cutoff)
        return result

    def fit_distribution(self, roi_data, hbins=0):
        cut = np.nan
        method = 'poisson'
        # method = 'gaussian'
        max_atoms = 1  # maybe update later for arb. n
        # use a gaussian mixture model to find initial guess at signal distributions
        gmix = mixture.GaussianMixture(n_components=max_atoms+1)
        gmix.fit(np.array([roi_data]).transpose())
        # order the components by the size of the signal
        indicies = np.argsort(gmix.means_.flatten())
        guess = []
        guess_gauss = []
        for n in range(max_atoms+1):
            idx = indicies[n]
            if method == 'poisson':
                guess.append([
                    gmix.weights_[idx],  # amplitudes
                    gmix.means_.flatten()[idx]  # x0s
                ])
            guess_gauss.append([
                gmix.weights_[idx],  # amplitudes
                gmix.means_.flatten()[idx],  # x0s
                np.sqrt(gmix.means_.flatten()[idx])  # sigmas
            ])
        # reorder the parameters, drop the 0 atom amplitude
        guess = np.transpose(guess).flatten()[1:]
        # bin the data, default binning is just range([0,max])
        if hbins < 1:
            hbins = range(int(np.max(roi_data))+1)
        hist, bin_edges = np.histogram(roi_data, bins=hbins, normed=True)

        # define deafult parameters in the case of an exception
        popt = np.array([0, 0, 0])
        pcov = np.array([])
        cut = [np.nan]  # [intersection(*guess)]
        rload = np.nan  # frac(*guess)
        success = False
        if method == 'poisson':
            func = dblpoisson
            try:
                popt, pcov = optimize.curve_fit(
                    dblpoisson,
                    bin_edges[:-1],
                    hist,
                    p0=guess,
                    bounds=[(0, 0, 0), (1, np.inf, np.inf)]
                )
                success = True
            except RuntimeError:
                logger.exception("Unable to fit data")
            except TypeError:
                msg = "There may not be enough data for a fit. ( {} x {} )"
                logger.exception(msg.format(len(bin_edges)-1, len(hist)))
            except ValueError:
                logger.exception('There may be some issue with your guess: `{}`'.format(guess))

        if not success or method == 'gaussian':
            try:
                logger.warning('Poissonian fit failed, trying guassian.')
                popt, pcov = optimize.curve_fit(dblgauss, bin_edges[:-1], hist, p0=guess_gauss)
                success = True
                method = 'gaussian'  # set flag so we know what type
                func = dblpoisson
            except:
                logger.error('Gaussian fit failed.')

        # if none of the fits succeed you can add in support for Marty's old algorithm
        # you could also add a single gaussian fit (no loading) too
        if success:
            cut = [intersection(method, popt)]
            rload = frac(popt)

        return {
            'hist_x': bin_edges,
            'hist_y': hist,
            'max_atoms': max_atoms,
            'fit_params': popt,
            'fit_cov': pcov,
            'cuts': cut,
            'guess': guess,
            'rload': rload,
            'method': method,
            'function': func,
        }

    def analytic_cutoff(self, x1, x2, w1, w2, a1, a2):
        """Find the cutoffs analytically.  See MTL thesis for derivation."""
        return np.where(w1 == w2, self.intersection_of_two_gaussians_of_equal_width(x1, x2, w1, w2, a1, a2), self.intersection_of_two_gaussians(x1, x2, w1, w2, a1, a2))

    def intersection_of_two_gaussians_of_equal_width(self, x1, x2, w1, w2, a1, a2):
        return (- x1**2 + x2**2 + w1**2/2*np.log(a1/a2))/(2*(x2-x1))

    def intersection_of_two_gaussians(self, x1, x2, w1, w2, a1, a2):
        a = w2**2*x1 - w1**2*x2
        # TODO: protect against imaginary root
        b = w1*w2*np.sqrt((x1-x2)**2 + (w2**2 - w1**2)*np.log(a1/a2)/2.0)
        c = w2**2 - w1**2
        return (a+b)/c  # use the positive root, as that will be the one between x1 and x2

    def histogram_patch(self, ax, x, y, color):
        # create vertices for histogram patch
        #   repeat each x twice, and two different y values
        #   repeat each y twice, at two different x values
        #   extra +1 length of verts array allows for CLOSEPOLY code
        verts = np.zeros((2*len(x)+1, 2))
        # verts = np.zeros((2*len(x), 2))
        verts[0:-1:2, 0] = x
        verts[1:-1:2, 0] = x
        verts[1:-2:2, 1] = y
        verts[2:-2:2, 1] = y
        # create codes for histogram patch
        codes = np.ones(2*len(x)+1, int) * mpl.path.Path.LINETO
        codes[0] = mpl.path.Path.MOVETO
        codes[-1] = mpl.path.Path.CLOSEPOLY
        # create patch and add it to axes
        my_path = mpl.path.Path(verts, codes)
        patch = patches.PathPatch(my_path, facecolor=color, edgecolor=color, alpha=0.5)
        ax.add_patch(patch)

    def two_color_histogram(self, ax, data):
        # plot histogram for data below the cutoff
        # It is intentional that len(x1)=len(y1)+1 and len(x2)=len(y2)+1 because y=0 is added at the beginning and
        # end of the below and above segments when plotted in histogram_patch, and we require 1 more x point than y.
        x = data['hist_x']
        cut = data['cuts'][0]
        x1 = x[x < cut]  # take only data below the cutoff
        xc = len(x1)
        x1 = np.append(x1, cut)  # add the cutoff to the end of the 1st patch
        y = data['hist_y']
        y1 = y[:xc]  # take the corresponding histogram counts
        x2 = x[xc:]  # take the remaining values that are above the cutoff
        x2 = np.insert(x2, 0, cut)  # add the cutoff to the beginning of the 2nd patch
        y2 = y[xc-1:]
        if len(x1) > 1 and len(x2) > 1:  # only draw if there is some data (not including cutoff)
            self.histogram_patch(ax, x1, y1, 'b')  # plot the 0 atom peak in blue
            self.histogram_patch(ax, x2, y2, 'r')  # plot the 1 atom peak in red
        else:
            self.simple_histogram(ax, data)

    def simple_histogram(self, ax, data):
        # plot histogram for all data below the cutoff
        x = data['hist_x'][:-1]
        y = data['hist_y']
        ax.step(x, y, where='post')

    def histogram_grid_plot(self, fig, shot, photoelectronScaling=None, exposure_time=None, font=8, log=True):
        """Plot a grid of histograms in the same shape as the ROIs."""
        rows = self.experiment.ROI_rows
        columns = self.experiment.ROI_columns
        # create a grid.  The extra row and column hold the row/column
        # averaged data.
        # width_ratios and height_ratios make those extra cells smaller than
        # the graphs.
        gs1 = GridSpec(
            rows+1,
            columns+1,
            left=0.02,
            bottom=0.05,
            top=.95,
            right=.98,
            wspace=0.2,
            hspace=0.75,
            width_ratios=columns * [1] + [.25],
            height_ratios=rows * [1] + [.25]
        )

        # get the maxes for the shot
        self.x_max = 0
        self.x_min = 0
        self.y_max = 0
        self.y_min = 1
        for i in xrange(rows):
            for j in xrange(columns):
                # choose correct saved data
                n = columns*i+j
                data = self.histogram_results[shot][n]
                # vertical range
                y_max = np.nanmax(data['hist_y']).astype('float')
                # get smallest non-zero histogram bin height
                y_min = np.nanmin(data['hist_y'][data['hist_y'] > 0]).astype('float')
                if y_max > self.y_max:
                    self.y_max = y_max
                if y_min < self.y_min:
                    self.y_min = y_min
                # horizontal range
                x_max = np.nanmax(data['hist_x'][data['hist_y'] > 0]).astype('float')
                # get smallest non-zero histogram bin height
                x_min = np.nanmin(data['hist_x'][data['hist_x'] > 0]).astype('float')
                if x_max > self.x_max:
                    self.x_max = x_max
                if x_min < self.x_min:
                    self.x_min = x_min

        # make histograms for each site
        for i in xrange(rows):
            for j in xrange(columns):
                try:
                    # choose correct saved data
                    n = columns*i+j
                    data = self.histogram_results[shot][n]

                    # create new plot
                    ax = fig.add_subplot(gs1[i, j])
                    self.two_color_histogram(ax, data)

                    local_max = np.nanmax(data['hist_y'])
                    p_max = self.y_max
                    if self.y_max > 10*local_max:
                        p_max = local_max

                    if log:
                        ax.set_yscale('log', nonposy='clip')
                        ax.set_ylim([np.power(10, max([-4, int(np.log10(self.y_min))])), 2*p_max])
                    else:
                        ax.set_yscale('linear', nonposy='clip')
                        ax.set_ylim([0., 1.05*p_max])
                    # ax.set_title(u'{}: {:.0f}\u00B1{:.1f}%'.format(n, data['loading']*100,data['overlap']*100), size=font)
                    ax.text(
                        0.95, 0.85,
                        u'{}: {:.0f}\u00B1{:.1f}%'.format(
                            n,
                            data['loading']*100,
                            data['overlap']*100
                        ),
                        horizontalalignment='right',
                        verticalalignment='center',
                        transform=ax.transAxes,
                        fontsize=font
                    )

                    lab = u'{}\u00B1{:.1f}'
                    mean1, mean2 = data['fit_params'][1:3]
                    if data['method'] == 'gaussian':
                        width1, width2 = data['fit_params'][3:5]
                    if data['method'] == 'poisson':
                        width1 = np.sqrt(mean1)
                        width2 = np.sqrt(mean2)

                    if np.isnan(mean1):
                        lab1 = lab.format('nan', 0)
                    else:
                        lab1 = lab.format(int(mean1), width1)

                    if np.isnan(mean2):
                        lab2 = lab.format('nan', 0)
                    else:
                        lab2 = lab.format(int(mean2), width2)

                    # put x ticks at the center of each gaussian and the cutoff
                    # The one at x_max just holds 'e3' to show that the values
                    # should be multiplied by 1000
                    cut = data['cuts'][0]
                    if not np.any(np.isnan([mean1, cut, mean2])):
                        ax.set_xticks([mean1, cut, mean2])
                        ax.set_xticklabels(
                            [lab1, str(int(cut)), lab2],
                            size=font,
                            rotation=90
                        )
                    # add this to xticklabels to print gaussian widths:
                        # u'\u00B1{:.1f}'.format(data['width1']/1000)
                        # u'\u00B1{:.1f}'.format(data['width2']/1000)
                    # put y ticks at the peak of each gaussian fit
                    # yticks = [0]
                    # yticklabels = ['0']
                    # ytickleft = [True]
                    # ytickright = [False]
                    # if (data['width1'] != 0):
                    #     y1 = data['amplitude1']/(data['width1']*np.sqrt(2*np.pi))
                    #     if np.isnan(y1):
                    #         y1 = 1.0
                    #     yticks += [y1]
                    #     yticklabels += [str(int(np.rint(y1)))]
                    #     ytickleft += [True]
                    #     ytickright += [False]
                    # if (data['width2'] != 0):
                    #     y2 = data['amplitude2']/(data['width2']*np.sqrt(2*np.pi))
                    #     if np.isnan(y2):
                    #         y2 = 1.0
                    #     yticks += [y2]
                    #     yticklabels += [str(int(np.rint(y2)))]
                    #     ytickleft += [False]
                    #     ytickright += [True]
                    # ax.set_yticks(yticks)
                    # ax.set_yticklabels(yticklabels, size=font)
                    # for tick, left, right in zip(ax.yaxis.get_major_ticks(), ytickleft, ytickright):
                    #     tick.label1On = left
                    #     tick.label2On = right
                    #     tick.size = font
                    # plot distributions
                    if data['method'] == 'poisson':
                        # poisson is a discrete function (could change to gamma)
                        x = np.arange(self.x_min, self.x_max+1)
                    else:
                        x = np.linspace(self.x_min, self.x_max, 100)
                    ax.plot(x, data['function'](x, *data['fit_params']), 'k')
                    # plot cutoff line
                    ax.vlines(cut, 0, self.y_max)
                    ax.tick_params(labelsize=font)
                except:
                    msg = 'Could not plot histogram for shot {} roi {}'
                    logger.exception(msg.format(shot, n))

        # make stats for each row
        for i in xrange(rows):
            row_load = np.mean([d['loading'] for d in self.histogram_results[shot][i*columns:(i+1)*columns]])
            ax = fig.add_subplot(gs1[i, columns])
            ax.axis('off')
            ax.text(
                0.5, 0.5,
                'row {}\navg loading\n{:.0f}%'.format(i, 100*row_load),
                horizontalalignment='center',
                verticalalignment='center',
                transform=ax.transAxes,
                fontsize=font
            )

        # make stats for each column
        for i in xrange(columns):
            col_load = np.mean([self.histogram_results[shot][r*columns + i]['loading'] for r in xrange(rows)])
            ax = fig.add_subplot(gs1[rows, i])
            ax.axis('off')
            ax.text(
                0.5, 0.5,
                'column {}\navg loading\n{:.0f}%'.format(i, 100*col_load),
                horizontalalignment='center',
                verticalalignment='center',
                transform=ax.transAxes,
                fontsize=font
            )

        # make stats for whole array
        ax = fig.add_subplot(gs1[rows, columns])
        all_load = np.mean([d['loading'] for i in self.histogram_results[shot]])
        ax.axis('off')
        ax.text(
            0.5, 0.5,
            'array\navg loading\n{:.0f}%'.format(100*all_load),
            horizontalalignment='center',
            verticalalignment='center',
            transform=ax.transAxes,
            fontsize=font
        )

        # add note about photoelectron scaling and exposure time
        if photoelectronScaling is not None:
            fig.text(.05, .985, 'scaling applied = {} photoelectrons/count'.format(photoelectronScaling))
        if exposure_time is not None:
            fig.text(.05, .97, 'exposure_time = {} s'.format(exposure_time))
        fig.text(.05, .955, 'cutoffs from {}'.format(self.cutoffs_from_which_experiment))
        fig.text(.05, .94, 'target # measurements = {}'.format(self.experiment.measurementsPerIteration))
