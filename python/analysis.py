from atom.api import Bool, Typed, Str, Member, List, Int, observe
from instrument_property import Prop

#MPL plotting
from matplotlib.figure import Figure
from enaml.application import deferred_call

import threading, numpy, logging, traceback
logger = logging.getLogger(__name__)

from cs_errors import PauseError

class Analysis(Prop):
    '''This is the parent class for all data analyses.  New analyses should subclass off this,
    and redefine at least one of setupExperiment(), postMeasurement(), postIteration() or postExperiment().
    You can enable multi-threading of analyses using queueAfterMeasurement and queueAfterIteration, but only if those results are not needed for other things (filtering, other analyses, optimization).
    If multi-threading, you can also chose to dropMeasurementIfSlow or dropIterationIfSlow, which will not delete the data but will just not process it.
    An analysis can return a success code after analyzeMesurement, which can be used to filter results.  The highest returned code dominates others:
        0 or None: good measurement, increment measurement total
        1: soft fail, continue with other analyses, but do not increment measurement total
        2: med fail, continue with other analyses, do not increment measurement total, and delete measurement data after all analyses
        3: hard fail, do not continue with other analyses, do not increment measurement total, delete measurement data'''
    
    queueAfterMeasurement=Bool() #Set to True to allow multi-threading on this analysis.  Only do this if you are NOT filtering on this analysis, and if you do NOT depend on the results of this analysis later. Default is False.
    dropMeasurementIfSlow=Bool() #Set to True to skip measurements when slow.  Applies only to multi-threading.  Raw data can still be used post-iteration and post-experiment. Default is False.
    queueAfterIteration=Bool() #Set to True to allow multi-threading on this analysis.  Only do this if you do NOT depend on the results of this analysis later. Default is False.
    dropIterationIfSlow=Bool() #Set to True to skip iterations when slow.  Applies only to multi-threading.  Raw data can still be used in post-experiment.  Default is False.
    
    #internal variables, user should not modify
    measurementProcessing=Bool()
    iterationProcessing=Bool()
    measurementQueue=[]
    iterationQueue=[]
    
    #Text output that can be updated back to the GUI
    text=Str()
    
    def __init__(self,name,experiment,description=''): #subclassing from Prop provides save/load mechanisms
        super(Analysis,self).__init__(name,experiment,description)
        self.properties+=['updateAfterMeasurement,dropMeasurementIfSlow,updateAfterIteration,dropIterationIfSlow,updateAfterExperiment,text']
    
    def preExperiment(self,experimentResults):
        #no queueing, must complete this before experiment
        self.setupExperiment(experimentResults)
    
    def setupExperiment(self,experimentResults):
        '''This is called before an experiment.
        The parameter experimentResults is a reference to the HDF5 file for this experiment.
        Subclass this to update the analysis appropriately.'''
        return
    
    def postMeasurement(self,measurementResults,iterationResults,experimentResults):
        '''results is a tuple of (measurementResult,iterationResult,experimentResult) references to HDF5 nodes for this measurement'''
        if self.queueAfterMeasurement: #if self.updateAfterMeasurement:
            if not self.measurementProcessing: #check to see if a processing queue is already going
                self.measurementProcessing=True
                self.measurementQueue.append((measurementResults,iterationResults,experimentResults))
                threading.Thread(target=self.measurementProcessLoop).start()
            elif not self.dropMeasurementIfSlow: #if a queue is already going, add to it, unless we can't tolerate being behind
                self.measurementQueue.append((measurementResults,iterationResults,experimentResults))
            return
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
            return
        else:
            return self.analyzeIteration(iterationResults,experimentResults)
    
    def iterationProcessLoop(self):
        while len(self.iterationQueue)>0:
            self.analyzeIteration(*self.iterationQueue.pop(0)) #process the oldest element
        self.iterationProcessing=False
    
    def analyzeIteration(self,iterationResults,experimentResults):
        '''This is called after each iteration.
        The parameter results is a tuple of (iterationResult,experimentResult) references to HDF5 nodes for this measurement.
        Subclass this to update the analysis appropriately.'''
        return
    
    def postExperiment(self,experimentResults):
        #no queueing, must do post experiment processing at this time
        self.analyzeExperiment(experimentResults)
    
    def analyzeExperiment(self,experimentResults):
        '''This is called at the end of the experiment.
        The parameter experimentResults is a reference to the HDF5 file for the experiment.
        Subclass this to update the analysis appropriately.'''
        return

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

class ImagePlotAnalysis(AnalysisWithFigure):
    data=Member()
    
    def analyzeMeasurement(self,measurementResults,iterationResults,experimentResults):
        try:
            text='iteration {} measurement {}\n{}'.format(iterationResults.attrs['iteration'],measurementResults.name.split('/')[-1],iterationResults.attrs['variableReportStr'])
        except KeyError as e:
            logger.warning('HDF5 text does not exist in analysis.ImagePlotAnalysis.analyzeMeasurement()\n'+str(e))
            raise PauseError
        if ('data/Hamamatsu/shots/0' in measurementResults):
            try:
                self.data=measurementResults['data/Hamamatsu/shots/0']
            except KeyError as e:
                logger.warning('HDF5 data/Hamamatsu/shots/0 does not exist in analysis.ImagePlotAnalysis.analyzeMeasurement()\n'+str(e))
                raise PauseError
            self.updateFigure() #only update figure if image was loaded
        else:
            text+='\n\nno image data'
        deferred_call(setattr,self,'text',text)
    
    def updateFigure(self):
        fig=self.backFigure
        fig.clf()
        ax=fig.add_subplot(111)
        ax.matshow(numpy.array(self.data[...]))
        ax.set_title('shot 0')
        #fig.tight_layout()
        super(ImagePlotAnalysis,self).updateFigure()

class XYPlotAnalysis(AnalysisWithFigure):
    #### needs updating
    X=Member()
    Y=Member()
    
    def updateFigure(self):
        fig=self.backFigure
        fig.clf()
        ax=fig.add_subplot(111)
        if (self.X is not None) and (self.Y is not None):
            ax.plot(self.X,self.Y)
        super(ImagePlotAnalysis,self).updateFigure()

class SampleXYAnalysis(XYPlotAnalysis):
    #### needs updating
    
    '''This analysis plots the sum of the whole camera image every measurement.'''
    def analyzeMeasurement(self,measurementResults,iterationResults,experimentResults):
        self.Y=numpy.append(self.Y,numpy.sum(measurementResults['data/Hamamatsu/shots/0']))
        self.X=numpy.arange(len(self.Y))
        self.updateFigure()

class ShotsBrowserAnalysis(AnalysisWithFigure):
    
    ivarNames=List(default=[])
    ivarValueLists=List(default=[])
    selection=List(default=[])
    measurement=Int(0)
    shot=Int(0)
    array=Member()
    experimentResults=Member()
    
    def __init__(self,experiment):
        super(ShotsBrowserAnalysis,self).__init__('ShotsBrowser',experiment,'Shows a particular shot from the experiment')
    
    def setupExperiment(self,experimentResults):
        self.experimentResults=experimentResults
        self.ivarValueLists=[i for i in experimentResults.attrs['ivarValueLists']]
        self.selection=[0]*len(self.ivarValueLists)
        deferred_call(setattr,self,'ivarNames',[i for i in experimentResults.attrs['ivarNames']])
    
    def setIteration(self,ivarIndex,index):
        try:
            self.selection[ivarIndex]=index
        except Exception as e:
            logger.warning('Invalid ivarIndex in analysis.ShotsBrowserAnalysis.setSelection({},{})\n{}\n[]'.format(ivarIndex,index,e,traceback.format_exc()))
            raise PauseError
        self.load()
    
    @observe('measurement')
    def setMeasurement(self,change):
        self.load()
    
    @observe('shot')
    def setShot(self,change):
        self.load()
    
    def load(self):
        if self.experimentResults is not None:
            #find the first matching iteration
            m=str(self.measurement)
            s=str(self.shot)
            if 'iterations' in self.experimentResults:
                for i in self.experimentResults['iterations'].itervalues():
                    if numpy.all(i.attrs['ivarIndex']==self.selection):
                        try:
                            self.array=i['measurements/{}/data/Hamamatsu/shots/{}'.format(m,s)].value
                            self.updateFigure()
                        except Exception as e:
                            logger.warning('Exception trying to plot measurement {}, shot {}, in analysis.ShotsBrowserAnalysis.load()\n'.format(m,s))
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
        ax.matshow(self.array)
        super(ShotsBrowserAnalysis,self).updateFigure()
        #self.swapFigures()
        