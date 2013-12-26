from traits.api import Bool, Instance, Array
from experiment import result
import threading
from instrumentProperty import Prop
from enthought.enable.api import Component
import numpy, logging
logger = logging.getLogger(__name__)

def analysis(Prop):
    '''This is the parent class for all data analyses.  New analyses should subclass off this,
    and redefine at least one of postMeasurement(), postIteration() or postExperiment().'''
    
    updateAfterMeasurement=Bool
    dropMeasurementIfSlow=Bool
    updateAfterIteration=Bool
    dropIterationIfSlow=Bool
    updateAfterExperiment=Bool
    measurementProcessing=Bool
    iterationProcessing=Bool
    experimentProcessing=Bool
    measurementQueue=[]
    iterationQueue=[]
    
    def __init__(self,name,experiment,description=''): #subclassing from Prop provides save/load mechanisms
        super(analysis,self).__init__(name,experiment,description)
        properties+=['updateAfterMeasurement,dropMeasurementIfSlow,updateAfterIteration,dropIterationIfSlow,updateAfterExperiment']
    
    def postMeasurement(self,result):
        if self.updateAfterMeasurement:
            if not measurementProcessing: #check to see if a processing queue is already going
                measurementProcessing=True
                measurementQueue.append(result)
                threading.Thread(target=self.measurementProcessLoop).start()
            elif not dropMeasurementIfSlow: #if a queue is already going, add to it, unless we can't tolerate being behind
                measurementQueue.append(result)
    
    def measurementProcessLoop(self,function):
        while len(measurementQueue)>0:
            analyzeMeasurement(measurementQueue.pop(0)) #process the oldest element
        measurementProcessing=False
    
    def analyzeMeasurement(self,result):
        '''This is called after each measurement.  The parameter result is a single experiment.result object.
        Subclass this to update the analysis appropriately.'''
        pass
    
    def postIteration(self,results):
        if self.updateAfterIteration:
            if not iterationProcessing: #check to see if a processing queue is already going
                iterationProcessing=True
                iterationQueue.append(results)
                threading.Thread(target=self.iterationProcessLoop).start()
            elif not dropIterationIfSlow: #if a queue is already going, add to it, unless we can't tolerate being behind
                iterationQueue.append(results)
    
    def iterationProcessLoop(self,function):
        while len(iterationQueue)>0:
            analyzeIteration(iterationQueue.pop(0)) #process the oldest element
        iterationProcessing=False
    
    def analyzeIteration(self,results):
        '''This is called after each iteration.  The parameter results is a list of experiment.result objects.
        Subclass this to update the analysis appropriately.'''
        pass
    
    def postExperiment(self,results):
        if self.updateAfterExperiment:
            postExperiment(results)
    
    def analyzeExperiment(self,results):
        '''This is called after each experiment.  The parameter result is a list of experiment.result objects'''
    
def XYAnalysis(analysis):
    X=Array
    Y=Array
    plot=Instance(Component)
    
    def __init__(self,name,experiment,description=''):
        super(YAnalysis,self).__init__(name,experiment,description)
        
        X=numpy.arange(2)
        Y=numpy.zeros(2)
        
        #create an empty plot
        self.plotdata = ArrayPlotData(x=X,y=Y)
        self.plot = Plot(self.plotdata)
        self.plot.plot(("x", "y"), type="line", color="blue")
        self.plot.title = self.description
        
    def _X_changed(self,old,new):
        self.plotdata.set_data("x",new)
        
    def _Y_changed(self,old,new):
        self.plotdata.set_data("y",new)
