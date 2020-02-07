from __future__ import division

import logging
logger = logging.getLogger(__name__)

from atom.api import Str, Member, Int, List, observe
from enaml.application import deferred_call
from instrument_property import Prop, ListProp, FloatProp
from cs_instruments import Instrument
import numpy
import requests

class Noise_Eater(Prop):
    # must keep track of position changes and send only difference
    target_setting = Member() #set from 0 to 100
    ip = Str()
    ID = Int()

    def __init__(self, name, experiment, description=''):
        super(Noise_Eater, self).__init__(name, experiment, description)
        self.target_setting = FloatProp('target_setting1', experiment, 'the target Voltage','1')
        self.properties += ['target_setting', 'ip', 'ID']


    def update(self):
        # calculate relative move necessary
        data = {'setpointv': self.target_setting.value}
        return self.ip, data, self.ID


class Noise_Eaters(Instrument):
    version = '2017.07.21'
    NEchannels = Member()


    def __init__(self, name, experiment, description=''):
        super(Noise_Eaters, self).__init__(name, experiment, description)
        self.NEchannels = ListProp('NEchannels', experiment, 'A list of Noise Eater channels', listElementType=Noise_Eater,
                               listElementName='NEchannel')
        self.properties += ['version','NEchannels']

    def initialize(self):
        """Open the TCP socket"""
        if self.enable:
            self.isInitialized = True

    def start(self):
        self.isDone = True


    def configChangeRequest(self, ip, data, ID):
        url = "http://"+ip+":5000/update/"+ID+"/config"
        payload = ''
        for key in data.keys():
            payload += key+'='+str(data[key])+'&'
        headers = {
            'content-type': "application/x-www-form-urlencoded",
            'cache-control': "no-cache",
            'postman-token': "09ba4097-3e23-694d-3d87-1b8d5bc3aaaa"
            }

        response = requests.request("POST", url, data=payload, headers=headers)



    def update(self):
        """
        Every iteration, send the motors updated positions.
        """
        for i in self.NEchannels:
            if self.enable:
                ip, data, ID = i.update()
                self.configChangeRequest(ip, data, str(ID))
