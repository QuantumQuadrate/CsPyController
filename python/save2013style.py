'''This file contains all the machinery to save 2013 style files (individual PNGs and text files with variable info).  This is done in the structure of an analysis routine.'''

from cs_errors import PauseError, setupLog
logger=setupLog(__name__)

from analysis import Analysis
import os, numpy
import png, itertools #for PyPNG support
from atom.api import Bool, Member, Str

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
        super(Save2013Analysis,self).__init__('save2013Analysis',experiment,'save 2013 style files')
    
    def setupExperiment(self,experimentResults):
        if self.experiment.saveData and self.experiment.save2013styleFiles:
            
            #save "Processed Data.txt"
            #processed data just holds ivar names - save at beginning (or end in analysis?)
            #Row 1: tab separated ivar names
            #Row 2 onwards: supposed to be 2D array of variable values, but was never actually functional.  don't include
            with open(os.path.join(self.experiment.path,'Processed Data.txt'),'w') as f:
                f.write('\t'.join(experimentResults.attrs['ivarNames'])+'\n')
            
            #save "All Signal.txt"
            #Lists number of steps for each ivar.  "Formulas" was never operational.
            #a Iterations:	1	b Iterations:	1	l0 Iterations:	11	Formulas:	0
            with open(os.path.join(self.experiment.path,'All Signal.txt'),'w') as f:
                f.write('\t'.join(['{} Iterations:\t{}'.format(name,steps) for name,steps in zip(experimentResults.attrs['ivarNames'],experimentResults.attrs['ivarSteps'])]))
            
            #save variables.txt
            #Description	Name (a,a0...a9)	min	max	# steps
            #raman frequency 	a	9172.618868	9172.618868	1
            #microwave frequency	b	9192.632496	9192.632496	1
            #459 Raman Pulse	l0	0.000000	0.030000	11
            with open(os.path.join(self.experiment.path,'variables.txt'),'w') as f:
                f.write('Description	Name (a,a0...a9)	min	max	# steps\n')
                f.write('\n'.join(['{}\t{}\t{}\t{}'.format(i.description,i.name,numpy.amin(i.valueList),numpy.amax(i.valueList),i.steps) for i in self.experiment.indepenedentVariables]))
                f.write('\n')
            
            #begin Data Order Log.txt
            #Data Order Log.txt
            #        one line with ivar indices
            #        (a,b,l0): 	0,0,0	0,0,1	0,0,2	0,0,3	0,0,4	0,0,5	0,0,6	0,0,7	0,0,8	0,0,9	0,0,10
            #write the variable names now, and update with indices after each iteration
            with open(os.path.join(self.experiment.path,'Data Order Log.txt'),'w') as f:
                f.write('('+','.join(experimentResults.attrs['ivarNames'])+'): ')
    
    def analyzeMeasurement(self,measurementResults,iterationResults,experimentResults):
        if self.experiment.saveData and self.experiment.save2013styleFiles:
            
            #create a directory to hold measurement images, if it doesn't exist
            iterationPath=os.path.join(self.experiment.path,'images','Iteration'+str(iterationResults.attrs['iteration']))
            if not os.path.isdir(iterationPath):
                #create the directory
                #use os.makedirs instead of os.mkdir to create the intermediate directory if it does not exist
                os.makedirs(iterationPath)
            
            #save image PNG
            if 'data/Hamamatsu/shots' in measurementResults:
                for key,value in measurementResults['data/Hamamatsu/shots'].iteritems():
                    self.savePNG(value.value,os.path.join(iterationPath,'Iteration'+str(iterationResults.attrs['iteration'])+'Measurement'+str(measurementResults.attrs['measurement'])+'Shot'+str(key)+'.png'))
    
    def analyzeIteration(self,iterationResults,experimentResults):
        if self.experiment.saveData and self.experiment.save2013styleFiles:
        
            #Data Order Log.txt
            #one line with ivar indices
            #(a,b,l0): 	0,0,0	0,0,1	0,0,2	0,0,3	0,0,4	0,0,5	0,0,6	0,0,7	0,0,8	0,0,9	0,0,10
            with open(os.path.join(self.experiment.path,'Data Order Log.txt'),'a') as f:
                f.write('\t'+','.join(map(str,iterationResults.attrs['ivarIndex'])))
    
    def analyzeExperiment(self,experimentResults):
        if self.experiment.saveData and self.experiment.save2013styleFiles:
        
            #sum images
            sumlist=[]
            if 'iterations' in experimentResults:
                for i in experimentResults['iterations'].itervalues():
                    if 'measurements' in i:
                        for m in i['measurements'].itervalues():
                            if 'data/Hamamatsu/shots' in m:
                                for s in m['data/Hamamatsu/shots'].itervalues():
                                    sumlist.append(s.value)
            sumarray=numpy.array(sumlist)
            average_of_images=numpy.mean(sumarray,axis=0)
            self.savePNG(average_of_images,os.path.join(self.experiment.path,'images','average_of_all_images_in_experiment.png'))
            
            #error log
            pass
    
    def create_iteration_directory(self,iterationResults):
        exp=self.experiment
        if exp.saveData and exp.save2013styleFiles:
            #check that it doesn't exist first
            iterationPath=os.path.join(exp.path,'iteration'+str(iterationResults.attrs['iteration']))
            if not os.path.isdir(iterationPath):
                #create the directory
                #use os.makedirs instead of os.mkdir to create the intermediate directory if it does not exist
                os.makedirs(iterationPath)
    
    def savePNG(self,array,filename):
        #L indicates monochrome, ;16 indicates 16-bit
        png.from_array(array,'L;16',info={'bitdepth':16}).save(filename)
    
    def readPNG(self,filename):
        a=png.Reader(filename=filename)
        b=a.read()
        c=numpy.vstack(itertools.imap(numpy.uint16,b[2]))
        return c
