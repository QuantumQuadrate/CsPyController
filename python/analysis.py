from atom.api import Bool, Typed, Str, Member
from instrument_property import Prop

#MPL plotting
from matplotlib.figure import Figure
from enaml.application import deferred_call

import threading, numpy, logging
logger = logging.getLogger(__name__)

class Analysis(Prop):
    '''This is the parent class for all data analyses.  New analyses should subclass off this,
    and redefine at least one of setupExperiment(), postMeasurement(), postIteration() or postExperiment(),
    and enable those methods with either updateBeforeExperiment, updateAfterMeasurement, updateAfterIteration or updateAfterExperiment.
    An analysis can return a success code after each of these methods, which can be used to filter results.  The highest returned code dominates others:
        0 or None: good measurement, increment measurement total
        1: soft fail, continue with other analyses, but do not increment measurement total
        2: med fail, continue with other analyses, do not increment measurement total, and delete measurement data after all analyses
        3: hard fail, do not continue with other analyses, do not increment measurement total, delete measurement data'''
    
    updateBeforeExperiment=Bool() #Set to True to enable pre-measurement analysis.  Default is False.
    updateAfterMeasurement=Bool() #Set to True to enable post-measurement analysis.  Default is False.
    dropMeasurementIfSlow=Bool() #Set to True to skip measurements when slow.  Data can still be used post-iteration and post-experiment. Default is False.
    updateAfterIteration=Bool() #Set to True to enable post-iteration analysis.  Default is False.
    dropIterationIfSlow=Bool() #Set to True to skip iterations when slow.  Data can still be used in post-experiment.  Default is False.
    updateAfterExperiment=Bool() #Set to True to enable post-experiment analysis.  Default is False.
    
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
        if self.updateBeforeExperiment:
            self.setupExperiment(experimentResults)
    
    def setupExperiment(self,experimentResults):
        '''This is called before an experiment.
        The parameter experimentResults is a reference to the HDF5 file for this experiment.
        Subclass this to update the analysis appropriately.'''
        return 0
    
    def postMeasurement(self,measurementResults,iterationResults,experimentResults):
        '''results is a tuple of (measurementResult,iterationResult,experimentResult) references to HDF5 nodes for this measurement'''
        if self.updateAfterMeasurement:
            if not self.measurementProcessing: #check to see if a processing queue is already going
                self.measurementProcessing=True
                self.measurementQueue.append((measurementResults,iterationResults,experimentResults))
                threading.Thread(target=self.measurementProcessLoop).start()
            elif not self.dropMeasurementIfSlow: #if a queue is already going, add to it, unless we can't tolerate being behind
                self.measurementQueue.append((measurementResults,iterationResults,experimentResults))
    
    def measurementProcessLoop(self):
        while len(self.measurementQueue)>0:
            self.analyzeMeasurement(*self.measurementQueue.pop(0)) #process the oldest element
        self.measurementProcessing=False
    
    def analyzeMeasurement(self,measurementResults,iterationResults,experimentResults):
        '''This is called after each measurement.
        The parameter results is a tuple of (measurementResult,iterationResult,experimentResult) references to HDF5 nodes for this measurement.
        Subclass this to update the analysis appropriately.'''
        return 0
    
    def postIteration(self,iterationResults,experimentResults):
        if self.updateAfterIteration:
            if not self.iterationProcessing: #check to see if a processing queue is already going
                self.iterationProcessing=True
                self.iterationQueue.append((iterationResults,experimentResults))
                threading.Thread(target=self.iterationProcessLoop).start()
            elif not self.dropIterationIfSlow: #if a queue is already going, add to it, unless we can't tolerate being behind
                self.iterationQueue.append((iterationResults,experimentResults))
    
    def iterationProcessLoop(self):
        while len(self.iterationQueue)>0:
            self.analyzeIteration(*self.iterationQueue.pop(0)) #process the oldest element
        self.iterationProcessing=False
    
    def analyzeIteration(self,iterationResults,experimentResults):
        '''This is called after each iteration.
        The parameter results is a tuple of (iterationResult,experimentResult) references to HDF5 nodes for this measurement.
        Subclass this to update the analysis appropriately.'''
        return 0
    
    def postExperiment(self,experimentResults):
        if self.updateAfterExperiment:
            self.analyzeExperiment(experimentResults)
    
    def analyzeExperiment(self,experimentResults):
        '''This is called at the end of the experiment.
        The parameter experimentResults is a reference to the HDF5 file for the experiment.
        Subclass this to update the analysis appropriately.'''
        return 0

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
    updateAfterMeasurement=Bool(True)

    def analyzeMeasurement(self,measurementResults,iterationResults,experimentResults):
        try:
            self.text='iteration {} measurement {}\n{}'.format(iterationResults.attrs['iteration'],measurementResults.name.split('/')[-1],iterationResults.attrs['variableReportStr'])
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
            
            self.text+='\n\nno image data'
        
    
    def updateFigure(self):
        fig=self.backFigure
        fig.clf()
        ax=fig.add_subplot(111)
        ax.matshow(numpy.array(self.data[...]))
        ax.set_title('shot 0')
        #fig.tight_layout()
        super(ImagePlotAnalysis,self).updateFigure()

class XYPlotAnalysis(AnalysisWithFigure):
    #needs updating
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
    #needs updating
    updateAfterMeasurement=Bool(True)

    '''This analysis plots the sum of the whole camera image every measurement.'''
    def analyzeMeasurement(self,measurementResults,iterationResults,experimentResults):
        self.Y=numpy.append(self.Y,numpy.sum(measurementResults['data/Hamamatsu/shots/0']))
        self.X=numpy.arange(len(self.Y))
        self.updateFigure()

class ShotsBrowserAnalysis(Analysis):
    updateBeforeExperiment=Bool()
    
    #matplotlib figures
    figure=Typed(Figure)
    backFigure=Typed(Figure)
    figure1=Typed(Figure)
    figure2=Typed(Figure)
    
    def __init__(self,experiment):
        self.experiment=experiment
    
    def setupExperiment(self,experimentResults):
        pass

    def load(self,ivarIndices):
        self.ivar_indices=numpy.zeros(len(experiment.independentVariables))
        
        #make a list of candidate pictures
        candidates=[]
        if 'iterations' in f:
            for i in experimentResults['iterations'].itervalues():
                if 'measurements' in i:
                    for m in i['measurements'].itervalues():
                        if 'data/Hamamatsu/shots' in m:
                            for s in m['data/Hamamatsu/shots'].itervalues():
                                sumlist.append(s.value)
        sumarray=array(sumlist)
        average_of_images=mean(sumarray,axis=0)
        self.savePNG(average_of_images,os.path.join('images','average_of_all_images_in_experiment.png'))

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
