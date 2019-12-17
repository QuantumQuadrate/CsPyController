from numpy import *
import scipy.optimize as opt
from scipy.special import erf


def load_data(h5file, inst, iteration, measurements, shots, roi=None):
    """
    Loads data from h5file into the array hist_dat
    :param h5file: reference to an hdf5 data file
    :param inst: instrument sourcing of data, (so far only supports 'Hamamatsu', will implement 'Counter' support)
    :param iteration: int, current iteration number
    :param measurements: int, number of measurements per iteration
    :param shots: number of shots per measurement
    :param roi: nX2 numpy array. format roi = array([range(top,bottom),range(left,right)])
    :return: hist_dat: numpy array of histogram data. hist_dat.shape() = (measurements,shots)
    """
    if roi is None:
        roi = array([range(4, 7), range(3, 6)])
    if inst == 'Hamamatsu':
        # roi = array([range(4, 7), range(3, 6)])
        imdat = zeros((measurements, shots, len(roi[0, :]), len(roi[1, :])), dtype=int)  # image data
        for ms in range(measurements):
            for sht in range(shots):
                datpath = '/iterations/{}/measurements/{}/data/Hamamatsu/shots/{}'.format(iteration, ms, sht)
                try:
                    im = array(h5file[(datpath)])
                    imdat[ms, sht, :, :] = im[roi[0], :][:, roi[1]]
                except KeyError as er:
                    print("Error while loading data : {}".format(er))
                    print(datpath)
        hist_dat = imdat.sum(2).sum(2)
    else:
        hist_dat = None
    return hist_dat


def loading(hist_dat, cut, shot = 0):
    """
    Returns rate of loading more than 0 atoms in given shot, based on the cut provided, and statistical uncertainty in
    that value
    :param hist_dat: numpy array of counting data
    :param cut: int, threshold above which an event is considered to be >0 atoms loaded into the trap
    :param shot: int, on which shot to perform this analysis

    :return: r_load: float, ratio of events in which >0 atoms were loaded to number of measurements
    :return: r_load_err: float, statistical uncertainty in r_load
    """
    r_load = (hist_dat[:, shot] >= cut).sum()/(len(hist_dat[:, 0])*1.0)
    r_load_err = sqrt(r_load*(1-r_load)/len(hist_dat[:, shot]))
    return r_load, r_load_err


def j_ret(hist_dat,cut):
    """
    Computes retention rate of hist_dat based on the cut provided
    :param hist_dat: numpy array of counting data
    :param cut: int, counting threshold above which an event is considered to be >0 atoms loaded into the trap

    :return: retention: float, fraction of loaded atoms retained between shots 0 and 1
    """
    retention = (1.0 * (hist_dat[:, 0] >= cut) * (hist_dat[:, 1] > cut)).sum() / (hist_dat[:, 0] >= cut).sum()
    return retention


def ret(hist_dat, cut, cut_err=0, ovlp=0):
    """
    Computes retention rate of hist_dat based on the cut provided
    :param hist_dat: numpy array of counting data
    :param cut: int, counting threshold above which an event is considered to be >0 atoms loaded into the trap
    :param cut_err: int, uncertainty in cut
    :param ovlp: normalized overlap between 0 and 1 atom gaussian curves
    :return: retention: float, fraction of loaded atoms retained in between readout shots 0 and 1
    :return: retention_error: float, statistical uncertainty in retention
    """
    r_load = (hist_dat[:, 0] >= cut).sum()/(len(hist_dat[:, 0])*1.0)
    # print r_load
    if r_load > 0:  # Make sure retention number doesn't blow up for no-loading events
        # compute retention rate
        retention = j_ret(hist_dat, cut)
        # compute statistical uncertainty in "retention" due to shot noise
        shot_error = sqrt(retention*(1-retention)/(hist_dat[:, 0] >= cut).sum())
        # compute statistical uncertainty in "retention" due to uncertainty in the cut
        if cut_err > 0 :
            ct_error_plus = abs(j_ret(hist_dat, cut+cut_err)-retention)
            ct_error_minus = abs(j_ret(hist_dat, cut-cut_err)-retention)
            ct_err = mean([ct_error_plus, ct_error_minus])
        else:
            ct_err = 0
        retention_error = sqrt(shot_error**2+ct_err**2+ovlp**2)
    else:
        retention = 0
        retention_error = 0
    return retention, retention_error


def fit_hist(hist_dat, guess=None):
    """
    fits hist_dat histogram to a function with two gaussian curves
    :param hist_dat: numpy array of counting data
    :param guess: initial guess for final fitted parameters, of form [x0g, x1g, std0g, std1g, a0g, a1g]
    :return: popt: len()=6 array of fitted parameters
    :return: perr: len()=6 array of uncertainty in each of the corresponding parameters
    """
    func = dbl_gauss

    bns = range(min(hist_dat), max(hist_dat), (max(hist_dat)-min(hist_dat))/30)
    h = histogram(hist_dat, bins=bns)
    xdat = array(h[1][1:], dtype=float)
    ydat = array(h[0], dtype=float)

    if guess is None:
        x0g = 21000
        x1g = 28000
        std0g = 1000.0
        std1g = 2000.0
        a0g = 6.0e1
        a1g = 6.0e1
        guess = [x0g, x1g, std0g, std1g, a0g, a1g]

    popt, pcov = opt.curve_fit(f=func, xdata=xdat, ydata=ydat, p0=guess)
    perr = sqrt(diag(pcov))

    # if the means of the two fits are switched, the overlap error will blow up. Here we make sure that won't happen
    if popt[1] < popt[0]:
        pcop = copy(popt)
        per_cop = copy(perr)
        popt[[0, 2, 4]] = pcop[[1, 3, 5]]
        popt[[1, 3, 5]] = pcop[[0, 2, 4]]
        perr[[0, 2, 4]] = per_cop[[1, 3, 5]]
        perr[[1, 3, 5]] = per_cop[[0, 2, 4]]
    return popt, perr


def dbl_gauss(x, x0, x1, std0, std1, a0, a1):
    """
    Returns value of a double gaussian function at x.
    :param x: Position to sample function
    :param x0: mean of 0th gaussian
    :param x1: mean of 1st gaussian
    :param std0: standard deviation of 0th gaussian
    :param std1: standard deviation of 1st gaussian
    :param a0: amplitude of 0th gaussian
    :param a1: amplitude of 1st gaussian
    :return: function's value at x
    """
    xp0 = x-x0
    xp1 = x-x1
    g0 = a0*exp(-0.5*(xp0/std0)**2)
    g1 = a1*exp(-0.5*(xp1/std1)**2)
    return g0+g1


def get_overlap_error(xc, x0, x1, s0, s1):
    """
    Returns error rate due to overlap of both normal distributions
    :param xc: float, int between x0 and x1
    :param x0: mean of 0th normal distribution
    :param x1: mean of 1st normal distribution
    :param s0: standard deviation of 0th normal distribution
    :param s1: standard deviation of 1st normal distribution
    """
    return 0.5*(1-erf((xc-x0)/(sqrt(2)*s0)) + 1-erf((x1-xc)/(sqrt(2)*s1)))


def get_cut(x0, x1, s0, s1):
    """
    Returns optimal cut between two normal distribution
    :param x0: mean of 0th normal distribution
    :param x1: mean of 1st normal distribution
    :param s0: standard deviation of 0th normal distribution
    :param s1: standard deviation of 1st normal distribution
    :return: xc: optimal cut
    """
    rad = (x0-x1)**2+2*(s1**2-s0**2)*log(s1/s0)
    num = x1*s0**2-x0*s1**2-s0*s1*sqrt(rad)
    denum_inv = 1/(s0**2-s1**2)
    xc = num*denum_inv

    return xc


def get_cut_err(x0, x1, s0, s1, dx0, dx1, ds0, ds1):
    """
    Returns uncertainty in optimal cut between two normal distributions
    :param x0: mean of 0th normal distribution
    :param x1: mean of 1st normal distribution
    :param s0: standard deviation of 0th normal distribution
    :param s1: standard deviation of 1st normal distribution
    :param dx0: uncertainty in mean of 0th normal distribution
    :param dx1: uncertainty in mean of 1st normal distribution
    :param ds0: uncertainty in standard deviation of 0th normal distribution
    :param ds1: uncertainty in standard deviation of 1st normal distribution
    """
    rad = (x0-x1)**2+2*(s1**2-s0**2)*log(s1/s0)
    num = x1*s0**2-x0*s1**2-s0*s1*sqrt(rad)
    rd_inv = 1/sqrt(rad)
    denum_inv = 1/(s0**2-s1**2)
    xc = num*denum_inv

    px0 = -denum_inv*(s1**2+s0*s1*rd_inv*(x0-x1))
    px1 = denum_inv*(s0**2+s0*s1*rd_inv*(x0-x1))
    ps0 = denum_inv*s0*(2*(x1-xc)-s1*sqrt(rad)/s0+s1*(s1**2/s0+s0*(2*log(s1/s0)+1)))/sqrt(rad)
    ps1 = denum_inv*s1*(2*(xc-x0)-s0*sqrt(rad)/s1+s0*(s0**2/s1-s1*(2*log(s1/s0)+1)))/sqrt(rad)

    return dx0*px0+dx1*px1+ds0*ps0+ds1*ps1