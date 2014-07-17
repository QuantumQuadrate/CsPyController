from __future__ import division
__author__ = 'Martin Lichtman'
import logging
logger = logging.getLogger(__name__)

from cs_errors import PauseError

from atom.api import Bool, Typed, Str, Member, List, Int, observe, Float
from instrument_property import Prop
import cs_evaluate

#MPL plotting
from matplotlib.figure import Figure
from matplotlib.path import Path
import matplotlib.patches as patches
from matplotlib.gridspec import GridSpec
from matplotlib.backends.backend_pdf import PdfPages
from enaml.application import deferred_call
import matplotlib.pyplot as plt

import threading, numpy, traceback, os
from scipy.optimize import curve_fit

from colors import my_cmap, green_cmap


def mpl_rectangle(ax, ROI):
    """Draws a rectangle, for use in drawing ROIs on images"""
    #left, top, right, bottom, threshold = (0, 1, 2, 3, 4)  # column ordering of ROI boundaries in each ROI in ROIs
    left = ROI[0] - 0.5
    top = ROI[1] - 0.5
    right = ROI[2] - 0.5
    bottom = ROI[3] - 0.5
    verts = [
        (left, bottom),  # left, bottom
        (left, top),  # left, top
        (right, top),  # right, top
        (right, bottom),  # right, bottom
        (0., 0.),  # ignored
        ]

    codes = [Path.MOVETO,
             Path.LINETO,
             Path.LINETO,
             Path.LINETO,
             Path.CLOSEPOLY,
             ]

    path = Path(verts, codes)

    patch = patches.PathPatch(path, edgecolor='orange', facecolor='none', lw=1)
    ax.add_patch(patch)

class Analysis(Prop):
    """This is the parent class for all data analyses.  New analyses should subclass off this,
    and redefine at least one of preExperiment(), preIteration(), postMeasurement(), postIteration() or
    postExperiment().  You can enable multi-threading of analyses using queueAfterMeasurement and queueAfterIteration,
    but only if those results are not needed for other things (filtering, other analyses, optimization).  If
    multi-threading, you can also chose to dropMeasurementIfSlow or dropIterationIfSlow, which will not delete the data
    but will just not process it.  An analysis can return a success code after analyzeMesurement, which can be used to
    filter results.  The highest returned code dominates others:
        0 or None: good measurement, increment measurement total
        1: soft fail, continue with other analyses, but do not increment measurement total
        2: med fail, continue with other analyses, do not increment measurement total, and delete measurement data after all analyses
        3: hard fail, do not continue with other analyses, do not increment measurement total, delete measurement data
    """
    
    queueAfterMeasurement = Bool()  # Set to True to allow multi-threading on this analysis.  Only do this if you are NOT filtering on this analysis, and if you do NOT depend on the results of this analysis later. Default is False.
    dropMeasurementIfSlow = Bool()  # Set to True to skip measurements when slow.  Applies only to multi-threading.  Raw data can still be used post-iteration and post-experiment. Default is False.
    queueAfterIteration = Bool()  # Set to True to allow multi-threading on this analysis.  Only do this if you do NOT depend on the results of this analysis later. Default is False.
    dropIterationIfSlow = Bool()  # Set to True to skip iterations when slow.  Applies only to multi-threading.  Raw data can still be used in post-experiment.  Default is False.
    
    #internal variables, user should not modify
    measurementProcessing = Bool()
    iterationProcessing = Bool()
    measurementQueue = []
    iterationQueue = []

    def __init__(self, name, experiment, description=''):  # subclassing from Prop provides save/load mechanisms
        super(Analysis, self).__init__(name, experiment, description)
        self.properties += ['dropMeasurementIfSlow', 'dropIterationIfSlow']
    
    def preExperiment(self, experimentResults):
        """This is called before an experiment.
        The parameter experimentResults is a reference to the HDF5 file for this experiment.
        Subclass this to prepare the analysis appropriately."""
        pass

    def preIteration(self, iterationResults, experimentResults):
        """This is called before an iteration.
        The parameter experimentResults is a reference to the HDF5 file for this experiment.
        The parameter iterationResults is a reference to the HDF5 node for this coming iteration.
        Subclass this to prepare the analysis appropriately."""
        pass

    def postMeasurement(self, measurementResults, iterationResults, experimentResults):
        """Results is a tuple of (measurementResult,iterationResult,experimentResult) references to HDF5 nodes for this
        measurement."""
        if self.queueAfterMeasurement:  # if self.updateAfterMeasurement:
            if not self.measurementProcessing:  # check to see if a processing queue is already going
                self.measurementProcessing  =True
                self.measurementQueue.append((measurementResults, iterationResults, experimentResults))
                threading.Thread(target=self.measurementProcessLoop).start()
            elif not self.dropMeasurementIfSlow:  # if a queue is already going, add to it, unless we can't tolerate being behind
                self.measurementQueue.append((measurementResults, iterationResults, experimentResults))
        else:
            return self.analyzeMeasurement(measurementResults, iterationResults, experimentResults)
    
    def measurementProcessLoop(self):
        while len(self.measurementQueue) > 0:
            self.analyzeMeasurement(*self.measurementQueue.pop(0))  # process the oldest element
        self.measurementProcessing = False
    
    def analyzeMeasurement(self, measurementResults, iterationResults, experimentResults):
        """This is called after each measurement.
        The parameter results is a tuple of (measurementResult,iterationResult,experimentResult) references to HDF5 nodes for this measurement.
        Subclass this to update the analysis appropriately."""
        return
    
    def postIteration(self, iterationResults, experimentResults):
        if self.queueAfterIteration:
            if not self.iterationProcessing:  # check to see if a processing queue is already going
                self.iterationProcessing = True
                self.iterationQueue.append((iterationResults, experimentResults))
                threading.Thread(target=self.iterationProcessLoop).start()
            elif not self.dropIterationIfSlow:
                # if a queue is already going, add to it, unless we can't tolerate being behind
                self.iterationQueue.append((iterationResults, experimentResults))
        else:
            self.analyzeIteration(iterationResults, experimentResults)
    
    def iterationProcessLoop(self):
        while len(self.iterationQueue) > 0:
            self.analyzeIteration(*self.iterationQueue.pop(0))  # process the oldest element
        self.iterationProcessing = False
    
    def analyzeIteration(self, iterationResults, experimentResults):
        """This is called after each iteration.
        The parameter results is a tuple of (iterationResult,experimentResult) references to HDF5 nodes for this measurement.
        Subclass this to update the analysis appropriately."""
        pass
    
    def postExperiment(self, experimentResults):
        #no queueing, must do post experiment processing at this time
        self.analyzeExperiment(experimentResults)
    
    def analyzeExperiment(self, experimentResults):
        """This is called at the end of the experiment.
        The parameter experimentResults is a reference to the HDF5 file for the experiment.
        Subclass this to update the analysis appropriately."""
        pass

class AnalysisWithFigure(Analysis):
    
    #matplotlib figures
    figure = Typed(Figure)
    backFigure = Typed(Figure)
    figure1 = Typed(Figure)
    figure2 = Typed(Figure)
    
    def __init__(self, name, experiment, description=''):
        super(AnalysisWithFigure, self).__init__(name, experiment, description)
        
        #set up the matplotlib figures
        self.figure1 = Figure()
        self.figure2 = Figure()
        self.backFigure = self.figure2
        self.figure = self.figure1
    
    def swapFigures(self):
        temp = self.backFigure
        self.backFigure = self.figure
        self.figure = temp
    
    def updateFigure(self):
        #signal the GUI to redraw figure
        try:
            deferred_call(self.swapFigures)
        except RuntimeError: #application not started yet
            self.swapFigures()

    def blankFigure(self):
        fig = self.backFigure
        fig.clf()
        self.updateFigure()

class TextAnalysis(Analysis):
    #Text output that can be updated back to the GUI
    text = Str()

    def __init__(self, name, experiment, description=''):
        super(TextAnalysis, self).__init__(name, experiment, description)
        self.properties += ['text']

    def analyzeMeasurement(self, measurementResults, iterationResults, experimentResults):
        try:
            text = 'iteration {} measurement {}\nCamera temperature: {} C'.format(iterationResults.attrs['iteration'],
                                                              measurementResults.name.split('/')[-1],
                                                              measurementResults['data/Hamamatsu/temperature'].value)
        except KeyError as e:
            logger.warning('HDF5 text does not exist in TextAnalysis\n{}\n'.format(e))
            return
        self.set_gui({'text': text})

class TTL_filters(Analysis):
    """This analysis monitors the TTL inputs and does either hard or soft cuts of the data accordingly.
    Low is good, high is bad."""

    text = Str()
    lines = Str('PXI1Slot6/port0')
    filter_level = Int()

    def __init__(self, name, experiment, description=''):
        super(TTL_filters, self).__init__(name, experiment, description)
        self.properties += ['lines', 'filter_level']

    def analyzeMeasurement(self, measurementResults, iterationResults, experimentResults):
        text = 'none'
        if self.experiment.LabView.TTL.enable and ('TTL/data' in measurementResults['data']):
            a = measurementResults['data/TTL/data']
            #check to see if any of the inputs were True
            if numpy.any(a):
                #report the true inputs
                text = 'TTL Filters failed:\n'
                for i, b in enumerate(a):
                    #print out the row and column of the True input
                    text += 'Check {}: Laser(s) {}\n'.format(i, numpy.arange(len(b))[b])
                #record to the log and screen
                logger.warning(text)
                self.set_gui({'text': text})
                # User chooses whether or not to delete data.
                # max takes care of ComboBox returning -1 for no selection
                return max(0, self.filter_level)
            else:
                text = 'okay'
        self.set_gui({'text': text})

class RecentShotAnalysis(AnalysisWithFigure):
    """Plots the currently incoming shot"""
    data = Member()
    showROIs = Bool(False)
    shot = Int(0)
    update_lock = Bool(False)

    def __init__(self, name, experiment, description=''):
        super(RecentShotAnalysis, self).__init__(name, experiment, description)
        self.properties += ['showROIs','shot']

    def analyzeMeasurement(self,measurementResults,iterationResults,experimentResults):
        self.data = []
        if 'data/Hamamatsu/shots' in measurementResults:
            #for each image
            for shot in measurementResults['data/Hamamatsu/shots'].values():
                self.data.append(shot)
        self.updateFigure()  # only update figure if image was loaded

    @observe('shot', 'showROIs')
    def reload(self, change):
        self.updateFigure()

    def updateFigure(self):
        if not self.update_lock:
            try:
                self.update_lock = True
                fig = self.backFigure
                fig.clf()

                if (self.data is not None) and (self.shot < len(self.data)):
                    ax = fig.add_subplot(111)
                    ax.matshow(self.data[self.shot], cmap=my_cmap, vmin=self.experiment.imageSumAnalysis.min, vmax=self.experiment.imageSumAnalysis.max)
                    ax.set_title('most recent shot '+str(self.shot))
                    if self.showROIs:
                        #overlay ROIs
                        for ROI in self.experiment.squareROIAnalysis.ROIs:
                            mpl_rectangle(ax, ROI)

                super(RecentShotAnalysis, self).updateFigure()
            except Exception as e:
                logger.warning('Problem in RecentShotAnalysis.updateFigure()\n:{}'.format(e))
            finally:
                self.update_lock = False

class XYPlotAnalysis(AnalysisWithFigure):
    #### needs updating
    X=Member()
    Y=Member()
    
    def updateFigure(self):
        fig=self.backFigure
        fig.clf()
        ax=fig.add_subplot(111)
        if (self.X is not None) and (self.Y is not None):
            ax.plot(self.X, self.Y)
        super(XYPlotAnalysis, self).updateFigure()

class SampleXYAnalysis(XYPlotAnalysis):
    #### needs updating
    
    '''This analysis plots the sum of the whole camera image every measurement.'''
    def analyzeMeasurement(self,measurementResults,iterationResults,experimentResults):
        if 'data/Hamamatsu/shots' in measurementResults:
            self.Y = numpy.append(self.Y,numpy.sum(measurementResults['data/Hamamatsu/shots/0']))
            self.X = numpy.arange(len(self.Y))
        self.updateFigure()

class ShotsBrowserAnalysis(AnalysisWithFigure):
    
    ivarNames=List(default=[])
    ivarValueLists=List(default=[])
    selection=List(default=[])
    measurement=Int(0)
    shot=Int(0)
    array=Member()
    experimentResults=Member()
    showROIs = Bool(False)
    
    def __init__(self, experiment):
        super(ShotsBrowserAnalysis, self).__init__('ShotsBrowser', experiment, 'Shows a particular shot from the experiment')
        self.properties += ['measurement', 'shot', 'showROIs']
    
    def preExperiment(self, experimentResults):
        self.experimentResults = experimentResults
        self.ivarValueLists = [i for i in self.experiment.ivarValueLists]  # this line used to access the hdf5 file, but I have temporarily removed ivarValueLists from the HDF5 because it could not handle arbitrary lists of lists
        self.selection = [0]*len(self.ivarValueLists)
        deferred_call(setattr, self, 'ivarNames', [i for i in experimentResults.attrs['ivarNames']])
    
    def setIteration(self,ivarIndex,index):
        try:
            self.selection[ivarIndex] = index
        except Exception as e:
            logger.warning('Invalid ivarIndex in analysis.ShotsBrowserAnalysis.setSelection({},{})\n{}\n[]'.format(ivarIndex,index,e,traceback.format_exc()))
            raise PauseError
        self.load()
    
    @observe('measurement','shot','showROIs')
    def reload(self,change):
        self.load()
    
    def load(self):
        if self.experimentResults is not None:
            #find the first matching iteration
            m=str(self.measurement)
            s=str(self.shot)
            if 'iterations' in self.experimentResults:
                for i in self.experimentResults['iterations'].itervalues():
                    #find the first iteration that matches all the selected ivar indices
                    if numpy.all(i.attrs['ivarIndex'] == self.selection):
                        try:
                            self.array = i['measurements/{}/data/Hamamatsu/shots/{}'.format(m,s)]
                            self.updateFigure()
                        except Exception as e:
                            logger.warning('Exception trying to plot measurement {}, shot {}, in analysis.ShotsBrowserAnalysis.load()\n{}\n'.format(m,s,e))
                            self.blankFigure()
                        break
    
    def blankFigure(self):
        fig=self.backFigure
        fig.clf()
        super(ShotsBrowserAnalysis,self).updateFigure()
    
    def updateFigure(self):
        fig=self.backFigure
        fig.clf()
        ax=fig.add_subplot(111)
        ax.matshow(self.array, cmap=my_cmap, vmin=self.experiment.imageSumAnalysis.min, vmax=self.experiment.imageSumAnalysis.max)
        ax.set_title('browser')
        if self.showROIs:
            #overlay ROIs
            for ROI in self.experiment.squareROIAnalysis.ROIs:
                mpl_rectangle(ax, ROI)

        super(ShotsBrowserAnalysis,self).updateFigure() #makes a deferred_call to swap_figures()
    
class ImageSumAnalysis(AnalysisWithFigure):
    data = Member()
    enable = Bool()
    sum_array = Member()  # holds the sum of each shot
    count_array = Member()  # holds the number of measurements summed
    mean_array = Member()  # holds the mean image for each shot
    showROIs = Bool(False)  # should we superimpose ROIs?
    shot = Int()  # which shot to display
    update_lock = Bool(False)
    min = Member()
    max = Member()
    pdf = Member()

    def __init__(self, experiment):
        super(ImageSumAnalysis, self).__init__('ImageSumAnalysis', experiment, 'Sums shot0 images as they come in')
        self.properties += ['enable', 'showROIs', 'shot']
        self.min = 0
        self.max = 1

    def preExperiment(self, experimentResults):
        if self.enable and self.experiment.saveData:
            self.pdf = PdfPages(os.path.join(self.experiment.path, 'image_mean_{}.pdf'.format(self.experiment.experimentPath)))

    def preIteration(self, iterationResults, experimentResults):
        #clear old data
        self.mean_array = None

    def analyzeMeasurement(self, measurementResults,iterationResults,experimentResults):

        if 'data/Hamamatsu/shots' in measurementResults:
            if self.mean_array is None:
                #start a sum array of the right shape
                self.sum_array = numpy.array([shot for shot in measurementResults['data/Hamamatsu/shots'].itervalues()], dtype=numpy.uint64)
                self.count_array = numpy.zeros(len(self.sum_array), dtype=numpy.uint64)
                self.mean_array = self.sum_array.astype(numpy.float64)

            else:
                #add new data
                for i, shot in enumerate(measurementResults['data/Hamamatsu/shots'].itervalues()):
                    self.sum_array[i] += shot
                    self.count_array[i] += 1
                    self.mean_array[i] = self.sum_array[i]/self.count_array[i]

            #update the min/max that other image plots will use
            self.min = numpy.amin(self.mean_array)
            self.max = numpy.amax(self.mean_array)

            self.updateFigure()  # only update figure if image was loaded

    def analyzeIteration(self, iterationResults, experimentResults):
        if self.enable:
            iterationResults['sum_array'] = self.sum_array
            iterationResults['mean_array'] = self.mean_array

            # create image of all shots for pdf
            if self.experiment.saveData:

                # save to pdf
                self.pdf.savefig(self.figure, transparent=True, dpi=80)

    @observe('shot', 'showROIs')
    def reload(self, change):
        self.updateFigure()

    def updateFigure(self):
        if not self.update_lock:
            try:
                self.update_lock = True

                fig = self.backFigure
                fig.clf()

                if (self.mean_array is not None) and (self.shot < len(self.mean_array)):
                    gs = GridSpec(1, 2, width_ratios=[5,1])
                    ax = fig.add_subplot(gs[0,0])
                    im = ax.matshow(self.mean_array[self.shot], cmap=my_cmap)

                    #label plot
                    ax.set_title('{} shot {} mean'.format(self.experiment.experimentPath, self.shot))

                    # make a colorbar
                    cax = fig.add_subplot(gs[0,1])
                    fig.colorbar(im, cax=cax)

                    if self.showROIs:
                        #overlay ROIs
                        for ROI in self.experiment.squareROIAnalysis.ROIs:
                            mpl_rectangle(ax, ROI)

                super(ImageSumAnalysis, self).updateFigure()
            except Exception as e:
                logger.warning('Problem in ImageSumAnalysis.updateFigure()\n:{}'.format(e))
            finally:
                self.update_lock = False

    def postExperiment(self, experimentResults):
        if self.enable and self.experiment.saveData:
            self.pdf.close()


class SquareROIAnalysis(AnalysisWithFigure):
    """Add up the sums of pixels in a region, and evaluate whether or not an atom is present based on the totals."""

    version = '2014.05.01'
    ROI_rows = Int()
    ROI_columns = Int()
    ROIs = Member()  # a numpy array holding an ROI in each row
    filter_level = Int()
    #left, top, right, bottom, threshold = (0, 1, 2, 3, 4)  # column ordering of ROI boundaries in each ROI in ROIs
    loadingArray = Member()

    def __init__(self, experiment, ROI_rows=1, ROI_columns=1):
        super(SquareROIAnalysis, self).__init__('SquareROIAnalysis', experiment, 'Does analysis on square regions of interest')
        self.loadingArray = numpy.zeros((0, ROI_rows, ROI_columns), dtype=numpy.bool_)  # blank array that will hold digital representation of atom loading
        self.ROI_rows = ROI_rows
        self.ROI_columns = ROI_columns
        dtype = [('left', numpy.uint16), ('top', numpy.uint16), ('right', numpy.uint16), ('bottom', numpy.uint16), ('threshold', numpy.uint32)]
        self.ROIs = numpy.zeros(ROI_rows*ROI_columns, dtype=dtype)  # initialize with a blank array
        self.properties += ['version', 'ROIs', 'filter_level']

    def sum(self, roi, shot):
        return numpy.sum(shot[roi['top']:roi['bottom'], roi['left']:roi['right']])

    def sums(self, rois, shot):
        return numpy.array([self.sum(roi, shot) for roi in rois], dtype=numpy.uint32)

    def analyzeMeasurement(self, measurementResults, iterationResults, experimentResults):
        if 'data/Hamamatsu/shots' in measurementResults:
            #here we want to live update a digital plot of atom loading as it happens
            numROIs=len(self.ROIs)
            numShots = len(measurementResults['data/Hamamatsu/shots'])
            sum_array = numpy.zeros((numShots, numROIs), dtype=numpy.uint32)  # uint32 allows for summing ~65535 regions
            thresholdArray = numpy.zeros((numShots, numROIs), dtype=numpy.bool_)
            #loadingArray = numpy.zeros((numShots, self.ROI_rows, self.ROI_columns), dtype=numpy.bool_)

            #for each image
            for i, (name, shot) in enumerate(measurementResults['data/Hamamatsu/shots'].items()):
                #calculate sum of pixels in each ROI
                shot_sums = self.sums(self.ROIs, shot)
                sum_array[i] = shot_sums

                #compare each roi to threshold
                thresholdArray[i] = (shot_sums >= self.ROIs['threshold'])

            self.loadingArray = thresholdArray.reshape((numShots, self.ROI_rows, self.ROI_columns))
            #data will be stored in hdf5 so that save2013style can then append to Camera Data Iteration0 (signal).txt
            measurementResults['analysis/squareROIsums'] = sum_array
            measurementResults['analysis/squareROIthresholded'] = thresholdArray
            self.updateFigure()

    def updateFigure(self):
        fig = self.backFigure
        fig.clf()
        if self.loadingArray.size > 0:
            n = len(self.loadingArray)
            for i in range(n):
                ax = fig.add_subplot(n, 1, i+1)
                #make the digital plot here
                ax.matshow(self.loadingArray[i], cmap=green_cmap)
                ax.set_title('shot '+str(i))
        super(SquareROIAnalysis, self).updateFigure()


class LoadingFilters(Analysis):
    """This analysis monitors the brightess in the regions of interest, to decide if an atom was loaded or not"""
    version = '2014.05.01'

    enable = Bool()
    text = Str()
    filter_expression = Str()
    filter_level = Int()
    valid = Bool(True)

    def __init__(self, name, experiment, description=''):
        super(LoadingFilters, self).__init__(name, experiment, description)
        self.properties += ['version', 'enable', 'filter_expression', 'filter_level']

    def analyzeMeasurement(self, measurementResults, iterationResults, experimentResults):
        text = 'none'
        if self.enable:
            text = 'okay'
            if self.filter_expression != '':
                if ('analysis/squareROIsums' in measurementResults):

                    #evaluate the boolean expression, with the squareROIsums as 't' in the namespace
                    #This will overwrite any previous value, so we make a copy of the dictionary
                    vars = self.experiment.vars.copy()
                    vars['t'] = measurementResults['analysis/squareROIsums']
                    value, valid = cs_evaluate.evalWithDict(self.filter_expression, varDict=vars)
                    if not valid:
                        #raise an error
                        text = 'Failed to evaluate loading filter: {}:\n'.format(self.filter_expression)
                        logger.error(text)
                        self.set_gui({'text': text,
                                      'valid': False})
                        raise PauseError
                    elif not ((value == True) or (value == False)):
                        #Enforce that the expression must evaluate to a bool
                        text = 'Loading filter must be True or False, but it evaluated to: {}\nfor expression: {}:\n'.format(value, self.filter_expression)
                        logger.error(text)
                        self.set_gui({'text': text,
                                      'valid': False})
                        raise PauseError
                    else:
                        #eval worked, save value
                        measurementResults['analysis/loading_filter'] = value
                        if not value:
                            #Measurement did not pass filter (We do not need to take special action if the filter passes.)
                            text = 'Loading filter failed.'
                            self.set_gui({'text': text,
                                          'valid': True})
                            # User chooses whether or not to delete data.
                            # max takes care of ComboBox returning -1 for no selection
                            return max(0, self.filter_level)
        self.set_gui({'text': text,
                      'valid': True})


class DropFirstMeasurementsFilter(Analysis):
    """This analysis allows the user to drop the first N measurements in an 
    iteration, to ensure that all measurements are done at equivalent conditions
    ."""

    version = '2014.06.12'
    enable = Bool()
    filter_level = Int()
    N = Int()

    def __init__(self, name, experiment, description=''):
        super(DropFirstMeasurementsFilter, self).__init__(name, experiment, description)
        self.properties += ['version', 'enable', 'filter_level', 'N']

    def analyzeMeasurement(self, measurementResults, iterationResults, experimentResults):
        if self.enable:
            i = measurementResults.attrs['measurement']
            if i < self.N:
                # User chooses whether or not to delete data.
                # max takes care of ComboBox returning -1 for no selection
                logger.info('dropping measurement {} of {}'.format(i,self.N))
                return max(0, self.filter_level)

class HistogramAnalysis(AnalysisWithFigure):
    """This class live updates a histogram as data comes in."""
    enable = Bool()
    all_shots_array = Member()
    update_lock = Bool(False)
    list_of_what_to_plot = Str()

    def __init__(self, name, experiment, description=''):
        super(HistogramAnalysis, self).__init__(name, experiment, description)
        self.properties += ['enable', 'list_of_what_to_plot']

    def preIteration(self, iterationResults, experimentResults):
        #reset the histogram data
        self.all_shots_array = None

    def analyzeMeasurement(self, measurementResults, iterationResults, experimentResults):
        if self.enable:
            #every measurement, update a big array of all the ROI sums, then histogram only the requested shot/site
            d = measurementResults['analysis/squareROIsums']
            if self.all_shots_array is None:
                self.all_shots_array = numpy.array([d])
            else:
                self.all_shots_array = numpy.append(self.all_shots_array, numpy.array([d]), axis=0)
            self.updateFigure()

    @observe('list_of_what_to_plot')
    def reload(self, change):
        self.updateFigure()

    def updateFigure(self):
        if not self.update_lock:
            try:
                self.update_lock = True
                fig = self.backFigure
                fig.clf()

                if (self.all_shots_array is not None) and (len(self.all_shots_array) > 1):

                    #parse the list of what to plot from a string to a list of numbers
                    try:
                        plotlist = eval(self.list_of_what_to_plot)
                    except Exception as e:
                        logger.warning('Could not eval plotlist in MeasurementsGraph:\n{}\n'.format(e))
                        return

                    ax = fig.add_subplot(111)
                    #for i in plotlist:
                    #    try:
                    #        data = self.all_shots_array[:, i[0], i[1]]
                    #    except:
                    #        logger.warning('Trying to plot data that does not exist in MeasurementsGraph: shot {} roi {}'.format(i[0], i[1]))
                    #        continue
                    #    bins = int(numpy.rint(numpy.sqrt(len(data))))
                    #    ax.hist(data, bins, histtype='step')
                    shots = [i[0] for i in plotlist]
                    rois = [i[1] for i in plotlist]
                    data = self.all_shots_array[:, shots, rois]
                    bins = int(1.2*numpy.rint(numpy.sqrt(len(data))))
                    ax.hist(data, bins, histtype='step', label=['({},{})'.format(i[0], i[1]) for i in plotlist])
                    ax.legend()
                super(HistogramAnalysis, self).updateFigure()
            except Exception as e:
                logger.warning('Problem in HistogramAnalysis.updateFigure()\n:{}'.format(e))
            finally:
                self.update_lock = False


class HistogramGrid(AnalysisWithFigure):
    """This class gives a big histogram grid with 0 and 1 atom cutoffs after every iteration."""
    enable = Bool()
    all_shots_array = Member()
    shot = Int()
    pdf = Member()

    def __init__(self, name, experiment, description=''):
        super(HistogramGrid, self).__init__(name, experiment, description)
        self.properties += ['enable', 'shot']

    def preExperiment(self, experimentResults):
        if self.enable and self.experiment.saveData:
            self.pdf = PdfPages(os.path.join(self.experiment.path, 'histogram_grid_{}.pdf'.format(self.experiment.experimentPath)))

    def postExperiment(self, experimentResults):
        if self.enable and self.experiment.saveData:
            self.pdf.close()

    def preIteration(self, iterationResults, experimentResults):
        #reset the histogram data
        self.all_shots_array = None

    def analyzeIteration(self, iterationResults, experimentResults):
        if self.enable:
            # all_shots_array will be shape (measurements,shots,rois)
            self.all_shots_array = numpy.array([m['analysis/squareROIsums'] for m in iterationResults['measurements'].itervalues()])

            self.updateFigure()

            # save to PDF
            if self.experiment.saveData:
                self.pdf.savefig(self.figure, transparent=True, dpi=80)

    @observe('shot')
    def refresh(self, change):
        if self.enable:
            self.updateFigure()

    def updateFigure(self):
        try:
            fig = self.backFigure
            fig.clf()

            if self.all_shots_array is not None:
                # take shot 0
                roidata = self.all_shots_array[:, self.shot, :]
                fig.suptitle('{} shot {}'.format(self.experiment.experimentPath, self.shot))
                histogram_grid_plot(fig, roidata, self.experiment.ROI_rows, self.experiment.ROI_columns)

            super(HistogramGrid, self).updateFigure()

        except Exception as e:
            logger.warning('Problem in HistogramGrid.updateFigure():\n{}\n{}\n'.format(e, traceback.format_exc()))

def gaussian1D(x, x0, a, w):
    """returns the height of a gaussian (with mean x0, amplitude, a and width w) at the value(s) x"""
    g = a/(w*numpy.sqrt(2*numpy.pi))*numpy.exp(-0.5*(x-x0)**2/w**2)  # normalize
    g[numpy.isnan(g)] = 0  # eliminate bad elements
    return g
    
def two_gaussians(x,x0,a0,w0,x1,a1,w1):
    return gaussian1D(x,x0,a0,w0)+gaussian1D(x,x1,a1,w1)

def histogram_grid_plot(fig, roidata, ROI_rows, ROI_columns):
    #takes in a blank figure to work with, and roidata which is size (measurements, num_regions)
    N = roidata.shape[1]
    
    #first numerically take histograms
    bins = int(numpy.rint(numpy.sqrt(len(roidata))))
    hists = []
    bin_edges_list = []
    mins = []
    maxs = []
    maxcounts = []
    for i in xrange(N):
        ROI_sums = roidata[:, i]
        hist, bin_edges = numpy.histogram(ROI_sums, bins=bins)
        hists.append(hist)
        bin_edges_list.append(bin_edges)
        mins.append(min(ROI_sums))
        maxs.append(max(ROI_sums))
        maxcounts.append(max(hist))
    overall_min = min(mins)
    overall_max = max(maxs)
    overall_maxcount = max(maxcounts)

    #then calculate cutoffs
    best_g1s = []
    best_g2s = []
    best_errors = []
    best_mean1s = []
    best_mean2s = []
    best_width1s = []
    best_width2s = []
    best_amplitude1s = []
    best_amplitude2s = []
    best_cutoffs = []
    loading = []
    overlap = []
    xs = []
    popts=[]
    for i in xrange(N):
        cutoffs = bin_edges_list[i]  # use bin edges as possible cutoff locations
        bin_size = (bin_edges_list[i][1:]-bin_edges_list[i][:-1])
        x = (bin_edges_list[i][1:]+bin_edges_list[i][:-1])/2  # take center of each bin as test points (same in number as y)
        xs.append(x)
        y = hists[i]
        best_error = float('inf')
        for j in xrange(1, bins-1):  # leave off 0th and last bin edge to prevent divide by zero on one of the gaussian sums

            #fit a gaussian below the cutoff
            mean1 = numpy.sum(x[:j]*y[:j])/numpy.sum(y[:j])
            r1 = numpy.sqrt((x[:j]-mean1)**2)  # an array of distances from the mean
            width1 = numpy.sqrt(numpy.abs(numpy.sum((r1**2)*y[:j])/numpy.sum(y[:j])))  # the standard deviation
            amplitude1 = numpy.sum(y[:j]*bin_size[:j])  # area under gaussian is 1, so scale by total volume (i.e. the sum of y)
            g1 = gaussian1D(x, mean1, amplitude1, width1)

            #fit a gaussian above the cutoff
            mean2 = numpy.sum(x[j:]*y[j:])/numpy.sum(y[j:])
            r2 = numpy.sqrt((x[j:]-mean2)**2) #an array of distances from the mean
            width2 = numpy.sqrt(numpy.abs(numpy.sum((r2**2)*y[j:])/numpy.sum(y[j:]))) #the standard deviation
            amplitude2 = numpy.sum(y[j:]*bin_size[j:]) #area under gaussian is 1, so scale by total volume (i.e. the sum of y * step size)
            g2 = gaussian1D(x, mean2, amplitude2, width2)

            #find the total error
            error = sum(abs(y-g1-g2))
            if error < best_error:
                best_g1 = g1
                best_g2 = g2
                best_error = error
                best_mean1 = mean1
                best_mean2 = mean2
                best_width1 = width1
                best_width2 = width2
                best_amplitude1 = amplitude1
                best_amplitude2 = amplitude2
                best_cutoff = cutoffs[j]

        #record the best fit
        best_g1s.append(best_g1)
        best_g2s.append(best_g2)
        best_errors.append(best_error)
        best_mean1s.append(best_mean1)
        best_mean2s.append(best_mean2)
        best_width1s.append(best_width1)
        best_width2s.append(best_width2)
        best_amplitude1s.append(best_amplitude1)
        best_amplitude2s.append(best_amplitude2)

        #the cutoff found is for the digital data, not necessarily the best in terms of the gaussian fits
        #to find a better cutoff:
        #find the lowest point on the sum of the two gaussians
        #go in steps on 1 from peak to peak
        xc = numpy.arange(best_mean1, best_mean2)
        y1 = gaussian1D(xc, best_mean1, best_amplitude1, best_width1)
        y2 = gaussian1D(xc, best_mean2, best_amplitude2, best_width2)
        yc = y1 + y2
        cutoff = xc[numpy.argmin(yc)]
        best_cutoffs.append(cutoff)
        
        # calculate the loading
        loading.append(best_amplitude2/(best_amplitude1+best_amplitude2))
        
        #calculalate the overlap
        mins=numpy.amin([y1,y2],axis=0)
        overlap.append(numpy.sum(mins) / (numpy.sum(y1) + numpy.sum(y2)))
    
        #now do it using scipy curvefit
        #initial_guess = (best_mean1, best_amplitude1, best_width1, best_mean2, best_amplitude2, best_width2)
        #popt, pcov = curve_fit(two_gaussians, x, y, p0=initial_guess)
        #popts.append(popt)
    
    #plot
    gs1 = GridSpec(ROI_rows+1, ROI_columns+1,
                    left=0.02, bottom=0.05, top=.95, right=.98, wspace=0.2, hspace=0.5)
    font = 12
    
    #make histograms for each site
    for i in xrange(ROI_rows):
        for j in xrange(ROI_columns):
            n = ROI_columns*i+j
            #ax = fig.add_subplot(7, 7, n+1)
            ax = fig.add_subplot(gs1[i, j])
            #plot histogram
            x = numpy.zeros(bins+2)
            x[1:] = bin_edges_list[n]
            y = numpy.zeros(bins+2, dtype=int)
            y[1:-1] = hists[n]
            ax.step(x, y, where='post')
            ax.set_xlim([overall_min, overall_max])
            ax.set_ylim([0, overall_maxcount])
            ax.set_title('site {}, {:.0f}$\pm${:.1f}%'.format(n,loading[n]*100,overlap[n]*100))  # , size=font)
            ax.set_xticks([best_mean1s[n], best_cutoffs[n], best_mean2s[n], overall_max])
            ax.set_xticklabels(['{}$\pm${:.0f}'.format(int(best_mean1s[n]/1000),best_width1s[n]/1000), str(int(best_cutoffs[n]/1000)), '{}$\pm${:.1f}'.format(int(best_mean2s[n]/1000),best_width2s[n]/1000), 'e3'], size=font, rotation=90, verticalalignment='baseline')
            ax.set_yticks([0, max(best_g1s[n]), max(best_g2s[n])])
            ax.set_yticklabels([str(0), str(int(max(best_g1s[n]))), str(int(max(best_g2s[n])))])  # , size=font)
            #plot gaussians
            x = numpy.linspace(overall_min, overall_max, 100)
            #ax.plot(x,two_gaussians(x,*popts[n]),'g',lw=3)
            y1 = numpy.concatenate([[0], gaussian1D(x, best_mean1s[n], best_amplitude1s[n], best_width1s[n]), [0]]) #pad with zeros so that matplotlib fill shows up correctly
            y2 = numpy.concatenate([[0], gaussian1D(x, best_mean2s[n], best_amplitude2s[n], best_width2s[n]), [0]])
            x = numpy.concatenate([[x[0]], x, [x[-1]]])
            ax.fill(x, y1, 'b', x, y2, 'r', alpha=0.5)
            #plot cutoff line
            ax.vlines(best_cutoffs[n], 0, overall_maxcount)
    
    font=20  # larger font for average stats
    
    #make stats for each row
    for i in xrange(ROI_rows):
        ax = fig.add_subplot(gs1[i,ROI_columns])
        ax.axis('off')
        ax.text(0.5,0.5,'row {}\navg loading\n{:.0f}%'.format(i,100*numpy.mean(loading[i*ROI_columns:(i+1)*ROI_columns])),
            horizontalalignment='center',
            verticalalignment='center',
            transform=ax.transAxes)  # ,
            #fontsize=font)

    #make stats for each column
    for i in xrange(ROI_columns):
        ax = fig.add_subplot(gs1[ROI_rows,i])
        ax.axis('off')
        ax.text(0.5,0.5,'column {}\navg loading\n{:.0f}%'.format(i,100*numpy.mean(loading[i:i+(ROI_rows-1)*ROI_columns:ROI_columns])),
            horizontalalignment='center',
            verticalalignment='center',
            transform=ax.transAxes)  # ,
            #fontsize=font)

    #make stats for whole array
    ax = fig.add_subplot(gs1[ROI_rows,ROI_columns])
    ax.axis('off')
    ax.text(0.5,0.5,'array\navg loading\n{:.0f}%'.format(100*numpy.mean(loading)),
        horizontalalignment='center',
        verticalalignment='center',
        transform=ax.transAxes)  # ,
        #fontsize=font)

class MeasurementsGraph(AnalysisWithFigure):
    """Plots a region of interest sum after every measurement"""
    enable = Bool()
    data = Member()
    update_lock = Bool(False)
    list_of_what_to_plot = Str()

    def __init__(self, name, experiment, description=''):
        super(MeasurementsGraph, self).__init__(name, experiment, description)
        self.properties += ['enable', 'list_of_what_to_plot']
        self.data = None

    def analyzeMeasurement(self, measurementResults, iterationResults, experimentResults):
        if self.enable:
            #every measurement, update a big array of all the ROI sums, then histogram only the requested shot/site
            d = measurementResults['analysis/squareROIsums']
            if self.data is None:
                self.data = numpy.array([d])
            else:
                self.data = numpy.append(self.data, numpy.array([d]), axis=0)
            self.updateFigure()

    @observe('list_of_what_to_plot')
    def reload(self, change):
        self.updateFigure()

    def clear(self):
        self.data = None
        self.updateFigure()

    def updateFigure(self):
        if not self.update_lock:
            try:
                self.update_lock = True
                fig = self.backFigure
                fig.clf()

                if self.data is not None:
                    #parse the list of what to plot from a string to a list of numbers
                    try:
                        plotlist = eval(self.list_of_what_to_plot)
                    except Exception as e:
                        logger.warning('Could not eval plotlist in MeasurementsGraph:\n{}\n'.format(e))
                        return
                    #make one plot
                    ax = fig.add_subplot(111)
                    for i in plotlist:
                        try:
                            data = self.data[:, i[0], i[1]]
                        except:
                            logger.warning('Trying to plot data that does not exist in MeasurementsGraph: shot {} roi {}'.format(i[0], i[1]))
                            continue
                        label = '({},{})'.format(i[0], i[1])
                        ax.plot(data, 'o', label=label)
                    #add legend using the labels assigned during ax.plot()
                    ax.legend()
                super(MeasurementsGraph, self).updateFigure()
            except Exception as e:
                logger.warning('Problem in MeasurementsGraph.updateFigure()\n:{}'.format(e))
            finally:
                self.update_lock = False


class IterationsGraph(AnalysisWithFigure):
    """Plots the average of a region of interest sum for an iteration, after each iteration"""
    enable = Bool()
    mean = Member()
    sigma = Member()
    current_iteration_data = Member()
    update_lock = Bool(False)
    list_of_what_to_plot = Str()
    draw_connecting_lines = Bool()
    draw_error_bars = Bool()
    add_only_filtered_data = Bool()
    ymin = Str()
    ymax = Str()

    def __init__(self, name, experiment, description=''):
        super(IterationsGraph, self).__init__(name, experiment, description)
        self.properties += ['enable', 'list_of_what_to_plot', 'draw_connecting_lines', 'draw_error_bars', 'ymin', 'ymax']

    def preExperiment(self, experimentResults):
        #erase the old data at the start of the experiment
        self.mean = None
        self.sigma = None

    def preIteration(self, iterationResults, experimentResults):
        self.current_iteration_data = None

    def analyzeMeasurement(self, measurementResults, iterationResults, experimentResults):
        # Check to see if we want to do anything with this data, based on the LoadingFilters.
        # Careful here to use .value, otherwise it will always be True if the dataset exists.
        if self.enable:
            if (not self.add_only_filtered_data) or (('analysis/loading_filter' in measurementResults) and measurementResults['analysis/loading_filter'].value):

                d = numpy.array([measurementResults['analysis/squareROIsums']])

                if self.current_iteration_data is None:
                    #on first measurement of an iteration, start anew
                    new_iteration = True
                    self.current_iteration_data = d
                else:
                    #else append
                    new_iteration = False
                    self.current_iteration_data = numpy.append(self.current_iteration_data, d, axis=0)

                # average across measurements
                # keepdims gives result with size (1 x shots X rois)
                mean = numpy.mean(self.current_iteration_data, axis=0, keepdims=True)
                #find standard deviation
                sigma = numpy.std(self.current_iteration_data, axis=0, keepdims=True)/numpy.sqrt(len(self.current_iteration_data))

                if self.mean is None:
                    #on first iteration start anew
                    self.mean = mean
                    self.sigma = sigma
                else:
                    if new_iteration:
                        #append
                        self.mean = numpy.append(self.mean, mean, axis=0)
                        self.sigma = numpy.append(self.sigma, sigma, axis=0)
                    else:
                        #replace last entry
                        self.mean[-1] = mean
                        self.sigma[-1] = sigma
                self.updateFigure()

    @observe('list_of_what_to_plot', 'draw_connecting_lines', 'ymin', 'ymax')
    def reload(self, change):
        self.updateFigure()

    def updateFigure(self):
        if not self.update_lock:
            try:
                self.update_lock = True
                fig = self.backFigure
                fig.clf()

                if self.mean is not None:
                    #parse the list of what to plot from a string to a list of numbers
                    try:
                        plotlist = eval(self.list_of_what_to_plot)
                    except Exception as e:
                        logger.warning('Could not eval plotlist in IterationsGraph:\n{}\n'.format(e))
                        return
                    #make one plot
                    ax = fig.add_subplot(111)
                    for i in plotlist:
                        try:
                            mean = self.mean[:, i[0], i[1]]
                            sigma = self.sigma[:, i[0], i[1]]
                        except:
                            logger.warning('Trying to plot data that does not exist in IterationsGraph: shot {} roi {}'.format(i[0], i[1]))
                            continue
                        label = '({},{})'.format(i[0], i[1])
                        linestyle = '-o' if self.draw_connecting_lines else 'o'
                        if self.draw_error_bars:
                            ax.errorbar(numpy.arange(len(mean)), mean, yerr=sigma, fmt=linestyle, label=label)
                        else:
                            ax.plot(numpy.arange(len(mean)), mean, linestyle, label=label)
                    #adjust the limits so that the data isn't right on the edge of the graph
                    ax.set_xlim(-.5, len(self.mean)+0.5)
                    if self.ymin != '':
                        ax.set_ylim(bottom=float(self.ymin))
                    if self.ymax != '':
                        ax.set_ylim(top=float(self.ymax))
                    #add legend using the labels assigned during ax.plot() or ax.errorbar()
                    ax.legend()
                super(IterationsGraph, self).updateFigure()
            except Exception as e:
                logger.warning('Problem in IterationsGraph.updateFigure()\n{}\n{}\n'.format(e, traceback.format_exc()))
            finally:
                self.update_lock = False


class RetentionGraph(AnalysisWithFigure):
    """Plots the average of a region of interest sum for an iteration, after each iteration"""
    enable = Bool()
    mean = Member()
    sigma = Member()
    current_iteration_data = Member()
    update_lock = Bool(False)
    list_of_what_to_plot = Str()
    draw_connecting_lines = Bool()
    draw_error_bars = Bool()
    add_only_filtered_data = Bool()
    ymin = Str()
    ymax = Str()

    def __init__(self, name, experiment, description=''):
        super(RetentionGraph, self).__init__(name, experiment, description)
        self.properties += ['enable', 'list_of_what_to_plot', 'draw_connecting_lines', 'draw_error_bars', 'ymin', 'ymax']

    def preExperiment(self, experimentResults):
        #erase the old data at the start of the experiment
        self.mean = None
        self.sigma = None

    def preIteration(self, iterationResults, experimentResults):
        self.current_iteration_data = None

    def analyzeMeasurement(self, measurementResults, iterationResults, experimentResults):
        """Every measurement, update the results.  Plot the ratio of shots with an atom to shots without."""
        # Check to see if we want to do anything with this data, based on the LoadingFilters.
        # Careful here to use .value, otherwise it will always be True if the dataset exists.
        if self.enable:
            if (not self.add_only_filtered_data) or (('analysis/loading_filter' in measurementResults) and measurementResults['analysis/loading_filter'].value):

                # grab already thresholded data from SquareROIAnalysis
                a = measurementResults['analysis/squareROIthresholded']
                # add one dimension to the data to help with appending
                d = numpy.reshape(a, (1, a.shape[0], a.shape[1]))

                if self.current_iteration_data is None:
                    #on first measurement of an iteration, start anew
                    new_iteration = True
                    self.current_iteration_data = d
                else:
                    #else append
                    new_iteration = False
                    self.current_iteration_data = numpy.append(self.current_iteration_data, d, axis=0)

                # average across measurements
                # keepdims gives result with size (1 x shots X rois)
                mean = numpy.mean(self.current_iteration_data, axis=0, keepdims=True)
                #find the 1 sigma confidence interval using the normal approximation: http://en.wikipedia.org/wiki/Binomial_proportion_confidence_interval
                sigma = numpy.sqrt(mean*(1-mean)/len(self.current_iteration_data))

                if self.mean is None:
                    #on first iteration start anew
                    self.mean = mean
                    self.sigma = sigma
                else:
                    if new_iteration:
                        #append
                        self.mean = numpy.append(self.mean, mean, axis=0)
                        self.sigma = numpy.append(self.sigma, sigma, axis=0)
                    else:
                        #replace last entry
                        self.mean[-1] = mean
                        self.sigma[-1] = sigma
                self.updateFigure()

    @observe('list_of_what_to_plot', 'draw_connecting_lines', 'draw_error_bars', 'ymin', 'ymax')
    def reload(self, change):
        self.updateFigure()

    def updateFigure(self):
        if not self.update_lock:
            try:
                self.update_lock = True
                fig = self.backFigure
                fig.clf()

                if self.mean is not None:
                    #parse the list of what to plot from a string to a list of numbers
                    try:
                        plotlist = eval(self.list_of_what_to_plot)
                    except Exception as e:
                        logger.warning('Could not eval plotlist in RetentionGraph:\n{}\n'.format(e))
                        return
                    #make one plot
                    ax = fig.add_subplot(111)
                    for i in plotlist:
                        try:
                            mean = self.mean[:, i[0], i[1]]
                            sigma = self.sigma[:, i[0], i[1]]
                        except:
                            logger.warning('Trying to plot data that does not exist in RetentionGraph: shot {} roi {}'.format(i[0], i[1]))
                            continue
                        label = '({},{})'.format(i[0], i[1])
                        linestyle = '-o' if self.draw_connecting_lines else 'o'
                        if self.draw_error_bars:
                            ax.errorbar(numpy.arange(len(mean)), mean, yerr=sigma, fmt=linestyle, label=label)
                        else:
                            ax.plot(numpy.arange(len(mean)), mean, linestyle, label=label)
                    #adjust the limits so that the data isn't right on the edge of the graph
                    ax.set_xlim(-.5, len(self.mean)+0.5)
                    if self.ymin != '':
                        ax.set_ylim(bottom=float(self.ymin))
                    if self.ymax != '':
                        ax.set_ylim(top=float(self.ymax))
                    #add legend using the labels assigned during ax.plot() or ax.errorbar()
                    ax.legend()
                super(RetentionGraph, self).updateFigure()
            except Exception as e:
                logger.warning('Problem in RetentionGraph.updateFigure()\n{}\n{}\n'.format(e, traceback.format_exc()))
            finally:
                self.update_lock = False
