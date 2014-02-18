#cs_evaluate.py
#A separate module where things can be evaluated without access to programmatic variables.
#author: Martin Lichtman
#created = 2013-08-22
#modified >= 2013-08-22

from __future__ import division #always do float division
from numpy import * #make all numpy functions accessible in this scope
import traceback
from cs_errors import PauseError, setupLog
logger=setupLog()


def evalWithDict(string,varDict={},errStr=''):
    '''string: the python expression to be evaluated
       varDict: a dictionary of variables, functions, modules, etc, to be used during the evaluation
       errStr: a string that says something about what is being evaluated, to make the error reporting useful
       '''
    if string!='':
        try:
            return eval(string,globals(),varDict)
        except Exception as e:
            logger.warning(errStr+'Could not eval string: '+string+'\n'+str(e)+str(traceback.format_exc())+'\n')
            return None
    return None

def execWithDict(string,varDict={}):
    '''This executes a string with the globals context including only numpy, and the locals including only what is passed in.
    The passed in dictionary gets updated with newly defined locals.'''
    if string!='':
        try:
            exec(string,globals(),varDict)
            #varDict gets updated implicitly
        except Exception as e:
            logger.warning('\nCould not exec string: '+string+'\n'+str(e)+str(traceback.format_exc())+'\n')