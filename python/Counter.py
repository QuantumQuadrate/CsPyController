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
logger = logging.getLogger(__name__)

import numpy as np

import traceback
from atom.api import Str, Float, Typed, Member, Bool, Int
from cs_instruments import Instrument
from instrument_property import Prop, ListProp
from analysis import AnalysisWithFigure
from sklearn import mixture
from scipy.optimize import curve_fit
from scipy.optimize import minimize
from scipy.special import erf


import matplotlib.gridspec as gridspec


gs = gridspec.GridSpec(2, 2)
gmix = mixture.GMM(n_components=2)

class Counters(Instrument):
    version = '2015.05.11'
    counters = Typed(ListProp)

    def __init__(self, name, experiment, description=''):
        super(Counters, self).__init__(name, experiment, description)
        # start with a blank list of counters
        self.counters = ListProp('counters', experiment, listElementType=Counter, listElementName='counter')
        self.properties += ['version', 'counters']


class Counter(Prop):
    """Each individual counter has a field for the signal source, clock source, and clock rate (in Hz, used only for
    internal clocking).
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
    update_lock = Bool(False)
    enable = Bool()
    drops = Int(3)
    bins = Int(25)
    shots = Int(2)
    ROIs = Member()

    def __init__(self, name, experiment, description=''):
        super(CounterAnalysis, self).__init__(name, experiment, description)
        self.meas_analysis_path = 'analysis/counter_data'
        self.properties += ['enable', 'drops', 'bins', 'shots']
        self.ROIs = [0]

    def preExperiment(self, experimentResults):
        self.counter_array = None
        self.binned_array = []
        # measurements x bins

    def analyzeMeasurement(self, measurementResults, iterationResults, experimentResults):
        # TODO: update this to pull data from hdf5 file (measurementResults) instead of being set in the
        # labview class
        if self.enable:
            rois = self.counter_array.shape[1]  # get the number of counters
            graph_roi = 0  # counter number to display
            bins_per_shot = self.drops + self.bins
            # counter array is appended with new data every measurement in Labview.py
            num_shots = int(len(self.counter_array[-1, graph_roi])/bins_per_shot)
            # build a mask up of dropped bins and actual counter bins
            ctr_mask = np.array(([False]*self.drops + [True]*self.bins)*num_shots, dtype='bool')
            # calculate new data for each roi
            new_ctr_data = np.array([
                self.counter_array[-1, r, ctr_mask].reshape((num_shots, self.bins)).sum(1)
                for r in range(rois)
            ])
            # binned_array(for graphing) only works with one counter at the moment
            self.binned_array.append(new_ctr_data[graph_roi])
            # write this cycle's data into hdf5 file so that the threshold analysis can read it
            # when multiple counter support is enabled, the ROIs parameter will hold the count
            sum_array = np.transpose(new_ctr_data).reshape((num_shots, rois, 1))
            measurementResults[self.meas_analysis_path] = sum_array
        self.updateFigure()

    def analyzeIteration(self, iterationResults, experimentResults):
        '''Save shot1, shot2 data and reset counter/bin_arrays.'''
        if self.enable:
            iterationResults['shotData'] = np.transpose(self.binned_array)
            self.counter_array = None
            self.binned_array = []
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
                        graph_roi = 0  # counter number to display

                        # make one plot
                        # Single shot
                        ax = fig.add_subplot(221)
                        ax.bar(np.arange(len(self.counter_array[-1, graph_roi, self.drops:])), self.counter_array[-1, graph_roi, self.drops:])
                        ax.set_title('Shot: {}'.format(len(self.counter_array)))

                        # Average over all shots/iteration
                        ax = fig.add_subplot(222)
                        ax.bar(np.arange(len(self.counter_array[-1, graph_roi, self.drops:])), self.counter_array[:, graph_roi, self.drops:].mean(0))
                        ax.set_title('Iteration average')

                        tmp = np.array(self.binned_array)
                        ax = fig.add_subplot(223)
                        ax.plot(tmp, '.')
                        ax.set_title('Binned Data')

                        ax = fig.add_subplot(224)
                        num_shots = tmp.shape[1]
                        for s in range(num_shots):
                            # bins = max + 2 takes care of the case where all entries are 0, which casues an error in the plot
                            ax.hist(tmp[:, s], bins=np.arange(np.max(tmp[:, s])+2), histtype='step')
                        ax.legend(['shot {}'.format(s+1) for s in range(num_shots)], fontsize='small', loc=0)

                        super(CounterAnalysis, self).updateFigure()

                    except:
                        logger.exception('Problem in CounterAnalysis.updateFigure()')
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
            shots = iterationResults['shotData']
            hbins = self.hbins
            if self.hbins < 0:
                hbins = np.arange(np.max(shots)+1)
            for i in range(len(shots)):
                print i, shots[i].shape
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
                    print i
                    print len(est)
                    popt, pcov = curve_fit(self.dblgauss, h[1][1:], h[0], est)
                    # popt=[A0,A1,m0,m1,s0,s1] : Absolute value
                    popt = np.abs(popt)
                    xc = self.intersection(*popt)
                    if np.isnan(xc):
                        print 'Bad Cut on Shot: {}'.format(i)
                        fitout[i] = np.nan, np.nan, np.nan
                        optout[i] = popt*np.nan
                    else:
                        fitout[i] = self.overlap(xc, *popt), self.frac(*popt), xc
                        optout[i] = popt
                except (RuntimeError, RuntimeWarning, TypeError):
                    print 'Bad fit on Shot: {} '.format(i)
                    fitout[i] = np.nan, np.nan, np.nan
                    optout[i] = np.ones(6)*np.nan
            iterationResults['analysis/dblGaussPopt'] = optout
            iterationResults['analysis/dblGaussFit'] = fitout
            print histout
            iterationResults['analysis/histogram'] = np.array(histout, dtype='uint32')
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
                        shots = iterationResults['shotData']
                        popts = iterationResults['analysis/dblGaussPopt']
                        # fits = iterationResults['analysis/dblGaussFit']

                        # make one plot
                        for i in range(len(shots)):
                            ax = fig.add_subplot('21{}'.format(1+i))
                            hbins = self.hbins
                            if self.hbins < 0:
                                hbins = np.arange(np.max(shots[i])+1)
                            h = ax.hist(shots[i], bins=hbins, histtype='step', normed=True)
                            ax.plot(h[1][1:]-.5, self.dblgauss(h[1][1:], *popts[i]))
                            if i == 1:
                                ax.set_yscale('log', nonposy='clip')
                                ax.set_ylim(0.001, 1)

                        super(CounterHistogramAnalysis, self).updateFigure()

                    except:
                        logger.exception('Problem in CounterHistogramAnalysis.updateFigure().')
                    finally:
                        self.update_lock = False
