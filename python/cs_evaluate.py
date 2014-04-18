#cs_evaluate.py
#A separate module where things can be evaluated without access to programmatic variables.
#author: Martin Lichtman
#created = 2013-08-22
#modified >= 2013-08-22

from __future__ import division  # always do float division
import logging
logger = logging.getLogger(__name__)

from numpy import *
#create a nice clean globals with only numpy, so we can keep resetting to this point
myGlobalSetup = globals().copy()
#the global dict that will hold the variables
myGlobals = myGlobalSetup.copy()

from cs_errors import PauseError

import traceback


def evalIvar(string):
    if string == '':
        return None
    else:
        try:
            return eval(string, myGlobalSetup.copy())
        except Exception as e:
            logger.warning('Could not evaluate independent variable: '+string+'\n'+str(e)+'\n'+str(traceback.format_exc())+'\n')
            raise PauseError

def evalWithDict(string, varDict=None, errStr=''):
    """string: the python expression to be evaluated
       varDict: a dictionary of variables, functions, modules, etc, to be used during the evaluation
       errStr: a string that says something about what is being evaluated, to make the error reporting useful
    """

    global myGlobals

    if varDict is None:
        #create default here, otherwise ALL default varDicts would be one-in-the-same
        varDict={}

    if string == '':
        return None
    else:
        try:
            #myGlobals is reset and filled with the dependent variables, and numpy, in execWithDict
            #varDict acts as locals, and in general will remain unchanged
            return eval(string, myGlobals, varDict)
        except Exception as e:
            print errStr+'Could not eval string: '+string+'\n'+str(e)+'\n'
            raise PauseError

def execWithDict(string, varDict=None):
    """This executes a string with a globals context containing only numpy.
    The passed in dictionary gets updated with newly defined locals.
    myGlobals persists so it can be used in evalWithDict."""

    global myGlobals

    if varDict is None:
        #create default here, otherwise ALL default varDicts would be one-in-the-same
        varDict={}

    if string != '':
        try:
            #globals_trap = {}
            myGlobals = myGlobalSetup.copy()
            exec(string, myGlobals, varDict)
            myGlobals.update(varDict)

            ##global_trap gets polluted with all sorts of built-in variables and gets thrown away
            #varDict acts as locals and gets updated implicitly,
            #so new variable values do not need to be passed back out of this function
        except Exception as e:
            logger.warning('Could not exec string:\n{}\n{}\n{}\n'.format(string, e, traceback.format_exc()))
            raise PauseError
