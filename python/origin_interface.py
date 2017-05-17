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

ORIGIN_TEST = False
#ORIGIN_TEST = True

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


# get the config file
from __init__ import import_config
config = import_config()

#still need to import config parser for origin
import ConfigParser
sys.path.append(config.get('ORIGIN','OriginLibPath'))
#print config.get('ORIGIN','OriginLibPath')

from origin.client import server
from origin import current_time, timestamp

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

def pass_measurement(dset):
  return dset.dtype in dtype_list

def pass_iteration(dset):
  return (dset.dtype in dtype_list) and not ('/measurements/' in dset.name)

def formatData(data):
  '''returns data into relevant type
  ND arrays to 1D arrays
  '''
  channels = 1
  if type(data) is np.ndarray:
    # flatten ND arrays to 1D
    channels = data.size
    data = data.flatten()
  return (channels, data)

################################################################################
################################################################################
################################################################################
# ORIGIN DATA STREAM OBJECT
################################################################################
################################################################################
################################################################################

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
  channels = Int() # number of data entries to be logged in this stream
  fieldsStr = Str() # str for displaying the stream's fields
  fieldsList = Member() # list of field names, can be set to be updated in the GUI

  # these are logged on a new connection so we can detect a change in the stream
  # parameters
  old_streamNameFull = Str()
  old_dtype = Str()

  #=============================================================================
  def __init__(self, name, experiment):
    super(Stream, self).__init__(name, experiment)
    self.stream = False
    self.streamName = ""
    self.streamNameFull = ""
    self.server = None
    self.error = False

    self.properties += ['name', 'dtype', 'stream', 'streamName', 'fullPath']
    self.properties += ['streamNameFull', 'channels','fieldsStr','fieldsList']

  #=============================================================================
  def new_entry(self, name, dset, ts):
    # initialize the non-user settable parameters
    self.name = name
    self.fullPath = dset.name
    self.dtype = str(dset.dtype)
    self.time = ts # timestamp
    self.channels, self.data = formatData(dset[()])

    # record the fields names
    if self.channels == 1:
      self.fieldsList = [self.name]
    else:
      self.fieldsList = range(0,self.channels)
    self.fieldsStr = '[{}]'.format(', '.join(map(str, self.fieldsList)))

  #=============================================================================
  def print_status(self):
    '''returns a string listing the status'''
    streamStatus = self.stream
    if self.error:
      streamStatus = "Error"

    return "*--- Dataset: {}, type: {}, streamName: {}, stream?: {}".format(self.name, self.dtype, self.streamName, streamStatus)

  #=============================================================================
  def is_streamed(self, server, namespace):
    '''performs error checking and will deactivate a stream for common user errors.
    If no errors are detected will attempt to register the stream.
    Returns True if the stream registration succeeded.
    '''

    # if we aren't attempting to stream go about your business
    if not self.stream:
      return False

    # common messages
    msg = 'You have requested that the `{}` dataset be logged to the Origin data server, but'.format(self.name)
    msgDisabled = ' The stream has been disabled in the settings.'

    # the stream needs to have a name
    if not self.streamName:
      self.stream = False
      msg += 'you have not specified a stream name.'
      msg += msgDisabled
      logger.warning(msg)
      return False

    # the stream needs to have a namespace
    if not namespace:
      self.stream = False
      msg += ' you have not specified a stream namespace.'
      msg += msgDisabled
      logger.warning(msg)
      return False

    # data type must be recognizable
    if not (self.dtype in dtype_list):
      self.stream = False
      msg += ' the data type you specified `{}` is not recognized.'
      msg += msgDisabled
      logger.warning(' The stream has been disabled in the settings.'.format(self.dtype))
      return False

    # define the stream name with the experiment namespace
    self.streamNameFull = namespace + self.streamName

    # build the records dictionary
    records = { self.name: self.dtype }
    if self.channels != 1:
      records = {}
      for i in xrange(self.channels):
        records[str(i)] = self.dtype

    # register the stream
    self.connection = server.registerStream(
      stream=self.streamNameFull,
      records=records
    )

    # error checking
    if not self.connection:
      msg = 'There was a problem registering the stream: `{}` with the server.'
      logger.error(msg.format(self.name))
      self.error = True
      return False
    else:
      # record the settings on a successful registration so we can detect a change
      self.old_streamNameFull = self.streamNameFull
      self.old_dtype = self.dtype
      self.error = False
      return True

  #=============================================================================
  def logData(self):
    if self.channels == 1:
      data = { timestamp: self.time, self.name: self.data }
    else:
      data = { timestamp: self.time }
      for i, d in enumerate(self.data):
        data[str(i)] = d
    self.connection.send(**data)
    msg = 'Stream `{}` for dataset `{}` logged to Origin server.'
    logger.debug(msg.format(self.streamName, self.name))

  #=============================================================================
  def connected(self, namespace):
    # if the stream name or data type has changed then we need to re-register
    self.streamNameFull = namespace + self.streamName
    if (self.old_streamNameFull == self.streamNameFull) and (self.dtype == self.old_dtype):
      if self.connection:
        return True
    else:
      if self.connection:
        self.connection.close()
    return False

################################################################################
################################################################################
################################################################################
# ORIGIN DATA SERVER INTERFACE
################################################################################
################################################################################
################################################################################

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

  #=============================================================================
  def __init__(self, name, experiment, description=''):
    super(Origin, self).__init__(name, experiment, description)
    #self.timeout = FloatProp('timeout', experiment, 'how long before TCP gives up [s]', '1.0')
    self.isInitialized = False
    self.streamNameSpace = ''

    self.configure()

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

    self.properties += ['measurementDataList','iterationDataList','enable']
    self.properties += ['streamNameSpace']

  #=============================================================================
  def configure(self):
    # read in the correct config file
    cfg_path = config.get('ORIGIN','OriginCfgPath')
    if ORIGIN_TEST:
      configfile = os.path.join(cfg_path, "origin-server-test.cfg")
    else:
      configfile = os.path.join(cfg_path, "origin-server.cfg")
    # read in the configuration file from the origin lib
    self.config = ConfigParser.ConfigParser()
    self.config.read(configfile)

    # these are for display only
    self.IP = self.config.get('Server','ip')
    self.port_register = int(self.config.get('Server','register_port'))
    self.port_measure  = int(self.config.get('Server','measure_port'))
    self.port_register_json = int(self.config.get('Server','json_register_port'))
    self.port_measure_json  = int(self.config.get('Server','json_measure_port'))

  #=============================================================================
  def register(self, list):
    cnt=0
    for i in list:
      if not i.connected(self.streamNameSpace):
        if i.is_streamed(self.server, self.streamNameSpace): #register the streams
          cnt+=1
        logger.debug(i.print_status())
    return cnt

  #=============================================================================
  def preExperiment(self, experimentResults):
    """This is called before an experiment."""
    #print "measurementDataList: ", self.measurementDataList
    #print "iterationDataList: ", self.iterationDataList

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
      self.isInitialized = True

    logger.debug('Registering streams...')
    logger.debug('Registering per-measurement streams...')
    cnt =  self.register(self.measurementDataList)
    logger.debug('Registering per-measurement streams...done')

    logger.debug('Registering per-iteration streams...')
    cnt += self.register(self.iterationDataList)
    logger.debug('Registering per-iteration streams...done')

    logger.debug('Registering streams...done')
    logger.info('Origin streams registered: {}'.format(cnt))
    logger.info('Initializing Origin server interface...done')
    return 0

  #=============================================================================
  def preIteration(self, iterationResults, experimentResults):
    # initialize any logged parameters that are on a per iteration basis
    return 0

  #=============================================================================
  def postMeasurement(self, measurementResults, iterationResults, experimentResults):
    """Results is a tuple of (measurementResult,iterationResult,experimentResult) references to HDF5 nodes for this
    measurement."""
    # set timestamp
    self.ts = long(time.time()*2**32)
    # build list of per measurement loggable datasets
    measurementResults.visititems(self.processDatasets(self.measurementDataList, pass_measurement))

    # process measurement data from hdf5 file
    if not self.enable:
      return 0

    for i in self.measurementDataList:
      if i.stream and not i.error:
        i.logData()
    return 0

  #=============================================================================
  def postIteration(self, iterationResults, experimentResults):
    # log any per iteration parameters here
    # set timestamp
    self.ts = long(time.time()*2**32)
    # process iteration data from hdf5 file
    iterationResults.visititems(self.processDatasets(self.iterationDataList, pass_iteration))

    if not self.enable:
      return 0

    for i in self.iterationDataList:
      if i.stream and not i.error:
        i.logData()
    return 0

  #=============================================================================
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
      logger.exception('Uncaught Exception in origin.postExperiment.')
    finally:
      f.close() #close the file
    return 0

  #=============================================================================
  def finalize(self,experimentResults):
    return 0

  #=============================================================================
  def newEntry(self, dset):
    return Stream(dset.name, self.experiment, dset, self.ts, '')

  #=============================================================================
  def processDatasets(self, data_list, pass_func):
    '''pass in the data list to be scaned and a pass function returning True if
    the object should be kept
    '''
    def process(name, obj):
      if isinstance(obj, Dataset):
        if pass_func(obj):
          parsedName = name.replace('/','_')
          append=True
          for item in data_list:
            if item.name == parsedName:
              logger.debug("dataset `{}` already exists in list".format(parsedName))
              if item.dtype == str(obj.dtype):
                item.time = self.ts
                channels, item.data = formatData(obj[()])
              else:
                try:
                  msg = 'Attempting to cast dataset `{}` of type `{}` to type `{}` to match stream definition.'
                  logger.debug(msg.format(parsedName, obj.dtype, item.dtype))
                  data = eval('np.'+item.dtype+'(obj[()])')
                  channels, item.data = formatData(data)
                  item.time = self.ts
                except Exception as e:
                  logger.error('Uncaught Exception in origin.postExperiment:\n{}\n{}'.format(e, traceback.format_exc()))
                  msg = "Dataset `{}` type mismatch with stored type. new: `{}`, old: `{}`"
                  logger.error(msg.format(parsedName, obj.dtype, item.dtype))
              append = False
              break
          if append:
            new_entry = data_list.add()
            new_entry.new_entry(parsedName, obj, self.ts)
            msg = "New dataset `{}` of type `{}` with `{}` channels detected."
            logger.info(msg.format(parsedName, obj.dtype, new_entry.channels))
    return process

  #=============================================================================
  def toHDF5(self, hdf_parent_node, name):
    #print "name: ", name
    #print "hdf_parent_node: ", hdf_parent_node
    #print "path: ", hdf_parent_node.name

    # save the origin settings hdf5 object so we can rerun the toHDF5 method
    # after the experiment fills out the dicts
    self.settings = hdf_parent_node.name
    # dont save to hdf5 when everyone else is
    logger.debug("This is the pre-experiment save event.  Origin reruns its save event at the end.")
