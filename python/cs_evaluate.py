"""cs_evaluate.py
A separate module where things can be evaluated without access to programmatic variables.
author: Martin Lichtman
created = 2013-08-22
modified >= 2013-08-22
"""

from __future__ import division  # always do float division
__author__ = 'Martin Lichtman'
import logging
logger = logging.getLogger(__name__)

from numpy import *
#create a nice clean globals with only numpy, so we can keep resetting to this point
myGlobalSetup = globals().copy()
#the global dict that will hold the variables
myGlobals = myGlobalSetup.copy()

from cs_errors import PauseError

import traceback

def evalIvar(string, constants=None):
    """
    This function is used for the evaluation of independent variables.
    It uses a dictionary containing builtins and all numpy imports, and adds to that the previously evaluated constants.
    :param string: the independent variable function
    :param constants: the dictionary of previously evaluated constants.
    :return: the evaluated 1D numpy array
    """

    if string == '':
        return None
    else:
        if constants is None:
            constants = {}
        vars = myGlobalSetup.copy()
        vars.update(constants)
        try:
            return eval(string, vars)
        except Exception as e:
            logger.warning('Could not evaluate independent variable: '+string+'\n'+str(e)+'\n'+str(traceback.format_exc())+'\n')
            raise PauseError

def evalWithDict(string, varDict=None):
    """
    This function evalutes a string as python code.  It is used as the general evaluator for most input boxes.
    It is not used for the independent or dependent variable evaluation.
    It uses a passed in dictionary as the local namespace.
    inputs:
        string: the python expression to be evaluated
        varDict: a dictionary of variables, functions, modules, etc, to be used during the evaluation.
    outputs:
        value: the result of the evaluation
        valid: a boolean that says if the evaluation succeeded
    """

    global myGlobals

    if varDict is None:
        #create default here, otherwise ALL default varDicts would be one-in-the-same
        varDict = {}

    if string == '':
        # In the case of a blank string, we return None.  We do not let eval() run, because it would error
        # on a blank input.  We return valid=True, because blank might be an okay input in some cases (such as
        # in wavefom states where it means 'no change').  The caller can choose to set valid=False or raise an
        # Exception on value=None.
        return None, True
    else:
        try:
            # myGlobals is reset and filled with the dependent variables and numpy whenever execWithDict is run
            # varDict acts as locals, and in general will remain unchanged
            # If the eval succeeds, we return the value and valid=True
            return eval(string, myGlobals, varDict), True
        except Exception as e:
            #in case of a genuine eval error, we return value=None and valid=False
            logger.warning('Could not eval string: {}\n{}\n'.format(string, e))
            return None, False

def execWithDict(string, varDict=None):
    """This executes a string with a globals context containing only numpy.
    The passed in dictionary gets updated with newly defined locals.
    varDict persists so it can be used in evalWithDict."""

    global myGlobals

    if varDict is None:
        #create default here, otherwise ALL default varDicts would be one-in-the-same
        varDict={}
    myGlobals = myGlobalSetup.copy()
    if string != '':
        try:
            #varDict acts as locals and gets updated implicitly,
            #so new variable values do not need to be passed back out of this function
            exec(string, myGlobals, varDict)
        except Exception as e:
            logger.warning('Could not exec string:\n{}\n{}\n{}\n'.format(string, e, traceback.format_exc()))
            raise PauseError
    myGlobals.update(varDict)

def execWithGlobalDict(string, varDict=None):
    """This executes a string with a the global context containing the previous established global namespace plus
    any passed in variables.
    Variables defined in this context do not persist."""

    global myGlobals

    myVars = myGlobals.copy()

    if varDict is not None:
        myVars.update(varDict)

    if string != '':
        try:
            exec(string, myVars)
        except Exception as e:
            logger.warning('In execWithGlobalDict: Could not exec string:\n{}\n{}\n{}\n'.format(string, e,
                                                                                                traceback.format_exc()))
            raise PauseError
