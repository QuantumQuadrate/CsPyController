"""experiments.py
This file contains the model to describe and experiment, and the machinery of
how an iteration based experiment is run.

author=Martin Lichtman
"""
# filename whitespace problem may have been fixed. See
# IndependentVariable.__init__ - PH

from __future__ import division

# import core python modules
import threading
import time
import datetime
import traceback
import os
import shutil
import cStringIO
import numpy
import h5py
import zipfile
import inspect

# Use Atom traits to automate Enaml updating
from atom.api import Int, Float, Str, Member, Bool

# Bring in other files in this package
from cs_errors import PauseError
import cs_evaluate
import sound
import optimization
from instrument_property import Prop, EvalProp, ListProp, StrProp
import functional_waveforms

import logging
__author__ = 'Martin Lichtman'
logger = logging.getLogger(__name__)

# set numpy print options to limit to 2 digits
numpy.set_printoptions(formatter=dict(float=lambda t: "%.2e" % t))


class IndependentVariable(EvalProp):
    """A class to hold the independent variables for an experiment.  These are
    the variables that get stepped through during the iterations.  Each
    independent variable is defined by a valueList which holds an array of
    values. Using this technique, the valueList can be assigned as single
    value, an arange, linspace, logspace, sin(logspace), as complicated as you
    like, so long as it can be eval()'d and then cast to an array.
    """

    valueListStr = Str()
    steps = Member()
    index = Member()
    currentValueStr = Str()
    valueList = Member()
    currentValue = Member()

    # optimizer variables
    optimize = Bool()
    optimizer_initial_step = Float()
    optimizer_min = Float()
    optimizer_max = Float()
    optimizer_end_tolerance = Float()

    def __init__(self, name, experiment, description='', function=''):
        # super(IndependentVariable, self).__init__(name, experiment, description, function)
        super(IndependentVariable, self).__init__(name, experiment,
                                                  description, function)
        self.steps = 0
        self.index = 0
        self.valueList = numpy.array([]).flatten()
        self.currentValue = None
        self.properties += ['optimize', 'optimizer_initial_step', 'optimizer_min', 'optimizer_max',
                            'optimizer_end_tolerance']

    def evaluate(self):
        """This function evaluates just the independent variables.  We do not update the rest of the experiment,
        although it may depend on this change, because it would be too cumbersome.  There is a button available that
        calls experiment.evaluateAll() to update the whole experiment at will."""
        if self.experiment.allow_evaluation:
            if self.function == '':
                a = None
            else:

                #Evaluate the independent variable.
                #Cast it to a 1D numpy array as part of the evaluation.  If this cannot be done, the function is not
                #valid as an independent variable and an error is returned.
                #Pass in a dictionary with numpy as the keyword np, for the user to create array variables using
                #linspace, arange, etc.

                a = cs_evaluate.evalIvar('array('+self.function+').flatten()', self.experiment.constants)
            if a is None:
                a = numpy.array([]).flatten()
            self.valueList = a
            self.steps = len(a)
            self.valueListStr = str(self.valueList)
            self.setIndex(self.index)

    def setIndex(self, index):
        if self.steps == 0:
            self.currentValue = None
        else:
            if 0 <= index < self.steps:
                self.index = index
            else:
                logger.warning('Index='+str(index)+' out of range for independent variable '+self.name+'. Setting '+self.name+'.index=0\n')
                self.index = 0
            self.currentValue = self.valueList[self.index]
        self.currentValueStr = str(self.currentValue)
        return self.index


class Experiment(Prop):

    version = '2014.04.30'

    # experiment control
    Config = Member()
    status = Str('idle')
    statusStr = Str()
    valid = Bool(True)  # the window will flash red on error
    pauseAfterIteration = Bool()
    pauseAfterMeasurement = Bool()
    pauseAfterError = Bool()
    reload_settings_after_pause = Bool()
    repeat_experiment_automatically = Bool()
    saveData = Bool()
    saveSettings = Bool()
    save_separate_notes = Bool()
    save2013styleFiles = Bool()
    localDataPath = Str()
    networkDataPath = Str()
    copyDataToNetwork = Bool()
    experimentDescriptionFilenameSuffix = Str()
    measurementTimeout = Float()
    measurementsPerIteration = Int()
    willSendEmail = Bool()
    emailAddresses = Str()
    notes = Str()
    enable_sounds = Bool()
    enable_instrument_threads = Bool()
    cache_dir = Str()
    setting_path = Str()
    temp_path = Str()

    #iteration traits
    progress = Int()
    progressGUI = Int()
    path = Member()  # full path to current experiment directory
    dailyPath = Member()
    experimentPath = Member()

    iteration = Int(0)
    iterationStr = Str()
    measurement = Int(0)
    measurementStr = Str()
    goodMeasurements = Member()
    goodMeasurementsStr = Str()
    totalIterations = Member()

    #time traits
    timeStarted = Float()
    timeStartedStr = Str()
    currentTime = Float()
    currentTimeStr = Str()
    timeElapsed = Float()
    timeElapsedStr = Str()
    totalTime = Float()
    totalTimeStr = Str()
    timeRemaining = Float()
    timeRemainingStr = Str()
    completionTime = Float()
    completionTimeStr = Str()

    #variables traits
    dependentVariablesStr = Str()
    constantsStr = Str()
    constantReport = Member()
    variableReport = Member()
    variablesNotToSave = Str()

    #list of Analysis objects
    analyses = Member()

    #optimization
    max_iterations = Int()
    optimizer_count = Int()
    optimizer_iteration_count = Int()
    experiment_hdf5 = Member()

    #things we would rather not have to make Atom definitions for, but are forced to by Atom
    timeOutExpired = Member()
    instruments = Member()
    completedMeasurementsByIteration = Member()
    independentVariables = Member()
    ivarNames = Member()
    ivarIndex = Member()
    ivarValueLists = Member()
    ivarSteps = Member()
    constants = Member()
    vars = Member()
    hdf5 = Member()
    measurementResults = Member()
    iterationResults = Member()
    allow_evaluation = Member()
    gui = Member()  # a reference to the gui Main, for use in Prop.set_gui
    optimizer = Member()
    ivarBases = Member()
    instrument_update_needed = Bool(True)
    ROITypeString = Str()
    functional_waveforms = Member()


    # threading
    exp_thread = Member()  # thread running the exp so gui is not blocked
    restart = Member()  # threading event for communication
    task = Member()  # signaling which task should be completed

    def __init__(self,
                 config_instrument=None,
                 cache_location=None,
                 settings_location=None,
                 temp_location=None):
        """
        Defines a set of instruments, and a sequence of what to do with them.
        """
        logger.debug('experiment.__init__()')

        if config_instrument is None:
            logger.critical(
                "Experiment received no ConfigInstrument: {}".format(self))
            raise PauseError
        if cache_location is None:
            logger.critical(
                "Experiment received no cache location: {}".format(self))
            raise PauseError
        if settings_location is None:
            logger.critical(
                "Experiment received no settings file location: {}".format(self)
            )
            raise PauseError
        if temp_location is None:
            logger.critical(
                "Experiment received no temporary file location:"
                " {}".format(self))
            raise PauseError

        self.allow_evaluation = False
        # name is 'experiment', associated experiment is self
        super(Experiment, self).__init__('experiment', self)
        self.Config = config_instrument
        self.Config.experiment = self
        # default values
        self.cache_dir = cache_location
        self.setting_path = settings_location
        self.temp_path = temp_location

        self.constantReport = StrProp('constantReport', self, 'Important output that does not change with iterations', '""')
        self.variableReport = StrProp('variableReport', self, 'Important output that might change with iterations', '""')
        self.optimizer = optimization.Optimization('optimizer', self, 'updates independent variables to minimize cost function')

        # a list of the instruments this experiment has defined
        self.instruments = []
        self.completedMeasurementsByIteration = []
        self.independentVariables = ListProp('independentVariables', self, listElementType=IndependentVariable,
                                             listElementName='independentVariable')
        self.ivarIndex = []
        self.vars = {}
        self.analyses = []
        self.ROITypeString = 'gaussian_roi'  # used in analysis.py; can be overwritten by experiment classes
        self.functional_waveforms = functional_waveforms.FunctionalWaveforms('functional_waveforms', self,
                                                                             'Waveforms for HSDIO, DAQmx DIO, and DAQmx AO; defined as functions')

        self.properties += ['version', 'constantsStr', 'independentVariables', 'dependentVariablesStr',
                            'pauseAfterIteration', 'pauseAfterMeasurement', 'pauseAfterError',
                            'reload_settings_after_pause', 'repeat_experiment_automatically',
                            'saveData', 'saveSettings',
                            'save_separate_notes', 'save2013styleFiles', 'localDataPath', 'networkDataPath',
                            'copyDataToNetwork', 'experimentDescriptionFilenameSuffix', 'measurementTimeout',
                            'measurementsPerIteration', 'willSendEmail', 'emailAddresses', 'progress', 'progressGUI',
                            'iteration', 'measurement', 'goodMeasurements', 'totalIterations', 'timeStarted',
                            'currentTime', 'timeElapsed', 'timeRemaining', 'totalTime', 'completionTime',
                            'constantReport', 'variableReport', 'variablesNotToSave', 'notes', 'max_iterations',
                            'enable_sounds', 'enable_instrument_threads', 'optimizer', 'optimizer_count',
                            'optimizer_iteration_count']
        #we do not load in status as a variable, to allow old settings to be loaded without bringing in the status of
        #the saved experiments

        # experiment variable should be excluded from the hdf5 file
        # any variables added here should be csv format
        self.variablesNotToSave='experiment'

        # setup the experiment thread
        self.restart = threading.Event()
        self.exp_thread = threading.Thread(
            target=self.exp_loop,
            name='exp_thread'
        )
        self.exp_thread.daemon = True
        self.exp_thread.start()
        self.task = 'none'

    def exp_loop(self):
        """Run the experimental loop sequence.

        This is designed to be run in a separate thread.
        """
        while True:  # run forever
            # wait for the cue to restart the experiment
            self.restart.wait()

            # check the task flag to see what to do
            if self.task == 'go':
                # now do that fancy experiment
                self.go()
            elif self.task == 'upload':
                # upload the stuff to the instruments
                self.upload()
            elif self.task == 'end':
                # end the current experiment
                self.end()
            else:
                msg = 'Unrecognized task flag `{}` encountered. Doing nothing.'
                self.error(msg.format(self.task))

            # clear the task flag
            self.task = 'none'

    def applyToSelf(self, dict):
        """Used to apply a bunch of variables at once.  This function is called
         using an Enaml deferred_call so that the updates are done in the GUI
         thread.
         """

        for key, value in dict.iteritems():
            try:
                setattr(self, key, value)
            except Exception as e:
                logger.warning('Exception applying {} with value {} in experiments.applyToSelf.\n{}'.format(key, value, e))
                raise PauseError

    def autosave(self):
        logger.debug('Saving settings to default settings.hdf5 ...')
        # remove old autosave file
        try:
            os.remove(self.temp_path)
        except Exception as e:
            logger.debug('Could not delete previous_settings.hdf5:\n'+str(e))
        try:
            os.rename(self.setting_path, self.temp_path)
        except Exception as e:
            logger.error('Could not rename old settings.hdf5 to '
                         'previous_settings.hdf5:\n'+str(e))
        # create file
        f = h5py.File(self.setting_path, 'w')
        # recursively add all properties
        x = f.create_group('settings')
        self.toHDF5(x)
        f.flush()
        return f
        # you will need to do autosave().close() wherever this is called

    def create_data_files(self):
        """Create a new HDF5 file to store results.  This is done at the
        beginning of every experiment.
        """

        # if a prior HDF5 results file is open, then close it
        if hasattr(self, 'hdf5') and (self.hdf5 is not None):
            try:
                self.hdf5.flush()
                self.hdf5.close()
            except Exception as e:
                logger.warning('Exception closing hdf5 file.\n'+str(e))
                raise PauseError

        if self.saveData:
            #create a new directory for experiment

            #build the path
            self.dailyPath = datetime.datetime.fromtimestamp(self.timeStarted).strftime('%Y_%m_%d')
            self.experimentPath = datetime.datetime.fromtimestamp(self.timeStarted).strftime('%Y_%m_%d_%H_%M_%S_')+self.experimentDescriptionFilenameSuffix.rstrip()
            self.path = os.path.join(self.localDataPath, self.dailyPath, self.experimentPath)

            #check that it doesn't exist first
            if not os.path.isdir(self.path):
                #create the directory
                #use os.makedirs instead of os.mkdir to create the intermediate dailyPath directory if it does not exist
                os.makedirs(self.path)

            #save to a real file
            self.hdf5 = h5py.File(os.path.join(self.path, 'results.hdf5'), 'a')

        else:
            #hold results only in memory
            self.hdf5 = h5py.File('results.hdf5', 'a', driver='core', backing_store=False)

        #add settings
        if self.saveSettings:

            #start by saving settings
            logger.debug('Autosaving')
            autosave_file = self.autosave()
            logger.debug('Done autosaving')

            try:
                logger.debug('Copying autosave data to current HDF5')
                autosave_file['settings'].copy(autosave_file['settings'], self.hdf5)
            except:
                logger.warning('Problem trying to copy autosave settings to HDF5 results file.')
                raise PauseError
            finally:
                autosave_file.close()
                logger.debug('Autosave closed')

        #store independent variable data for experiment
        t = time.time()
        self.hdf5.attrs['start_time'] = t
        self.hdf5.attrs['start_time_str'] = self.date2str(t)
        self.hdf5.attrs['ivarNames'] = self.ivarNames
        #self.hdf5.attrs['ivarValueLists'] = self.ivarValueLists  # temporarily disabled because HDF5 cannot handle arbitrary length lists of lists
        self.hdf5.attrs['ivarSteps'] = self.ivarSteps

        #create a group to hold iterations in the hdf5 file
        self.hdf5.create_group('iterations')

        #store notes.  They will be stored again at the end of the experiment.
        self.hdf5['notes'] = self.notes

        logger.debug('Finished create_data_files()')

    def create_hdf5_iteration(self):
        #write the iteration settings to the hdf5 file
        self.iterationResults = self.hdf5.create_group('iterations/'+str(self.iteration))
        t = time.time()
        self.iterationResults.attrs['start_time'] = t
        self.iterationResults.attrs['start_time_str'] = self.date2str(t)
        self.iterationResults.attrs['iteration'] = self.iteration
        self.iterationResults.attrs['ivarNames'] = self.ivarNames
        self.iterationResults.attrs['ivarValues'] = [i.currentValue for i in self.independentVariables]
        self.iterationResults.attrs['ivarIndex'] = self.ivarIndex
        self.iterationResults['report'] = self.variableReport.value

        #store the independent and dependent variable space
        v = self.iterationResults.create_group('variables')
        ignoreList = self.variablesNotToSave.split(',')
        for key, value in self.vars.iteritems():
            if key not in ignoreList:
                try:
                    if not inspect.isfunction(value):
                        if isinstance(value, dict):
                            v[key] = str(value)
                        else:
                            v[key] = value
                except Exception as e:
                    logger.warning('Could not save variable '+key+' as an hdf5 dataset with value: '+str(value)+'\n'+str(e))

    def create_optimizer_iteration(self):
        """
        This method sets up the hdf5 storage for a new optimization loop.  It is called whenever a new iteration is
        started, and then checks to see that we really are at the beginning of a whole optimization loop.
        An hdf5 group is created to store the iterations for only this optimization loop.  Hard links are created so
        that the iteration results will show up both in this new group, and in the iterations directory that stores
        the iterations for all loops.  An optimizer_iteration_count resets every loop so that the results can be stored
        into this new directory counting for zero.
        """

        # if this is a new optimization loop
        experiment_hdf5_path = 'experiments/{}'.format(self.optimizer_count)
        if experiment_hdf5_path not in self.hdf5:
            # create a new group to store all the iterations in this loop
            self.experiment_hdf5 = self.hdf5.create_group(experiment_hdf5_path)
            self.experiment_hdf5.attrs['experiment_number'] = self.optimizer_count
            # reset the optimization_iteration number, which tracks how many iterations are in this loop
            self.optimizer_iteration_count = 0
        # add this iteration to the group
        self.experiment_hdf5['iterations/'+str(self.optimizer_iteration_count)] = self.iterationResults

    def date2str(self, time):
        return datetime.datetime.fromtimestamp(time).strftime('%Y-%m-%d %H:%M:%S')

    def end_now(self):
        """Launches end() in a new thread, to keep GUI free"""
        if self.status == 'running':
            msg = (
                'You cannot manually finish an experiment that is still'
                ' running.  Pause first.'
            )
            logger.warning(msg)
        else:
            self.task = 'end'
            self.restart.set()
            self.restart.clear()

    def end(self):
        """Finishes the current experiment, and then uploads data"""

        try:
            # run final analysis
            self.postExperiment()
            # save final PDF images and such
            for i in self.analyses:
                i.finalize(self.hdf5)
            self.optimizer.finalize(self.hdf5)
            # upload results
            self.upload()
        except PauseError:
            self.set_status('paused after error')
        except Exception as e:
            logger.warning('Uncaught Exception in experiment.end:\n{}\n{}'.format(e, traceback.format_exc()))
            self.set_status('paused after error')


    def eval_general(self, string):
        return cs_evaluate.evalWithDict(string, self.vars)

    def eval_bool(self, string):
        value, valid = self.eval_general(string)
        if value is None:
            return value, valid
        else:
            try:
                return bool(value), valid
            except Exception as e:
                logger.warning('Unable to convert string to bool: {}, {}\n{}\n'.format(string, value, e))
                return None, False

    def eval_float(self, string):
        value, valid = self.eval_general(string)
        if value is None:
            return value, valid
        else:
            try:
                return float(value), valid
            except Exception as e:
                logger.warning('Unable to convert string to bool: {}, {}\n{}\n'.format(string, value, e))
                return None, False

    def evaluate(self):
        """Resolve all equation in instruments.  This is overwritten from Prop."""
        if self.allow_evaluation:
            logger.debug('Experiment.evaluate() ...')

            # start with the constants
            self.evaluate_constants()

            # add the independent variables current values to the dict
            self.updateIndependentVariables()
            ivars = dict([(i.name, i.currentValue) for i in self.independentVariables])
            self.vars.update(ivars)
            self.vars.update({'experiment': self})

            #evaluate the dependent variable multi-line string
            cs_evaluate.execWithDict(self.dependentVariablesStr, self.vars)

            #evaluate variable report
            #at this time the properties are not all evaluated, so, we must do this one manually
            self.variableReport.evaluate()

            # evaluate everything else
            logger.debug('Evaluating experiment properties ...')
            super(Experiment, self).evaluate()

            # post the new experiment status variables to the GUI
            self.update_gui()

            logger.debug('Finished experiment.evaluate().')

    def evaluate_constants(self):
        if self.allow_evaluation:
            # create a new dictionary and evaluate the constants into it
            self.constants = {}
            cs_evaluate.execWithDict(self.constantsStr, self.constants)

            # reset self.vars so it can be used in evaluating the constantReport
            self.vars = self.constants.copy()

            # evaluate constant report
            #at this time the properties are not all evaluated, so, we must do this one manually
            self.constantReport.evaluate()

    def evaluateAll(self):
        if self.allow_evaluation:
            self.evaluate_constants()
            self.evaluateIndependentVariables()
            self.evaluate()

    def evaluateIndependentVariables(self):
        if self.allow_evaluation:
            logger.debug('Evaluating independent variables ...')

            #make sure ivar functions have been parsed
            self.independentVariables.evaluate()

            #set up independent variables
            self.ivarNames = [i.name for i in self.independentVariables]  # names of independent variables
            self.ivarValueLists = [i.valueList for i in self.independentVariables]
            self.ivarSteps = [i.steps for i in self.independentVariables]
            self.totalIterations = int(numpy.product(self.ivarSteps))

            # figure out how often each ivar will update with iterations (the "base")
            # the first (i.e. top) ivar becomes the "inner loop"
            self.ivarBases = numpy.roll(numpy.cumprod(self.ivarSteps), 1)
            if len(self.ivarBases>0):
                self.ivarBases[0] = 1

    def goThread(self):
        if self.progress == 100:
            logger.info("Experiment is already complete. "
                        "Reset to start a new one")
        else:
            if self.status == 'idle':
                self.pause_now()
            self.task = 'go'
            self.restart.set()
            self.restart.clear()

    def go(self):
        """Pick up the experiment wherever it was left off."""

        #check if we are ready to do an experiment
        if not self.status.startswith('paused'):
            logger.warning('Current status is {}. Cannot continue an experiment unless status is paused.'.format(self.status))
            return  # exit
        self.set_status('running')  # prevent another experiment from being started at the same time
        self.set_gui({'valid': True})
        logger.info('running experiment')

        try:  # if there is an error we exit the inner loops and respond appropriately

            # optimization and iteration loop
            logger.debug('Before go() loop: status = {}, and optimizer.is_done = {}'.format(self.status, self.optimizer.is_done))
            while (self.status == 'running') and ((not self.optimizer.enable) or (not self.optimizer.is_done)):
                logger.debug("starting new iteration")

                # at the start of a new iteration, or every time if requested
                if self.instrument_update_needed or self.reload_settings_after_pause:
                    logger.debug("evaluating")
                    self.evaluate()  # update ivars to current iteration and re-calculate dependent variables
                    logger.debug("updating instruments")
                    self.update()  # send current values to hardware
                    self.instrument_update_needed = False  # no need to update the settings until the next iteration

                # only at the start of a new iteration
                if len(self.completedMeasurementsByIteration) <= self.iteration:
                    self.completedMeasurementsByIteration.append(0)  # start a new counter for this iteration
                if not (str(self.iteration) in self.hdf5['iterations']):
                    self.create_hdf5_iteration()  # create an entry in the in hdf5 file
                    self.preIteration()  # reset the analyses

                    # only at the start of a new optimization experiment loop
                    self.create_optimizer_iteration()

                # loop until the desired number of measurements are taken
                # self.measurement = 0
                while (self.goodMeasurements < self.measurementsPerIteration) and (self.status == 'running'):
                    self.set_gui({'valid': True})  # reset all the red error background graphics to show no-error
                    logger.info('iteration {} measurement {}'.format(self.iteration, self.measurement))
                    self.measure()  # tell all instruments to do the experiment sequence and acquire data
                    self.updateTime()  # update the countdown/countup clocks
                    logger.debug('updating measurement count')

                    # make sure results are written to disk
                    logger.debug('flushing hdf5')
                    self.hdf5.flush()

                    # increment the measurement counter, except at the end
                    if self.goodMeasurements < self.measurementsPerIteration:
                        self.measurement += 1
                    else:
                        break

                    # pause after measurement
                    if self.status == 'running' and self.pauseAfterMeasurement:
                        logger.info('paused after measurement')
                        self.set_status('paused after measurement')
                        self.set_gui({'valid': False})
                        if self.enable_sounds:
                            sound.error_sound()

                    self.update_gui()
                    logger.debug("completed measurement")

                # Measurement loop exited, but that might mean we are paused, or an error.
                # So check to see if we completed the iteration.
                if self.goodMeasurements >= self.measurementsPerIteration:

                    # We have completed this iteration, move on to the next one
                    logger.info("Finished iteration")

                    self.postIteration()  # run analysis

                    # if this was the last iteration in this optimization loop, then run analysis and run optimizer
                    if (self.iteration % self.totalIterations) == self.totalIterations-1:

                        logger.debug("Finished all iterations")
                        self.postExperiment()  # run analyses
                        self.optimizer.update(self.hdf5, self.experiment_hdf5)  # update optimizer variables
                        if self.optimizer.enable:
                            self.preExperiment()
                        if self.optimizer.is_done:
                            # the experiment is finished, run final analysis, upload data, and exit loop
                            for i in self.analyses:
                                i.finalize(self.hdf5)
                            self.optimizer.finalize(self.hdf5)
                            self.upload()
                            break
                        self.optimizer_count += 1

                    # if we didn't end the optimization above, we should advance to the next iteration
                    self.iteration += 1  # increase iteration number
                    self.optimizer_iteration_count += 1
                    self.measurement = 0  # reset measurement count
                    self.goodMeasurements = 0  # reset good measurement count

                    # pause after iteration
                    if self.pauseAfterIteration:
                        if self.status == 'running':
                            logger.info('paused after iteration')
                            self.set_status('paused after iteration')
                            self.set_gui({'valid': False})
                            # play sounds
                            if self.enable_sounds:
                                sound.error_sound()
                        elif self.status == 'paused after measurement':
                            self.set_status('paused after iteration')
                            self.set_gui({'valid': False})
                            # we already played the sounds after the measurement.  Don't play the sounds again.
                        # else the status is idle or error, and we should not downgrade the status to paused

                    # signal that the instrument settings need to be updated at the beginning of the next iteration
                    self.instrument_update_needed = True

        except PauseError:
            # This should be the only place that PauseError is explicitly handed.
            # All other non-fatal errors caught higher up in the experiment chain should
            # gracefully handle the error, then 'raise PauseError' so that the experiment
            # exits out to this point.

            # Delete this measurement from the results, since the data is probably no good anyway, and the
            # measurement number may not have incremented and may have to be reused.
            try:
                del self.measurementResults  # remove the reference to the bad data
                del self.hdf5['iterations/{}/measurements/{}'.format(self.iteration, self.measurement)]  # really remove the bad data
            except:
                pass

            if self.pauseAfterError:
                self.set_status('paused after error')
            self.set_gui({'valid': False})
            if self.enable_sounds:
                sound.error_sound()

        except Exception as e:
            logger.error('Exception during experiment:\n'+str(e)+'\n'+str(traceback.format_exc())+'\n')

            # Delete this measurement from the results, since the data is probably no good anyway, and the
            # measurement number may not have incremented and may have to be reused.
            try:
                del self.measurementResults  # remove the reference to the bad data
                del self.hdf5['iterations/{}/measurements/{}'.format(self.iteration, self.measurement)]  # really remove the bad data
            except:
                pass

            if self.pauseAfterError:
                self.set_status('paused after error')
            self.set_gui({'valid': False})
            if self.enable_sounds:
                sound.error_sound()

    def loadDefaultSettings(self):
        """Look for settings.hdf5 in cache and if it exists, load it."""
        logger.debug('Loading default settings ...')

        if os.path.isfile(self.setting_path):
            self.load(self.setting_path, check_loaded_from_setting_box=False)
        else:
            logger.debug('Default settings.hdf5 does not exist.')


    def load(self, path, check_loaded_from_setting_box=True):
        logger.debug('Loading file: '+path)

        # Disable any equation evaluation while loading.
        # We will evaluate everything after.
        if self.allow_evaluation:
            allow_evaluation_was_toggled = True
            self.allow_evaluation = False
        else:
            allow_evaluation_was_toggled = False

        # load hdf5 from a file
        if not os.path.isfile(path):
            logger.debug('Settings file {} does not exist'.format(path))
            raise PauseError

        # check if the requested file is a zip file, and if so,
        # convert it to a form h5py can read
        if zipfile.is_zipfile(path):
            zf = zipfile.ZipFile(path)
            filecontents = zf.read(os.path.basename(os.path.splitext(path)[0]))
            tempfile = open(os.path.join(self.cache_dir,
                                         "unzipped.hdf5"),
                            "wb")
            tempfile.write(filecontents)
            tempfile.close()
            path = os.path.join(self.cache_dir, "unzipped.hdf5")

        try:
            f = h5py.File(path, 'r')
        except Exception as e:
            logger.warning('Problem loading HDF5 settings file in experiment.l'
                           'oad().\n{}\n{}\n'.format(e, traceback.format_exc()))
            raise PauseError

        settings = f['settings/experiment']

        try:
            self.fromHDF5(settings)
        except Exception as e:
            logger.warning('in experiment.load()\n'+str(e)+'\n'+
                           str(traceback.format_exc()))
            # this is an error, but we will not pass it on,
            # in order to finish loading

        f.close()
        logger.debug('File load done.')

        if allow_evaluation_was_toggled:
            self.allow_evaluation = True

        # check the load from settings box in functional waveforms to ensure the waveform
        # in the loaded file is the one that gets use
        if check_loaded_from_setting_box:
            self.functional_waveforms.load_from_settings = True

        # now re-evaluate everything
        self.evaluateAll()

    def measure(self):
        """Enables all instruments to begin a measurement.

        Sent at the beginning of every measurement. Actual output or input from
        the measurement may yet wait for a signal from another device.
        """

        logger.debug('starting measurement')
        start_time = time.time()  # record start time of measurement
        self.timeOutExpired = False

        # start each instrument
        for i in self.instruments:
            if i.enable:
                # check that the instruments are initalized
                if not i.isInitialized:
                    logger.debug('experiment.measure() initializing '+i.name)
                    i.initialize()  # reinitialize
                    # Minho: Should i.update() be here?
                    #i.update()  # put the settings to where they should be at this iteration
                else:
                    # check that the instrument is not already occupied
                    if not i.isDone:
                        logger.warning('Instrument '+i.name+' is already busy, and will be stopped and restarted.')
                        i.stop()
                    # set a flag to indicate each instrument is now busy
                    i.isDone = False
                    # let each instrument begin measurement
                    # put each in a different thread, so they can proceed simultaneously
                    if self.enable_instrument_threads:
                        threading.Thread(target=i.start).start()
                    else:
                        i.start()
        logger.debug('all instruments started')

        # loop until all instruments are done
        # TODO: can we do this with a callback?
        while (not all([i.isDone for i in self.instruments])) and (self.status == 'running'):
            if time.time() - start_time > self.measurementTimeout:  # break if timeout exceeded
                self.timeOutExpired = True
                logger.warning('The following instruments timed out: '+str([i.name for i in self.instruments if not i.isDone]))
                return  # exit without saving results
            time.sleep(.01)  # wait a bit, then check again
        logger.debug('all instruments done')

        # give each instrument a chance to acquire final data
        for i in self.instruments:
            if i.enable:
                i.acquire_data()

        # record results to hdf5
        self.measurementResults = self.hdf5.create_group('iterations/'+str(self.iteration)+'/measurements/'+str(self.measurement))
        self.measurementResults.attrs['start_time'] = start_time
        self.measurementResults.attrs['start_time_str'] = self.date2str(start_time)
        self.measurementResults.attrs['measurement'] = self.measurement
        self.measurementResults.create_group('data')  # for storing data
        for i in self.instruments:
            # Pass the hdf5 group to each instrument so they can write results
            # to it.  We do it here because h5py is not thread safe, and also
            # this way we avoid saving results for aborted measurements.
            if i.enable:
                i.writeResults(self.measurementResults['data'])

        self.postMeasurement()

    def pause_now(self):
        """
        Pauses experiment as soon as possible. Should only be called in
        experiment logic, not via the GUI.
        """
        # Manually force the status to idle, to cause the experiment to end
        self.status = 'paused immediate'
        # stop each instrument
        for i in self.instruments:
            i.isDone = True

    def postExperiment(self):
        logger.info('Running postExperiment analyses ...')
        # run analysis
        for i in self.analyses:
            i.postExperiment(self.experiment_hdf5)

    def postIteration(self):
        logger.debug('Starting postIteration()')
        # run analysis
        for i in self.analyses:
            i.postIteration(self.iterationResults, self.hdf5)

    def finalizeMeasurement(self, analysisList, measResults, iterResults):
        good = True
        delete = False
        # get the analysis iteration
        iter = iterResults.attrs['iteration']
        for analysis in analysisList:
            # print "="*20
            # print analysis['name']
            # print analysis['good']
            # print analysis['delete']
            if analysis['delete']:
                good = False
                delete = True
                break
            if not analysis['good']:
                good = False

        if delete:
            try:
                # get the measurement number
                m = measResults.attrs['measurement']
                # remove the reference to the bad data
                del measResults
                # really remove the bad data
                del iterResults['measurements/'+str(m)]
            except:
                logger.exception('error when trying to delete measurement')

        if good:
            self.goodMeasurements += 1
            # add one to the last counter in the list
            self.completedMeasurementsByIteration[iter] += 1

    def postMeasurementCallBack(self, analysisList):
        """Returns a function pointer to be passed to the analysis so that it
        can be called when analysis finishes.

        This callback function is in charge of incrementing the
        goodMeasurements counter based on the results of the error parameter.

        There error parameter follows the following definition:
        None or 0   : no error, increment counter
        1           : error, continue don't increment
        2           : error, continue don't increment and purge data
        3           : error, stop other analyses don't increment and purge data

        Due to complexity of threading, error code 3 will be depricated.
        """

        # hdf5 datagroups as well
        measResults = self.measurementResults
        iterResults = self.iterationResults

        def wrapper(analysis):
            def callback(error):
                good = True
                delete = False
                if not self.saveData:
                    # we are not saving data so remove the measurement from the
                    # hdf5
                    delete = True

                if error is None or error == 0:
                    pass
                elif error == 1:
                    # continue, but do not increment goodMeasurements
                    good = False
                elif error == 2:
                    # continue, but do not increment goodMeasurements
                    # delete data when done
                    good = False
                    delete = True
                elif error == 3:
                    # stop, do not increment goodMeasurements
                    # delete data when done
                    good = False
                    delete = True
                    logger.warning('Analysis Error code 3 is no longer supported and will not stop other analyses.')
                else:
                    msg = (
                        'bad return value {} in experiment.postMeasurement()'
                    ).format(error)
                    logger.warning(msg)

                resultDict = {}
                resultDict['name'] = analysis.name
                resultDict['good'] = good
                resultDict['delete'] = delete
                analysisList.append(resultDict)
                logger.debug("{}: {}/{}".format(analysis.name, len(analysisList), len(self.analyses)))

                if len(analysisList) == len(self.analyses):
                    self.finalizeMeasurement(analysisList, measResults, iterResults)

            return callback

        return wrapper

    def postMeasurement(self):
        logger.debug('starting post measurement analyses')
        # run analyses
        analysisList = []
        callback = self.postMeasurementCallBack(analysisList)
        for i in self.analyses:
            #print(i.name)
            #time_debug=time.time()  # Start time measurement
            #logger.info('Running :{0}'.format(i))
            i.postMeasurement(
                callback(i),
                self.measurementResults,
                self.iterationResults,
                self.hdf5
            )
            #time2_debug=1000.0*(time.time()-time_debug)
            # To measure how long do analyses take.
            #if (time2_debug>0.5): # Don't display if the process takes less than 0.5 ms
            #logger.info('Completed Running :{0}, time usage : {1}ms'.format(i,round(time2_debug,0)))

    def preExperiment(self):
        # run analyses
        for count, i in enumerate(self.analyses):
            try:
                i.preExperiment(self.hdf5)
            except Exception as e:
                logger.exception("In evaluation of Analysis {}".format(count))
                raise PauseError

    def preIteration(self):
        # run analyses
        for i in self.analyses:
            i.preIteration(self.iterationResults, self.hdf5)

    def reset(self):
        """Reset the iteration variables and timing."""

        if self.status.startswith('paused'):
            self.stop()
            self.pauseAfterError = False
            self.pauseAfterIteration = False
            self.pauseAfterMeasurement = False

        if self.status != 'idle':
            logger.info('Current status is {}. Cannot reset experiment unless status is idle.  Try halting first.'.format(self.status))
            return False

        logger.info('resetting experiment')
        self.set_gui({'valid': True})

        self.set_status('beginning experiment')

        # reset experiment variables
        self.timeStarted = time.time()
        self.iteration = 0
        self.measurement = 0
        self.goodMeasurements = 0
        self.completedMeasurementsByIteration = []
        self.progress = 0

        self.update_gui()

        # setup data directory and files
        self.create_data_files()

        # evaluate the constants and independent variables
        self.evaluate_constants()
        self.evaluateIndependentVariables()
        self.updateIndependentVariables()
        self.hdf5['constant_report'] = self.constantReport.value

        # run analyses preExperiment
        self.preExperiment()

        # setup optimizer
        self.optimizer.setup(self.hdf5)
        self.optimizer_count = 0

        # signal that settings should be updated on 1st iteration
        self.instrument_update_needed = True

        self.set_status('paused before experiment')
        # returning True signals resetAndGo() to continue on to go()
        return True

    def resetAndGo(self):
        """Reset the iteration variables and timing, then proceed with an experiment."""
        if self.reset():
            self.task = 'go'
            # if the reset succeeded, then set the thread event
            self.restart.set()
            # then clear it
            self.restart.clear()
        else:
            logger.error("self.reset returned False")

    def save(self, path):
        """This function saves all the settings."""

        logger.info('Saving...')

        # HDF5
        self.autosave().close()

        # copy to default location
        logger.debug('Copying HDF5 to save path...')
        shutil.copy(self.setting_path, path)

        #XML
        #logger.debug('Creating XML...')
        #x = self.toXML()
        ##write to the chosen file
        #logger.debug('Writing XML to save path...')
        #f = open(path+'.xml', 'w')
        #f.write(x)
        #f.close()
        #logger.debug('Writing default XML...')
        ##write to the default file
        #f = open('settings.xml', 'w')
        #f.write(x)
        #f.close()

        logger.info('... Save Complete.')

    def set_status(self, s):
        self.status = s
        self.set_gui({'statusStr': s})

    def stop(self):
        """Stops output as soon as possible.  This is not run during the course of a normal experiment."""
        # Manually force the status to idle, to cause the experiment to end
        self.status = 'idle'
        # stop each instrument
        for i in self.instruments:
            i.isDone = True
            i.stop()
            i.isInitialized = False
        self.set_gui({'statusStr': self.status})

    def time2str(self, time):
        return str(datetime.timedelta(seconds=time))

    def update(self):
        """Sends current settings to the instrument.  This function is run at the beginning of every new iteration.
        Does not explicitly call evaluate, to avoid duplication of effort.
        All calls to evaluate should already have been accomplished."""

        for i in self.instruments:
            if i.enable:
                #check that the instruments are initialized
                if not i.isInitialized:
                    i.initialize()  # reinitialize
                i.update()  # put the settings to where they should be at this iteration

    def update_gui(self):
        logger.debug('experiment.update_gui()')
        self.set_gui({'measurementStr': str(self.measurement),
                    'iterationStr': '{} of {}'.format(self.iteration, self.totalIterations-1),
                    'goodMeasurementsStr': '{} of {}'.format(self.goodMeasurements, self.measurementsPerIteration-1),
                    'statusStr': self.status,
                    'timeStartedStr': self.date2str(self.timeStarted),
                    'currentTimeStr': self.date2str(self.currentTime),
                    'timeElapsedStr': self.time2str(self.timeElapsed),
                    'timeRemainingStr': self.time2str(self.timeRemaining),
                    'totalTimeStr': self.time2str(self.totalTime),
                    'completionTimeStr': self.date2str(self.completionTime),
                    'progressGUI': self.progress
        })

    def updateIndependentVariables(self):
        """takes the iteration number and figures out which index number each independent variable should have"""

        # find the current index for each
        index = (self.iteration//self.ivarBases) % self.ivarSteps

        for i, x in enumerate(self.independentVariables):
           if (not self.optimizer.enable) or (not x.optimize):  # update the variable is
                index[i] = x.setIndex(index[i])  # update each variable object
        self.ivarIndex = index

    def updateTime(self):
        """Updates the GUI clock and recalculates the time-to-completion predictions."""

        logger.debug('experiment.updateTime()')
        self.currentTime = time.time()

        self.timeElapsed = self.currentTime-self.timeStarted

        #calculate time per measurement
        completedMeasurements = sum(self.completedMeasurementsByIteration)
        if self.timeElapsed != 0:
            timePerMeasurement = completedMeasurements/self.timeElapsed
        else:
            timePerMeasurement = 1
        if len(self.completedMeasurementsByIteration) <= 1:
            #if we're still in the first iteration, use the intended number of measurements
            estTotalMeasurements = self.measurementsPerIteration*self.totalIterations
        else:
            #if we're after the first iteration, we have more information to work with, use the actual average number of measurements per iteration
            estTotalMeasurements = numpy.mean(self.completedMeasurementsByIteration[:-1])*self.totalIterations
        if estTotalMeasurements > 0:
            self.progress = int(100*completedMeasurements/estTotalMeasurements)
        else:
            self.progress = 0

        self.timeRemaining = timePerMeasurement*(estTotalMeasurements-completedMeasurements)
        self.totalTime = self.timeElapsed+self.timeRemaining
        self.completionTime = self.timeStarted+self.totalTime

    def upload(self):
        # store the notes again
        logger.info('Storing notes ...')
        del self.hdf5['notes']
        self.hdf5['notes'] = self.notes
        self.hdf5.flush()

        # copy to network
        if self.copyDataToNetwork:
            logger.info('Copying data to network...')
            shutil.copytree(self.path, os.path.join(self.networkDataPath,
                                                    self.dailyPath,
                                                    self.experimentPath))

        self.set_status('idle')
        logger.info('Finished Experiment.')
        self.progress = 100
        self.update_gui()
        if self.enable_sounds:
            sound.complete_sound()

    def upload_now(self):
        """Skip straight to uploading the current data."""
        if self.status == 'running':
            msg = (
                'You cannot manually finish an experiment that is still'
                ' running.  Pause first.'
            )
            logger.warning(msg)
        else:
            self.task = 'upload'
            self.restart.set()
            self.restart.clear()

    def exiting(self):
        pass
