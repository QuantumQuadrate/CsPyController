'''This file contains all the machinery to save 2013 style files (individual PNGs and text files with variable info).  This is done in the structure of an analysis routine.'''

from analysis import Analysis
import png, itertools #for PyPNG support

class Save2013Analysis(Analysis):
    updateBeforeExperiment=Bool(True)
    updateAfterMeasurement=Bool(True)
    updateAfterIteration=Bool(True)
    updateAfterExperiment=Bool(True)
    
    iteration=Member()
    measurement=Member()
    
    iterationPath=Str()
    measurementPath=Str()

    
    def __init__(self,experiment=None):
        self.iteration=None
        self.measurement=None
        super(Save2013Analysis,self).__init__('save2013Analysis',name,experiment,'save 2013 style files')
    
    def setupExperiment(self,experimentResults):
        #save "Processed Data.txt"
        #processed data just holds ivar names - save at beginning (or end in analysis?)
        #Row 1: tab separated ivar names
        #Row 2 onwards: supposed to be 2D array of variable values, but was never actually functional.  don't include
        with open('Processed Data.txt', 'w') as f:
            f.write('\t'.join(experimentResults.ivarNames)+'\n')
        
        #save All Signal.txt
        #Lists number of steps for each ivar.  "Formulas" was never operational.
        #a Iterations:	1	b Iterations:	1	l0 Iterations:	11	Formulas:	0
        with open('All Signal.txt', 'w') as f:
            f.write('\t'.join(['{} Iterations:\t{}'.format(name,steps) for name,steps in zip(experimentResults.ivarNames,experimentResults.ivarSteps)]))
    
    def analyzeMeasurement(self,measurementResults,iterationResults,experimentResults):
        #check if we are in a new iteration
        if iterationResults.=self.experiment.iteration:
            #update iteration
            self.iteration=self.experiment.iteration
            self.create_iteration_directory()
        #create a new directory to hold measurement images
        self.create_measurement_directory()
    
    def analyzeIteration(self,iterationResults,experimentResults):
    
    def analyzeExperiment(self,experimentResults):
    
    def create_measurement_directory(self):
        if exp.saveData and exp.save2013styleFiles:
            #check that it doesn't exist first
            self.measurementPath=os.path.join(self.iterationPath,'measurement'+str(self.measurement))
            if not os.path.isdir(measurementPath):
                #create the directory
                #use os.makedirs instead of os.mkdir to create the intermediate directory if it does not exist
                os.makedirs(self.measurementPath)

                def create_iteration_directory(self):
        exp=self.experiment
        if exp.saveData and exp.save2013styleFiles:
            #check that it doesn't exist first
            exp.iterationPath=os.path.join(exp.path,'iteration'+str(exp.iteration))
            if not os.path.isdir(iterationPath):
                #create the directory
                #use os.makedirs instead of os.mkdir to create the intermediate directory if it does not exist
                os.makedirs(self.iterationPath)
    
    def savePNG(self,array,filename):
        #L indicates monochrome, ;16 indicates 16-bit
        png.from_array(array,'L;16',info={'bitdepth':16}).save(filename)
    
    def readPNG(self,filename):
        a=png.Reader(filename=filename)
        b=a.read()
        c=numpy.vstack(itertools.imap(numpy.uint16,b[2]))
        return c