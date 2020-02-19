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

# Use Atom traits to automate Enaml updating
from atom.api import Int, Str, Member, Bool, Long

from instrument_property import Prop, ListProp

from analysis import Analysis

from h5py import Dataset, File
import traceback
import os.path

import time

import numpy as np

import logging
logger = logging.getLogger(__name__)


# get the config file
from __init__ import import_config
config = import_config()

# still need to import config parser for origin
import ConfigParser

from origin.client import server
from origin import TIMESTAMP, data_types

preExperimentMsg    = 'PEXP'
postExperimentMsg   = 'EXPR'
preIterationMsg     = 'PITR'
postIterationMsg    = 'ITER'
postMeasurementMsg  = 'MEAS'

dtype_list = []
for dtype in data_types.keys():
    if data_types[dtype]["binary_allowed"]:
        dtype_list.append(dtype)


def print_attrs(name, obj):
    logger.info(name)
    for key, val in obj.attrs.iteritems():
        logger.info("    {}: {}".format(key, val))


def print_dsets(name, obj):
    if isinstance(obj, Dataset):
        logger.info("{}{}{}{}{}".format('-'*10, name, obj.dtype, obj[()],
                                        '-'*10))


def pass_measurement(dset):
    if dset.dtype in dtype_list:
        return True
    return False


def pass_iteration(dset):
    if (dset.dtype in dtype_list) and not ('/measurements/' in dset.name):
        return True
    return False


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


###############################################################################
###############################################################################
###############################################################################
# ORIGIN DATA STREAM OBJECT
###############################################################################
###############################################################################
###############################################################################


class Stream(Prop):
    '''A class representing an origin stream
    '''
    name = Str()
    fullPath = Str()
    dtype = Str()
    time = Long()
    data = Member()
    stream = Bool()
    streamName = Str()
    streamNameFull = Str()
    server = Member()
    error = Bool()
    connection = Member()
    channels = Int()  # number of data entries to be logged in this stream
    fieldsStr = Str()  # str for displaying the stream's fields
    # list of field names, can be set to be updated in the GUI
    fieldsList = Member()

    # these are logged on a new connection so we can detect a change in the
    # stream parameters
    old_streamNameFull = Str()
    old_dtype = Str()

    # ==========================================================================
    def __init__(self, name, experiment):
        super(Stream, self).__init__(name, experiment)
        self.stream = False
        self.streamName = ""
        self.streamNameFull = ""
        self.server = None
        self.error = False

        self.properties += ['name', 'dtype', 'stream', 'streamName', 'fullPath']
        self.properties += ['streamNameFull', 'channels', 'fieldsStr', 'fieldsList']

    # ==========================================================================
    def new_entry(self, name, dset, ts):
        # initialize the non-user settable parameters
        self.name = name
        self.fullPath = dset.name
        self.dtype = str(dset.dtype)
        self.time = ts  # TIMESTAMP
        self.channels, self.data = formatData(dset[()])

        # record the fields names
        if self.channels == 1:
            self.fieldsList = [self.name]
        else:
            self.fieldsList = range(0, self.channels)
        self.fieldsStr = '[{}]'.format(', '.join(map(str, self.fieldsList)))

    # ==========================================================================
    def print_status(self):
        '''returns a string listing the status'''
        streamStatus = self.stream
        if self.error:
            streamStatus = "Error"

        msg = "*--- Dataset: {}, type: {}, streamName: {}, stream?: {}"
        return msg.format(self.name, self.dtype, self.streamName, streamStatus)

    # ==========================================================================
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
            records=records,
            timeout=20000
        )

        # error checking
        if not self.connection:
            msg = 'There was a problem registering the stream: `{}` with the server.'
            logger.error(msg.format(self.name))
            self.error = True
            return False
        else:
            # record the settings on a successful registration so we can detect
            # a change
            self.old_streamNameFull = self.streamNameFull
            self.old_dtype = self.dtype
            self.error = False
            return True

    # ==========================================================================
    def logData(self):
        if self.channels == 1:
            data = { TIMESTAMP: self.time, self.name: self.data }
        else:
            data = { TIMESTAMP: self.time }
            for i, d in enumerate(self.data):
                data[str(i)] = d
        self.connection.send(**data)
        msg = 'Stream `{}` for dataset `{}` logged to Origin server.'
        logger.debug(msg.format(self.streamName, self.name))

    # ==========================================================================
    def connected(self, namespace):
        """If the stream name or data type has changed then we need to
        re-register.
        """
        self.streamNameFull = namespace + self.streamName
        if (self.old_streamNameFull == self.streamNameFull) and (self.dtype == self.old_dtype):
            if self.connection:
                return True
        else:
            if self.connection:
                self.connection.close()
        return False


###############################################################################
###############################################################################
###############################################################################
# ORIGIN DATA SERVER INTERFACE
###############################################################################
###############################################################################
###############################################################################


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
    # hold the hdf5 group object so I can save resave the settings after the
    # experiment is finished
    settings = Member()
    server = Member()  # holds the server object
    config = Member()  # holds the origin configuration file
    # this is a string that will be prepended to all stream names for the
    # experiment
    streamNameSpace = Str()

    # ==========================================================================
    def __init__(self, name, experiment, description=''):
        super(Origin, self).__init__(name, experiment, description)
        #self.timeout = FloatProp('timeout', experiment, 'how long before TCP gives up [s]', '1.0')
        self.isInitialized = False
        self.streamNameSpace = ''

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

        self.properties += ['measurementDataList', 'iterationDataList', 'enable']
        self.properties += ['streamNameSpace']

        # threading stuff
        self.queueAfterMeasurement = True
        # dependencies are added pre experiment due to call order

        # set IP as a blank value in case the configuration doesn't work
        self.IP = ''

    # ==========================================================================
    def configure(self):
        # read in the correct config file
        cfg_path = self.experiment.Config.config.get('ORIGIN', 'OriginCfgPath')
        if self.experiment.Config.config.getboolean('ORIGIN', 'OriginTest'):
            logger.warning("Origin is running in test mode")
            configfile = os.path.join(cfg_path, "origin-server-test.cfg")
        else:
            configfile = os.path.join(cfg_path, "origin-server.cfg")
        # read in the configuration file from the origin lib
        self.config = ConfigParser.ConfigParser()
        self.config.read(configfile)

        # these are for display only
        self.streamNameSpace = self.experiment.Config.config.get('EXPERIMENT', 'Name')
        self.streamNameSpace += '_'
        self.IP = self.config.get('Server', 'ip')
        self.port_register = int(self.config.get('Server', 'register_port'))
        self.port_measure  = int(self.config.get('Server', 'measure_port'))
        self.port_register_json = int(self.config.get('Server', 'json_register_port'))
        self.port_measure_json  = int(self.config.get('Server', 'json_measure_port'))

    # ==========================================================================
    def register(self, list):
        cnt = 0
        for i in list:
            if not i.connected(self.streamNameSpace):
                # register the streams
                if i.is_streamed(self.server, self.streamNameSpace):
                    cnt += 1
                    logger.debug(i.print_status())
        return cnt

    # ==========================================================================
    def preExperiment(self, experimentResults):
        """This is called before an experiment."""

        # check to make sure origin has been configured
        if self.IP == '':
            self.configure()

        # this needs to be after the initialization so that variable has been
        # defined
        self.measurementDependencies = []
        for a in self.experiment.analyses:
            # filter out origin from the dependencies
            if a.name != self.name:
                self.measurementDependencies.append(a)

        # call therading setup code
        super(Origin, self).preExperiment(experimentResults)
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
        cnt = self.register(self.measurementDataList)
        logger.debug('Registering per-measurement streams...done')

        logger.debug('Registering per-iteration streams...')
        cnt += self.register(self.iterationDataList)
        logger.debug('Registering per-iteration streams...done')

        logger.debug('Registering streams...done')
        logger.info('Origin streams registered: {}'.format(cnt))
        logger.info('Initializing Origin server interface...done')
        return 0

    # ==========================================================================
    def preIteration(self, iterationResults, experimentResults):
        # initialize any logged parameters that are on a per iteration basis
        return 0

    # ==========================================================================
    def analyzeMeasurement(self, measurementResults, iterationResults, experimentResults):
        """Results is a tuple of
        (measurementResult, iterationResult, experimentResult) references to HDF5
        nodes for this measurement.
        """
        # set TIMESTAMP
        self.ts = long(measurementResults.attrs.get('start_time')*2**32)  # ts when measurement was taken
        measurementResults.visititems(self.processDatasets(self.measurementDataList, pass_measurement))

        # process measurement data from hdf5 file
        if not self.enable:
            return 0

        for i in self.measurementDataList:
            if i.stream and not i.error:
                i.logData()
        return 0

    # ==========================================================================
    def analyzeIteration(self, iterationResults, experimentResults):
        # log any per iteration parameters here
        # set TIMESTAMP
        self.ts = long(time.time()*2**32)
        # process iteration data from hdf5 file
        iterationResults.visititems(self.processDatasets(self.iterationDataList, pass_iteration))

        if not self.enable:
            return 0

        for i in self.iterationDataList:
            if i.stream and not i.error:
                i.logData()
        return 0

    # ==========================================================================
    def analyzeExperiment(self, experimentResults):
        # write to data file
        super(Origin, self).toHDF5(experimentResults[self.settings])
        # and to settings file
        try:
            f = File('settings.hdf5', 'a')
            super(Origin, self).toHDF5(f['settings/experiment'])
            f.flush()  # write changes
        except Exception as e:
            logger.exception('Uncaught Exception in origin.postExperiment.')
        finally:
            f.close()  # close the file
        return 0

    # ==========================================================================
    def finalize(self,experimentResults):
        return 0

    # ==========================================================================
    def newEntry(self, dset):
        return Stream(dset.name, self.experiment, dset, self.ts, '')

    # ==========================================================================
    def processDatasets(self, data_list, pass_func):
        '''pass in the data list to be scaned and a pass function returning True if
        the object should be kept
        '''
        def process(name, obj):
            if isinstance(obj, Dataset):
                if pass_func(obj):
                    parsedName = name.replace('/', '_')
                    append = True
                    # logger.warning('dataset: `{}` is acceptable.'.format(name))
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
                else:
                    logger.debug('dataset: `{}` not acceptable for some reason.'.format(name))
        return process

    # ==========================================================================
    def toHDF5(self, hdf_parent_node, name):
        # print "name: ", name
        # print "hdf_parent_node: ", hdf_parent_node
        # print "path: ", hdf_parent_node.name

        # save the origin settings hdf5 object to rerun the toHDF5 method
        # after the experiment fills out the dicts
        self.settings = hdf_parent_node.name
        # dont save to hdf5 when everyone else is
        logger.info("This is the pre-experiment save event.  Origin reruns its save event at the end.")
        super(Origin, self).toHDF5(hdf_parent_node)

    # ==========================================================================
    def fromHDF5(self, hdf):
        super(Origin, self).fromHDF5(hdf)
        self.configure()
