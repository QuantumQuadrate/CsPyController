# Martin Lichtman
# created = 2013-10-07
# modified >= 2013-10-07

"""
cs_errors.py

Exceptions for use in the cesium controller software.
"""

class PauseError(Exception):
    '''This class is defined so we can raise an exception to have the experiment pause immediately.
    Usually this will be raised in the except clause after another error is caught.
    We want to be able to have try-except blocks for tricky parts of the code, but then still have the experiment pause
    as soon as possible.  We could just raise an Exception at this point, but this allows us to keep better track of what has
    happened, and to not log a second error.
    
    The preferred usage is that try-except blocks will look like this:
    
    try:
        some code
    except PauseError:
        #pass it on to the next level to exit out of any loops
        raise PauseError
    except someUndesiredButPredictableError as e:
        logger.error('An exception occurred here because of bad user input or lost TCP connection or something.  This can be fixed without restarting the program.\n'+str(e))
        raise PauseError
    except Exception as e:
        logger.error('An exception occurred, and we don't know what to do about it.\n'+str(e))
        
    If general Exceptions are not caught, then unexpected Exceptions will cause the code to stop and the error will be reported by the default mechanism.
    '''
    pass

def setupLog(name):
    '''This function sets up the error logging to both console and file, and should be imported and run at the top of each module in this package, by doing:
    from cs_errors import PauseError, setupLog
    logger=setupLog(__name__)
    '''
    import logging
    logger = logging.getLogger(name)
    hdlr = logging.FileHandler('log.txt')
    formatter = logging.Formatter(fmt='%(asctime)s %(threadName)s %(name)s %(levelname)s %(message)s', datefmt='%Y/%m/%d %H:%M:%S')
    hdlr.setFormatter(formatter)
    logger.addHandler(hdlr)
    return logger
