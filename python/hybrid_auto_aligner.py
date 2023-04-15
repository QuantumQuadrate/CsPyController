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
from cs_instruments import TCP_Instrument
from instrument_property import StrProp
from TCP import CsClientSock

logger = logging.getLogger(__name__)

__author__ = "Juan C. Bohorquez"


class AutoAligner(TCP_Instrument):

    to_send = Member()

    def __init__(self, name, experiment, description):
        super(AutoAligner, self).__init__(name, experiment, description)
        self.to_send = StrProp("to_send", experiment, "Message to send to aligner", '')

    def receive(self):
        """
        Receives a messag from the aligner
        """

    def update(self):
        """
        Run at the start of each new iteration, sets exposed settings
        """
        pass

    def start(self):
        """
        Run at start of each measurement. Check for messages here
        """
        pass

    def initialize(self):
        """
        Initializes connection to device, initializes internal device properties
        """
        super(AutoAligner, self).initialize()
        # run code to initialize instrument properly
        pass

    def test_send(self):
        self.send(self.to_send.value)