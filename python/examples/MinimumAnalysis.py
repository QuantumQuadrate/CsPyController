class MinimumAnalysis(Analysis):
    version = '2016.06.02'

    def __init__(self, name, experiment, description=''):
        super(MinimumAnalysis, self).__init__(name, experiment, description)
        #self.properties += ['version', 'motors']

    def analyzeMeasurement(self,measurementresults,iterationresults,hdf5):
        return 0
        
    def preExperiment(self, hdf5):
        self.isInitialized = True

    def preIteration(self, iterationresults, hdf5):
        pass
     
    def postMeasurement(self, measurementresults, iterationresults, hdf5):
        return

    def postIteration(self, iterationresults, hdf5):
        return

    def postExperiment(self, hdf5):
        return

    def finalize(self,hdf5):
        return