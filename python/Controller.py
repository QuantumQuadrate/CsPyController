"""
The purpose of this class is to create an independent controller that knows about BOTH the experiment (model)
and enaml GUI (view).  It can then observe for changes on the model and update the view at that time.
"""
__author__ = 'Martin Lichtman'

#TODO: It is possible we can use this method more locally for each instrument.

from atom.api import Atom

class Controller(Atom):
    pass

