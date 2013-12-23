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
    happened, and to not log a second error.'''
    pass