#cs_evaluate.py
#A separate module where things can be evaluated without access to programmatic variables.
#author: Martin Lichtman
#created = 2013-08-22
#modified >= 2013-08-22

from __future__ import division #always do float division

from numpy import *
myGlobalSetup = globals().copy()
#a global dict to hold some variables

from cs_errors import setupLog, PauseError
logger = setupLog(__name__)

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

def evalWithDict(string, varDict={}, errStr=''):
    """string: the python expression to be evaluated
       varDict: a dictionary of variables, functions, modules, etc, to be used during the evaluation
       errStr: a string that says something about what is being evaluated, to make the error reporting useful
    """

    global myGlobals

    if string == '':
        return None
    else:
        try:
            #globals_trap = myGlobalSetup.copy()
            return eval(string, myGlobals, varDict)
            ##global_trap gets polluted with all sorts of built-in variables and gets thrown away
            #varDict acts as locals, and in general will remain unchanged
        except Exception as e:
            logger.warning(errStr+'Could not eval string: '+string+'\n'+str(e)+'\n'+str(traceback.format_exc())+'\n')
            raise PauseError

def execWithDict(string, varDict={}):
    """This executes a string with an empty globals context.  If the user wishes to have access to numpy they should
     import numpy as a part of the dependentVariablesStr.
    The passed in dictionary gets updated with newly defined locals."""

    global myGlobals

    if string != '':
        try:
            #globals_trap = {}
            myGlobals=myGlobalSetup.copy()
            exec(string, myGlobals, varDict)
            myGlobals.update(varDict)
            ##global_trap gets polluted with all sorts of built-in variables and gets thrown away
            #varDict acts as locals and gets updated implicitly,
            #so new variable values do not need to be passed back out of this function
        except Exception as e:
            logger.warning('Could not exec string:\n{}\n{}\n{}\n'.format(string, e, traceback.format_exc()))
            raise PauseError
