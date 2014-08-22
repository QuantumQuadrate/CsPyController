"""DCNoiseEater.py
Part of the AQuA Cesium Controller software package

author=Martin Lichtman
created=2014-08-22
modified>=2014-08-22

This file creates an instrument that grabs data from the DC Noise Eater.
It does so via TCP to a C# program, which in turn talks to a virtual
serial port, which in turn goes over USB, which goes to the little add-on
chip that is used to program the Propller MCU in on the noise eater board.

This instrument requests the settings every measurement, and stores them into
the hdf5.
"""

from __future__ import division
__author__ = 'Martin Lichtman'
import logging
logger = logging.getLogger(__name__)

import numpy
from atom.api import Str, Member, Bool
from cs_instruments import Instrument
import TCP
from analysis import AnalysisWithFigure


class DCNoiseEater(Instrument):
    version = '2014.08.22'

    IP = Str()
    port = Str()
    socket = Member()
    data = Member()

    def __init__(self, experiment):
        super(DCNoiseEater, self).__init__('DCNoiseEater', experiment, 'DC NoiseEater')
        self.properties += ['version', 'IP', 'port']

    def initialize(self):
        """Open the TCP socket"""
        if self.enable:
            self.socket = TCP.CsClientSock(self.IP, self.port)

            # TODO: add here some sort of communications check to see if it worked

            self.isInitialized = True

    def update(self):
        """
        Every iteration, send the motors updated positions.
        """
        if self.enable:
            msg = ''
            try:
                for i in motors:
                    # get the serial number, motor, and position from each motor
                    msg = i.update()
                    # send it to the picomotor server
                    self.socket.sendmsg(msg)
            except Exception as e:
                logger.error('Problem setting Picomotor position, closing socket:\n{}\n{}\n'.format(msg, e))
                self.socket.close()
                self.isInitialized = False
                raise PauseError

    def acquire_data(self):
        """Send a message to the C# program requesting data, and then receive it."""
        if self.enable:
            try:
                self.socket.sendmsg('get')
            except Exception as e:
                logger.error('Problem getting DC Noise Eater data, closing socket:\n{}\n{}\n'.format(msg, e))
                self.socket.close()
                self.isInitialized = False
                raise PauseError

            # TODO: now receive the data, and parse it into self.data

    def writeResults(self, hdf5):
        """Write results to the hdf5 file.  Must be overwritten in subclass to do anything."""
        hdf5['DC_noise_eater'] = self.data


class DCNoiseEaterGraph(AnalysisWithFigure):
    """Plots a region of interest sum after every measurement"""
    enable = Bool()
    data = Member()

    def __init__(self, name, experiment, description=''):
        super(DCNoiseEaterGraph, self).__init__(name, experiment, description)
        self.properties += ['enable']
        self.data = None

    def analyzeMeasurement(self, measurementResults, iterationResults, experimentResults):
        if self.enable and ('data/DC_noise_eater' in measurementResults):
            #every measurement, update a big array of all the noise eater data on all channels
            d = measurementResults['data/DC_noise_eater']
            if self.data is None:
                self.data = numpy.array([d])
            else:
                self.data = numpy.append(self.data, numpy.array([d]), axis=0)
            self.updateFigure()

    def clear(self):
        self.data = None
        self.updateFigure()

    def updateFigure(self):
        try:
            fig = self.backFigure
            fig.clf()

            if self.data is not None:
                #make one plot
                ax = fig.add_subplot(111)
                ax.plot(self.data)
                #add legend using the labels assigned during ax.plot()
                ax.legend()
            super(DCNoiseEaterGraph, self).updateFigure()
        except Exception as e:
            logger.warning('Problem in DCNoiseEaterGraph.updateFigure()\n:{}'.format(e))
