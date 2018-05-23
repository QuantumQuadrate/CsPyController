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
        self.binned_array = None
        # measurements x bins

    def analyzeMeasurement(self, measurementResults, iterationResults, experimentResults):
        # TODO: update this to pull data from hdf5 file (measurementResults) instead of being set in the
        # labview class
        if self.enable:
            # number of shots is hard coded right now
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
            ])
            # write this cycle's data into hdf5 file so that the threshold analysis can read it
            # when multiple counter support is enabled, the ROIs parameter will hold the count
            sum_array = self.binned_array[:, -1].reshape((num_shots, 1, 1))
            measurementResults[self.meas_analysis_path] = sum_array
        self.updateFigure()

    def analyzeIteration(self, iterationResults, experimentResults):
        '''Save shot1, shot2 data and reset counter/bin_arrays.'''
        if self.enable:
            iterationResults['shotData'] = self.binned_array
            self.counter_array = None
            self.binned_array = None
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

                        #make one plot
                        ax = fig.add_subplot(221)
                        # Drop first 3 bins
                        bins_per_shot = self.drops + self.bins
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

                        

                        #ax.legend(['shot 1', 'shot 2'], fontsize='small', loc=0)
                        ax.set_title('Binned Data')

                        ax = fig.add_subplot(224)
                        ax.hist(self.binned_array[0], bins=30, histtype='step')
                        ax.hist(self.binned_array[1], bins=30, histtype='step')


                        super(CounterAnalysis, self).updateFigure()

                    except Exception as e:
                        logger.warning('Problem in RetentionGraph.updateFigure()\n{}\n{}\n'.format(e, traceback.format_exc()))
                    finally:
                        self.update_lock = False

class CounterHistogramAnalysis(AnalysisWithFigure):
    '''
    Takes in shot data, generates histograms, fits histograms,
    and then plots various attributes as a function of iteration along with histograms with fit overplotted.
    '''

            #=====================Fit Functions=================#
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


            #====================================================#


    update_lock = Bool(False)
    enable = Bool(False)
    hbins = Int(30)
    hist1 = None
    hist2 = None



    def __init__(self, name, experiment, description=''):
        super(CounterHistogramAnalysis, self).__init__(name, experiment, description)
        self.properties += ['enable']


    def preExperiment(self, experimentResults):
        #self.hist_rec = np.recarray(1,)
        return

    def analyzeMeasurement(self, measurementResults, iterationResults, experimentResults):
        return

    def analyzeIteration(self, iterationResults, experimentResults):
        if self.enable:
            histout = [] # amplitudes, edges
            fitout = np.recarray(2,[('overlap',float),('fraction',float),('cutoff',float)]) # Overlap, fraction, cutoff
            optout = np.recarray(2,[('A0',float),('A1',float),('m0',float),('m1',float),('s0',float),('s1',float)])
            shots = iterationResults['shotData']
            for i in range(len(shots)):
                print i,shots[i].shape
                gmix.fit(np.array([shots[i]]).transpose())
                h = np.histogram(shots[i], bins = self.hbins, normed = True)
                histout.append((h[1][:-1],h[0]))
                est=[gmix.weights_.max()/10,gmix.weights_.min()/10,gmix.means_.min(),gmix.means_.max(),np.sqrt(gmix.means_.min()),np.sqrt(gmix.means_.max())]
                try:
                    print i
                    print len(est)
                    popt,pcov = curve_fit(self.dblgauss,h[1][1:],h[0],est)
                    #popt=[A0,A1,m0,m1,s0,s1] : Absolute value
                    popt=np.abs(popt)
                    xc=self.intersection(*popt)
                    if np.isnan(xc):
                        print 'Bad Cut on Shot: {}'.format(i)
                        fitout[i]=np.nan,np.nan,np.nan
                        optout[i]=popt*np.nan
                    else:
                        fitout[i]=self.overlap(xc,*popt),self.frac(*popt),xc
                        optout[i]=popt
                except (RuntimeError,RuntimeWarning):
                    print 'Bad fit on Shot: {} '.format(i)
                    fitout[i]=np.nan,np.nan,np.nan
                    optout[i]=np.ones(6)*np.nan
            iterationResults['analysis/dblGaussPopt'] = optout
            iterationResults['analysis/dblGaussFit'] = fitout
            iterationResults['analysis/histogram'] = histout
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
                        fits = iterationResults['analysis/dblGaussFit']

                        #make one plot
                        for i in range(len(shots)):
                            ax = fig.add_subplot('21{}'.format(1+i))
                            ax.hist(shots[i], bins=self.hbins, histtype='step', normed=True)
                            h = np.histogram(shots[i],normed=True,bins=self.hbins)
                            ax.plot(h[1][1:]-.5,self.dblgauss(h[1][1:],*popts[i]))

                        super(CounterHistogramAnalysis, self).updateFigure()

                    except Exception as e:
                        logger.warning('Problem in RetentionGraph.updateFigure()\n{}\n{}\n'.format(e, traceback.format_exc()))
                    finally:
                        self.update_lock = False
