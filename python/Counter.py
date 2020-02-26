"""Counter.py
Part of the AQuA Cesium Controller software package

author=Martin Lichtman
created=2013-10-19
modified>=2015-05-11

This file holds everything to model a National Instruments DAQmx counter.
It communicated to LabView via the higher up LabView(Instrument) class.
Saving of returned data is handled in the LabView class.
"""


from __future__ import division
__author__ = 'Martin Lichtman'
import logging

import numpy as np

from atom.api import Str, Float, Typed, Member, Bool, Int, List
from cs_instruments import Instrument
from instrument_property import Prop, ListProp
from analysis import AnalysisWithFigure
from sklearn import mixture
from scipy.optimize import curve_fit
from scipy.special import erf
import matplotlib.gridspec as gridspec
import time

logger = logging.getLogger(__name__)

gs = gridspec.GridSpec(2, 2)
gmix = mixture.GaussianMixture(n_components=2)


class Counters(Instrument):
    version = '2015.05.11'
    counters = Typed(ListProp)

    def __init__(self, name, experiment, description=''):
        super(Counters, self).__init__(name, experiment, description)
        # start with a blank list of counters
        self.counters = ListProp('counters', experiment, listElementType=Counter, listElementName='counter')
        self.properties += ['version', 'counters']


class Counter(Prop):
    """Each individual counter has a field for the signal source, clock source, and clock rate (in Hz,
    used only for internal clocking).
    """

    counter_source = Str()
    clock_source = Str()
    clock_rate = Float()

    def __init__(self, name, experiment, description=''):
        super(Counter, self).__init__(name, experiment, description)
        self.properties += ['counter_source', 'clock_source', 'clock_rate']


class CounterAnalysis(AnalysisWithFigure):
    counter_array = Member()
    binned_array = Member()
    meas_analysis_path = Str()
    meas_data_path = Str()
    iter_analysis_path = Str()
    update_lock = Bool(False)
    enable = Bool()
    drops = Int(3)
    bins = Int(25)
    shots = Int(2)
    ROIs = List([0])
    graph_roi = Int(0)

    def __init__(self, name, experiment, description=''):
        super(CounterAnalysis, self).__init__(name, experiment, description)
        self.meas_analysis_path = 'analysis/counter_data'
        self.meas_data_path = 'data/counter/data'
        self.iter_analysis_path = 'shotData'
        self.properties += ['enable', 'drops', 'bins', 'shots', 'graph_roi']

    def preIteration(self, iterationResults, experimentResults):
        self.counter_array = []
        self.binned_array = None

    def format_data(self, array):
        """Formats raw 2D counter data into the required 4D format.

        Formats raw 2D counter data with implicit stucture:
            [   # counter 0
                [ dropped_bins shot_time_series dropped_bins shot_time_series ... ],
                # counter 1
                [ dropped_bins shot_time_series dropped_bins shot_time_series ... ]
            ]
        into the 4D format expected by the subsequent analyses"
        [   # measurements, can have different lengths run-to-run
            [   # shots array, fixed size
                [   # roi list, shot 0
                    [ time_series_roi_0 ],
                    [ time_series_roi_1 ],
                    ...
                ],
                [   # roi list, shot 1
                    [ time_series_roi_0 ],
                    [ time_series_roi_1 ],
                    ...
                ],
                ...
            ],
            ...
        ]
        """
        rois, bins = array.shape[:2]
        bins_per_shot = self.drops + self.bins  # self.bins is data bins per shot
        # calculate the number of shots dynamically
        num_shots = int(bins/(bins_per_shot))
        # calculate the number of measurements contained in the raw data
        # there may be extra shots if we get branching implemented
        num_meas = num_shots//self.shots
        # build a mask for removing valid data
        shot_mask = ([False]*self.drops + [True]*self.bins)
        good_shots = self.shots*num_meas
        # mask for the roi
        ctr_mask = np.array(shot_mask*good_shots + 0*shot_mask*(num_shots-good_shots), dtype='bool')
        # apply mask a reshape partially
        array = array[:, ctr_mask].reshape((rois, num_meas, self.shots, self.bins))
        array = array.swapaxes(0, 1)  # swap rois and measurement axes
        array = array.swapaxes(1, 2)  # swap rois and shots axes
        return array

    def analyzeMeasurement(self, measurementResults, iterationResults, experimentResults):
        if self.enable:

            '''# number of shots is hard coded right now
            bins_per_shot = self.drops + self.bins
            num_shots = int(len(self.counter_array[-1])/bins_per_shot)
            #if self.draw_fig:
            #    print "Number of shots: {}".format(num_shots)
            #    print "Bins per shot: {}".format(bins_per_shot)
            #    print "Length of counter array: {}".format(int(len(self.counter_array[-1])))
            # counter array is appended every measurement so the counter hists can be calculated
            # updated every cycle
            # WARNING: counter_array only works with a single counter right now
            self.binned_array = np.array([
                self.counter_array[:, s*bins_per_shot + self.drops:(s+1)*bins_per_shot].sum(1)
                for s in range(num_shots)
            ])'''

            # MFE 2018/01: this analysis has been generalized such that multiple sub measurements can occur
            # in the same traditional measurement
            array = measurementResults[self.meas_data_path][()]
            try:
                # package data into an array with shape (sub measurements, shots, counters, time series data)
                array = self.format_data(array)
                # flatten the sub_measurements by converting top level to normal list and concatentating
                self.counter_array += list(array)
            except ValueError:
                errmsg = "Error retrieving counter data.  Offending counter data shape: {}"
                logger.exception(errmsg.format(array.shape))
            except Exception as e:
                logger.exception(
                    'Unhandled counter data exception: {}'.format(e))

            # write this cycle's data into hdf5 file so that the threshold analysis can read it
            # when multiple counter support is enabled, the ROIs parameter will hold the count
            # Note the constant 1 is for the roi column parameter, all counters get entered in a single row
            n_meas, n_shots, n_rois, bins = array.shape
            sum_array = array.sum(axis=3).reshape((n_meas, n_shots, n_rois, 1))
            measurementResults[self.meas_analysis_path] = sum_array
            # put the sum data in the expected format for display
            if self.binned_array is None:
                self.binned_array = [sum_array.reshape((n_meas, n_shots, n_rois))]
            else:
                self.binned_array = np.concatenate((
                    self.binned_array,
                    [sum_array.reshape((n_meas, n_shots, n_rois))]
                ))
        self.updateFigure()

    def analyzeIteration(self, iterationResults, experimentResults):
        if self.enable:
            # recalculate binned_array to get rid of cut data
            # iterationResults[self.iter_analysis_path] = self.binned_array
            meas = map(int, iterationResults['measurements'].keys())
            meas.sort()
            path = 'measurements/{}/' + self.meas_analysis_path
            try:
                res = np.array([iterationResults[path.format(m)] for m in meas])
            except KeyError:
                # I was having problem with the file maybe not being ready
                logger.warning("Issue reading hdf5 file. Waiting then repeating.")
                time.sleep(0.1)  # try again in a little
                res = []
                for m in meas:
                    try:
                        res.append(iterationResults[path.format(m)])
                    except KeyError:
                        msg = (
                            "Reading from hdf5 file during measurement `{}`"
                            " failed."
                        ).format(m)
                        logger.exception(msg)
                res = np.array(res)
            total_meas = len(self.binned_array)
            # drop superfluous ROI_columns dimension
            self.binned_array = res.reshape(res.shape[:4])
            logger.info('cut data: {}'.format(total_meas -
                                              len(self.binned_array)))
            iterationResults[self.iter_analysis_path] = self.binned_array
        return

    def updateFigure(self):
        if self.draw_fig:
            if self.enable:
                if not self.update_lock:
                    try:
                        self.update_lock = True

                        # There are two figures in an AnalysisWithFigure.  Draw to the offscreen figure.
                        fig = self.backFigure
                        # Clear figure.
                        fig.clf()

                        # make one plot
                        # Single shot
                        ax = fig.add_subplot(221)

                        # PREVIOUS HYBRID VERSION. COMMENTING OUT IN CASE IT IS NEEDED.
                        # Drop first 3 bins
                        '''bins_per_shot = self.drops + self.bins
                        num_shots = int(len(self.counter_array[-1])/bins_per_shot)
                        dropped_array = self.counter_array[:, self.drops:self.drops+self.bins]
                        for i in range(1,num_shots):
                            dropped_array=np.append(dropped_array,self.counter_array[:, self.drops*(i+1)+self.bins*i:self.drops*i+self.bins*(i+1)],axis=1)
                        ax.bar(np.arange(len(dropped_array[-1])), dropped_array[-1])
                        ax.set_title('Shot: {}'.format(len(self.counter_array)))#Singlt shot

                        ax = fig.add_subplot(222)
                        #ax.bar(np.arange(len(self.counter_array[-1, self.drops:])), self.counter_array[:, self.drops:].mean(0))
                        ax.bar(np.arange(len(dropped_array[-1])), dropped_array.mean(0))
                        ax.set_title('Iteration average') #Average over all shots/iteration

                        ax = fig.add_subplot(223)
                        ax.plot(self.binned_array.transpose(),'.')

                        

                        #ax.legend(['shot 1', 'shot 2'], fontsize='small', loc=0)'''

                        #merge conflict
                        # Average over all shots/iteration
                        ax2 = fig.add_subplot(222)
                        ptr = 0
                        ca = np.array(self.counter_array)
                        for s in range(self.shots):
                            xs = np.arange(ptr, ptr + self.bins)
                            ax.bar(xs, ca[-1, s, self.graph_roi])
                            ax2.bar(xs, ca[:, s, self.graph_roi].mean(0))
                            ptr += max(1.05*self.bins, self.bins+1)
                        ax.set_title('Measurement: {}'.format(len(ca)))
                        ax2.set_title('Iteration average')

                        # time series of sum data
                        ax = fig.add_subplot(223)
                        # histogram of sum data
                        ax2 = fig.add_subplot(224)
                        n_shots = self.binned_array.shape[2]
                        legends = []
                        for roi in range(self.binned_array.shape[3]):
                            for s in range(n_shots):
                                ax.plot(self.binned_array[:, :, s, roi].flatten(), '.')
                                # bins = max + 2 takes care of the case where all entries are 0, which casues
                                # an error in the plot
                                ax2.hist(
                                    self.binned_array[:, :, s, roi].flatten(),
                                    bins=np.arange(np.max(self.binned_array[:, :, s, roi].flatten())+2),
                                    histtype='step'
                                )
                                legends.append("c{}_s{}".format(roi, s))

                        ax.set_title('Binned Data')
                        ax2.legend(legends, fontsize='small', loc=0)
                        super(CounterAnalysis, self).updateFigure()

                    except Exception as e:
                        logger.exception(
                            'Exception in CounterAnalysis.updateFigure():'
                            ' {}'.format(e))
                    finally:
                        self.update_lock = False


class CounterHistogramAnalysis(AnalysisWithFigure):
    '''
    Takes in shot data, generates histograms, fits histograms,
    and then plots various attributes as a function of iteration along with histograms with fit overplotted.
    '''

    # =====================Fit Functions================= #
    def intersection(self, A0,A1,m0,m1,s0,s1):
        return (m1*s0**2-m0*s1**2-np.sqrt(s0**2*s1**2*(m0**2-2*m0*m1+m1**2+2*np.log(A0/A1)*(s1**2-s0**2))))/(s0**2-s1**2)

    def area(self,A0,A1,m0,m1,s0,s1):
        return np.sqrt(np.pi/2)*(A0*s0+A0*s0*erf(m0/np.sqrt(2)/s0)+A1*s1+A1*s1*erf(m1/np.sqrt(2)/s1))

        # Normed Overlap for arbitrary cut point
    def overlap(self,xc,A0,A1,m0,m1,s0,s1):
        err0=A0*np.sqrt(np.pi/2)*s0*(1-erf((xc-m0)/np.sqrt(2)/s0))
        err1=A1*np.sqrt(np.pi/2)*s1*(erf((xc-m1)/np.sqrt(2)/s1)+erf(m1/np.sqrt(2)/s1))
        return (err0+err1)/self.area(A0,A1,m0,m1,s0,s1)

        # Relative Fraction in 1
    def frac(self, A0,A1,m0,m1,s0,s1):
        return 1/(1+A0*s0*(1+erf(m0/np.sqrt(2)/s0))/A1/s1/(1+erf(m1/np.sqrt(2)/s1)))

    def dblgauss(self, x,A0,A1,m0,m1,s0,s1):
        return A0*np.exp(-(x-m0)**2 / (2*s0**2)) +  A1*np.exp(-(x-m1)**2 / (2*s1**2))

    # ==================================================== #

    update_lock = Bool(False)
    enable = Bool(False)
    hbins = Int(30)
    hist1 = None
    hist2 = None

    def __init__(self, name, experiment, description=''):
        super(CounterHistogramAnalysis, self).__init__(name, experiment, description)
        self.properties += ['enable']

    def preExperiment(self, experimentResults):
        # self.hist_rec = np.recarray(1,)
        return

    def analyzeMeasurement(self, measurementResults, iterationResults, experimentResults):
        return

    def analyzeIteration(self, iterationResults, experimentResults):
        if self.enable:
            histout = []  # amplitudes, edges
            # Overlap, fraction, cutoff
            fitout = np.recarray(2, [('overlap', float), ('fraction', float), ('cutoff', float)])
            optout = np.recarray(2, [('A0', float), ('A1', float), ('m0', float), ('m1', float), ('s0', float), ('s1', float)])
            shots = iterationResults['shotData'][()]
            # make shot number the primary axis
            shots = shots.reshape(-1, *shots.shape[2:]).swapaxes(0, 1)
            shots = shots[:, :, 0]  # pick out first roi only
            hbins = self.hbins
            if self.hbins < 0:
                hbins = np.arange(np.max(shots)+1)
            for i in range(shots.shape[0]):
                gmix.fit(np.array([shots[i]]).transpose())
                h = np.histogram(shots[i], bins=hbins, normed=True)
                histout.append((h[1][:-1], h[0]))
                est = [
                    gmix.weights_.max()/10,
                    gmix.weights_.min()/10,
                    gmix.means_.min(),
                    gmix.means_.max(),
                    np.sqrt(gmix.means_.min()),
                    np.sqrt(gmix.means_.max())
                ]
                try:
                    popt, pcov = curve_fit(self.dblgauss, h[1][1:], h[0], est)
                    # popt=[A0,A1,m0,m1,s0,s1] : Absolute value
                    popt = np.abs(popt)
                    xc = self.intersection(*popt)
                    if np.isnan(xc):
                        logger.warning('Bad Cut on Shot: {}'.format(i))
                        fitout[i] = np.nan, np.nan, np.nan
                        optout[i] = popt*np.nan
                    else:
                        fitout[i] = self.overlap(xc, *popt), self.frac(*popt), xc
                        optout[i] = popt
                except (RuntimeError, RuntimeWarning, TypeError):
                    logger.exception('Bad fit on Shot: {} '.format(i))
                    fitout[i] = np.nan, np.nan, np.nan
                    optout[i] = np.ones(6)*np.nan
            iterationResults['analysis/dblGaussPopt'] = optout
            iterationResults['analysis/dblGaussFit'] = fitout
            logger.info("histout: {}".format(histout))
            iterationResults['analysis/histogram'] = np.array(histout,
                                                              dtype='uint32')
            self.updateFigure(iterationResults)
        return

    def updateFigure(self, iterationResults):
        if self.draw_fig:
            if self.enable:
                if not self.update_lock:
                    try:
                        self.update_lock = True

                        # There are two figures in an AnalysisWithFigure.  Draw to the offscreen figure.
                        fig = self.backFigure
                        # Clear figure.
                        fig.clf()
                        shots = iterationResults['shotData'][()]
                        # flatten sub-measurement dimension
                        # make shot number the primary axis (not measurement)
                        shots = shots.reshape(-1, *shots.shape[2:]).swapaxes(0, 1)
                        roi = 0
                        shots = shots[:, :, roi]  # pick out first roi only
                        popts = iterationResults['analysis/dblGaussPopt']
                        # fits = iterationResults['analysis/dblGaussFit']

                        # make one plot
                        for i in range(len(shots)):
                            ax = fig.add_subplot('{}1{}'.format(len(shots), 1+i))
                            hbins = self.hbins
                            if self.hbins < 0:
                                # use explicit bins
                                hbins = np.arange(np.max(shots[i, :])+1)
                            h = ax.hist(shots[i], bins=hbins, histtype='step', normed=True)
                            ax.plot(h[1][1:]-.5, self.dblgauss(h[1][1:], *popts[i]))
                            if i == 1:
                                ax.set_yscale('log', nonposy='clip')
                                ax.set_ylim(10**int(-np.log10(len(shots[i]))-1), 1)
                            else:
                                ax.set_ylim(0, 1.05*np.max(h[0]))

                        super(CounterHistogramAnalysis, self).updateFigure()

                    except Exception as e:
                        logger.exception(
                            'Problem in CounterHistogramAnalysis.updateFigure()'
                            ' {}'.format(e))
                    finally:
                        self.update_lock = False
