import logging
import numpy as np
from scipy.special import erf, gammainc, gammaincc, gamma
from scipy import optimize
from sklearn import mixture
from scipy.stats import poisson
import matplotlib as mpl
import matplotlib.pyplot as plt
import matplotlib.patches as patches
from matplotlib.gridspec import GridSpec

logger = logging.getLogger(__name__)


def calculate_histogram(data):
    """Takes in raw data which is size measurements, bins it and generates a new cut

    data: dictionary with keys:
        data: raw signal data
        cutoff: old threshold for 1 atom if not updating, None if updating
        backup_cutoff: old threshold for 1 atom
        bins: the number of bins to use

    returns a dictionary with keys:
        cuts: A list of new thresholds between atom numbers
        loading: The site loading rate
        overlap: the integrated overlap between atom signal histograms
    """
    # first numerically take histograms
    result = fit_distribution(data)
    # cuts is a list to later enable support for multi-atom cuts
    if data['cutoff'] is None:
        cut = result['cuts'][0]
        if cut is None or np.isnan(cut):
            # if failed fall back on previous cut
            cutoff = data['backup_cutoff']
            result['cuts'] = [cutoff]
        else:
            cutoff = cut
    else:
        result['cuts'] = [data['cutoff']]
        cutoff = data['cutoff']

    # calculate the loading based on the cuts (updated if specified) and
    # the actual atom data
    total = len(data['data'])
    # make a boolean array of loading
    atoms = data['data'] >= cutoff
    # find the loading for each roi
    loaded = np.sum(atoms).astype(np.float)
    result['loading'] = loaded / total

    # calculate the overlap
    result['overlap'] = overlap(result['method'], result['fit_params'], cutoff)
    return result


def fit_distribution(data, method='gaussian'):
    """Finds the optimal distribution describing the histogram.

        data: dictionary with keys:
            data: raw signal data
            bins: the number of bins to use
        method: gaussian or poisson for the 0 or 1 atom signal distributions
        Returns a dictionary object with the relevant fit parameters.
    """
    max_atoms = 1  # maybe update later for arb. n
    # use a gaussian mixture model to find initial guess at signal distributions
    gmix = mixture.GaussianMixture(n_components=max_atoms + 1)
    gmix.fit(np.array([data['data']]).transpose())
    # order the components by the size of the signal
    indices = np.argsort(gmix.means_.flatten())
    guess = []
    guess_gauss = []
    for n in range(max_atoms + 1):
        idx = indices[n]
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
    guess_gauss = np.transpose(guess_gauss).flatten()[1:]
    # bin the data, default binning is just range([0,max])
    data['bins'] = int(data['bins'])
    if data['bins'] < 1:
        data['bins'] = range(int(np.max(data['data'])) + 1)
    hist, bin_edges = np.histogram(data['data'], bins=data['bins'], density=True)

    # define default parameters in the case of an exception
    popt = np.array([0, 0, 0])
    pcov = np.array([])
    cut = [np.nan]  # [intersection(*guess)]
    rload = np.nan  # frac(*guess)
    success = False
    if method == 'poisson':
        func = dblpoisson
        try:
            popt, pcov = optimize.curve_fit(
                func,
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
            logger.exception(msg.format(len(bin_edges) - 1, len(hist)))
        except ValueError:
            logger.exception('There may be some issue with your guess: `{}`'.format(guess))

    if not success or method == 'gaussian':
        try:
            if not method == 'gaussian':
                logger.warning('Poissonian fit failed, trying Guassian.')
            guess = guess_gauss
            func = dblgauss
            popt, pcov = optimize.curve_fit(func, bin_edges[:-1], hist, p0=guess)
            success = True
            method = 'gaussian'  # set flag so we know what type

        except Exception as e:
            logger.exception('Gaussian fit failed.')

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
        # intersection over union, see MTL thesis for motivation
        overlap1 = 0.5*(1 + erf((fparams[1]-cutoff)/(fparams[3]*np.sqrt(2))))
        overlap2 = 0.5*(1 + erf((cutoff-fparams[2])/(fparams[4]*np.sqrt(2))))
        return (overlap1*(1-fparams[0]) + overlap2*fparams[0]) / min(fparams[0], 1-fparams[0])
    if ftype == 'poisson':
        # use incomplete regularized gamma functions to get type 1 and 2 error rates
        # do the calculation at p = 0.5, and not the actual loading rate
        # return fparams[0]*gammainc(fparams[2], cutoff) + (1-fparams[0])*gammaincc(fparams[1], cutoff)
        return 0.5*(gammainc(fparams[2], cutoff) + gammaincc(fparams[1], cutoff))


def frac(fparams):
    'Relative Fraction in 1'
    return fparams[0]


def dblgauss(x, A1, m0, m1, s0, s1):
    return (1-A1)*np.exp(-(x-m0)**2 / (2*s0**2))/np.sqrt(2*np.pi*s0**2) + A1*np.exp(-(x-m1)**2 / (2*s1**2))/np.sqrt(2*np.pi*s1**2)


def poisson_pdf(x, mu):
    """Continuous approximation of the Poisson PMF to prevent failures from non-integer bin edges"""
    result = np.power(float(mu), x)*np.exp(-float(mu))/gamma(x+1)
    # large values of x will cause overflow, so use gaussian instead
    nans = np.argwhere(np.logical_or(np.isnan(result), np.isinf(result)))
    result[nans] = np.exp(-(x[nans]-mu)**2 / (2*np.sqrt(mu)**2))/np.sqrt(2*np.pi*np.sqrt(mu)**2)
    return result


def dblpoisson(x, A1, m0, m1):
    return (1-A1)*poisson_pdf(x, m0) + A1*poisson_pdf(x, m1)


def get_hist_domain_range(hist_data):
    """Find the max and min for all ROIs in the shot.

    hist_data: processed histogram data (from calculate_histogram above)
    Returns A tuple (x_max, x_min, y_max, y_min)
    """
    # get the maxes for the shot
    x_max = 0
    x_min = 0
    y_max = 0
    y_min = 1
    for roi in hist_data:
        # vertical range
        y_max = np.nanmax([y_max, np.nanmax(roi['hist_y']).astype('float')])
        # get smallest non-zero histogram bin height
        y_min = np.nanmin([y_min, np.nanmin(roi['hist_y'][roi['hist_y'] > 0]).astype('float')])
        # horizontal range (drop last entry)
        x_max = np.nanmax([x_max, np.nanmax(roi['hist_x'][:-1][roi['hist_y'] > 0]).astype('float')])
        x_min = np.nanmin([x_min, np.nanmin(roi['hist_x'][:-1][roi['hist_y'] > 0]).astype('float')])
    return x_max, x_min, y_max, y_min


def histogram_grid_plot(data, save=True):
    """Plot a grid of histograms in the same shape as the ROIs.

    data: dictionary with keys:
            hist_data: processed histogram data (from calculate_histogram above)
            iteration: current iteration number
            shot: current shot number
            roi_rows: number of roi rows
            roi_columns: number of roi columns
            cutoff_source: text string
            save_path: path to optionally save a pdf
            dpi: dot per inch
            font: font size
            log: use log scale
            scaling: scaling factor to multiply signal by
            exposure_time: image exposure time
            experiment_path: experiment path string
            meas_per_iteration: goal measurements per iteration
    save: [Optional] boolean to save the image to disk, default: True

    Returns a MPL figure
    """
    # get the ranges to use in the shot histograms
    x_max, x_min, y_max, y_min = get_hist_domain_range(data['hist_data'])
    # create the figure
    fig = plt.figure(figsize=(23.6, 12.3))
    fig.set_dpi(data['dpi'])
    fig.suptitle('{experiment_path} iteration {iteration} shot {shot}'.format(**data))
    # create a grid.  The extra row and column hold the row/column averaged data.
    # width_ratios and height_ratios make those extra cells smaller than the graphs.
    gs1 = GridSpec(
        data['roi_rows']+1,
        data['roi_columns']+1,
        left=0.02,
        bottom=0.05,
        top=.95,
        right=.98,
        wspace=0.2,
        hspace=0.75,
        width_ratios=data['roi_columns'] * [1] + [0.25],
        height_ratios=data['roi_rows'] * [1] + [0.25]
    )
    # make histograms for each site
    for i in range(data['roi_rows']):
        for j in range(data['roi_columns']):
            try:
                # choose correct saved data
                n = data['roi_columns']*i+j
                hist_data = data['hist_data'][n]
                # create new plot
                ax = fig.add_subplot(gs1[i, j])
                two_color_histogram(ax, hist_data)

                local_max = np.nanmax(hist_data['hist_y'])
                p_max = y_max
                if y_max > 10*local_max:
                    p_max = local_max

                if data['log']:
                    ax.set_yscale('log', nonposy='clip')
                    ax.set_ylim([np.power(10., max([-4, int(np.log10(y_min))])), 2*p_max])
                else:
                    ax.set_yscale('linear', nonposy='clip')
                    ax.set_ylim([0., 1.05*p_max])
                ax.text(
                    0.95, 0.85,
                    u'{}: {:.0f}\u00B1{:.1f}%'.format(
                        n,
                        hist_data['loading']*100,
                        hist_data['overlap']*100
                    ),
                    horizontalalignment='right',
                    verticalalignment='center',
                    transform=ax.transAxes,
                    fontsize=data['font']
                )
                lab = u'{}\u00B1{:.1f}'
                mean1, mean2 = hist_data['fit_params'][1:3]
                width1, width2 = map(np.sqrt, (mean1, mean2))
                if hist_data['method'] == 'gaussian':
                    width1, width2 = hist_data['fit_params'][3:5]

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
                cut = hist_data['cuts'][0]
                if not np.any(np.isnan([mean1, cut, mean2])):
                    ax.set_xticks([mean1, cut, mean2])
                    ax.set_xticklabels(
                        [lab1, str(int(cut)), lab2],
                        size=data['font'],
                        rotation=90
                    )
                # plot distributions
                if hist_data['method'] == 'poisson':
                    # poisson is a discrete function (could change to gamma)
                    x = np.arange(x_min, x_max+1)
                else:
                    x = np.linspace(x_min, x_max, 100)
                ax.plot(x, hist_data['function'](x, *hist_data['fit_params']), 'k')
                # plot cutoff line
                ax.vlines(cut, 0, y_max)
                ax.tick_params(labelsize=data['font'])
            except:
                msg = 'Could not plot histogram for shot {} roi {}'
                logger.exception(msg.format(data['shot'], n))

    # make stats for each row
    cols = data['roi_columns']
    rows = data['roi_rows']
    for i in range(rows):
        row_load = np.mean([d['loading'] for d in data['hist_data'][i*cols:(i+1)*cols]])
        ax = fig.add_subplot(gs1[i, cols])
        ax.axis('off')
        ax.text(
            0.5, 0.5,
            'row {}\navg loading\n{:.0f}%'.format(i, 100*row_load),
            horizontalalignment='center',
            verticalalignment='center',
            transform=ax.transAxes,
            fontsize=data['font']
        )

    # make stats for each column
    for i in range(cols):
        col_load = np.mean([data['hist_data'][r*cols + i]['loading'] for r in range(rows)])
        ax = fig.add_subplot(gs1[rows, i])
        ax.axis('off')
        ax.text(
            0.5, 0.5,
            'column {}\navg loading\n{:.0f}%'.format(i, 100*col_load),
            horizontalalignment='center',
            verticalalignment='center',
            transform=ax.transAxes,
            fontsize=data['font']
        )

    # make stats for whole array
    ax = fig.add_subplot(gs1[rows, cols])
    all_load = np.mean([d['loading'] for d in data['hist_data']])
    ax.axis('off')
    ax.text(
        0.5, 0.5,
        'array\navg loading\n{:.0f}%'.format(100*all_load),
        horizontalalignment='center',
        verticalalignment='center',
        transform=ax.transAxes,
        fontsize=data['font']
    )

    # add note about photoelectron scaling and exposure time
    if data['scaling'] is not None:
        fig.text(.05, .985, 'scaling applied = {} pe/count'.format(data['scaling']))
    if data['exposure_time'] is not None:
        fig.text(.05, .97, 'exposure_time = {} s'.format(data['exposure_time']))
    fig.text(.05, .955, 'cutoffs from {}'.format(data['cutoff_source']))
    fig.text(.05, .94, 'target # measurements = {}'.format(data['meas_per_iteration']))

    # if save:
    #     plt.savefig(
    #         '{}_{}_{}.pdf'.format(
    #             self.pdf_path,
    #             iteration,
    #             shot
    #         ),
    #         format='pdf',
    #         dpi=dpi,
    #         transparent=True,
    #         bbox_inches='tight',
    #         pad_inches=.25,
    #         frameon=False
    #     )
    #     plt.close(fig)
    return fig


def histogram_patch(ax, x, y, color):
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


def two_color_histogram(ax, data):
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
        histogram_patch(ax, x1, y1, 'b')  # plot the 0 atom peak in blue
        histogram_patch(ax, x2, y2, 'r')  # plot the 1 atom peak in red
    else:
        simple_histogram(ax, data)


def simple_histogram(ax, data):
    # plot histogram for all data below the cutoff
    x = data['hist_x'][:-1]
    y = data['hist_y']
    ax.step(x, y, where='post')
