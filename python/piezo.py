from __future__ import division
__author__ = 'Martin Lichtman'
import logging
logger = logging.getLogger(__name__)

from atom.api import Bool, Float, Str, Typed, Member
from instrument_property import Prop, BoolProp, FloatProp, ListProp
from cs_instruments import Instrument


class PiezoChannel(Prop):
    version = '2014.04.06'
    setServo = Typed(BoolProp)
    setPosition = Typed(FloatProp)
    readAxis = Str()
    readServo = Member()
    readPosition=Float()
    
    def __init__(self, name, experiment, description=''):
        super(PiezoChannel, self).__init__(name, experiment, description)
        self.readServo = False
        self.setServo = BoolProp('setServo', self.experiment, '', 'False')
        self.setPosition = FloatProp('setPosition', self.experiment, '', '0')
        self.readAxis = ''
        self.readServo = False
        self.readPosition = float('nan')
        self.properties += ['version', 'setServo', 'setPosition', 'readAxis', 'readServo', 'readPosition']


class PiezoController(Prop):
    version = '2014.04.06'
    enable = Member()
    serialNumber = Str()
    identificationRead = Str()
    serialNumberRead = Str()
    channels = Typed(ListProp)
    
    def __init__(self, name, experiment, description=''):
        super(PiezoController, self).__init__(name, experiment, description)
        self.enable = False
        self.serialNumber = ''
        self.identificationRead = ''
        self.serialNumberRead = ''
        self.channels = ListProp('channels', self.experiment, listProperty=[PiezoChannel('channel'+str(i), self.experiment) for i in range(9)], listElementType=PiezoChannel, listElementName='channel')
        self.properties = ['version', 'enable', 'serialNumber', 'identificationRead', 'serialNumberRead', 'channels']


class Piezo(Instrument):
    version = '2014.04.06'
    channels = Typed(ListProp)
    controllers = Member()
    
    def __init__(self, experiment):
        super(Piezo, self).__init__('piezo', experiment)
        self.controllers = ListProp('controllers', self.experiment, listProperty=[PiezoController('controller'+str(i), self.experiment) for i in range(2)], listElementType=PiezoController, listElementName='controller')
        self.properties += ['version', 'controllers']

    def evaluate(self):
        if self.experiment.allow_evaluation:
            logger.debug('piezo.evaluate()')
            return super(Piezo, self).evaluate()

