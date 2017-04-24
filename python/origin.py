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

from h5py import Dataset, File
import sys, traceback

import time

import logging
logger = logging.getLogger(__name__)

preExperimentMsg    = 'PEXP'
postExperimentMsg   = 'EXPR'
preIterationMsg     = 'PITR'
postIterationMsg    = 'ITER'
postMeasurementMsg  = 'MEAS'

dtype_list = [
  "int","uint",
  "int64","uint64",
  "int32","uint32",
  "int16","uint16",
  "int8","uint8",
  "float32","float64"
  ]

def print_attrs(name, obj):
  print name
  for key, val in obj.attrs.iteritems():
    print("    {}: {}".format(key, val))

def print_dsets(name, obj):
  if isinstance(obj, Dataset):
    print '-'*10
    print name
    print obj.dtype
    print obj[()]
    print '-'*10

class Origin(Analysis):
  version = '2017.04.20'
  port = Member()
  IP = Str()
  measurementDataDict = Member()
  iterationDataDict = Member()
  ts = Member()  
  settings = Member() # hold the hdf5 group object so I can save resave the settigns after the experiment is finished


  def __init__(self, name, experiment, description=''):
    super(Origin, self).__init__(name, experiment, description)
    #self.streams = []
    self.IP = ''
    self.port = 0
    self.measurementDataDict = {}
    self.iterationDataDict = {}

    self.properties += ['measurementDataDict','iterationDataDict']

  def preExperiment(self, experimentResults):
    """This is called before an experiment."""
    print "measurementDataDict: ", self.measurementDataDict
    print "iterationDataDict: ", self.iterationDataDict
    return 0

  def preIteration(self, iterationResults, experimentResults):
    # initialize any logged parameters that are on a per iteration basis
    return 0
   
  def postMeasurement(self, measurementResults, iterationResults, experimentResults):
    """Results is a tuple of (measurementResult,iterationResult,experimentResult) references to HDF5 nodes for this
    measurement."""
    # set timestamp
    self.ts = long(time.time()*2**32)
    # process measurement data from hdf5 file
    measurementResults.visititems(self.processDatasets(self.measurementDataDict))
    return 0

  def postIteration(self, iterationResults, experimentResults):
    # log any per iteration parameters here
    # set timestamp
    self.ts = long(time.time()*2**32)
    # process iteration data from hdf5 file
    iterationResults.visititems(self.processDatasets(self.iterationDataDict))
    return 0

  def postExperiment(self, experimentResults):
    # log any per experiment parameters here

    # resave the properties now, since the dicts have been edited during the experiment
    super(Origin, self).toHDF5(experimentResults[self.settings])
    # open the settings.hdf5 file and resave this part
    try:
      f = File('settings.hdf5', 'a')
      super(Origin, self).toHDF5(f['settings/experiment'])
      f.flush() # write changes
    except Exception as e:
      logger.error('Uncaught Exception in origin.postExperiment:\n{}\n{}'.format(e, traceback.format_exc()))
    finally:
      f.close() #close the file
    return 0

  def finalize(self,experimentResults):
    return 0

  def newEntry(self, dset):
    return {
      'dtype': dset.dtype,  
      'time':self.ts, 
      'data':dset[()],
      'stream': False,
      'streamName': ''
    }

  def processDatasets(self, data_dict):
    def process(name, obj):
      if isinstance(obj, Dataset):
        #print '-'*10
        if(obj.dtype in dtype_list):
          print '='*10
          print name
          print obj.dtype
          #print 'shape: ', obj.shape
          if name in data_dict:
            print "dataset `", name, "` already exists in dict"
            if data_dict[name]['dtype'] == obj.dtype:
              data_dict[name]['time'] = self.ts
              data_dict[name]['data'] = obj[()]
            else:
              print "dataset type mismatch with stored type"
          else:
            data_dict[name] = self.newEntry(obj)
        
          print data_dict
          print '='*10
    return process

  def toHDF5(self, hdf_parent_node, name):
    print('hi I am here')
    print "name: ", name
    print "hdf_parent_node: ", hdf_parent_node
    print "path: ", hdf_parent_node.name
    # save the origin settings hdf5 object so we can rerun the toHDF5 method 
    # after the experiment fills out the dicts
    self.settings = hdf_parent_node.name
    super(Origin, self).toHDF5(hdf_parent_node)