"""A ZeroMQ instrument communication class.

zmq_instrument.py
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
import zmq
from cs_errors import PauseError
from cs_instruments import Instrument
from analysis import Analysis
from atom.api import Int, Str, Bool, Member, Float

__author__ = 'Matthew Ebert'
logger = logging.getLogger(__name__)


class ZMQInstrument(Instrument, Analysis):
    """A instrument communication class for ZeroMQ servers.

    This class inherets from Instrument but has the capability to do ZMQ
    communication with an instrument server.

    This class is generalized from the LabView class.
    """

    port = Int(0)
    IP = Str('127.0.0.1')
    transport = Str('tcp')
    connected = Bool(False)
    msg = Str()
    results = Member()
    sock = Member()
    timeout = Float(1.0)
    error = Bool(False)
    log = Str()

    def __init__(self, name, experiment, description=''):
        """Initialize the class."""
        super(ZMQInstrument, self).__init__(name, experiment, description)
        self.results = {}
        self.setup_socket()
        self.properties += ['IP', 'port', 'timeout']
        self.doNotSendToHardware += ['IP', 'port', 'timeout']

    def acquire_data(self):
        """Retrieve data from the server."""
        self.results = self.send_json({
            'action': 'GET_RESULTS'
        })

    def close_socket(self):
        """Close the socket."""
        self.sock.close()
        self.connected = False
        self.isInitialized = False

    def close(self):
        """Prepare to shutdown."""
        self.close_socket()
        self.context.term()

    def echo_test(self):
        """Test the server connection with a quick echo request."""
        msg = 'Connection test with `{}` server '.format(self.name)
        try:
            self.send_json({'action': 'ECHO'})
            logger.info(msg + 'successful.')
            return True
        except PauseError:
            self.logger.exception(msg + 'failed.')
            return False

    def HardwareProtocol(self, o, p, settings):
        """Edit the settings dictionary to update the necessary settings.

        Should be overwritten for more complicated properties.
        """
        # The settings dict is mutable so it is passed by reference and will
        # change the variable in the higher scope.
        settings[o] = p

    def initialize(self):
        """Test connection to server."""
        if self.enable:
            logger.info('Testing `{}` server connection.'.format(self.name))
            if self.echo_test():
                self.connected = True
            else:
                self.connected = False
                self.isInitialized = False
                raise PauseError

    def toHardware(self):
        """Generate a dictionary containing the hardware settings.

        Overwrites the Prop.toHardware method to return a dictionary rather
        than an XML string.
        """
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

    def send_json(self, obj):
        """Send a dictionary object with JSON formatting to the server.

        Expects a JSON response with response['status'] == 0 for no error.
        """
        try:
            self.sock.send_json(obj)
            resp = self.sock.recv_json()
        except:
            msg = 'ZMQInstrument.update failed for `{}`.'
            logger.exception(msg.format(self.name))
            raise PauseError

        # check the response status
        if resp['status'] != 0:
            msg = 'ZMQInstrument.update failed for `{}`. Server response:\n{}'
            logger.exception(msg.format(self.name, resp['message']))
            raise PauseError

        return resp

    def setup_socket(self):
        """Set up basic client socket."""
        self.context = zmq.Context()
        # set up a request socket as the client
        self.sock = self.context.socket(zmq.REQ)
        self.update_socket()

    def start(self):
        """Send software trigger."""
        self.send_json({
            'action': 'START_ACQUISITION'
        })

    def update(self):
        """Send update command to hardware with settings."""
        self.send_json({
            'action': 'UPDATE',
            'settings': self.toHardware()
        })

    def update_socket(self):
        """Close and reopen socket with new settings."""
        addr = "{}://{}:{}".format(self.transport, self.IP, self.port)
        if self.current_addr != addr:
            try:
                self.sock.disconnect(self.current_addr)
            except zmq.ZMQError as e:
                if e.errno != zmq.ENOENT:
                    logger.exception("Unexpected error during disconnect.")

        # set timeout in ms
        self.sock.setsockopt(zmq.RCVTIMEO, self.timeout*1000)
        # zmq doesn't make an actual connection until you start sending data
        # so this is more of a formality
        self.sock.connect(addr)
        self.current_addr = addr

    def writeResults(self, hdf5):
        """Write the previously obtained results to the experiment hdf5 file.

        hdf5 is an hdf5 group, typically the data group in the appropriate part
        of the hierarchy for the current measurement.
        """
        for key, value in self.results.iteritems():
            # no special protocol
            try:
                hdf5[key] = value
            except:
                msg = (
                    'Exception in {}.writeResults() doing hdf5[key]=value for'
                    ' key={}'
                ).format(key, self.name)
                logger.exception(msg)
                raise PauseError
