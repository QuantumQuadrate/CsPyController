import logging
import numpy as np
from scipy.special import erf, gammainc, gammaincc, gamma
from scipy import optimize
from sklearn import mixture
from scipy.stats import poisson

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