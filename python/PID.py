"""PID.py
Part of the AQuA Cesium Controller software package

author=Martin Lichtman
created=2014-10-14
modified>=2014-10-14

This file implements a digital PID feedback loop.  It was written to replace the DC Noise Eater.
Data is read from the Analog Input.  The PID function is calculated, and the result is used to update the static Analog
Output.  This is updated directly, instead of via a variables update, so that it can be done every measurement
without incuring a delay.
"""

from __future__ import division
__author__ = 'Martin Lichtman'
import logging
logger = logging.getLogger(__name__)

from analysis import Analysis


class PID(AnalysisWithFigure):
    """Calculates a PID feedback control loop"""
    version = '2014.10.14'
    enable = Bool()
    P = Float()
    I = Float()
    D = Float()
    input_data_location = Str()  # something like measurementResults['data/AI/data'][4][0] for channel 4, sample 0
    output_channel = Str()

    update_lock = Bool(False)

    def __init__(self, name, experiment, description=''):
        super(PID, self).__init__(name, experiment, description)
        self.properties += ['version', 'enable', 'P', 'I', 'D', 'input_data_location', 'output_channel']
        self.data = None

    def analyzeMeasurement(self, measurementResults, iterationResults, experimentResults):
        if self.enable and (input_data_location in measurementResults):
            #every measurement, update a big array of all the noise eater data on all channels
            d = eval(input_data_location)
            if self.data is None:
                self.data = numpy.array([d])
            else:
                self.data = numpy.append(self.data, numpy.array([d]), axis=0)
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
                            data = self.data[:, i[0], i[1], i[2]]  # All measurements. Selected box, channel, and var.
                        except:
                            logger.warning('Trying to plot data that does not exist in MeasurementsGraph: box {} channel {} var {}'.format(i[0], i[1], i[2]))
                            continue
                        label = '({},{},{})'.format(i[0], i[1], i[2])
                        ax.plot(data, 'o', label=label)
                    #add legend using the labels assigned during ax.plot()
                    ax.legend()
                super(DCNoiseEaterGraph, self).updateFigure()
            except Exception as e:
                logger.warning('Problem in DCNoiseEaterGraph.updateFigure()\n:{}'.format(e))
            finally:
                self.update_lock = False
