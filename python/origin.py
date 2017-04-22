"""origin.py
   Part of the AQuA Cesium Controller software package

   author=Matthew Ebert
   created=2017-04-20

   This code saves registered parameters to the origin data sever on a per 
   measurement, iteration, or experiment cycle.

   The origin data server for SaffmanLab can be found here:
   https://github.com/QuantumQuadrate/Origin

   for other purposes (i.e. not SaffmanLab) it can be found here:
   https://github.com/Orthogonal-Systems/Origin
   """

__author__ = 'Matthew Ebert'

# Use Atom traits to automate Enaml updating
from atom.api import Int, Float, Str, Member, Bool

from analysis import Analysis
from cs_instruments import TCP_Instrument
from TCP import makemsg

from instrument_property import StrProp, IntProp

import sys, traceback

preExperimentMsg    = 'PEXP'
postExperimentMsg   = 'EXPR'
preIterationMsg     = 'PITR'
postIterationMsg    = 'ITER'
postMeasurementMsg  = 'MEAS'

class Origin(TCP_Instrument, Analysis):
    version = '2017.04.20'

    def __init__(self, name, experiment, description=''):
        super(Origin, self).__init__(name, experiment, description)
                #self.streams = []
        #self.properties += ['enable','IP','port']
        self.IP = ''
        self.port = 0

    def update(self):
        """There is no need to send instrument updates
        """
        pass

    def sendEvent(self, experimentResults, iterationResults, measurementResults, eventStr):
        if self.enable:
            msg = eventStr
            try:
                msg+= makemsg('file',experimentResults.filename)
                try: # if its a measurement then do that
                    msg+= makemsg('group',measurementResults.name)
                except Exception as e:
                    # otherwise if its an iteration then do that
                    # if not then just fail after the experiment
                    msg+= makemsg('group',iterationResults.name)

            except Exception as e:
                #print "Exception in user code:"
                #print '-'*60
                #traceback.print_exc(file=sys.stdout)
                #print '-'*60  
                pass

            resp = self.send(msg) 
        return 0

    def preExperiment(self, experimentResults):
        """This is called before an experiment."""
        return self.sendEvent(experimentResults, None, None, preExperimentMsg)

    def preIteration(self, iterationResults, experimentResults):
        # initialize any logged parameters that are on a per iteration basis
        return self.sendEvent(experimentResults, iterationResults, None, preIterationMsg)
     
    def postMeasurement(self, measurementResults, iterationResults, experimentResults):
        """Results is a tuple of (measurementResult,iterationResult,experimentResult) references to HDF5 nodes for this
        measurement."""
        return self.sendEvent(experimentResults, iterationResults, measurementResults, postMeasurementMsg)

    def postIteration(self, iterationResults, experimentResults):
        # log any per iteration parameters here
        return self.sendEvent(experimentResults, iterationResults, None, postIterationMsg)

    def postExperiment(self, experimentResults):
        # log any per experiment parameters here
        return self.sendEvent(experimentResults, None, None, postExperimentMsg)

    def finalize(self,experimentResults):
        return 0