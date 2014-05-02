from __future__ import division
import logging
logger = logging.getLogger(__name__)

from cs_errors import PauseError

from atom.api import Bool, Typed, Str, Member, List, Int, observe
from instrument_property import Prop
import cs_evaluate

#MPL plotting
from matplotlib.figure import Figure
from matplotlib.path import Path
import matplotlib.patches as patches
from enaml.application import deferred_call

import threading, numpy, traceback

from colors import my_cmap, green_cmap


def mpl_rectangle(ax, ROI):
    """Draws a rectangle, for use in drawing ROIs on images"""
    #left, top, right, bottom, threshold = (0, 1, 2, 3, 4)  # column ordering of ROI boundaries in each ROI in ROIs
    left = ROI[0] - 0.5
    top = ROI[1] - 0.5
    right = ROI[2] - 0.5
    bottom = ROI[3] - 0.5
    verts = [
        (left, bottom), # left, bottom
        (left, top), # left, top
        (right, top), # right, top
        (right, bottom), # right, bottom
        (0., 0.), # ignored
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
    '''This is the parent class for all data analyses.  New analyses should subclass off this,
    and redefine at least one of preExperiment(), preIteration(), postMeasurement(), postIteration() or postExperiment().
    You can enable multi-threading of analyses using queueAfterMeasurement and queueAfterIteration, but only if those results are not needed for other things (filtering, other analyses, optimization).
    If multi-threading, you can also chose to dropMeasurementIfSlow or dropIterationIfSlow, which will not delete the data but will just not process it.
    An analysis can return a success code after analyzeMesurement, which can be used to filter results.  The highest returned code dominates others:
        0 or None: good measurement, increment measurement total
        1: soft fail, continue with other analyses, but do not increment measurement total
        2: med fail, continue with other analyses, do not increment measurement total, and delete measurement data after all analyses
        3: hard fail, do not continue with other analyses, do not increment measurement total, delete measurement data'''
    
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

    def postMeasurement(self,measurementResults,iterationResults,experimentResults):
        '''results is a tuple of (measurementResult,iterationResult,experimentResult) references to HDF5 nodes for this measurement'''
        if self.queueAfterMeasurement: #if self.updateAfterMeasurement:
            if not self.measurementProcessing: #check to see if a processing queue is already going
                self.measurementProcessing=True
                self.measurementQueue.append((measurementResults,iterationResults,experimentResults))
                threading.Thread(target=self.measurementProcessLoop).start()
            elif not self.dropMeasurementIfSlow: #if a queue is already going, add to it, unless we can't tolerate being behind
                self.measurementQueue.append((measurementResults,iterationResults,experimentResults))
        else:
            return self.analyzeMeasurement(measurementResults,iterationResults,experimentResults)
    
    def measurementProcessLoop(self):
        while len(self.measurementQueue)>0:
            self.analyzeMeasurement(*self.measurementQueue.pop(0)) #process the oldest element
        self.measurementProcessing=False
    
    def analyzeMeasurement(self,measurementResults,iterationResults,experimentResults):
        '''This is called after each measurement.
        The parameter results is a tuple of (measurementResult,iterationResult,experimentResult) references to HDF5 nodes for this measurement.
        Subclass this to update the analysis appropriately.'''
        return
    
    def postIteration(self,iterationResults,experimentResults):
        if self.queueAfterIteration:
            if not self.iterationProcessing: #check to see if a processing queue is already going
                self.iterationProcessing=True
                self.iterationQueue.append((iterationResults,experimentResults))
                threading.Thread(target=self.iterationProcessLoop).start()
            elif not self.dropIterationIfSlow: #if a queue is already going, add to it, unless we can't tolerate being behind
                self.iterationQueue.append((iterationResults,experimentResults))
        else:
            self.analyzeIteration(iterationResults,experimentResults)
    
    def iterationProcessLoop(self):
        while len(self.iterationQueue)>0:
            self.analyzeIteration(*self.iterationQueue.pop(0)) #process the oldest element
        self.iterationProcessing=False
    
    def analyzeIteration(self,iterationResults,experimentResults):
        '''This is called after each iteration.
        The parameter results is a tuple of (iterationResult,experimentResult) references to HDF5 nodes for this measurement.
        Subclass this to update the analysis appropriately.'''
        pass
    
    def postExperiment(self,experimentResults):
        #no queueing, must do post experiment processing at this time
        self.analyzeExperiment(experimentResults)
    
    def analyzeExperiment(self,experimentResults):
        '''This is called at the end of the experiment.
        The parameter experimentResults is a reference to the HDF5 file for the experiment.
        Subclass this to update the analysis appropriately.'''
        pass

class AnalysisWithFigure(Analysis):
    
    #matplotlib figures
    figure=Typed(Figure)
    backFigure=Typed(Figure)
    figure1=Typed(Figure)
    figure2=Typed(Figure)
    
    def __init__(self,name,experiment,description=''):
        super(AnalysisWithFigure,self).__init__(name,experiment,description)
        
        #set up the matplotlib figures
        self.figure1=Figure()
        self.figure2=Figure()
        self.backFigure=self.figure2
        self.figure=self.figure1
    
    def swapFigures(self):
        temp=self.backFigure
        self.backFigure=self.figure
        self.figure=temp
    
    def updateFigure(self):
        #signal the GUI to redraw figure
        try:
            deferred_call(self.swapFigures)
        except RuntimeError: #application not started yet
            self.swapFigures()

    def blankFigure(self):
        fig=self.backFigure
        fig.clf()
        super(AnalysisWithFigure,self).updateFigure()

class TextAnalysis(Analysis):
    #Text output that can be updated back to the GUI
    text = Str()

    def __init__(self, name, experiment, description=''):
        super(TextAnalysis,self).__init__(name, experiment, description)
        self.properties += ['text']

    def analyzeMeasurement(self, measurementResults, iterationResults, experimentResults):
        try:
            text = 'iteration {} measurement {}\nCamera temperature: {} C'.format(iterationResults.attrs['iteration'],measurementResults.name.split('/')[-1],measurementResults['data/Hamamatsu/temperature'].value)
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
        super(ShotsBrowserAnalysis, self).__init__('ShotsBrowser',experiment,'Shows a particular shot from the experiment')
        self.properties += ['measurement', 'shot', 'showROIs']
    
    def preExperiment(self,experimentResults):
        self.experimentResults=experimentResults
        self.ivarValueLists=[i for i in self.experiment.ivarValueLists]  # this line used to access the hdf5 file, but I have temporarily removed ivarValueLists from the HDF5 because it could not handle arbitrary lists of lists
        self.selection=[0]*len(self.ivarValueLists)
        deferred_call(setattr,self,'ivarNames',[i for i in experimentResults.attrs['ivarNames']])
    
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
                    if numpy.all(i.attrs['ivarIndex']==self.selection):
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
    sum_array = Member()  # holds the sum of each shot
    count_array = Member()  # holds the number of measurements summed
    mean_array = Member()  # holds the mean image for each shot
    showROIs = Bool(False)  # should we superimpose ROIs?
    shot = Int()  # which shot to display
    update_lock = Bool(False)
    min = Member()
    max = Member()

    def __init__(self, experiment):
        super(ImageSumAnalysis, self).__init__('ImageSumAnalysis',experiment,'Sums shot0 images as they come in')
        self.properties += ['showROIs', 'shot']
        self.min = 0
        self.max = 1

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

    def analyzeIteration(self, iterationResults,experimentResults):
        iterationResults['sum_array'] = self.sum_array

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
                    ax = fig.add_subplot(111)
                    ax.matshow(self.mean_array[self.shot], cmap=my_cmap)

                    #TODO: make a colorbar (this doesn't work and we can't use pyplot)
                    #fig.colorbar(plot,cax=ax,ax=ax)
                    ax.set_title('shot {} mean'.format(self.shot))

                    if self.showROIs:
                        #overlay ROIs
                        for ROI in self.experiment.squareROIAnalysis.ROIs:
                            mpl_rectangle(ax, ROI)

                super(ImageSumAnalysis, self).updateFigure()
            except Exception as e:
                logger.warning('Problem in ImageSumAnalysish.updateFigure()\n:{}'.format(e))
            finally:
                self.update_lock = False

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
        super(SquareROIAnalysis, self).__init__('SquareROIAnalysis', experiment,'Does analysis on square regions of interest')
        self.loadingArray = numpy.zeros((0, ROI_rows, ROI_columns), dtype=numpy.bool_)  # blank array that will hold digital representation of atom loading
        self.ROI_rows = ROI_rows
        self.ROI_columns = ROI_columns
        dtype=[('left', numpy.uint16), ('top', numpy.uint16), ('right', numpy.uint16), ('bottom', numpy.uint16), ('threshold', numpy.uint32)]
        self.ROIs = numpy.zeros(ROI_rows*ROI_columns, dtype=dtype)  # initialize with a blank array
        self.properties += ['ROIs', 'filter_level']
    
    def sum(self, roi, shot):
        return numpy.sum(shot[roi['top']:roi['bottom'], roi['left']:roi['right']])

    def sums(self, rois, shot):
        return numpy.array([self.sum(roi, shot) for roi in rois], dtype=numpy.uint32)

    def analyzeMeasurement(self, measurementResults, iterationResults, experimentResults):
        #here we want to live update a digital plot of atom loading as it happens
        numROIs=len(self.ROIs)
        numShots = len(measurementResults['data/Hamamatsu/shots'])
        sum_array = numpy.zeros((numShots, numROIs), dtype=numpy.uint32)  # uint32 allows for summing ~65535 regions
        loadingArray = numpy.zeros((numShots, self.ROI_rows, self.ROI_columns), dtype=numpy.bool_)

        #for each image
        for i, (name, shot) in enumerate(measurementResults['data/Hamamatsu/shots'].items()):
            #calculate sum of pixels in each ROI
            shot_sums = self.sums(self.ROIs, shot)
            sum_array[i] = shot_sums

            #compare each roi to threshold
            thresholdArray = (shot_sums >= self.ROIs['threshold'])
            loadingArray[i] = numpy.reshape(thresholdArray, (self.ROI_rows, self.ROI_columns))

        #data will be stored in hdf5 so that save2013style can then append to Camera Data Iteration0 (signal).txt
        measurementResults['analysis/squareROIsums'] = sum_array
        self.loadingArray = loadingArray
        self.updateFigure()

        # Cut data based on atom loading
        # User chooses whether or not to delete data.
        # max takes care of ComboBox returning -1 for no selection
        #return max(0, self.filter_level)

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
        self.properties += ['enable', 'filter_expression', 'filter_level']

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


class HistogramAnalysis(AnalysisWithFigure):
    """This class live updates a histogram as data comes in."""
    shot = Int(0)
    roi = Int(0)
    all_shots_array = Member()
    update_lock = Bool(False)

    def __init__(self, name, experiment, description=''):
        super(HistogramAnalysis, self).__init__(name, experiment, description)
        self.properties += ['shot', 'roi']

    def preIteration(self, iterationResults, experimentResults):
        #reset the histogram data
        self.all_shots_array = None
        #m = self.experiment.LabView.camera.shotsPerMeasurement.value
        #n = len(self.experiment.squareROIAnalysis.ROIs)
        #self.all_shots_array = numpy.zeros((0, m, n), dtype=numpy.uint32)

    def analyzeMeasurement(self, measurementResults, iterationResults, experimentResults):
        #every measurement, update a big array of all the ROI sums, then histogram only the requested shot/site
        d = measurementResults['analysis/squareROIsums']
        if self.all_shots_array is None:
            self.all_shots_array = numpy.array([d])
        else:
            self.all_shots_array = numpy.append(self.all_shots_array, numpy.array([d]), axis=0)
        self.updateFigure()

    @observe('shot', 'roi')
    def reload(self, change):
        self.updateFigure()

    def updateFigure(self):
        if not self.update_lock:
            try:
                self.update_lock = True
                fig = self.backFigure
                fig.clf()

                if self.all_shots_array is not None:
                    ax = fig.add_subplot(111)
                    data = self.all_shots_array[:, self.shot, self.roi]
                    #n, bins, patches =
                    ax.hist(data, int(numpy.rint(numpy.sqrt(len(data)))), alpha=0.75)
                    #ax.add_patch(patches)
                super(HistogramAnalysis, self).updateFigure()
            except Exception as e:
                logger.warning('Problem in HistogramAnalysis.updateFigure()\n:{}'.format(e))
            finally:
                self.update_lock = False

class MeasurementsGraph(AnalysisWithFigure):
    """Plots a region of interest sum after every measurement"""
    data = Member()
    update_lock = Bool(False)
    list_of_what_to_plot = Str()

    def __init__(self, name, experiment, description=''):
        super(MeasurementsGraph, self).__init__(name, experiment, description)
        self.properties += ['list_of_what_to_plot']
        self.data = None

    def analyzeMeasurement(self, measurementResults, iterationResults, experimentResults):
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
                    plotlist = eval(self.list_of_what_to_plot)

                    #make one plot
                    ax = fig.add_subplot(111)
                    for i in plotlist:
                        data = self.data[:, i[0], i[1]]
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
        self.properties += ['list_of_what_to_plot', 'draw_connecting_lines', 'draw_error_bars', 'ymin', 'ymax']

    def preExperiment(self, experimentResults):
        #erase the old data at the start of the experiment
        self.mean = None
        self.sigma = None

    def preIteration(self, iterationResults, experimentResults):
        self.current_iteration_data = None

    def analyzeMeasurement(self, measurementResults, iterationResults, experimentResults):
        # Check to see if we want to do anything with this data, based on the LoadingFilters.
        # Careful here to use .value, otherwise it will always be True if the dataset exists.
        if measurementResults['analysis/loading_filter'].value or (not self.add_only_filtered_data):

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
            sigma = numpy.std(self.current_iteration_data, axis=0, keepdims=True)

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

    # def analyzeIteration(self, iterationResults, experimentResults):
    #
    #     #load in data from all the measurements (ROI sums produced in SquareROIAnalysis)
    #     d = numpy.array([m['analysis/squareROIsums'] for m in iterationResults['measurements'].itervalues()])
    #
    #     #average across measurements (result is (shots X rois))
    #     averages = numpy.sum(d, axis=0, keepdims=True)/len(d)
    #     #find standard deviation
    #     sigma = numpy.std(d, axis=0, keepdims=True)
    #
    #     if self.data is None:
    #     #on first iteration start anew
    #         self.data = averages
    #     else:
    #     #else append
    #         self.data = numpy.append(self.data, averages, axis=0)
    #     self.updateFigure()

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
                    plotlist = eval(self.list_of_what_to_plot)

                    #make one plot
                    ax = fig.add_subplot(111)
                    for i in plotlist:
                        mean = self.mean[:, i[0], i[1]]
                        sigma = self.sigma[:, i[0], i[1]]
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
                logger.warning('Problem in IterationsGraph.updateFigure()\n{}\n{}\n'.format(e,traceback.format_exc()))
            finally:
                self.update_lock = False


class RetentionAnalysis(AnalysisWithFigure):
    pass

class OptimizerAnalysis(AnalysisWithFigure):
    costfunction = Str('')
    
    def __init__(self, experiment):
        super(OptimizerAnalysis, self).__init__('OptimizerAnalysis', experiment, 'updates independent variables to minimize cost function')
