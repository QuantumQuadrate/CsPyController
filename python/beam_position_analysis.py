"""
beam_position.py
Part of the CsPyController package.

This analysis takes beam position data and generates a movement correction for
feedback.

author = 'Matt Ebert'
created = '2017.09.06'
"""

import logging
from atom.api import Bool, Str, Float, Member
from analysis import Analysis
import numpy as np

logger = logging.getLogger(__name__)


class BeamPositionAnalysis(Analysis):
    """Acts as the error signal generator and process controller in a feedback
    loop to stabilize beam position.
    """

    version = '2017.09.06'

    enable = Bool(False)
    enable_feedback = Bool(False)
    enable_reorder = Bool(False)
    meas_analysis_path = Str('analysis/positions/')
    iter_analysis_path = Str('analysis/iter_positions/')
    meas_error_path = Str()
    positions_path = Str()
    setpoint_X = Float(0.0)
    setpoint_Y = Float(0.0)
    calibration_X = Float(1.0)
    calibration_Y = Float(1.0)
    positions = Member()
    position_iter_stat = Member()
    actuator_vname_X = Str()
    actuator_variable_X = Member()  # holds independentVariable for x actuator
    actuator_X = Member()  # holds picomotor object for x actuator to get current position
    actuator_vname_Y = Str()
    actuator_variable_Y = Member()  # holds independentVariable for y actuator
    actuator_Y = Member()  # holds picomotor object for y actuator to get current position

    def __init__(self, experiment):
        super(BeamPositionAnalysis, self).__init__(
            'BeamPositionAnalysis',
            experiment,
            'Error signal and feedback for beam position'
        )
        # location of position data in hdf5
        self.positions_path = 'data/'
        self.positions_path += self.experiment.Config.config.get(
            'AAS',
            'DataGroup'
        )

        # Needs to be improved to accomodate multiple data paths.
        # Center finding function can be implemented within BeamPositionAnalysis, in case it has access to raw data.
        
        self.meas_error_path = self.positions_path + '/error'
        self.positions_path += '/stats'
        self.initialize_positions()
        self.position_iter_stat = {
            'x': 0, 'y': 0, 'sigma_x': 0, 'sigma_y': 0,
            'error_x': 0, 'error_y': 0
        }
        # analyze in a separate thread
        self.queueAfterMeasurement = True
        # properties to save
        self.properties += [
            'version', 'enable', 'enable_feedback', 'setpoint_X', 'setpoint_Y',
            'actuator_vname_X', 'actuator_vname_Y', 'actuator_variable_X',
            'actuator_variable_Y', 'calibration_X', 'calibration_Y',
            'enable_reorder'
        ]

    def initialize_positions(self):
        # stores positions from each measurement for an iteration
        self.positions = {
            'valid_cnt': 0,
            'x': np.array([]),
            'y': np.array([]),
            'x0': np.array([]),
            'y0': np.array([]),
            'x1': np.array([]),
            'y1': np.array([]),
        }

    def analyzeMeasurement(self, measResults, iterResults, expResults):
        if self.enable:
            # check that the data exists and it is valid
            if (self.positions_path in measResults and
                    measResults[self.meas_error_path][()] == 0):
                # every append operation on an np array requires reallocation
                # of memory, so maybe we should try to not do all these appends
                self.positions['x0'] = np.append(
                    self.positions['x0'],
                    measResults[self.positions_path]['X0'][()]
                )
                self.positions['y0'] = np.append(
                    self.positions['y0'],
                    measResults[self.positions_path]['Y0'][()]
                )
                self.positions['x1'] = np.append(
                    self.positions['x1'],
                    measResults[self.positions_path]['X1'][()]
                )
                self.positions['y1'] = np.append(
                    self.positions['y1'],
                    measResults[self.positions_path]['Y1'][()]
                )
                self.positions['x'] = np.append(
                    self.positions['x'],
                    self.positions['x1'] - self.positions['x0']
                )
                self.positions['y'] = np.append(
                    self.positions['y'],
                    self.positions['y1'] - self.positions['y0']
                )
                self.positions['valid_cnt'] += 1
            else:
                logger.error("Unable to find positions in measurementResults.")

    def savetohdf5(self,iterationResults):
        for key in self.position_iter_stat:
            #print self.iter_analysis_path+key
            #print self.position_iter_stat[key]
            iterationResults[self.iter_analysis_path+key]=self.position_iter_stat[key]

    def analyzeIteration(self, iterResults, expResults):
        """Analyze all measurements taken in the iteration.

        process the data stored in positions and generate an error signal
        """
        if self.enable:
            self.calculateError()
            self.savetohdf5(iterResults)
            if self.enable_feedback and self.positions['valid_cnt'] >= 10:
                self.updateActuators()
            self.initialize_positions()


    def preExperiment(self, expResults):
        self.initialize_positions()
        super(BeamPositionAnalysis, self).preExperiment(expResults)

    def calculateError(self):
        xs = self.positions['x']
        ys = self.positions['y']
        x = np.mean(xs)
        sigma_x = np.std(xs)
        y = np.mean(ys)
        sigma_y = np.std(ys)
        if self.enable_reorder and (sigma_x > 0 and sigma_y > 0):
            logger.info("testing for swaps")
            # look for events where the x and y are more than 5 sigma away
            x_errs = np.divide(np.abs(np.subtract(xs, x)), sigma_x) > 5
            y_errs = np.divide(np.abs(np.subtract(ys, y)), sigma_y) > 5
            # simultaneously
            swaps = np.logical_and(x_errs, y_errs)
            # these events are where the images were swapped in order
            # unswap them
            xs_fixed = np.where(swaps, np.multiply(-1.0, xs), xs)
            ys_fixed = np.where(swaps, np.multiply(-1.0, ys), ys)
            # recalculate positions
            x = np.mean(xs_fixed)
            sigma_x = np.std(xs_fixed)
            y = np.mean(ys_fixed)
            sigma_y = np.std(ys_fixed)
        self.position_iter_stat['x'] = x
        self.position_iter_stat['sigma_x'] = sigma_x
        self.position_iter_stat['y'] = y
        self.position_iter_stat['sigma_y'] = sigma_y
        # calculate the error signal
        error_x = (x - self.setpoint_X) * self.calibration_X
        self.position_iter_stat['error_x'] = error_x
        error_y = (y - self.setpoint_Y) * self.calibration_Y
        self.position_iter_stat['error_y'] = error_y
        print self.position_iter_stat

    def find_ivar(self, ivar_name):
        for ivar in self.experiment.independentVariables:
            if ivar.name == ivar_name:
                return ivar
        return None

    def updateActuators(self):
        """Change the value of the independentVariables for the actuators."""
        # x direction
        if self.actuator_variable_X is None:
            logger.info("No ivar set for actuator X, searching")
            self.actuator_variable_X = self.find_ivar(self.actuator_vname_X)
        # get
        if self.actuator_X is None:
            logger.info("No datagroup set for actuator X, searching")
            for m in self.experiment.pyPicoServer.motors:
                if m.motor_number == '0':
                    self.actuator_X = m
        # y direction
        if self.actuator_variable_Y is None:
            logger.info("No ivar set for actuator Y, searching")
            self.actuator_variable_Y = self.find_ivar(self.actuator_vname_Y)
        if self.actuator_Y is None:
            logger.info("No datagroup set for actuator Y, searching")
            for m in self.experiment.pyPicoServer.motors:
                if m.motor_number == '1':
                    self.actuator_Y = m

        # only correct drift if we aren't already stepping position variable
        if (len(self.actuator_variable_X.valueList) == 1 and
                len(self.actuator_variable_Y.valueList == 1)):
            msg = "Moving actuator {} to position: {:.3f}, delta: {:.3f}"

            print "old X value: {}".format(self.actuator_variable_X.currentValue)
            self.updateIndependentVariableDelta(
                self.actuator_variable_X,
                self.actuator_X.current_position - self.position_iter_stat['error_x']
            )
            logger.info(msg.format(
                'X',
                self.actuator_variable_X.currentValue,
                self.position_iter_stat['error_x']
            ))

            print "old Y value: {}".format(self.actuator_variable_Y.currentValue)
            self.updateIndependentVariableDelta(
                self.actuator_variable_Y,
                self.actuator_Y.current_position - self.position_iter_stat['error_y']
            )
            logger.info(msg.format(
                'Y',
                self.actuator_variable_Y.currentValue,
                self.position_iter_stat['error_y']
            ))
        else:
            logger.warning("Detected that actuator position is being stepped. Feedback is turned off.")

    def updateIndependentVariableDelta(self, ivar, new_value):
        ivar.valueList = ivar.valueList.astype('float')
        ivar.valueList[0] = new_value
        ivar.currentValue = ivar.valueList[0]
        ivar.function = str(ivar.currentValue)
        ivar.set_gui({'currentValueStr': str(ivar.currentValue)})
