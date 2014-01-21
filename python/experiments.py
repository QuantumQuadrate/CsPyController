import threading, time, datetime, logging, traceback, xml.etree.ElementTree, pickle, os, numpy
logger = logging.getLogger(__name__)

#for saving data in hdf5 files
import h5py

#set numpy print options to limit to 2 digits
numpy.set_printoptions(formatter=dict(float=lambda t: "%.2e" % t))

# Use Atom traits to automate Enaml updating
from atom.api import Bool, Int, Float, Str, Typed, Member

# Bring in other files in this package
import cs_evaluate
from instrument_property import Prop, EvalProp, ListProp
from cs_errors import PauseError
import LabView

from PyQt4 import QtCore

class experimentResetAndGoThread(QtCore.QThread):
    def __init__(self,experiment):
        super(experimentResetAndGoThread,self).__init__()
        self.experiment=experiment
    
    def run(self):
        self.experiment.resetAndGo()

class result(object):
    def __init__(self,start_time,iteration,measurement,ivarIndices,variables,data):
        self.t=start_time #the time.time() that the experiment was started
        self.i=iteration #the iteration number, a single integer
        self.indices=ivarIndices #a list of indices of each independent variable at this iteration
        self.m=measurement #the measurement number, reset each iteration
        self.v=variables #a dictionary of all variables
        self.d=data #a dictionary of all data.  To access camera data call result.d['camera'] to get a numpy array.

class independentVariables(ListProp):
    def fromXML(self,xmlNode):
        super(independentVariables,self).fromXML(xmlNode)
        if hasattr(self.experiment,'ivarRefreshButton'): #prevents trying to do this before GUI is active
            self.experiment.ivarRefreshButton.clicked() #refresh variables GUI
        return self

class independentVariable(EvalProp):
    '''A class to hold the independent variables for an experiment.  These are
    the variables that get stepped through during the iterations.  Each 
    independent variable is defined by a valueList which holds an array of values.
    Using this technique, the valueList can be assigned as single value, an arange, linspace,
    logspace, sin(logspace), as complicated as you like, so long as it can be eval()'d and then
    cast to an array.'''
    
    valueListStr=Str()
    steps=Int()
    index=Int()
    currentValueStr=Str()
    valueList=Member()
    currentValue=Member()
    
    def __init__(self,name,experiment,description='',function='',kwargs={}):
        super(independentVariable,self).__init__(name,experiment,description,function)
        self.valueList=[]
        self.currentValue=None
    
    #override from EvalProp()
    def _function_changed(self,val):
        #re-evaluate the variable when the function is changed
        self.evaluate()
        self.setIndex(self.index)
        
        #TODO: should we re-evaluate() the whole experiment on this change?
    
    #override from EvalProp()
    def evaluate(self):
        if self.function=='':
            a=None
        else:
            a=cs_evaluate.evalWithDict('array('+self.function+').flatten()',errStr='Evaluating independent variable '+', '.join([self.name,self.description,self.function])+'\n')
        if a==None:
            a=numpy.array([]).flatten()
        self.valueList=a
        self.steps=len(a)
        self.valueListStr=str(self.valueList)
    
    def setIndex(self,index):
        if self.steps==0:
            self.currentValue=None
        else:
            if 0<=index<self.steps:
                self.index=index
            else:
                logger.warning('Index='+str(index)+' out of range for independent variable '+self.name+'. Setting '+self.name+'.index=0\n')
                self.index=0
            self.currentValue=self.valueList[self.index]
        self.currentValueStr=str(self.currentValue)
        return self.index

class Experiment(Prop):

    version='2013.10.19'

    #experiment control Traits
    status=Str('idle')
    pauseAfterIteration=Bool(False)
    pauseAfterMeasurement=Bool(False)
    pauseAfterError=Bool(False)
    saveData=Bool()
    save2013styleFiles=Bool()
    localDataPath=Str()
    networkDataPath=Str()
    copyDataToNetwork=Bool()
    experimentDescriptionFilenameSuffix=Str()
    measurementTimeout=Float()
    measurementsPerIteration=Int()
    willSendEmail=Bool()
    emailAddresses=Str()
    notes=Str()
    
    #iteration Traits
    progress=Int()
    iteration=Int()
    measurement=Int()
    totalIterations=Int()
    
    #time Traits
    timeStartedStr=Str()
    currentTimeStr=Str()
    timeElapsedStr=Str()
    totalTimeStr=Str()
    timeRemainingStr=Str()
    completionTimeStr=Str()
    
    #variables Traits
    dependentVariablesStr=Str()
    variableReportFormat=Str()
    variableReportStr=Str()
    variablesNotToSave=Str()
    
    #things we would rather not define, but are forced to by Atom
    timeStarted=Member()
    currentTime=Member()
    timeElapsed=Member()
    timeRemaining=Member()
    totalTime=Member()
    completionTime=Member()
    timeOutExpired=Member()
    instruments=Member()
    completedMeasurementsByIteration=Member()
    independentVariables=Member()
    ivarNames=Member()
    ivarIndex=Member()
    ivarValueLists=Member()
    ivarSteps=Member()
    ivarRefreshButton=Member()
    vars=Member()
    hdf5=Member()
    measurementResults=Member()
    iterationResults=Member()
    
    resetAndGoThread=Typed(experimentResetAndGoThread)
 
    '''Defines a set of instruments, and a sequence of what to do with them.'''
    def __init__(self):
        super(Experiment,self).__init__('experiment',self) #name is 'experiment', associated experiment is self
        self.instruments=[] #a list of the instruments this experiment has defined
        self.completedMeasurementsByIteration=[]
        self.independentVariables=ListProp('independentVariables',self,listElementType=independentVariable,listElementName='independentVariable')
        self.ivarIndex=[]
        self.vars={}
        self.variableReportFormat='""'
        self.variableReportStr=''
        self.properties+=['version','independentVariables','dependentVariablesStr',
        'pauseAfterIteration','pauseAfterMeasurement','pauseAfterError','saveData',
        'save2013styleFiles','localDataPath','networkDataPath',
        'copyDataToNetwork','experimentDescriptionFilenameSuffix','measurementTimeout','measurementsPerIteration','willSendEmail',
        'emailAddresses','progress','iteration','measurement','totalIterations','timeStartedStr','currentTimeStr','timeElapsedStr','totalTimeStr',
        'timeRemainingStr','completionTimeStr','variableReportFormat','variableReportStr','variablesNotToSave','notes']
        
        self.resetAndGoThread=experimentResetAndGoThread(self)
        
    def evaluateIndependentVariables(self):
        #make sure ivar functions have been parsed, don't rely on GUI update
        for i in self.independentVariables:
            i.evaluate()
        
        #set up independent variables
        self.ivarNames=[i.name for i in self.independentVariables] #names of independent variables
        self.ivarValueLists=[i.valueList for i in self.independentVariables]
        self.ivarSteps=[i.steps for i in self.independentVariables]
        self.totalIterations=int(numpy.product(self.ivarSteps))
    
    def iterationToIndexArray(self):
        '''takes the iteration number and figures out which index number each independent variable should have'''
        n=len(self.independentVariables)
        index=numpy.zeros(n,dtype=int)
        #calculate the base for each variable place
        base=[1]
        for i in range(1,n):
            base.append(self.ivarSteps[i-1]*base[i-1])
        #build up the list
        seq=range(n)
        seq.reverse() #go from largest place to smallest
        iter=self.iteration
        for i in seq:
            index[i]=int(iter/base[i])
            iter-=index[i]*base[i]
            index[i]=self.independentVariables[i].setIndex(index[i]) #update each variable object
        self.ivarIndex=index #store the list
    
    def update(self):
        '''Sends updated settings to all instruments.  This function is run at the beginning of every new iteration.'''
        
        #update the instruments with new settings
        
        for i in self.instruments:
            print 'debug experiment.update() instrument='+i.name
            #check that the instruments are initialized
            if not i.isInitialized:
                i.initialize() #reinitialize
            print 'debug 2.6'
            i.update() #put the settings to where they should be at this iteration
    
    def evaluateAll(self):
        self.evaluateIndependentVariables()
        self.evaluate()
    
    def evaluateDependentVariables(self):
        self.iterationToIndexArray() #set the current value of the independent variables
        
        #update variables dictionary.
        #overwrite the old list and make new list starting with independent variables
        self.vars=dict(zip(self.ivarNames,[self.ivarValueLists[i][self.ivarIndex[i]] for i in xrange(len(self.ivarValueLists))]))
        #evaluate the dependent variable multi-line string
        cs_evaluate.execWithDict(self.dependentVariablesStr,self.vars)
        #update the report
        self.variableReportStr=cs_evaluate.evalWithDict(self.variableReportFormat+'%locals()',varDict=self.vars,errStr='evaluating variables report\n') #update the GUI
    
    #overwrite from Prop()
    def evaluate(self):
        '''resolves all equations'''
        
        #resolve independent variables for correct iteration, and evaluate dependent variables
        self.evaluateDependentVariables()
        
        #re-evaluate all instruments
        for i in self.instruments:
            i.evaluate() #each instrument will calculate its properties
    
    def measure(self):
        print 'experiment.measure()'
        '''Enables all instruments to begin a measurement.  Sent at the beginning of every measurement.
        Actual output or input from the measurement may yet wait for a signal from another device.'''
        
        start_time = time.time() #record start time of measurement
        self.timeOutExpired=False
        
        #for all instruments
        for i in self.instruments:
            #check that the instruments are initalized
            print 'initialized = ',i.isInitialized
            if not i.isInitialized:
                print 'experiment.measure() initializing '+i.name
                i.initialize() #reinitialize
                i.update() #put the settings to where they should be at this iteration
            else:
                #check that the instrument is not already occupied
                if not i.isDone:
                    logger.warning('Instrument '+i.name+' is already busy.')
                else:
                    #set a flag to indicate each instrument is now busy
                    i.isDone=False
                    #let each instrument begin measurement
                    #put each in a different thread, so they can proceed simultaneously
                    #TODO: enable threading?
                    #threading.Thread(target=i.start).start()
                    i.start()
        
        #loop until all instruments are done
        #TODO: can we do this with a callback?
        while not all([i.isDone for i in self.instruments]):
            if time.time() - start_time > self.measurementTimeout: #break if timeout exceeded
                self.timeOutExpired=True
                logger.warning('The following instruments timed out: '+str([i.name for i in self.instruments if not i.isDone]))
                return #exit without saving results
            time.sleep(.01) #wait a bit, then check again
        
        #set up the results container
        self.measurementResults=self.hdf5.create_group('iterations/'+str(self.iteration)+'/measurements/'+str(self.measurement))
        self.measurementResults['start_time']=start_time
        self.measurementResults['measurement']=self.measurement
        self.measurementResults.create_group('data') #for storing data
        for i in self.instruments:
            #pass the hdf5 group to each instrument so they can write results to it
            #we do it here because h5py is not thread safe, and also this way we avoid saving results for aborted measurements
            i.writeResults(self.measurementResults['data'])
        
        self.postMeasurement()
        self.completedMeasurementsByIteration[-1]+=1 #add one to the last counter in the list
    
    def postMeasurement(self):
        #Run this after every measurement.  Could be an analysis for example.
        #Override in a subclass to use.
        pass
        
    def stop(self):
        '''Stops output as soon as possible.  This is not run during the course of a normal experiment.'''
        [i.__setattr__('isDone',True) for i in self.instruments]
        [i.stop() for i in self.instruments]
    
    def date2str(self,time):
        return datetime.datetime.fromtimestamp(time).strftime('%Y-%m-%d %H:%M:%S')
    
    def time2str(self,time):
        return str(datetime.timedelta(seconds=time))
    
    def updateTime(self):
        '''Updates the GUI clock and recalculates the time-to-completion predictions.'''
        
        self.currentTime=time.time()
        self.currentTimeStr=self.date2str(self.currentTime)
        
        self.timeElapsed=self.currentTime-self.timeStarted
        self.timeElapsedStr=self.time2str(self.timeElapsed)
        
        #calculate time per measurement
        completedMeasurements=sum(self.completedMeasurementsByIteration)
        if self.timeElapsed!=0:
            timePerMeasurement=completedMeasurements/self.timeElapsed
        else:
            timePerMeasurement=1
        if len(self.completedMeasurementsByIteration)<=1:
            estTotalMeasurements=self.measurementsPerIteration*self.totalIterations
        else:
            estTotalMeasurements=numpy.mean(self.completedMeasurementsByIteration[:-1])*self.totalIterations
        self.progress=int(100*completedMeasurements/estTotalMeasurements)
        self.timeRemaining=timePerMeasurement*(estTotalMeasurements-completedMeasurements)
        self.timeRemainingStr=self.time2str(self.timeRemaining)
        self.totalTime=self.timeElapsed+self.timeRemaining
        self.totalTimeStr=self.time2str(self.totalTime)
        self.completionTime=self.timeStarted+self.totalTime
        self.completionTimeStr=self.date2str(self.completionTime)
    
    def resetAndGo(self):
        print 'experiment.resetAndGo()'
        '''Reset the iteration variables and timing, then proceed with an experiment.'''
        
        #check if we are ready to do an experiment
        if (self.status!='idle'):
            logger.info('Current status is {}. Cannot reset experiment unless status is idle.'.format(self.status))
            return #exit
        
        #reset experiment variables
        self.timeStarted=time.time()
        self.timeStartedStr=self.date2str(self.timeStarted)
        self.iteration=0
        self.measurement=0
        self.completedMeasurementsByIteration=[]
        
        #setup data directory and files
        self.create_data_files()
        
        self.status='paused before experiment'
        
        self.go()

    def go(self):
        print 'experiment.go()'
        '''Pick up the experiment wherever it was left off.'''
        
        #check if we are ready to do an experiment
        if not self.status.startswith('paused'):
            logger.info('Current status is {}. Cannot continue an experiment unless status is paused.'.format(self.status))
            return #exit
        self.status='running' #prevent another experiment from being started at the same time
        
        try: #if there is an error we exit the inner loops and respond appropriately
            print 'debug 1'
            #make sure the independent variables are processed
            self.evaluateIndependentVariables()
            
            #loop until iteration are complete
            while (self.iteration < self.totalIterations) and (self.status=='running'):
                print 'debug 2'
                
                #at the start of a new iteration, or if we are continuing
                self.evaluate()    #re-calculate all variables
                
                print 'debug 2.5'
                
                self.update()      #send current values to hardware
                
                print 'debug 3'
                
                #only at the start of a new iteration
                if self.measurement==0:
                    print 'debug 4'
                    self.completedMeasurementsByIteration.append(0) #start a new counter for this iteration
                    
                    #write the iteration settings to the hdf5 file
                    self.iterationResults=self.hdf5.create_group('iterations/'+str(self.iteration))
                    self.iterationResults.attrs['start_time']=self.date2str(time.time())
                    self.iterationResults.attrs['iteration']=self.iteration
                    self.iterationResults.attrs['ivarNames']=self.ivarNames
                    self.iterationResults.attrs['ivarValues']=[i.currentValue for i in self.independentVariables]
                    self.iterationResults.attrs['ivarIndex']=self.ivarIndex
                    self.iterationResults.attrs['variableReportStr']=self.variableReportStr
                    v=self.iterationResults.create_group('v')
                    ignoreList=self.variablesNotToSave.split(',')
                    for key,value in self.vars.iteritems():
                        if key not in ignoreList:
                            try:
                                v.attrs[key]=value
                            except Exception as e:
                                logger.warning('Could not save variable '+key+' as an hdf5 attribute with value: '+str(value)+'\n'+str(e))
                
                #loop until the desired number of measurements are taken
                while (self.measurement < self.measurementsPerIteration) and (self.status=='running'):
                    self.measure()     #tell all instruments to do the experiment sequence and acquire data
                    self.updateTime()  #update the countdown/countup clocks
                    self.measurement+=1 #update the measurement count
                    if self.status=='running' and self.pauseAfterMeasurement:
                        self.status='paused after measurement'
                    
                    #make sure results are written to disk
                    self.hdf5.flush()
                
                if self.measurement>=self.measurementsPerIteration:
                    # We have completed this iteration, move on to the next one
                    self.iteration+=1
                    self.measurement=0
                    if (self.status=='running' or self.status=='paused after measurement') and self.pauseAfterIteration:
                        self.status='paused after iteration'            
                if self.iteration>=self.totalIterations:
                    self.status='idle' #we are now ready for the next experiment
                    self.hdf5.attrs['notes']=self.notes #store the notes again
        except PauseError:
            #This should be the only place that PauseError is explicitly handed.
            #All other non-fatal error caught higher up in the experiment chain should
            #gracefully handle the error, then 'raise PauseError' so that the experiment
            #exits out to this point.
            if self.pauseAfterError:
                self.status='paused after error'
        except Exception as e:
            logger.error('Exception during experiment:\n'+str(e)+'\n'+str(traceback.format_exc())+'\n')
            if self.pauseAfterError:
                self.status='paused after error'
    
    def halt(self):
        self.status='idle'
    
    def loadDefaultSettings(self):
        '''Look for settings.xml in this directory, and if it exists, load it.'''
        try:
            self.load('settings.xml')
        except IOError as e:
            logger.warning('No default settings.xml found.')
    
    def load(self,path):
        #load xml from a file
        xmlNode=xml.etree.ElementTree.parse(path).getroot()
        
        #independentVariables
        ivarXML=xmlNode.find('independentVariables') 
        if ivarXML is not None:
            self.independentVariables.fromXML(ivarXML)
            #remove 'independentVariables' from xml to prevent repeat loading
            xmlNode.remove(ivarXML)
        try:
            self.evaluateIndependentVariables()
        except Exception as e:
            logger.warning('Exception in evaluateIndependentVariables() in load() in experiment.\n'+str(e)+'\n'+str(traceback.format_exc()))
        
        #dependentVariables
        dvarXML=xmlNode.find('dependentVariablesStr')
        if dvarXML is not None:
            self.dependentVariablesStr=pickle.loads(dvarXML.text)
            #remove 'dependentVariables' from xml to prevent repeat loading
            xmlNode.remove(dvarXML)
        try:
            self.evaluateDependentVariables()
        except Exception as e:
            logger.warning('Exception in evaluateDependentVariables() in load() in experiment.\n'+str(e)+'\n'+str(traceback.format_exc()))
        
        #now load the rest of the settings and instruments
        try:
            self.fromXML(xmlNode)
        except Exception as e:
            logger.warning('Exception while loading experiment variables XML\n'+str(e)+'\n'+str(traceback.format_exc()))
    
    def saveThread(self,path):
        '''Starts the saving in a separate thread, in case it takes a while.'''
        #TODO:  This doesn't work because if there are 61 characters in path, it thinks I am passing 61 arguments.
        threading.Thread(target=self.save,args=(path)).start()
    
    def save(self,path):
        '''This function saves all the settings.
        The experiment variables settings get put one layer deeper, under <variables> to keep things tidy.
        Do not put the instruments into properties, to prevent recursion problems (because the instruments all refer to experiment).'''
        x=self.toXML()
        #write to the chosen file
        f=open(path,'w')
        f.write(x)
        f.close()
        #write to the default file
        f=open('settings.xml','w')
        f.write(x)
        f.close()
    
    def create_data_files(self):
        '''CreateCreate a new HDF5 file to store results.  This is done at the beginning of
        every experiment.'''
        
        #if a prior HDF5 file is open, then close it
        if hasattr(self,'hdf5') and (self.hdf5 is not None):
            try:
                self.hdf5.flush()
                self.hdf5.close()
            except Exception as e:
                logger.warning('Exception closing hdf5 file.\n'+str(e))
                raise PauseError
        
        if self.saveData:
            #create a new directory for experiment
            
            #build the path
            dailyPath=datetime.datetime.fromtimestamp(self.timeStarted).strftime('%Y_%m_%d')
            experimentPath=datetime.datetime.fromtimestamp(self.timeStarted).strftime('%Y_%m_%d_%H_%M_%S_')+self.experimentDescriptionFilenameSuffix
            path=os.path.join(self.localDataPath,dailyPath,experimentPath)
            
            #check that it doesn't exist first
            if not os.path.isdir(path):
                #create the directory
                #use os.makedirs instead of os.mkdir to create the intermediate dailyPath directory if it does not exist
                os.makedirs(path)
        
            #save to a real file
            self.hdf5=h5py.File(os.path.join(path,'results.hdf5'),'a')
        
        else:
            #hold results only in memory
            self.hdf5=h5py.File('results.hdf5','a',driver='core',backing_store=False)
        
        #create a group to hold iterations in the hdf5 file
        self.hdf5.create_group('iterations')
        
        #store notes.  They will be stored again at the end of the experiment.
        self.hdf5.attrs['notes']=self.notes

class AQuA(Experiment):
    '''A subclass of Experiment which knows about all our particular hardware'''
    
    LabView=Member()
    
    def __init__(self):
        super(AQuA,self).__init__()
        
        self.properties+=['LabView']
        
        self.LabView=LabView.LabView(experiment=self)
        self.instruments=[self.LabView]
        
        self.loadDefaultSettings()
        
        #update variables
        try:
            self.evaluateAll()
        except PauseError:
            print 'PauseError'
