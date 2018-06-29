from __future__ import division

import logging
logger = logging.getLogger(__name__)

import socket, pickle     

from atom.api import Bool, Str, Member, Int, List, observe
from enaml.application import deferred_call
from instrument_property import Prop, IntProp, ListProp, FloatProp
from cs_instruments import Instrument
from analysis import Analysis, AnalysisWithFigure
import numpy

class Noise_Eater(Prop):
    # must keep track of position changes and send only difference
    target_setting1 = Member() #set from 0 to 100
    target_setting2 = Member() #set from 0 to 100
    target_setting3 = Member() #set from 0 to 100
    target_setting4 = Member() #set from 0 to 100
    IP = Str()
    port = Int()
    setting_array = List()

    def __init__(self, name, experiment, description=''):
        super(Noise_Eater, self).__init__(name, experiment, description)
        self.target_setting1 = FloatProp('target_setting1', experiment, 'the target power 1 percentage','100')
        self.target_setting2 = FloatProp('target_setting2', experiment, 'the target power 2 percentage','100')
        self.target_setting3 = FloatProp('target_setting3', experiment, 'the target power 3 percentage','100')
        self.target_setting4 = FloatProp('target_setting4', experiment, 'the target power 4 percentage','100') 
        self.properties += ['target_setting1', 'target_setting2', 'target_setting3', 'target_setting4', 'IP', 'port']
        self.setting_array = [self.target_setting1, self.target_setting2, self.target_setting3, self.target_setting4]

    def update(self):
        # calculate relative move necessary
        return self.IP, self.port, self.setting_array
        

class Noise_Eaters(Instrument):   
    version = '2017.07.21'  
    #host = '10.141.210.242' # ip of raspberry pi 
    #port = 12345
    #arr = [1,5,3,4]

    pis = Member()
    s = Member()
    resultsArray = Member()

    def __init__(self, name, experiment, description=''):
        super(Noise_Eaters, self).__init__(name, experiment, description)
        self.pis = ListProp('pis', experiment, 'A list of individual Raspberry Pis', listElementType=Noise_Eater,
                               listElementName='pi')
        self.properties += ['version','pis']

    def initialize(self):
        """Open the TCP socket"""
        if self.enable:
            self.isInitialized = True

    def start(self):
        self.update()
        self.isDone = True

    def update(self):
        """
        Every iteration, send the motors updated positions.
        """
        self.resultsArray = numpy.delete(numpy.empty([1,4]), (0), axis=0)
        
        for i in self.pis:
            if self.enable:
                #arr = update()
                #arr2 = [1,2,3,4]
                #IP2 = '10.141.210.242' # ip of raspberry pi 
                #port2 = 12345
                IP, port, settings_array = i.update()
                self.s = socket.socket()
                settings_array = [ d.value for d in settings_array ]
                #print(settings_array)
                data_string = pickle.dumps(settings_array)
                self.s.connect((IP, port))
                self.s.send(data_string)
                self.resultsArray = numpy.append(self.resultsArray, [pickle.loads(self.s.recv(1024))], axis = 0)
                self.s.close()

    def writeResults(self, hdf5):
        if self.enable:
            hdf5['noise_eater'] = self.resultsArray


class Noise_EatersGraph(AnalysisWithFigure):
    """Plots a region of interest sum after every measurement"""
    version = '2017.08.15'
    enable = Bool()
    data = Member()
    update_lock = Bool(False)
    list_of_what_to_plot = Str()

    def __init__(self, name, experiment, description=''):
        super(Noise_EatersGraph, self).__init__(name, experiment, description)
        self.properties += ['version', 'enable', 'list_of_what_to_plot']
        self.data = None

    def analyzeMeasurement(self, measurementResults, iterationResults, experimentResults):
        if self.enable and ('data/noise_eater' in measurementResults):
            #every measurement, update a big array of all the noise eater data on all channels
            d = measurementResults['data/noise_eater']
            if self.data is None:
                self.data = [numpy.array([d]).flatten()]
            else:
                self.data = numpy.append(self.data, [numpy.array([d]).flatten()], axis=0)
            self.updateFigure()

    @observe('list_of_what_to_plot')
    def reload(self, change):
        self.updateFigure()

    def clear(self):
        self.data = None
        self.updateFigure()

    def updateFigure(self):
        if self.enable and (not self.update_lock):
            try:
                self.update_lock = True
                fig = self.backFigure
                fig.clf()

                if self.data is not None:
                    #parse the list of what to plot from a string to a list of numbers
                    try:
                        plotlist = eval(self.list_of_what_to_plot)
                    except Exception as e:
                        logger.warning('Could not eval plotlist in DCNoiseEaterGraph:\n{}\n'.format(e))
                        return
                    #make one plot
                    ax = fig.add_subplot(111)
                    for i in plotlist:
                        try:
                            data = self.data[:, 4*i[0] + i[1]]  # All measurements. Selected pi and channel.
                        except:
                            logger.warning('Trying to plot data that does not exist in MeasurementsGraph: box {} channel {}'.format(i[0], i[1]))
                            continue
                        label = '({},{})'.format(i[0], i[1])
                        ax.plot(data, 'o', label=label)
                    #add legend using the labels assigned during ax.plot()
                    ax.legend(bbox_to_anchor=(0., 1.02, 1., .102), loc=2, ncol = 4, mode = "expand", borderaxespad=0.0)
                    ax.grid('on')
                super(Noise_EatersGraph, self).updateFigure()
            except Exception as e:
                logger.warning('Problem in Noise_EaterGraph.updateFigure()\n:{}'.format(e))
            finally:
                self.update_lock = False
       
