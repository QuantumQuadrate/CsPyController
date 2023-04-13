"""
Communicates with the Hybrid-Auto-Alignment system

hybrid_auto_aligner.py
author = Juan C. Bohorquez
created = 2023-04-13

This largely works to communicate with the auto-aligner. The auto-aligner will send cs.py messages when the beam is
being moved, so data is not stored during movement. This will also serve to set the auto-aligner settings.
"""

import logging
from cs_errors import PauseError
from atom.api import Typed, Member, Int, Float, Bool, Str
from cs_instruments import Instrument
from TCP import CsClientSock

logger = logging.getLogger(__name__)

__author__ = "Juan C. Bohorquez"


class AutoAligner(Instrument):

    # Comm settings
    port = Member()
    IP = Str()
    connected = Member()
    sock = Member()
    error = Bool()

    # messages
    message = Str("")
    received = Str("")

    def __init__(self, name, experiment, description):
        """

        """


        super(AutoAligner, self).__init__(name, experiment, description)
        self.properties += ["message", "received"]

    def send(self):
        """
        Sends self.message to the aligner
        """

    def receive(self):
        """
        Receives a messag from the aligner
        """

    def update(self):
        """
        Run at the start of each new iteration
        """
        pass

    def start(self):
        """
        Run at start of each measurement. Check for messages here
        """
        pass

    def initialize(self):
        """
        Initializes connection to device, sets exposed settings
        """
        pass

    def