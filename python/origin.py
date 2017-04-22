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

from instrument_property import StrProp, IntProp

class Origin(TCP_Instrument, Analysis):
    version = '2017.04.20'

    def __init__(self, name, experiment, description=''):
        super(Origin, self).__init__(name, experiment, description)
                #self.streams = []
        #self.properties += ['enable','IP','port']
        self.IP = ''
        self.port = 0

    def start(self):
        print('hi')
        if self.enable:
            print('sending')
            self.send('get')
        self.isDone = True

    def update(self):
        pass

    def preExperiment(self, experimentResults):
        """This is called before an experiment.
        
        Args:
            experimentResults (obj): Reference to the HDF5 file for this experiment
        """

        # initialize any logged parameters that are on a per experiment basis
        # verify that all the streams are active
        # if not activate them
        #self.isInitialized = True
        print("does this get called?")
        print "origin.enable state: ", self.enable
        print "origin.IP: ", self.IP
        print "origin.port: ", self.port
        print "origin.timeout [s]: ", self.timeout.value

    def preIteration(self, iterationResults, experimentResults):
        # initialize any logged parameters that are on a per iteration basis
        pass
     
    def postMeasurement(self, measurementresults, iterationresults, experimentResults):
        """Results is a tuple of (measurementResult,iterationResult,experimentResult) references to HDF5 nodes for this
        measurement."""
        # log any per measurement parameters here
        return 0

    def postIteration(self, iterationresults, experimentResults):
        # log any per iteration parameters here
        return 0

    def postExperiment(self, experimentResults):
        # log any per experiment parameters here
        return 0

    def finalize(self,experimentResults):
        return 0

    def registerStream(self, streamName, dataType):
        raise NotImplementedError
        return streamObj

    def logData(self, stream, data):
        raise NotImplementedError        

    def closeStream(self, stream):
        raise NotImplementedError