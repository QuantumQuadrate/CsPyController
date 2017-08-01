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
from instrument_property import ListProp

__author__ = 'Matthew Ebert'
logger = logging.getLogger(__name__)


class BlackflyCamera(Instrument):
    """An actual camera object."""

    def __init__(self, name, experiment, description=''):
        super(BlackflyCamera, self).__init__(name, experiment, description)


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
        self.cameras = ListProp(
            'cameras',
            experiment,
            'A list of individual Blackfly cameras',
            listElementType=Blackfly,
            listElementName='camera'
        )
        self.get_available_cameras()
        self.properties += ['version', 'cameras']

    def get_available_cameras(self):
        resp = self.send({'action': 'GET_CAMERAS'})
        self.available_cameras = resp['cameras']
