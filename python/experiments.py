"""experiments.py
This file contains the model to describe and experiment, and the machinery of how an iteration based experiment is run.

author=Martin Lichtman
"""

from __future__ import division

from cs_errors import PauseError, setupLog
logger=setupLog(__name__)

import threading, time, datetime, traceback, xml.etree.ElementTree, pickle, os, numpy, h5py, shutil

#set numpy print options to limit to 2 digits
numpy.set_printoptions(formatter=dict(float=lambda t: "%.2e" % t))

# Use Atom traits to automate Enaml updating
from atom.api import Bool, Int, Float, Str, Member, Value
from enaml.application import deferred_call

# Bring in other files in this package
import cs_evaluate, analysis, save2013style
from instrument_property import Prop, EvalProp, ListProp
import LabView


class IndependentVariables(ListProp):
    dyno=Member()
    
    def __init__(self, experiment=None):
        super(IndependentVariables, self).__init__('independentVariables', experiment,
                                                   listElementType=IndependentVariable,
                                                   listElementName='independentVariable')
    
    def fromXML(self, xmlNode):
        super(IndependentVariables, self).fromXML(xmlNode)
        if self.dyno is not None:
            self.dyno.refresh_items()
        #if hasattr(self.experiment,'ivarRefreshButton'): #prevents trying to do this before GUI is active
        #    self.experiment.ivarRefreshButton.clicked() #refresh variables GUI
        return self


class IndependentVariable(EvalProp):
    """A class to hold the independent variables for an experiment.  These are
    the variables that get stepped through during the iterations.  Each 
    independent variable is defined by a valueList which holds an array of values.
    Using this technique, the valueList can be assigned as single value, an arange, linspace,
    logspace, sin(logspace), as complicated as you like, so long as it can be eval()'d and then
    cast to an array."""
    
    valueListStr=Str()
    steps=Int()
    index=Int()
    currentValueStr=Str()
    valueList=Member()
    currentValue=Member()
    
    def __init__(self,name,experiment,description='',function=''):
        super(IndependentVariable,self).__init__(name,experiment,description,function)
        self.valueList=numpy.array([]).flatten()
        self.currentValue=None
    
    #override from EvalProp()
    def _function_changed(self,val):
        #re-evaluate the variable when the function is changed
        self.evaluate()
        self.setIndex(self.index)
        
        #TODO: should we re-evaluate() the whole experiment on this change?
    
    #override from EvalProp()
    def evaluate(self):
        if self.experiment.allow_evaluation:
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

    version = '2014.01.30'

    #experiment control Traits
    status = Str('idle')
    pauseAfterIteration = Member()
    pauseAfterMeasurement = Member()
    pauseAfterError = Member()
    saveData = Member()
    saveSettings = Member()
    save2013styleFiles = Member()
    localDataPath = Str()
    networkDataPath = Str()
    copyDataToNetwork = Member()
    experimentDescriptionFilenameSuffix = Str()
    measurementTimeout = Float()
    measurementsPerIteration = Int()
    willSendEmail = Member()
    emailAddresses = Str()
    notes = Str()
    
    #iteration Traits
    progress = Int()
    path = Member()  # full path to current experiment directory
    iteration = Int()
    measurement = Int()
    goodMeasurements = Int()
    totalIterations = Int()
    
    #time Traits
    timeStartedStr = Str()
    currentTimeStr = Str()
    timeElapsedStr = Str()
    totalTimeStr = Str()
    timeRemainingStr = Str()
    completionTimeStr = Str()
    
    #variables Traits
    dependentVariablesStr = Str()
    variableReportFormat = Str()
    variableReportStr = Str()
    variablesNotToSave = Str()
    
    #list of Analysis objects
    analyses = Member()
    
    #things we would rather not define, but are forced to by Atom
    timeStarted = Member()
    currentTime = Member()
    timeElapsed = Member()
    timeRemaining = Member()
    totalTime = Member()
    completionTime = Member()
    timeOutExpired = Member()
    instruments = Member()
    completedMeasurementsByIteration = Member()
    independentVariables = Member()
    ivarNames = Member()
    ivarIndex = Member()
    ivarValueLists = Member()
    ivarSteps = Member()
    #ivarRefreshButton = Member()
    vars = Member()
    hdf5 = Member()
    measurementResults = Member()
    iterationResults = Member()
    allow_evaluation = Member()

    def __init__(self):
        """Defines a set of instruments, and a sequence of what to do with them."""

        self.allow_evaluation = False
        super(Experiment, self).__init__('experiment',self) #name is 'experiment', associated experiment is self
        self.instruments = []  # a list of the instruments this experiment has defined
        self.completedMeasurementsByIteration = []
        self.independentVariables=IndependentVariables(self)
        self.ivarIndex=[]
        self.vars = {}
        self.variableReportFormat = '""'
        self.variableReportStr = ''
        self.analyses = []
        self.properties += ['version', 'independentVariables', 'dependentVariablesStr', 'pauseAfterIteration',
                            'pauseAfterMeasurement', 'pauseAfterError', 'saveData', 'saveSettings',
                            'save2013styleFiles', 'localDataPath', 'networkDataPath', 'copyDataToNetwork',
                            'experimentDescriptionFilenameSuffix', 'measurementTimeout', 'measurementsPerIteration',
                            'willSendEmail', 'emailAddresses', 'progress', 'iteration', 'measurement',
                            'totalIterations', 'timeStartedStr', 'currentTimeStr', 'timeElapsedStr', 'totalTimeStr',
                            'timeRemainingStr', 'completionTimeStr', 'variableReportFormat', 'variableReportStr',
                            'variablesNotToSave', 'notes']

    def evaluateIndependentVariables(self):
        #make sure ivar functions have been parsed, don't rely on GUI update
        for i in self.independentVariables:
            i.evaluate()
        
        #set up independent variables
        self.ivarNames=[i.name for i in self.independentVariables] #names of independent variables
        self.ivarValueLists=[i.valueList for i in self.independentVariables]
        self.ivarSteps=[i.steps for i in self.independentVariables]
        self.totalIterations=int(numpy.product(self.ivarSteps))
        
        #set the current value of the independent variables
        self.iterationToIndexArray()
    
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
            i.update() #put the settings to where they should be at this iteration
    
    def evaluateAll(self):
        self.evaluateIndependentVariables()
        self.evaluate()
    
    def evaluateDependentVariables(self):
        
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
        if self.allow_evaluation:
            
            #resolve independent variables for correct iteration, and evaluate dependent variables
            self.evaluateDependentVariables()
            
            #re-evaluate all instruments
            for i in self.instruments:
                i.evaluate() #each instrument will calculate its properties
    
    def eval_general(self,string):
        return cs_evaluate.evalWithDict(string,self.vars)
    
    def eval_bool(self,string):
        return bool(self.eval_general(string))
    
    def eval_float(self,string):
        return float(self.eval_general(string))
    
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
            timePerMeasurement = 1
        if len(self.completedMeasurementsByIteration)<=1:
            estTotalMeasurements=self.measurementsPerIteration*self.totalIterations
        else:
            estTotalMeasurements=numpy.mean(self.completedMeasurementsByIteration[:-1])*self.totalIterations
        if estTotalMeasurements>0:
            deferred_call(setattr, self, 'progress', int(100*completedMeasurements/estTotalMeasurements))
            #self.progress=int(100*completedMeasurements/estTotalMeasurements)
        else:
            deferred_call(setattr, self, 'progress', 0)
            #self.progress=0
        self.timeRemaining=timePerMeasurement*(estTotalMeasurements-completedMeasurements)
        self.timeRemainingStr=self.time2str(self.timeRemaining)
        self.totalTime=self.timeElapsed+self.timeRemaining
        self.totalTimeStr=self.time2str(self.totalTime)
        self.completionTime=self.timeStarted+self.totalTime
        self.completionTimeStr=self.date2str(self.completionTime)
    
    def applyToSelf(self,dict):
        '''Used to apply a bunch of variables at once.  This function is called using an Enaml deferred_call so that the updates are done in the GUI thread.'''
        
        for key,value in dict.iteritems():
            try:
                setattr(self,key,value)
            except Exception as e:
                logger.warning('Exception applying {} with value {} in experiments.applyToSelf.\n{}'.format(key,value,e))
                raise PauseError
    
    def resetAndGo1(self):
        thread = threading.Thread(target=self.resetAndGo2)
        thread.daemon = True
        thread.start()
    
    def resetAndGo2(self):
        '''Reset the iteration variables and timing, then proceed with an experiment.'''
        self.reset()
        self.go2()
    
    def reset(self):
        '''Reset the iteration variables and timing.'''
        
        #check if we are ready to do an experiment
        if (self.status!='idle'):
            logger.info('Current status is {}. Cannot reset experiment unless status is idle.  Try halting first.'.format(self.status))
            return #exit
        
        #reset experiment variables
        self.timeStarted=time.time()
        self.timeStartedStr=self.date2str(self.timeStarted)
        self.iteration=0
        self.measurement=0
        self.goodMeasurements=0
        self.completedMeasurementsByIteration=[]
        
        #setup data directory and files
        self.create_data_files()
        #run analyses setupExperiment
        self.preExperiment()
        
        self.status='paused before experiment'
        
        self.go2()
    
    def go1(self):
        thread = threading.Thread(target=self.go2)
        thread.daemon = True
        thread.start()
    
    def go2(self):
        '''Pick up the experiment wherever it was left off.'''
        
        #check if we are ready to do an experiment
        if not self.status.startswith('paused'):
            logger.info('Current status is {}. Cannot continue an experiment unless status is paused.'.format(self.status))
            return #exit
        self.status='running' #prevent another experiment from being started at the same time
        
        try: #if there is an error we exit the inner loops and respond appropriately
            #make sure the independent variables are processed
            self.evaluateIndependentVariables()
            
            #loop until iteration are complete
            while (self.iteration < self.totalIterations) and (self.status=='running'):
                
                #at the start of a new iteration, or if we are continuing
                self.evaluate()    #re-calculate all variables
                
                self.update()      #send current values to hardware
                
                #only at the start of a new iteration
                if self.measurement==0:
                    self.completedMeasurementsByIteration.append(0) #start a new counter for this iteration
                    self.create_hdf5_iteration()
                
                #loop until the desired number of measurements are taken
                while (self.goodMeasurements < self.measurementsPerIteration) and (self.status=='running'):
                    print 'iteration {} measurement {}'.format(self.iteration,self.measurement)
                    self.measure()     #tell all instruments to do the experiment sequence and acquire data
                    self.updateTime()  #update the countdown/countup clocks
                    self.measurement+=1 #update the measurement count
                    if self.status=='running' and self.pauseAfterMeasurement:
                        self.status='paused after measurement'
                    
                    #make sure results are written to disk
                    self.hdf5.flush()
                
                if self.goodMeasurements>=self.measurementsPerIteration:
                    # We have completed this iteration, move on to the next one
                    self.postIteration() #run analysis
                    self.iteration+=1
                    self.measurement=0
                    self.goodMeasurements=0
                    if (self.status=='running' or self.status=='paused after measurement') and self.pauseAfterIteration:
                        self.status='paused after iteration'            
                if self.iteration>=self.totalIterations:
                    self.status='idle' #we are now ready for the next experiment
                    self.hdf5.attrs['notes']=self.notes #store the notes again
                    self.postExperiment()
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
    
    def measure(self):
        '''Enables all instruments to begin a measurement.  Sent at the beginning of every measurement.
        Actual output or input from the measurement may yet wait for a signal from another device.'''
        
        start_time = time.time() #record start time of measurement
        self.timeOutExpired=False
        
        #for all instruments
        for i in self.instruments:
            #check that the instruments are initalized
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
            if time.time() - start_time > self.measurementTimeout:  # break if timeout exceeded
                self.timeOutExpired = True
                logger.warning('The following instruments timed out: '+str([i.name for i in self.instruments if not i.isDone]))
                return  # exit without saving results
            time.sleep(.01)  # wait a bit, then check again
        
        #set up the results container
        self.measurementResults = self.hdf5.create_group('iterations/'+str(self.iteration)+'/measurements/'+str(self.measurement))
        self.measurementResults.attrs['start_time'] = start_time
        self.measurementResults.attrs['measurement'] = self.measurement
        self.measurementResults.create_group('data') #for storing data
        for i in self.instruments:
            #pass the hdf5 group to each instrument so they can write results to it
            #we do it here because h5py is not thread safe, and also this way we avoid saving results for aborted measurements
            i.writeResults(self.measurementResults['data'])
        
        self.postMeasurement()
        self.completedMeasurementsByIteration[-1]+=1 #add one to the last counter in the list
    
    def halt(self):
        self.status='idle'
    
    def loadDefaultSettings(self):
        """Look for settings.hdf5 in this directory, and if it exists, load it."""
        try:
            self.load('settings.hdf5')
        except IOError as e:
            logger.warning('No default settings.hdf5 found.\n'+str(e))
            
    def load(self, path):
        logger.debug('starting file load')

        #Disable any equation evaluation while loading.  We will evaluate everything after.
        if self.allow_evaluation:
            allow_evaluation_was_toggled = True
            self.allow_evaluation = False
        else:
            allow_evaluation_was_toggled = False

        #load hdf5 from a file
        f = h5py.File(path, 'a')
        settings = f['settings/experiment']
        
        ##independentVariables
        #if 'experiment/independentVariables' in settings:
        #    self.independentVariables.fromHDF5(settings['experiment/independentVariables'])
        #try:
        #    self.evaluateIndependentVariables()
        #except PauseError:
        #    raise PauseError
        #except Exception as e:
        #    logger.warning('Exception in evaluateIndependentVariables() in load() in experiment.\n'+str(e)+'\n'+str(traceback.format_exc()))
        #    raise PauseError
        #
        ##dependentVariables
        #if 'dependentVariablesStr'
        #dvarXML=xmlNode.find('dependentVariablesStr')
        #if dvarXML is not None:
        #    self.dependentVariablesStr=pickle.loads(dvarXML.text)
        #    #remove 'dependentVariables' from xml to prevent repeat loading
        #    xmlNode.remove(dvarXML)
        #try:
        #    self.evaluateDependentVariables()
        #except Exception as e:
        #    logger.warning('Exception in evaluateDependentVariables() in load() in experiment.\n'+str(e)+'\n'+str(traceback.format_exc()))
        #
        ##now load the rest of the settings and instruments
        ##TODO: skip 'independentVariables' and 'dependentVariables' from xml to prevent repeat loading!!!!!!!!!

        try:
            self.fromHDF5(settings)
        except PauseError:
            raise PauseError #pass it along
        except Exception as e:
            logger.warning('Exception while loading experiment variables XML\n'+str(e)+'\n'+str(traceback.format_exc()))
        logger.debug('ended file load')

        if allow_evaluation_was_toggled:
            self.allow_evaluation = True
        #TODO: evaluate here?
    
    def saveThread(self, path):
        '''Starts the saving in a separate thread, in case it takes a while.'''
        #TODO:  This doesn't work because if there are 61 characters in path, it thinks I am passing 61 arguments.
        threading.Thread(target=self.save, args=(path)).start()
    
    def autosave(self):
        logger.debug('Saving default HDF5...')
        #create file
        f = h5py.File('settings.hdf5', 'w')
        #recursively add all properties
        x = f.create_group('settings')
        self.toHDF5(x)
        f.flush()
        return f
        #you will need to do autosave().close() wherever this is called

    def save(self, path):
        """This function saves all the settings."""
        
        logger.debug('Saving...')        
        
        #HDF5
        self.autosave().close()
        #copy to default location
        logger.debug('Copying HDF5 to save path...')
        shutil.copy('settings.hdf5',path+'.hdf5')
        
        #XML
        logger.debug('Creating XML...')
        x=self.toXML()
        #write to the chosen file
        logger.debug('Writing XML to save path...')
        f=open(path+'.xml','w')
        f.write(x)
        f.close()
        logger.debug('Writing default XML...')
        #write to the default file
        f=open('settings.xml','w')
        f.write(x)
        f.close()
        logger.debug('... Save Complete.')
    
    def create_data_files(self):
        '''Create a new HDF5 file to store results.  This is done at the beginning of
        every experiment.'''
        
        #if a prior HDF5 results file is open, then close it
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
            self.path=os.path.join(self.localDataPath,dailyPath,experimentPath)
            
            #check that it doesn't exist first
            if not os.path.isdir(self.path):
                #create the directory
                #use os.makedirs instead of os.mkdir to create the intermediate dailyPath directory if it does not exist
                os.makedirs(self.path)
            
            #save to a real file
            self.hdf5=h5py.File(os.path.join(self.path,'results.hdf5'),'a')
        
        else:
            #hold results only in memory
            self.hdf5=h5py.File('results.hdf5','a',driver='core',backing_store=False)
        
        #add settings
        if self.saveSettings:
        
            #start by saving settings
            logger.debug('Autosaving')
            autosave_file=self.autosave()
            logger.debug('Done autosaving')
            
            try:
                logger.debug('Copying autosave data to current HDF5')
                autosave_file['settings'].copy(autosave_file['settings'],self.hdf5)
            except:
                logger.warning('Problem trying to copy autosave settings to HDF5 results file.')
                raise PauseError
            finally:
                autosave_file.close()
                logger.debug('Autosave closed')
        
        #store independent variable data for experiment
        self.hdf5.attrs['start_time']=self.date2str(time.time())
        self.hdf5.attrs['ivarNames']=self.ivarNames
        self.hdf5.attrs['ivarValueLists']=self.ivarValueLists
        self.hdf5.attrs['ivarSteps']=self.ivarSteps
        
        #create a group to hold iterations in the hdf5 file
        self.hdf5.create_group('iterations')
        
        #store notes.  They will be stored again at the end of the experiment.
        self.hdf5.attrs['notes']=self.notes
        
        logger.debug('Finished create_data_files()')
    
    def create_hdf5_iteration(self):
        #write the iteration settings to the hdf5 file
        self.iterationResults=self.hdf5.create_group('iterations/'+str(self.iteration))
        self.iterationResults.attrs['start_time']=self.date2str(time.time())
        self.iterationResults.attrs['iteration']=self.iteration
        self.iterationResults.attrs['ivarNames']=self.ivarNames
        self.iterationResults.attrs['ivarValues']=[i.currentValue for i in self.independentVariables]
        self.iterationResults.attrs['ivarIndex']=self.ivarIndex
        self.iterationResults.attrs['variableReportStr']=self.variableReportStr
        
        #store the indepenedent and dependent variable space
        v=self.iterationResults.create_group('v')
        ignoreList=self.variablesNotToSave.split(',')
        for key,value in self.vars.iteritems():
            if key not in ignoreList:
                try:
                    v[key]=value
                except Exception as e:
                    logger.warning('Could not save variable '+key+' as an hdf5 dataset with value: '+str(value)+'\n'+str(e))
    
    def preExperiment(self):
        #run analysis
        for i in self.analyses:
            i.preExperiment(self.hdf5)
    
    def postMeasurement(self):
        #run analysis
        good=True
        delete=False
        for i in self.analyses:
            a=i.postMeasurement(self.measurementResults,self.iterationResults,self.hdf5)
            if (a is None) or (a==0):
                continue
            elif a==1:
                #continue, but do not increment goodMeasurements
                good=False
                continue
            elif a==2:
                #continue, but do not increment goodMeasurements, delete data when done
                good=False
                delete=True
                continue
            elif a==3:
                #stop, do not increment goodMeasurements, delete data when done
                good=False
                delete=True
                break
            else:
                logger.warning('bad return value {} in experiment.postMeasurement() for analysis {}: {}'.format(a,i.name,i.description))
        if not self.saveData:
            #we are not saving data so remove the measurement from the hdf5
            delete=True
        if delete:
            del self.measurementResults #remove the bad data
        if good:
            self.goodMeasurements+=1
    
    def postIteration(self):
        #run analysis
        for i in self.analyses:
            i.postIteration(self.iterationResults,self.hdf5)
    
    def postExperiment(self):
        #run analysis
        for i in self.analyses:
            i.postExperiment(self.hdf5)


class AQuA(Experiment):
    """A subclass of Experiment which knows about all our particular hardware"""
    
    LabView = Member()
    shot0_analysis = Member()
    shotBrowserAnalysis = Member()
    imageSumAnalysis = Member()
    squareROIAnalysis = Member()
    save2013Analysis = Member()
    optimizer = Member()

    def __init__(self):
        super(AQuA, self).__init__()
        
        #add instruments
        self.LabView = LabView.LabView(experiment=self)
        self.instruments = [self.LabView]
        
        #analyses
        self.shot0_analysis = analysis.ImagePlotAnalysis('analysisShot0', self.experiment, description='just show the incoming shot 0')
        self.shotBrowserAnalysis = analysis.ShotsBrowserAnalysis(self.experiment)
        self.imageSumAnalysis = analysis.ImageSumAnalysis(self.experiment)
        self.squareROIAnalysis = analysis.SquareROIAnalysis(self.experiment)
        self.save2013Analysis = save2013style.Save2013Analysis(self.experiment)
        self.optimizer = analysis.OptimizerAnalysis(self.experiment)
        self.analyses += [self.shot0_analysis, self.shotBrowserAnalysis, self.imageSumAnalysis, self.squareROIAnalysis,
                          self.save2013Analysis]

        self.properties += ['LabView']

        try:
            self.loadDefaultSettings()
        except PauseError:
            logger.warning('PauseError')
        except Exception as e:
            logger.warning('While trying Experiment.loadDefaultSettings in AQuA.__init__().\n'+str(e)+'\n'+str(traceback.format_exc())+'\n')

        #update variables
        self.allow_evaluation = True
        try:
            logger.debug('starting evaluateAll')
            self.evaluateAll()
            logger.debug('ended evaluateAll')
        except PauseError:
            logger.warning('PauseError')
        except Exception as e:
            logger.warning('While trying Experiment.evaluateAll() on in AQuA.__init().\n'+str(e)+'\n'+str(traceback.format_exc())+'\n')
