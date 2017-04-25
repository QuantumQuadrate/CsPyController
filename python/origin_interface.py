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

   TODO: Add timeout on register stream
   """

__author__ = 'Matthew Ebert'

# don't send to main server if we are testing
TEST = False

# Use Atom traits to automate Enaml updating
from atom.api import Int, Float, Str, Member, Bool, Long, Typed

from instrument_property import Prop, ListProp, BoolProp, StrProp, FloatProp

from analysis import Analysis

from h5py import Dataset, File
import sys, traceback, os.path

import time

import numpy as np

import logging
logger = logging.getLogger(__name__)

# first find ourself
fullBasePath = "C:\\LabSoftware\\Origin"
# do not change this
fullLibPath  = os.path.join(fullBasePath, "lib")
# use the default config file since we are all sharing a server
fullCfgPath  = os.path.join(fullBasePath, "config")
sys.path.append(fullLibPath)

from origin.client import server
from origin import current_time, timestamp

import ConfigParser

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

class Stream(Prop):
  ''' a class representing an origin stream
  '''
  name   = Str()
  fullPath = Str()
  dtype  = Str()  
  time   = Long()
  data   = Member()
  stream = Bool()
  streamName = Str()
  streamNameFull = Str()
  server = Member()
  error = Bool()
  connection = Member()

  def __init__(self, name, experiment):
    super(Stream, self).__init__(name, experiment)
    self.stream = False
    self.streamName = ""
    self.streamNameFull = ""
    self.server = None
    self.error = False

    self.properties += ['name', 'dtype', 'stream', 'streamName', 'fullPath','streamNameFull']
    #self.doNotSendToHardware = ['name', 'dtype', 'stream', 'streamName', 'fullPath']

  def new_entry(self, name, dset, ts):
    # initialize the non-user settable parameters
    self.name = name
    self.fullPath = dset.name
    self.dtype = str(dset.dtype)
    self.time = ts # timestamp
    self.data = dset[()]

  def print_status(self):
    '''returns a string listing the status'''
    streamStatus = self.stream
    if self.error:
      streamStatus = "Error"
    
    return "*--- Dataset: {}, type: {}, streamName: {}, stream?: {}".format(self.name, self.dtype, self.streamName, streamStatus)

  def is_streamed(self, server, namespace):
    '''performs error checking and will deactivate a stream if there is an error.
    Returns True if the stream registration succeeded.
    '''
    if not self.stream:
      return False

    # the stream needs to have a name
    if not self.streamName:
      self.stream = False
      logger.warning('You have requested that the `{}` dataset be logged to the Origin data server, but you have not specified a stream name.  The stream has been disabled in the settings.'.format(self.name))
      return False

    # the stream needs to have a namespace
    if not namespace:
      self.stream = False
      logger.warning('You have requested that the `{}` dataset be logged to the Origin data server, but you have not specified a stream namespace.  The stream has been disabled in the settings.'.format(self.name))
      return False

    # data type must be recognizable
    if not (self.dtype in dtype_list):
      self.stream = False
      logger.warning('You have requested that the `{}` dataset be logged to the Origin data server, but the data type you specified `` is not recognized.  The stream has been disabled in the settings.'.format(self.name,self.dtype))
      return False

    self.streamNameFull = namespace + self.streamName
    self.connection = server.registerStream(
      stream=self.streamNameFull,
      records={ self.name: self.dtype }
    )
    if not self.connection:
      logger.error('There was a problem registering the stream: `{}` with the server.'.format(self.name))
      self.error = True
      return False
    else:
      self.error = False
      return True

  def logData(self):
    data = { timestamp: self.time, self.name: self.data }
    self.connection.send(**data)
    logger.info('Stream `{}` for dataset `{}` logged to Origin server.'.format(self.streamName, self.name))


class Origin(Analysis):
  version = '2017.04.20'
  enable = Bool()
  isInitialized = Bool()
  IP = Str()
  port_register = Int()
  port_measure  = Int()
  port_register_json = Int()
  port_measure_json  = Int()
  #timeout = Typed(FloatProp)
  measurementDataList = Member()
  iterationDataList = Member()
  ts = Member()  
  settings = Member() # hold the hdf5 group object so I can save resave the settigns after the experiment is finished
  server = Member() # holds the server object
  config = Member() # holds the origin configuration file
  streamNameSpace = Str() # this is a string that will be prepended to all stream names for the experiment

  def __init__(self, name, experiment, description=''):
    super(Origin, self).__init__(name, experiment, description)
    #self.timeout = FloatProp('timeout', experiment, 'how long before TCP gives up [s]', '1.0')
    self.isInitialized = False
    self.streamNameSpace = ''

    # read in the correct config file
    if TEST:
      configfile = os.path.join(fullCfgPath, "origin-server-test.cfg")
    else:
      configfile = os.path.join(fullCfgPath, "origin-server.cfg")
    # read in the configuration
    self.config = ConfigParser.ConfigParser()
    self.config.read(configfile)

    # these are for display only
    self.IP = self.config.get('Server','ip')
    print self.IP
    self.port_register = int(self.config.get('Server','register_port'))
    self.port_measure  = int(self.config.get('Server','measure_port'))
    self.port_register_json = int(self.config.get('Server','json_register_port'))
    self.port_measure_json  = int(self.config.get('Server','json_measure_port'))

    self.measurementDataList = ListProp(
      'measurementDataList', 
      experiment, 
      'A list of per-measurement values that can be sent to the origin data server', 
      listElementType=Stream,
      listElementName='stream'
    )
    self.iterationDataList = ListProp(
      'iterationDataList', 
      experiment, 
      'A list of per-iteration values that can be sent to the origin data server', 
      listElementType=Stream,
      listElementName='stream'
    )

    self.properties += ['measurementDataList','iterationDataList','enable','IP','port','timeout','streamNameSpace']

  def preExperiment(self, experimentResults):
    """This is called before an experiment."""
    print "measurementDataList: ", self.measurementDataList
    print "iterationDataList: ", self.iterationDataList

    # just move on, done throw an error
    if not self.enable:
      return 0

    # if the name space is empty do not allow the streams to be logged
    if not self.streamNameSpace:
      logger.warning('The Origin data server interface is enabled, but you have not entered a namespace for you experiment so no data will be logged.')
      return 0

    # prepare server interface if not already set up
    if self.isInitialized:
      logger.info('Origin server already initialized.')
    else:
      logger.info('Initializing Origin server interface...')
      self.server = server(self.config)
      logger.info('    Registering streams...')

      logger.info('        Registering per-measurement streams...')
      cnt=0
      for i in self.measurementDataList:
        if i.is_streamed(self.server, self.streamNameSpace): #register the streams
          cnt+=1
        logger.info(i.print_status())
      logger.info('        Registering per-measurement streams...done')

      logger.info('        Registering per-iteration streams...')
      for i in self.iterationDataList:
        if i.is_streamed(self.server, self.streamNameSpace): #register the streams
          cnt+=1
        logger.info(i.print_status())
      logger.info('        Registering per-iteration streams...done')

      logger.info('    Registering streams...done')
      logger.info('Origin streams successfully registered: {}'.format(cnt))
      logger.info('Initializing Origin server interface...done')
      #self.isInitialized = True # just run the initialization every time right now
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
    measurementResults.visititems(self.processDatasets(self.measurementDataList))
    for i in self.measurementDataList:
      if i.stream and not i.error:
        i.logData()
    return 0

  def postIteration(self, iterationResults, experimentResults):
    # log any per iteration parameters here
    # set timestamp
    self.ts = long(time.time()*2**32)
    # process iteration data from hdf5 file
    iterationResults.visititems(self.processDatasets(self.iterationDataList))
    for i in self.iterationDataList:
      if i.stream and not i.error:
        i.logData()
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
    return Stream(dset.name, self.experiment, dset, self.ts, '')

  def processDatasets(self, data_list):
    def process(name, obj):
      if isinstance(obj, Dataset):
        if(obj.dtype in dtype_list):
          print '='*10
          parsedName = name.replace('/','_')
          print parsedName
          print obj.dtype
          append=True
          for item in data_list:
            if item.name == parsedName:
              print "dataset `", parsedName, "` already exists in list"
              if item.dtype == str(obj.dtype):
                item.time = self.ts
                item.data = obj[()]
              else:
                print "dataset type mismatch with stored type"
              append = False
              break
          if append:
            print "appending new entry"
            new_entry = data_list.add()
            new_entry.new_entry(parsedName, obj, self.ts)
        
          print data_list
          print '='*10
    return process

  def toHDF5(self, hdf_parent_node, name):
    #print "name: ", name
    #print "hdf_parent_node: ", hdf_parent_node
    #print "path: ", hdf_parent_node.name

    # save the origin settings hdf5 object so we can rerun the toHDF5 method 
    # after the experiment fills out the dicts
    self.settings = hdf_parent_node.name
    super(Origin, self).toHDF5(hdf_parent_node)