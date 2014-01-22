from atom.api import Bool, Typed, Str, Member
from instrument_property import Prop

#chaco plotting
#from enthought.enable.api import Component
#from traits.api import Array

#MPL plotting
from matplotlib.figure import Figure
from PyQt4 import QtCore

import threading, numpy, logging
logger = logging.getLogger(__name__)

class Analysis(Prop):
    '''This is the parent class for all data analyses.  New analyses should subclass off this,
    and redefine at least one of postMeasurement(), postIteration() or postExperiment().'''
    
    updateAfterMeasurement=Bool()
    dropMeasurementIfSlow=Bool()
    updateAfterIteration=Bool()
    dropIterationIfSlow=Bool()
    updateAfterExperiment=Bool()
    measurementProcessing=Bool()
    iterationProcessing=Bool()
    experimentProcessing=Bool()
    measurementQueue=[]
    iterationQueue=[]
    text=Str()
    
    def __init__(self,name,experiment,description=''): #subclassing from Prop provides save/load mechanisms
        super(Analysis,self).__init__(name,experiment,description)
        self.properties+=['updateAfterMeasurement,dropMeasurementIfSlow,updateAfterIteration,dropIterationIfSlow,updateAfterExperiment,text']
    
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
        pass
    
    def postIteration(self,iterationResults,experimentResults):
        if self.updateAfterIteration:
            if not self.iterationProcessing: #check to see if a processing queue is already going
                self.iterationProcessing=True
                self.iterationQueue.append((iterationResults,experimentResults))
                threading.Thread(target=self.iterationProcessLoop).start()
            elif not self.dropIterationIfSlow: #if a queue is already going, add to it, unless we can't tolerate being behind
                self.iterationQueue.append((iterationResults,experimentResults))
    
    def iterationProcessLoop(self):
        while len(iterationQueue)>0:
            analyzeIteration(*iterationQueue.pop(0)) #process the oldest element
        iterationProcessing=False
    
    def analyzeIteration(self,iterationResults,experimentResults):
        '''This is called after each iteration.
        The parameter results is a tuple of (iterationResult,experimentResult) references to HDF5 nodes for this measurement.
        Subclass this to update the analysis appropriately.'''
        pass
    
    def postExperiment(self,experimentResults):
        if self.updateAfterExperiment:
            postExperiment(experimentResults)
    
    def analyzeExperiment(self,experimentResults):
        '''This is called at the end of the experiment.
        The parameter results is a tuple of (measurementResult,iterationResult,experimentResult) references to HDF5 nodes for this measurement.
        Subclass this to update the analysis appropriately.'''
        pass

class signal_holder(QtCore.QObject):
    signal = QtCore.pyqtSignal()

class AnalysisWithFigure(Analysis):
    
    #matplotlib figures
    figure=Typed(Figure)
    backFigure=Typed(Figure)
    figure1=Typed(Figure)
    figure2=Typed(Figure)
    
    #for refreshing the plot
    signal_holder = Typed(signal_holder)
    
    def __init__(self,name,experiment,description=''):
        super(AnalysisWithFigure,self).__init__(name,experiment,description)
        
        #set up the signal that allows to plot update to occur in the GUI thread
        self.signal_holder=signal_holder()
        self.signal_holder.signal.connect(self.swapFigures)
        
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
        self.signal_holder.signal.emit()

class ImagePlotAnalysis(AnalysisWithFigure):
    data=Member()
    updateAfterMeasurement=Bool(True)

    def analyzeMeasurement(self,measurementResults,iterationResults,experimentResults):
        try:
            self.text='iteration {} measurement {}\n{}'.format(iterationResults.attrs['iteration'],measurementResults.name.split('/')[-1],iterationResults.attrs['variableReportStr'])
        except KeyError as e:
            logger.warning('HDF5 data does not exist'+str(e))
            return
        try:
            self.data=measurementResults['data/Hamamatsu/shots/0']
        except KeyError as e:
            logger.warning('HDF5 data does not exist'+str(e))
            return
        self.updateFigure()
    
    def updateFigure(self):
        fig=self.backFigure
        fig.clf()
        ax=fig.add_subplot(111)
        ax.matshow(numpy.array(self.data[...]))
        ax.set_title('shot 0')
        fig.tight_layout()
        super(ImagePlotAnalysis,self).updateFigure()

class XYPlotAnalysis(AnalysisWithFigure):
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
    updateAfterMeasurement=Bool(True)

    '''This analysis plots the sum of the whole camera image every measurement.'''
    def analyzeMeasurement(self,measurementResults,iterationResults,experimentResults):
        self.Y=numpy.append(self.Y,numpy.sum(measurementResults['data/Hamamatsu/shots/0']))
        self.X=numpy.arange(len(self.Y))
        self.updateFigure()

