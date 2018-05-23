from __future__ import division
__author__ = 'Martin Lichtman'
import logging
logger = logging.getLogger(__name__)

from cs_errors import PauseError

import threading, numpy, traceback, time

import matplotlib as mpl
mpl.use('PDF')

import matplotlib.pyplot as plt
from matplotlib.figure import Figure
from matplotlib.path import Path
import matplotlib.patches as patches
from mpl_toolkits.axes_grid1 import make_axes_locatable
#from matplotlib.backends.backend_pdf import PdfPages
from enaml.application import deferred_call

from atom.api import Bool, Typed, Str, Member, List, Int, observe, Float
np = numpy
from scipy.optimize import curve_fit
from scipy.special import erf

from colors import my_cmap, green_cmap

from instrument_property import Prop,StrProp
import cs_evaluate

def mpl_rectangle(ax, ROI):
    """Draws a rectangle, for use in drawing ROIs on images."""
    # left, top, right, bottom, threshold = (0, 1, 2, 3, 4)
    # column ordering of ROI boundaries in each ROI in ROIs
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

    codes = [
        Path.MOVETO,
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
    enable = Bool(default=False)
    # holds the analysis thread that handles measurement analysis
    measurementThread = Member()
    # analysis thread wake event
    restart = Member()
    # Set to True to allow multi-threading on this analysis.
    # Only do this if you are NOT filtering on this analysis, and if you do NOT
    # depend on the results of this analysis later. Default is False.
    queueAfterMeasurement = Bool()
    # Set to True to skip measurements when slow.
    # Applies only to multi-threading. Raw data can still be used
    # post-iteration and post-experiment. Default is False.
    dropMeasurementIfSlow = Bool()
    # Set to False if iteration analysis requires measurement data,
    # default True
    waitForMeasurements = Bool(default=True)

    # Set to True to allow multi-threading on this analysis.  Only do this if
    # you do NOT depend on the results of this analysis later.
    # Default is False.
    queueAfterIteration = Bool()
    # Set to True to skip iterations when slow.
    # Applies only to multi-threading.  Raw data can still be used in
    # post-experiment.  Default is False.
    dropIterationIfSlow = Bool()

    # dependencies of analysis to wait to finish before continuing
    measurementDependencies = Member()
    # things that depend on this analysis, filled automatically
    measurementDependents = Member()
    # holds the analysis' last completed iteration and measurement numbers as
    # a tuple (iter, meas)
    analysisStatus = Member()

    # internal variables, user should not modify
    measurementProcessing = Bool()
    iterationProcessing = Bool()
    measurementQueue = Member()
    measurementQueueEmpty = Bool()
    iterationQueue = []

    def __init__(self, name, experiment, description=''):  # subclassing from Prop provides save/load mechanisms
        super(Analysis, self).__init__(name, experiment, description)
        self.properties += [
            'dropMeasurementIfSlow', 'dropIterationIfSlow', 'enable'
        ]
        self.measurementDependencies = []
        self.measurementDependents = []
        self.measurementQueue = []
        # set up the analysis thread
        self.measurementThread = threading.Thread(
            target=self.measurementProcessLoop,
            name=self.name + '_meas_analysis'
        )
        self.measurementThread.daemon = True
        self.measurementProcessing = False
        self.measurementQueueEmpty = True

    def preExperiment(self, experimentResults):
        """Performs experiment initialization tasks.

        This is called before an experiment.
        The parameter experimentResults is a reference to the HDF5 file for
        this experiment. Subclass this to prepare the analysis appropriately.
        """
        # reset the analysis status tracker
        self.analysisStatus = (0, -1)
        # begin the measurement analysis thread if indicated
        if self.queueAfterMeasurement:
            self.measurementProcessing = True
            self.measurementQueueEmpty = False
            if self.measurementThread and self.measurementThread.is_alive():
                # send event to thread
                self.restart.set()
                self.restart.clear()
            else:
                self.restart = threading.Event()
                self.measurementThread.start()
                # append the wake event obj to the parent analyses
                for dep in self.measurementDependencies:
                    dep.measurementDependents.append(self.restart)

    def preIteration(self, iterationResults, experimentResults):
        """This is called before an iteration.
        The parameter experimentResults is a reference to the HDF5 file for this experiment.
        The parameter iterationResults is a reference to the HDF5 node for this coming iteration.
        Subclass this to prepare the analysis appropriately.
        """
        pass

    def postMeasurement(self, callback, measurementResults, iterationResults, experimentResults):
        """Processes post-measurement analysis if defined.

        Results is a tuple of:
        (measurementResult, iterationResult, experimentResult)
        references to HDF5 nodes for this measurement.
        """

        m_data = [
            self.analyzeMeasurement,        # function pointer
            (measurementResults, iterationResults, experimentResults),  # args
            (self.experiment.iteration, self.experiment.measurement),  # status
            self.name,
            callback        # callback function
        ]
        # see if we can thread this analysis
        if self.queueAfterMeasurement:
            # if we can't tolerate tardiness then drop the measurement with a
            # warning
            if self.measurementProcessing and self.dropMeasurementIfSlow:
                msg = '`{}` dropped during i:m `{}:{}` due to tardiness'
                logger.warning(msg.format(self.name, *m_data[2]))
                # increment the status I guess, anything that depends on it
                # better check that the data is present
                self.analysisStatus = m_data[2]

            else:
                # otherwise queue it up
                self.measurementQueue.append(m_data)

        else:
            result = self.analyzeMeasurement(*m_data[1])
            # update the analysis status
            self.analysisStatus = m_data[2]
            callback(result)

    def measurementProcessLoop(self):
        while True:  # run forever
            while self.measurementProcessing or len(self.measurementQueue) > 0:
                if len(self.measurementQueue) > 0:
                    self.measurementQueueEmpty = False
                    # process the oldest element
                    m_data = self.measurementQueue.pop(0)
                    for dep in self.measurementDependencies:
                        msg = '`{}` waiting for dep: `{}``'
                        logger.debug(msg.format(self.name, dep.name))
                        self.wait_for_dependency(dep, m_data[2])
                        logger.debug('dep: `{}` satisfied'.format(dep.name))
                    msg = '`{}` processing data from {}:{} (iter:meas)'
                    logger.debug(msg.format(self.name, *m_data[2]))

                    result = 0
                    try:
                        # use the function pointer that was stored in the list
                        result = m_data[0](*m_data[1])
                    except:
                        msg = (
                            'Measurement analysis thread encountered an error'
                            ' on analysis `{}` at `{}:{}`.'
                        ).format(self.name, *m_data[2])
                        logger.exception(msg)

                    msg = (
                        'Measurement analysis thread finished'
                        ' analysis `{}` at `{}:{}`.'
                    ).format(self.name, *m_data[2])
                    logger.debug(msg)
                    self.analysisStatus = m_data[2]

                    # fire threading wake events for sleeping analyses
                    for a in self.measurementDependents:
                        a.set()
                        a.clear()

                    # run the callback function to increment counter
                    m_data[4](result)
                else:
                    self.measurementQueueEmpty = True
                    time.sleep(0.01)
            self.measurementQueueEmpty = True
            logger.debug('Analysis thread finished. Entering wait state.')
            self.restart.wait()
            logger.debug('Restarting analysis thread.')

    def wait_for_dependency(self, dep, status):
        """Waits until dep reaches the status tuple (iter, meas).

        Used to synchronize between analysis threads.
        """
        (iter, meas) = status
        # synchronize iteration
        while (dep.analysisStatus[0] < iter) or (dep.analysisStatus[1] < meas):
            # wait until woken up by dependent analysis
            self.restart.wait()

    def analyzeMeasurement(self, measurementResults, iterationResults, experimentResults):
        """This is called after each measurement.

        The parameters
        (measurementResults, iterationResults, experimentResults)
        reference the HDF5 nodes for this measurement.
        Subclass this to update the analysis appropriately.
        """
        pass

    def postIteration(self, iterationResults, experimentResults):
        # block while any threaded measurements for this analysis finish
        if self.waitForMeasurements:
            while (not self.measurementQueueEmpty):
                msg = "waiting for `{}`".format(self.name)
                logger.info(msg)
                # TODO: add timeout

                # with no sleep the standard threading library will not allow
                # the threaded application to get processor time for a while
                # TODO: switch to an actual threading library like
                # multiprocessing
                time.sleep(0.1)

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
        """Analyzes all measurements in an iteration.

        This is called after each iteration.
        The parameters (iterationResults, experimentResults) reference the HDF5
        nodes for this iteration. Subclass this to update the analysis
        appropriately.
        """
        pass

    def postExperiment(self, experimentResults):
        # no queueing, must do post experiment processing at this time
        # block while any threaded iterations finish
        while self.iterationProcessing:
            # TODO: add timeout

            # with no sleep the standard threading library will not allow
            # the threaded application to get processor time for a while
            # TODO: switch to an actual threading library like
            # multiprocessing

            time.sleep(0.01)
        # signal to analysis thread to stop
        self.measurementProcessing = False
        # wait for measurements to finish before finalizing experiment
        while not self.measurementQueueEmpty:
            time.sleep(0.01)
        self.analyzeExperiment(experimentResults)

    def analyzeExperiment(self, experimentResults):
        """This is called at the end of the experiment.
        The parameter experimentResults is a reference to the HDF5 file for the
        experiment. Subclass this to update the analysis appropriately.
        """
        pass

    def finalize(self, hdf5):
        """To be run after all optimization loops are complete, so as to close
        files and such.
        """
        pass


class AnalysisWithFigure(Analysis):

    #matplotlib figures
    figure = Typed(Figure)
    backFigure = Typed(Figure)
    figure1 = Typed(Figure)
    figure2 = Typed(Figure)
    draw_fig = Bool(False) # do not draw the figure unless told to

    def __init__(self, name, experiment, description=''):
        super(AnalysisWithFigure, self).__init__(name, experiment, description)

        #set up the matplotlib figures
        self.figure1 = Figure()
        self.figure2 = Figure()
        self.backFigure = self.figure2
        self.figure = self.figure1

        self.properties += ['draw_fig']

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


class ROIAnalysis(AnalysisWithFigure):
    """Parent class for analyses that depend on the number of ROIs"""
    camera = Member()

    def set_rois(self):
        """This function is called following the normal fromHDF5 call and
        should be used to re-initialize anything that depends on the number
        of ROIs.

        The function should reference self.experiment.ROI_XXXXX to get the
        updated number of ROIs.
        """
        raise NotImplementedError

    def fromHDF5(self, hdf):
        """Overrides fromHDF5 to call set_rois following the read"""
        super(ROIAnalysis, self).fromHDF5(hdf)
        self.set_rois()

    def find_camera(self):
        """Find camera instrument object in experiment properties tree."""
        # get the property tree path to the camera object from the config file
        prop_tree = self.experiment.Config.config.get('CAMERA', 'CameraObj').split(',')

        camera = self.experiment
        for lvl in prop_tree:
            camera = getattr(camera, lvl)

        # if camera is stored in a ListProp list then use the index function
        # to retreive it
        camera_idx = self.experiment.Config.config.getint('CAMERA', 'CameraIdx')
        if camera_idx >= 0:
            try:
                camera = camera[camera_idx]
            except ValueError:
                logger.warning(
                    'No camera found at index `%d` in camera list: `%s`. Disabling analysis',
                    camera_idx,
                    '.'.join(prop_tree)
                )
                self.enable = False

        self.camera = camera

    def preExperiment(self, experimentResults):
        self.set_rois()
        super(ROIAnalysis, self).preExperiment(experimentResults)

class TextAnalysis(Analysis):
    #Text output that can be updated back to the GUI
    text = Str()

    def __init__(self, name, experiment, description=''):
        super(TextAnalysis, self).__init__(name, experiment, description)
        self.properties += ['text']

    def analyzeMeasurement(self, measurementResults, iterationResults, experimentResults):
        try:
            text = 'iteration {} measurement {}'.format(iterationResults.attrs['iteration'],
                                                              measurementResults.name.split('/')[-1])
            if 'data/Hamamatsu/temperature' in measurementResults:
                text += '\nCamera temperature: {} C'.format(measurementResults['data/Hamamatsu/temperature'].value)
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

class XYPlotAnalysis(AnalysisWithFigure):
    #### needs updating
    X=Member()
    Y=Member()

    def updateFigure(self):
        if self.draw_fig:
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
        if 'data/Andor_4522/shots' in measurementResults:
            self.Y = numpy.append(self.Y,numpy.sum(measurementResults['data/Andor_4522/shots/0']))
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
    data_path = Member()

    def __init__(self, experiment):
        super(ShotsBrowserAnalysis, self).__init__(
            'ShotsBrowser',
            experiment,
            'Shows a particular shot from the experiment'
        )
        self.data_path = 'data/' + self.experiment.Config.config.get('CAMERA', 'DataGroup') + '/shots'
        self.properties += ['measurement', 'shot', 'showROIs']

    def preExperiment(self, experimentResults):
        # call therading setup code
        super(ShotsBrowserAnalysis, self).preExperiment(experimentResults)
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
            # find the first matching iteration
            m = str(self.measurement)
            s = str(self.shot)
            if 'iterations' in self.experimentResults:
                for i in self.experimentResults['iterations'].itervalues():
                    # find the first iteration that matches all the selected
                    # ivar indices
                    if numpy.all(i.attrs['ivarIndex'] == self.selection):
                        try:
                            path = 'measurements/{}' + self.data_path + '{}'
                            self.array = i[path.format(m, s)]
                            self.updateFigure()
                        except Exception as e:
                            logger.warning('Exception trying to plot measurement {}, shot {}, in analysis.ShotsBrowserAnalysis.load()\n{}\n'.format(m, s, e))
                            self.blankFigure()
                        break

    def blankFigure(self):
        fig=self.backFigure
        fig.clf()
        super(ShotsBrowserAnalysis,self).updateFigure()

    def updateFigure(self):
        if self.draw_fig:
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

class LoadingFilters(Analysis):
    """This analysis monitors the brightess in the regions of interest, to decide if an atom was loaded or not"""
    version = '2014.05.01'

    enable = Bool()
    text = Str()
    filter_expression = Str()
    filter_level = Int()
    valid = Bool(True)
    roi_source_path = Member()

    def __init__(self, name, experiment, description=''):
        super(LoadingFilters, self).__init__(name, experiment, description)
        self.properties += [
            'version', 'enable', 'filter_expression', 'filter_level'
        ]
        # threading stuff
        self.queueAfterMeasurement = True
        self.measurementDependencies += [self.experiment.thresholdROIAnalysis]
        self.roi_source_path = self.experiment.thresholdROIAnalysis.meas_analysis_path

    def analyzeMeasurement(self, measurementResults, iterationResults, experimentResults):
        text = 'none'
        if self.enable:
            text = 'okay'
            if self.filter_expression != '':
                if (self.roi_source_path in measurementResults):

                    # evaluate the boolean expression, with the squareROIsums
                    # as 't' in the namespace. This will overwrite any previous
                    # value, so we make a copy of the dictionary
                    vars = self.experiment.vars.copy()
                    # choose only first sub-measurement to test
                    vars['t'] = measurementResults[self.roi_source_path][0]
                    value, valid = cs_evaluate.evalWithDict(self.filter_expression, varDict=vars)
                    if not valid:
                        # raise an error
                        text = 'Failed to evaluate loading filter: {}:\n'.format(self.filter_expression)
                        logger.error(text)
                        self.set_gui({'text': text,
                                      'valid': False})
                        raise PauseError
                    elif not ((value == True) or (value == False)):
                        # Enforce that the expression must evaluate to a bool
                        text = 'Loading filter must be True or False, but it evaluated to: {}\nfor expression: {}:\n'.format(value, self.filter_expression)
                        logger.error(text)
                        self.set_gui({'text': text,
                                      'valid': False})
                        raise PauseError
                    else:
                        # eval worked, save value
                        measurementResults['analysis/loading_filter'] = value
                        if not value:
                            # Measurement did not pass filter (We do not need
                            # to take special action if the filter passes.)
                            text = 'Loading filter failed.'
                            self.set_gui({'text': text,
                                          'valid': True})
                            # User chooses whether or not to delete data.
                            # max takes care of ComboBox returning -1 for no
                            # selection
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


class MeasurementsGraph(AnalysisWithFigure):
    """Plots a region of interest sum after every measurement"""
    enable = Bool()
    data = Member()
    update_lock = Bool(False)
    list_of_what_to_plot = Str()
    ROI_source = Member()

    def __init__(self, name, experiment, description=''):
        super(MeasurementsGraph, self).__init__(name, experiment, description)
        self.properties += ['enable', 'list_of_what_to_plot', 'ROI_source']
        self.data = None
        # point analysis at the roi sum source
        self.ROI_source = getattr(
            self.experiment,
            self.experiment.Config.config.get('CAMERA', 'ThresholdROISource')
        )
        self.queueAfterMeasurement = True
        self.measurementDependencies += [self.ROI_source]

    def analyzeMeasurement(self, measurementResults, iterationResults, experimentResults):
        if self.enable:
            # every measurement, update a big array of all the ROI sums, then
            # histogram only the requested shot/site
            d = measurementResults[self.ROI_source.meas_analysis_path]
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
        if self.draw_fig:
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
                                    data = self.data[:, i[0], 0, i[1]] #hardcoded '0' is to select the submeasurement No. 0
                            except:
                                logger.warning('Trying to plot data that does not exist in MeasurementsGraph: shot {} roi {}'.format(i[0], i[1]))
                                continue
                                label = '({},{})'.format(i[0], 0, i[1])
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
    update_every_measurement = Bool()

    def __init__(self, name, experiment, description=''):
        super(IterationsGraph, self).__init__(name, experiment, description)
        self.properties += [
            'enable', 'list_of_what_to_plot', 'draw_connecting_lines',
            'draw_error_bars', 'ymin', 'ymax', 'update_every_measurement'
        ]
        self.queueAfterMeasurement = True
        self.measurementDependencies += [
            self.experiment.squareROIAnalysis, self.experiment.loading_filters
        ]

    def preExperiment(self, experimentResults):
        # call therading setup code
        super(IterationsGraph, self).preExperiment(experimentResults)
        # erase the old data at the start of the experiment
        self.mean = None
        self.sigma = None

    def preIteration(self, iterationResults, experimentResults):
        self.current_iteration_data = None

    def analyzeMeasurement(self, measurementResults, iterationResults, experimentResults):
        # Check to see if we want to do anything with this data, based on the
        # LoadingFilters.
        # Careful here to use .value, otherwise it will always be True if the
        # dataset exists.
        if self.enable:  # and self.update_every_measurement:
            if (not self.add_only_filtered_data) or (('analysis/loading_filter' in measurementResults) and measurementResults['analysis/loading_filter'].value):

                d = numpy.array([measurementResults['analysis/squareROIsums']])

                if self.current_iteration_data is None:
                    # on first measurement of an iteration, start anew
                    new_iteration = True
                    self.current_iteration_data = d
                else:
                    # else append
                    new_iteration = False
                    self.current_iteration_data = numpy.append(self.current_iteration_data, d, axis=0)

                # average across measurements
                # keepdims gives result with size (1 x shots X rois)
                mean = numpy.mean(self.current_iteration_data, axis=0, keepdims=True)
                # find standard deviation of the mean
                sigma = numpy.std(self.current_iteration_data, axis=0, keepdims=True)/numpy.sqrt(len(self.current_iteration_data))

                if self.mean is None:
                    # on first iteration start anew
                    self.mean = mean
                    self.sigma = sigma
                else:
                    if new_iteration:
                        # append
                        self.mean = numpy.append(self.mean, mean, axis=0)
                        self.sigma = numpy.append(self.sigma, sigma, axis=0)
                    else:
                        # replace last entry
                        self.mean[-1] = mean
                        self.sigma[-1] = sigma
                self.updateFigure()

    # TODO: this needs to be made to update at the iteration update
    """
        def analyzeIteration(self, iterationResults, experimentResults):
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
    """

    @observe('list_of_what_to_plot', 'draw_connecting_lines', 'ymin', 'ymax')
    def reload(self, change):
        self.updateFigure()

    def updateFigure(self):
        if self.draw_fig:
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
                                    mean = self.mean[:, i[0], 0, i[1]] # i[0] : shot, i[1]: submeasurement? , i[2] : roi
                                    sigma = self.sigma[:, i[0], 0, i[1]]
                            except:
                                logger.warning('Trying to plot data that does not exist in IterationsGraph: shot {} roi {}'.format(i[0], i[1]))
                                continue
                            label = '(shot:{},roi:{})'.format(i[0],i[1])
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


class Ramsey(AnalysisWithFigure):
    """Plots the average of a region of interest sum for an iteration, after each iteration.  Can be used with the
    optimizer with the cost function:
    # ramsey experiment optimizer cost function:
    self.yi = -experimentResults['analysis/Ramsey/frequency']
    """

    enable = Bool()
    draw_error_bars = Bool()

    roi = Int()
    time_variable_name = Str()
    amplitude_guess = Float()
    frequency_guess = Float()
    offset_guess = Float()
    decay_guess = Float()

    y = Member()
    t = Member()
    sigma = Member()
    fitParams = Member()

    amplitude = Float()
    frequency = Float()
    offset = Float()
    decay = Float()

    def __init__(self, name, experiment, description=''):
        super(Ramsey, self).__init__(name, experiment, description)
        self.properties += [
            'enable', 'draw_error_bars', 'roi', 'time_variable_name',
            'amplitude_guess', 'frequency_guess', 'offset_guess', 'decay_guess'
        ]

    def fitFunc(self, t, amplitude, frequency, offset, decay):
        return amplitude*numpy.cos(2*numpy.pi*frequency*t)*numpy.exp(t/decay)+offset

    def analyzeExperiment(self, experimentResults):
        """For all iterations in this experiment, calculate the retention fraction.  This should result in a cosine
        curve.  Fit a cosine to this, and store the amplitude and frequency."""

        if self.enable:
            num_iterations = len(experimentResults)
            self.y = numpy.zeros(num_iterations, dtype=numpy.float64)
            self.t = numpy.zeros(num_iterations, dtype=numpy.float64)
            self.sigma = numpy.zeros(num_iterations, dtype=numpy.float64)
            for i in xrange(num_iterations):
                # check to see if retention analysis was done
                if 'analysis/loading_retention' not in experimentResults['iterations/{}'.format(i)]:
                    logger.warning('Ramsey analysis: Retention data not present in iteration {}'.format(i))
                    raise PauseError
                # get retention data from the retention analysis
                self.y[i] = experimentResults['iterations/{}/analysis/loading_retention/retention'.format(i)].value
                self.sigma[i] = experimentResults['iterations/{}/analysis/loading_retention/retention_sigma'.format(i)].value
                self.t[i] = experimentResults['iterations/'+str(i)+'/variables/'+self.time_variable_name].value

            # now that we have retention vs. time, do a curve fit
            initial_guess = (self.amplitude_guess, self.frequency_guess, self.offset_guess, self.decay_guess)

            try:
                self.fitParams, fitCovariances = curve_fit(self.fitFunc, self.t, self.y, p0=initial_guess)
            except Exception as e:
                # note the error, set the amplitude to 0 and move on:
                logger.warning("Exception in Ramsey.analyzeExperiment:\n{}\n".format(e))
                # set the results to zero
                self.fitParams = (0, 0, 0, 0)
                fitCovariances = numpy.zeros((4, 4))

            experimentResults['analysis/Ramsey/amplitude'] = self.fitParams[0]
            experimentResults['analysis/Ramsey/frequency'] = self.fitParams[1]
            experimentResults['analysis/Ramsey/offset'] = self.fitParams[2]
            experimentResults['analysis/Ramsey/decay'] = self.fitParams[3]
            experimentResults['analysis/Ramsey/covar'] = fitCovariances
            self.set_gui({'amplitude': self.fitParams[0], 'frequency': self.fitParams[1], 'offset': self.fitParams[2], 'decay': self.fitParams[3]})
            self.updateFigure()

    def optimizer_update_guess(self):
        if self.enable:
            self.set_gui({'amplitude_guess': self.fitParams[0], 'frequency_guess': self.fitParams[1], 'offset_guess': self.fitParams[2], 'decay_guess': self.fitParams[3]})

    def updateFigure(self):
        if self.draw_fig:
            try:
                fig = self.backFigure
                fig.clf()
                ax = fig.add_subplot(111)

                # plot the data points
                linestyle = 'o'
                if self.draw_error_bars:
                    ax.errorbar(self.t, self.y, yerr=self.sigma, fmt=linestyle)
                else:
                    ax.plot(self.t, self.y, linestyle)
                    # adjust the limits so that the data isn't right on the edge of
                    # the graph
                span = numpy.amax(self.t) - numpy.amin(self.t)
                xmin = numpy.amin(self.t)-.02*span
                xmax = numpy.amax(self.t)+.02*span
                ax.set_xlim(xmin, xmax)

                # draw the fit
                t = numpy.linspace(xmin, xmax, 200)
                ax.plot(t, self.fitFunc(t, *self.fitParams), '-')
                super(Ramsey, self).updateFigure()
            except Exception as e:
                logger.warning('Problem in Ramsey.updateFigure()\n{}\n{}\n'.format(e, traceback.format_exc()))
