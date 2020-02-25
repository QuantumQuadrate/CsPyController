"""A Blackfly ethernet camera instrument communication class.

blackfly.py
author = Matthew Ebert
created = 2017-08-01

This file is part of the Cesium Control program designed by Martin Lichtman in
2013 for the AQuA project. It contains classes that represent zeroMQ
instrument servers. In an effort to distribute computational load instruments
can be designed to do basic analysis. Since the server is running in a different
process this can improve performance, but analysis dependencies must be
appropriately handled.
"""

import logging
import numpy as np
from cs_errors import PauseError
from atom.api import Typed, Member, Int, Float, Bool
from cs_instruments import Instrument
import zmq_instrument
from instrument_property import Prop
logger = logging.getLogger(__name__)
try:
    from PyCapture2 import PROPERTY_TYPE, BUS_SPEED, GRAB_MODE, PIXEL_FORMAT
except:
    # just make fake values so stuff doesnt crash when testing
    logger.warning("PyCapture2 not installed, blackfly cameras are not usuable")
    class ptype(object):
        def __init__(self):
            self.TRIGGER_DELAY = 1
            self.BUFFER_FRAMES = 2
            self.S_FASTEST = 3
            self.MONO8 = 4

    PROPERTY_TYPE = ptype()
    BUS_SPEED = ptype()
    GRAB_MODE = ptype()
    PIXEL_FORMAT = ptype()

__author__ = 'Matthew Ebert'



class BFProperty(Prop):
    """Class that makes it easier to send class properties to the BF server."""

    def HardwareProtocol(self, o, name, settings):
        """Edit the settings dictionary to update the necessary settings.

        Should be overwritten for more complicated properties.
        """
        # The settings dict is mutable so it is passed by reference and will
        # change the variable in the higher scope.
        settings[name] = {}
        for p in self.properties:
            try:
                prop = getattr(self, p)
            except:
                msg = (
                    'In BFProperty.HardwareProtocol() for class `{}`: item'
                    ' `{}` in properties list does not exist.'
                ).format(self.name, p)
                logger.warning(msg)
                raise PauseError
            settings[name][p] = prop


class BFTriggerDelay(BFProperty):
    """Class containing the TriggerDelay properties for a Blackfly camera.

    Use this as a basis for other settings classes from blackfly.  If you mirror
    the structure in the reference manual it will make it easy to make the
    server.
    """

    propType = Int(PROPERTY_TYPE.TRIGGER_DELAY)
    present = Bool()  # ?
    absControl = Bool(True)
    onePush = Bool(True)
    onOff = Bool(True)
    autoManualMode = Bool(True)
    valueA = Int(0)
    valueB = Int(0)
    absValue = Float(0.0)  # the actual delay

    def __init__(self, name, experiment, description=''):
        """Add in the properties that need to be sent to the camera."""
        super(BFTriggerDelay, self).__init__(name, experiment, description)
        self.properties += [
            'propType', 'present', 'absControl', 'onePush', 'onOff',
            'autoManualMode', 'valueA', 'valueB', 'absValue'
        ]


class BFConfiguration(BFProperty):
    """Class containing the Configuration properties for a Blackfly camera.

    Use this as a basis for other settings classes from blackfly.  If you mirror
    the structure in the reference manual it will make it easy to make the
    server.
    """

    numBuffers = Int(2)  # image buffers on camera (shotsPerMeasurement)
    numImageNotification = Int(0)  # number of notifications per image
    grabTimeout = Int(1)  # time in ms before retrieve buffer times out
    grabMode = Int(GRAB_MODE.BUFFER_FRAMES)  # grab mode for camera
    isochBusSpeed = Int(BUS_SPEED.S_FASTEST)  # Isynchronous bus speed
    asyncBusSpeed = Int(BUS_SPEED.S_FASTEST)  # async bus speed
    bandwidthAllocation = Int(0)  # bandwidth allocation strategy
    registerTimeoutRetries = Int(0)  # times to retry on reg r/w timeout
    registerTimeout = Int(0)  # register r/w timeout in us

    def __init__(self, name, experiment, description=''):
        """Add in the properties that need to be sent to the camera."""
        super(BFConfiguration, self).__init__(name, experiment, description)
        # things not in the property list are not sent to the camera
        self.properties += [
            'grabMode', 'numBuffers'
        ]


class BFGigEConfig(BFProperty):
    """Class containing the Configuration properties for a Blackfly camera.

    Use this as a basis for other settings classes from blackfly.  If you mirror
    the structure in the reference manual it will make it easy to make the
    server.
    """

    enablePacketResend = Bool(True)  # packet resend functionality
    registerTimeoutRetries = Int(10)  # number of packet retries
    registerTimeout = Int(0)  # register r/w timeout in us (use default?)

    def __init__(self, name, experiment, description=''):
        """Add in the properties that need to be sent to the camera."""
        super(BFGigEConfig, self).__init__(name, experiment, description)
        # things not in the property list are not sent to the camera
        self.properties += [
            'enablePacketResend', 'registerTimeoutRetries'
        ]


class BFGigEStreamChannel(BFProperty):
    """Class containing the Configuration properties for a Blackfly camera.

    Use this as a basis for other settings classes from blackfly.  If you mirror
    the structure in the reference manual it will make it easy to make the
    server.
    """

    networkInterfaceIndex = Int(0)
    # hostPort = Int(0)
    doNotFragment = Bool(False)
    packetSize = Int(1224)
    interPacketDelay = Int(100)
    # destinationIpAddress = Int()
    # sourcePort = ()

    def __init__(self, name, experiment, description=''):
        """Add in the properties that need to be sent to the camera."""
        super(BFGigEStreamChannel, self).__init__(name, experiment, description)
        # things not in the property list are not sent to the camera
        self.properties += [
            'packetSize', 'interPacketDelay'
        ]


class BFGigEImageSettings(BFProperty):
    """Class containing the Configuration properties for a Blackfly camera.

    Use this as a basis for other settings classes from blackfly.  If you mirror
    the structure in the reference manual it will make it easy to make the
    server.
    """

    offsetX = Int(1)
    offsetY = Int(1)
    width = Int(1280)
    height = Int(960)
    pixelFormat = Int(PIXEL_FORMAT.MONO8)

    def __init__(self, name, experiment, description=''):
        """Add in the properties that need to be sent to the camera."""
        super(BFGigEImageSettings, self).__init__(name, experiment, description)
        # things not in the property list are not sent to the camera
        self.properties += [
            'offsetX', 'offsetY', 'width', 'height', 'pixelFormat'
        ]


class BlackflyCamera(Instrument):
    """An actual camera object."""

    serial = Int(0)
    exposureTime = Float(5.0)
    shotsPerMeasurement = Int(1)
    triggerDelay = Member()
    configuration = Member()
    gigEConfig = Member()
    gigEStreamChannel = Member()
    gigEImageSettings = Member()

    def __init__(self, name, experiment, description=''):
        super(BlackflyCamera, self).__init__(name, experiment, description)
        # To make this super easy name the properties the same way on the server
        # and here so we dont have to do anything special
        self.triggerDelay = BFTriggerDelay(
            'triggerDelay',
            experiment,
            'Blackfly trigger delay object'
        )
        self.configuration = BFConfiguration(
            'configuration',
            experiment,
            'Blackfly configuration object'
        )
        self.gigEConfig = BFGigEConfig(
            'GigE configuration',
            experiment,
            'Blackfly gigabit ethernet configuration object'
        )
        self.gigEStreamChannel = BFGigEStreamChannel(
            'GigE stream channel',
            experiment,
            'Blackfly gigabit ethernet stream channel object'
        )
        self.gigEImageSettings = BFGigEImageSettings(
            'GigE image settings',
            experiment,
            'Blackfly gigabit ethernet image settings object'
        )
        self.properties += [
            'serial', 'exposureTime', 'triggerDelay', 'configuration',
            'gigEConfig', 'gigEStreamChannel', 'gigEImageSettings',
            'shotsPerMeasurement'
        ]
        self.doNotSendToHardware += []

    def HardwareProtocol(self, o, name, settings):
        """Edit the settings dictionary to update the necessary settings."""
        # The settings dict is mutable so it is passed by reference and will
        # change the variable in the higher scope.
        settings[name] = o

    def toHardware(self):
        """Generate a dictionary of settings to be sent to the camera server."""
        # create a settings dict to send fromthe properties
        settings = {}
        for p in self.properties:
            if p not in self.doNotSendToHardware:
                # convert the string name to an actual object
                try:
                    o = getattr(self, p)
                except:
                    msg = (
                        'In ZMQInstrument.toHardware() for class `{}`: item'
                        ' `{}` in properties list does not exist.'
                    ).format(self.name, p)
                    logger.warning(msg)
                    raise PauseError
                try:
                    o.HardwareProtocol(o, p, settings)
                except:
                    self.HardwareProtocol(o, p, settings)
        return settings


class Blackfly(Instrument):
    """A camera object for display purposes."""

    camera = Typed(BlackflyCamera)

    def __init__(self, name, experiment, description=''):
        super(Blackfly, self).__init__(name, experiment, description)
        self.camera = BlackflyCamera(
            'Camera_{}'.format(name),
            experiment,
            'Blackfly Camera'
        )
        self.properties += ['camera']

    def evaluate(self):
        self.camera.evaluate()

    def HardwareProtocol(self, o, p, settings):
        """Edit the settings dictionary to update the necessary settings.

        Creates a new settings key that holds a dict of cameras.
        """
        settings[self.camera.serial] = self.camera.toHardware()


class BlackflyClient(zmq_instrument.ZMQInstrument):
    """A instrument communication class for a blackfly ZeroMQ server."""

    version = "2017.08.01"
    cameras = Typed(zmq_instrument.ZMQListProp)
    available_cameras = Member()

    def __init__(self, name, experiment):
        """Initialize the class."""
        super(BlackflyClient, self).__init__(
            name,
            experiment,
            "Blackfly camera server interface"
        )
        self.cameras = zmq_instrument.ZMQListProp(
            'cameras',
            experiment,
            'A list of individual Blackfly cameras',
            listElementType=Blackfly,
            listElementName='camera'
        )
        self.get_available_cameras()
        self.properties += ['version', 'cameras']
        self.doNotSendToHardware += ['available_cameras']

    def data_handler(self, hdf5, key, value):
        if key == "camera_data":
            for serial in value:
                try:
                    f = hdf5.create_group('{}/{}'.format(key, serial))
                    f['error'] = value[serial]['error']
                    raw_data = np.array(value[serial]['data'])
                    f.create_dataset('raw_data', data=raw_data)
                    f = f.create_group('stats')
                    for stat in value[serial]['stats']:
                        f[stat] = value[serial]['stats'][stat]
                    # f = hdf5.create_group('{}/{}'.format(key, serial))
                    # f['error'] = value[serial]['error']
                    # f = f.create_group('shots')
                    # for key in value[serial]['data']:
                    #     print key
                    #     shot = value[serial]['data'][key]
                    #     shot_grp = f.create_group(str(key))
                    #     raw_data = np.array(shot['image'])
                    #     shot_grp.create_dataset('raw_data', data=raw_data)
                    #     stat_grp = shot_grp.create_group('stats')
                    #     for stat in shot['stats']:
                    #         stat_grp[stat] = shot['stats'][stat]
                except:
                    logger.exception('problem')

    def get_available_cameras(self):
        resp = self.send_json({'action': 'GET_CAMERAS'})
        try:
            if 'cameras' in resp:
                self.available_cameras = resp['cameras']
            else:
                logger.warning('Unable to retrieve cameras list from server.')
                self.close_socket()
        except PauseError:
            logger.info('No response from Blackfly server found.')
            self.connected = False

    def initialize(self):
        super(BlackflyClient, self).initialize()
        self.isInitialized = True
        for i in self.cameras:
            try:
                if i.camera.enable:
                    msg = 'Initializing camera ser. no.: {}'
                    logger.info(msg.format(i.camera.serial))
                    msg = i.camera.initialize()
            except:
                msg = 'Problem initializing Blackfly camera ser. no.: {}.'
                logger.exception(msg.format(i.camera.serial))
                self.isInitialized = False
                raise PauseError
