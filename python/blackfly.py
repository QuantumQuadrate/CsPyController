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
from cs_errors import PauseError
from atom.api import Typed
from cs_instruments import Instrument
import zmq_instrument

__author__ = 'Matthew Ebert'
logger = logging.getLogger(__name__)


class BlackflyCamera(Instrument):
    """An actual camera object."""

    serial = Int(0)
    exposureTime = Float(1.0)


    def __init__(self, name, experiment, description=''):
        super(BlackflyCamera, self).__init__(name, experiment, description)
        # To make this super easy name the properties the same way on the server
        # and here so we dont have to do anything special
        self.properties += ['serial', 'exposureTime', 'triggerDelay']
        self.doNotSendToHardware += ['serial']

    def HardwareProtocol(self, o, p, settings):
        """Edit the settings dictionary to update the necessary settings.
        """
        # The settings dict is mutable so it is passed by reference and will
        # change the variable in the higher scope.
        settings[o] = p

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

                self.HardwareProtocol(o, p, settings)
        return settings

class Blackfly(Instrument):
    """A camera object for display purposes."""

    camera = Typed(BlackflyCamera)

    def __init__(self, name, experiment, description):
        super(Blackfly, self).__init__(name, experiment, description)
        self.camera = BlackflyCamera(
            'Camera_{}'.format(name),
            experiment,
            'Blackfly Camera'
        )
        properties += ['camera']

    def evaluate(self):
        self.camera.evaluate()

    def HardwareProtocol(self, o, p, settings):
        """Edit the settings dictionary to update the necessary settings.

        Creates a new settings key that holds a dict of cameras.
        """
        settings[self.camera.serial] = self.camera.get_settings()


class BlackflyClient(zmq_instrument.ZMQInstrument):
    """A instrument communication class for a blackfly ZeroMQ server.
    """

    version = "2017.08.01"
    cameras = Typed(ListProp)
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

    def get_available_cameras(self):
        resp = self.send({'action': 'GET_CAMERAS'})
        self.available_cameras = resp['cameras']

    def initialize(self):
        super(BlackflyClient, self).initialize()
        self.isInitialized = True
        for i in self.cameras:
            try:
                if i.camera.enable:
                    msg = 'Initializing camera ser. no.: {}'
                    logger.info(msg.format(i.camera.serial))
                    msg = i.camera.initialize()
            except Exception as e:
                msg = 'Problem initializing Blackfly camera ser. no.: {}.'
                logger.exception(msg.format(i.camera.serial))
                self.isInitialized = False
                raise PauseError
