import datetime
import numpy as np
import logging
import os
# MPL plotting
import matplotlib as mpl
import matplotlib.pyplot as plt
from matplotlib.gridspec import GridSpec
import matplotlib.patches as patches
from scipy.special import erf

from atom.api import Bool, Member, Str, observe, Int, Float

from analysis import AnalysisWithFigure, ROIAnalysis

logger = logging.getLogger(__name__)
mpl.use('PDF')


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
                        data = self.all_shots_array[:, shots, 0, rois]
                        bins = int(1.2 * np.rint(np.sqrt(len(data))))
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
            data_path = 'analysis/histogram_results'
            iterationResults[data_path] = self.histogram_results

            self.savefig(iterationResults.attrs['iteration'])

            # update the figure to show the histograms for the selected shot
            self.updateFigure()

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
                for shot in xrange(self.histogram_results.shape[0]):
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
        self.experiment.thresholdROIAnalysis.set_thresholds(
            self.histogram_results['cutoff'],
            experiment_timestamp
        )

    def calculate_all_histograms(self, all_shots_array):
        measurements, shots, rois = all_shots_array.shape

        # Since the number of measurements is the same for each shot and roi,
        # we can compute the number of bins here:
        # choose 1.5*sqrt(N) as the number of bins
        self.bins = int(np.rint(1.5 * np.sqrt(measurements)))

        # create arrays to hold results
        my_dtype = np.dtype([
            ('histogram', str(self.bins) + 'i4'),
            ('bin_edges', str(self.bins + 1) + 'f8'),
            ('error', 'f8'),
            ('mean1', 'f8'),
            ('mean2', 'f8'),
            ('width1', 'f8'),
            ('width2', 'f8'),
            ('amplitude1', 'f8'),
            ('amplitude2', 'f8'),
            ('cutoff', 'f8'),
            ('loading', 'f8'),
            ('overlap', 'f8')
        ])
        self.histogram_results = np.empty((shots, rois), dtype=my_dtype)
        # self.histogram_results.fill(np.nan)
        # MFE 01/2018: Not sure why it is necessary to
        self.histogram_results.fill(0)

        # go through each shot and roi and calculate the histograms and
        # gaussian fits
        for shot in xrange(shots):
            for roi in xrange(rois):
                roidata = all_shots_array[:, shot, roi]

                # get old cutoffs
                if self.calculate_new_cutoffs:
                    cutoff = None
                else:
                    cutoff = self.experiment.thresholdROIAnalysis.threshold_array[shot][roi]['1']
                self.histogram_results[shot, roi] = self.calculate_histogram(
                    roidata,
                    self.bins,
                    cutoff
                )
                # these all have the same number of measurements, so they will
                # all have the same size

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

        # find the min and max
        self.x_min = np.nanmin(all_shots_array).astype('float')
        self.x_max = np.nanmax(all_shots_array).astype('float')
        self.y_max = np.nanmax(self.histogram_results['histogram']).astype('float')
        # get smallest non-zero histogram bin height
        self.y_min = np.nanmin(self.histogram_results['histogram'][self.histogram_results['histogram']>0]).astype('float')

        # TODO: do cutoff finding, analytical overlap and loading in a
        # vectorized fashion

    def gaussian1D(self, x, x0, a, w):
        """returns the height of a gaussian (with mean x0, amplitude, a and
        width w) at the value(s) x
        """
        # normalize
        g = a/(w*np.sqrt(2*np.pi))*np.exp(-0.5*(x-x0)**2/w**2)
        g[np.isnan(g)] = 0  # eliminate bad elements
        return g

    def possion1D(self, x, x0, a, w):
        """returns the height of a poisson distribution (with mean x0, amplitude, a and
        width w) at the value(s) x
        """
        # normalize
        g = a/(w*np.sqrt(2*np.pi))*np.exp(-0.5*(x-x0)**2/w**2)
        g[np.isnan(g)] = 0  # eliminate bad elements
        return g

    def two_gaussians(self, x, x0, a0, w0, x1, a1, w1):
        return self.gaussian1D(x, x0, a0, w0) + self.gaussian1D(x, x1, a1, w1)

    def calculate_histogram(self, ROI_sums, bins, cutoff=None):
        """Takes in ROI_sums which is size (measurements) and contains the
        data to be histogrammed.
        """

        # first numerically take histograms
        hist, bin_edges = np.histogram(ROI_sums, bins=bins)
        bin_size = (bin_edges[1:]-bin_edges[:-1])
        y = hist

        if cutoff is None:  # find a new cutoff
            # take center of each bin as test points (same in number as y)
            x = (bin_edges[1:] + bin_edges[:-1]) / 2
            best_error = float('inf')

            # TODO: instead of bin edges, use unbinned data for gaussian fits,
            # and consider all datapoints as possible cutoffs

            # use the bin edges as possible cutoff locations
            # now go through each possible cutoff location and fit a gaussian
            # above and below
            # see which cutoff is the best fit

            # leave off 0th and last bin edge to prevent divide by zero on one
            # of the gaussian sums
            for j in xrange(1, bins - 1):

                # fit a gaussian below the cutoff
                mean1 = np.sum(x[:j] * y[:j])/np.sum(y[:j])
                # an array of distances from the mean
                r1 = np.sqrt((x[:j]-mean1)**2)
                # the standard deviation
                width1 = np.sqrt(np.abs(
                    np.sum((r1**2)*y[:j])/np.sum(y[:j])
                ))
                if width1 == 0:
                    width1 = 1.0
                # area under gaussian is 1, so scale by total volume (i.e. the
                # sum of y)
                amplitude1 = np.sum(y[:j]*bin_size[:j])
                g1 = self.gaussian1D(x, mean1, amplitude1, width1)

                # fit a gaussian above the cutoff
                mean2 = np.sum(x[j:]*y[j:])/np.sum(y[j:])
                # an array of distances from the mean
                r2 = np.sqrt((x[j:]-mean2)**2)
                # the standard deviation
                width2 = np.sqrt(np.abs(
                    np.sum((r2**2) * y[j:]) / np.sum(y[j:])
                ))
                if width2 == 0:
                    width2 = 1.0
                # area under gaussian is 1, so scale by total volume (i.e. the
                # sum of y * step size)
                amplitude2 = np.sum(y[j:]*bin_size[j:])
                g2 = self.gaussian1D(x, mean2, amplitude2, width2)

                # find the total error
                error = np.sum(np.abs(y-g1-g2))
                if error < best_error:
                    best_error = error
                    best_mean1 = mean1
                    best_mean2 = mean2
                    best_width1 = width1
                    best_width2 = width2
                    best_amplitude1 = amplitude1
                    best_amplitude2 = amplitude2

            # find a better cutoff
            # the cutoff found is for the digital data, not necessarily the
            # best in terms of the gaussian fits
            cutoff = self.analytic_cutoff(
                best_mean1,
                best_mean2,
                best_width1,
                best_width2,
                best_amplitude1,
                best_amplitude2
            )

        else:  # use the existing cutoff, unbinned data
            x = ROI_sums
            below = x[x < cutoff]
            above = x[x >= cutoff]

            mean1 = np.mean(below)
            mean2 = np.mean(above)
            width1 = np.std(below)
            width2 = np.std(above)

            bin_size = np.mean(bin_size)
            amplitude1 = len(below) * np.mean(bin_size)
            amplitude2 = len(above) * np.mean(bin_size)

            # find the fit error to the histogram
            # take center of each bin as test points (same in number as y)
            x = (bin_edges[1:]+bin_edges[:-1])/2
            g1 = self.gaussian1D(x, mean1, amplitude1, width1)
            g2 = self.gaussian1D(x, mean2, amplitude2, width2)
            error = np.sum(np.abs(y-g1-g2))

            # we only have one cutoff test here, so use it
            best_error = error
            best_mean1 = mean1
            best_mean2 = mean2
            best_width1 = width1
            best_width2 = width2
            best_amplitude1 = amplitude1
            best_amplitude2 = amplitude2

        # calculate the loading based on the cuts (updated if specified) and
        # the actual atom data
        total = len(ROI_sums.shape)
        # make a boolean array of loading
        atoms = ROI_sums >= cutoff
        # find the loading for each roi
        loaded = np.sum(atoms)

        loading = loaded/total

        # calculalate the overlap
        # use the cumulative normal distribution function to get the overlap
        # analytically
        # see MTL thesis for derivation
        overlap1 = 0.5*(1 + erf((best_mean1-cutoff)/(best_width1*np.sqrt(2))))
        overlap2 = 0.5*(1 + erf((cutoff-best_mean2)/(best_width2*np.sqrt(2))))
        overlap = (overlap1*best_amplitude1 + overlap2*best_amplitude2) / min(best_amplitude1, best_amplitude2)
        return hist, bin_edges, best_error, best_mean1, best_mean2, best_width1, best_width2, best_amplitude1, best_amplitude2, cutoff, loading, overlap

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
        x = data['bin_edges']
        x1 = x[x < data['cutoff']]  # take only data below the cutoff
        xc = len(x1)
        x1 = np.append(x1, data['cutoff'])  # add the cutoff to the end of the 1st patch
        y = data['histogram']
        y1 = y[:xc]  # take the corresponding histogram counts
        x2 = x[xc:]  # take the remaining values that are above the cutoff
        x2 = np.insert(x2, 0, data['cutoff'])  # add the cutoff to the beginning of the 2nd patch
        y2 = y[xc-1:]

        if len(x1) > 1:  # only draw if there is some data (not including cutoff)
            self.histogram_patch(ax, x1, y1, 'b')  # plot the 0 atom peak in blue
        if len(x2) > 1:  # only draw if there is some data (not including cutoff)
            self.histogram_patch(ax, x2, y2, 'r')  # plot the 1 atom peak in red

    def histogram_grid_plot(self, fig, shot, photoelectronScaling=None, exposure_time=None, font=8):
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

        # make histograms for each site
        for i in xrange(rows):
            for j in xrange(columns):
                try:
                    # choose correct saved data
                    n = columns*i+j
                    data = self.histogram_results[shot, n]

                    # create new plot
                    ax = fig.add_subplot(gs1[i, j])
                    self.two_color_histogram(ax, data)

                    ax.set_yscale('log', nonposy='clip')
                    # ax.set_ylim([np.power(10, max([-4, int(np.log10(self.y_min))])), 1.05*self.y_max])
                    ax.set_ylim([0.5, 1.05*self.y_max])
                    # ax.set_title(u'{}: {:.0f}\u00B1{:.1f}%'.format(n, data['loading']*100,data['overlap']*100), size=font)
                    ax.text(
                        0.95,
                        0.85,
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
                    if np.isnan(data['mean1']):
                        lab1 = lab.format('nan', 0)
                    else:
                        lab1 = lab.format(
                            int(data['mean1']),
                            data['width1']
                        )

                    if np.isnan(data['mean2']):
                        lab2 = lab.format('nan', 0)
                    else:
                        lab2 = lab.format(
                            int(data['mean2']),
                            data['width2']
                        )
                    # put x ticks at the center of each gaussian and the cutoff
                    # The one at x_max just holds 'e3' to show that the values
                    # should be multiplied by 1000
                    if not np.any(np.isnan([data['mean1'], data['cutoff'], data['mean2']])):
                        ax.set_xticks([
                            data['mean1'],
                            data['cutoff'],
                            data['mean2']
                        ])
                        ax.set_xticklabels([
                            lab1, str(int(data['cutoff'])), lab2],
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
                    # plot gaussians
                    x = np.linspace(self.x_min, self.x_max, 100)
                    y1 = self.gaussian1D(x, data['mean1'], data['amplitude1'], data['width1'])
                    y2 = self.gaussian1D(x, data['mean2'], data['amplitude2'], data['width2'])
                    ax.plot(x, y1, 'k', x, y2, 'k')
                    # plot cutoff line
                    ax.vlines(data['cutoff'], 0, self.y_max)
                    ax.tick_params(labelsize=font)
                except:
                    msg = 'Could not plot histogram for shot {} roi {}'
                    logger.exception(msg.format(shot, n))

        # make stats for each row
        for i in xrange(rows):
            ax = fig.add_subplot(gs1[i, columns])
            ax.axis('off')
            ax.text(0.5, 0.5,
                'row {}\navg loading\n{:.0f}%'.format(i, 100*np.mean(self.histogram_results['loading'][shot, i*columns:(i+1)*columns])),
                horizontalalignment='center',
                verticalalignment='center',
                transform=ax.transAxes,
                fontsize=font)

        # make stats for each column
        for i in xrange(columns):
            ax = fig.add_subplot(gs1[rows, i])
            ax.axis('off')
            ax.text(0.5, 0.5,
                'column {}\navg loading\n{:.0f}%'.format(i, 100*np.mean(self.histogram_results['loading'][shot, i:i+(rows-1)*columns:columns])),
                horizontalalignment='center',
                verticalalignment='center',
                transform=ax.transAxes,
                fontsize=font)

        # make stats for whole array
        ax = fig.add_subplot(gs1[rows, columns])
        ax.axis('off')
        ax.text(0.5, 0.5,
            'array\navg loading\n{:.0f}%'.format(100*np.mean(self.histogram_results['loading'][shot])),
            horizontalalignment='center',
            verticalalignment='center',
            transform=ax.transAxes,
            fontsize=font)

        # add note about photoelectron scaling and exposure time
        if photoelectronScaling is not None:
            fig.text(.05, .985,'scaling applied = {} photoelectrons/count'.format(photoelectronScaling))
        if exposure_time is not None:
            fig.text(.05, .97,'exposure_time = {} s'.format(exposure_time))
        fig.text(.05, .955,'cutoffs from {}'.format(self.cutoffs_from_which_experiment))
        fig.text(.05, .94, 'target # measurements = {}'.format(self.experiment.measurementsPerIteration))
