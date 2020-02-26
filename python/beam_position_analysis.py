"""
beam_position.py
Part of the CsPyController package.

This analysis takes beam position data and generates a movement correction for
feedback.

author = 'Matt Ebert'
created = '2017.09.06'
"""

import logging

import time
from atom.api import Bool, Str, Float, Member, List

from analysis import Analysis
import numpy as np
import os.path
import h5py

import scipy.ndimage.measurements as measurements
from scipy.ndimage.morphology import binary_opening
from scipy.optimize import curve_fit


logger = logging.getLogger(__name__)


class BeamPositionAnalysis(Analysis):
    """Acts as the error signal generator and process controller in a feedback
    loop to stabilize beam position.
    """


    version = '2018.02.26'

    enable = Bool(False)
    enable_feedback = Bool(False)
    enable_TemperatureCorrection = Bool(False)
    enable_reorder = Bool(False)
    invert_TemperatureCorrection_X=Bool(False)
    invert_TemperatureCorrection_Y=Bool(False)
    meas_analysis_path = Str('analysis/positions/')
    iter_analysis_path = Str('analysis/iter_positions/')
    meas_error_paths = List()
    positions_paths = List()
    setpoint_X = Float(0.0)
    setpoint_Y = Float(0.0)
    ts = Float(0.0)  # error timestamp
    error_ts = Float(0.0)  # previous calculated error timestamp
    int_error_X = Float(0.0)  # list of historical x errors
    int_error_Y = Float(0.0)  # list of historical y errors
    calibration_X = Float(1.0)
    calibration_Y = Float(1.0)
    tau_h = Float(2)  # smoothing factor timescale in hours
    k_p = Float(0.3)
    k_i = Float(0.1)

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
        # set up with the default configuration

        self.set_position_paths()

        self.initialize_positions()
        self.position_iter_stat = {
            'x': 0, 'y': 0, 'sigma_x': 0, 'sigma_y': 0,
            'error_x': 0, 'error_y': 0
        }
        # analyze in a separate thread
        self.queueAfterMeasurement = True
        # properties to save
        self.properties += [

            'version', 'enable', 'enable_feedback', 'enable_TemperatureCorrection',
            'invert_TemperatureCorrection_X','invert_TemperatureCorrection_Y',
            'setpoint_X', 'setpoint_Y',
            'actuator_vname_X', 'actuator_vname_Y', 'actuator_variable_X',
            'actuator_variable_Y', 'calibration_X', 'calibration_Y',
            'enable_reorder', 'meas_analysis_path', 'iter_analysis_path', 'k_p', 'k_i', 'k_d'
        ]

    def set_position_paths(self, section='AAS', datagroup='Camera0DataGroup'):
        '''Sets the hdf5 source of the input data for alignment feedback'''
        # location of position data in hdf5
        positions_path_base = 'data/'
        try:
            positions_paths = self.experiment.Config.config.get(section,
                                                                datagroup)
        except Exception:
            msg = 'ConfigParser was unable to find entry: `{}.{}`.'
            'Disabling module.'
            logger.warning(msg.format(section, datagroup))
            self.enable = False
            return

        positions_paths = positions_paths.split(',')
        # Center finding function can be implemented within BeamPositionAnalysis,
        # in case it has access to raw data.
        self.meas_error_paths = [
            positions_path_base + os.path.dirname(path) + '/error'
            for path in positions_paths
        ]
        self.positions_paths = [positions_path_base + path for path in positions_paths]


    def initialize_positions(self):
        # stores positions from each measurement for an iteration
        self.positions = {
            'valid_cnt': 0,

            'x': np.array([]),  # relative position
            'y': np.array([]),
            'x0': np.array([]),  # absolute positions
            'y0': np.array([]),
            'x1': np.array([]),
            'y1': np.array([]),
            'Xcorrection': np.array([]),
            'Ycorrection': np.array([]),

        }

    def calc_beam_position(self, img):
        '''Calculate the position of a beam from a 2D image array.
        append the results to the position array
        In Rb, this is most relevant to 480 beam imaged onto EMCCD camera.
        '''
        # Initial guesses with centroid
        [COM_X, COM_Y] = self.centroid_calc(img)
        if COM_X == np.NaN and COM_Y == np.NaN:
            error = 1
        # Width guesses
        else:
            # use your guess. Units of pixels.
            [Xsigma_guess, Ysigma_guess] = [2.0, 2.0]
            try:
                # last argument is axis.
                x, error_x = self.gaussianfit(img, COM_X, Xsigma_guess, 0)
                y, error_y = self.gaussianfit(img, COM_Y, Ysigma_guess, 1)
                error = 0
                logger.info('480 x: {}, 480 y:{}'.format(x,y))
            except Exception:
                error = 1
        if error == 1:
            x = np.NaN
            y = np.NaN
        # only x and y are necessary.  if a relative measurement is performed then use
        # x#/y# too
        self.positions['x'] = np.append(self.positions['x'], x)
        self.positions['y'] = np.append(self.positions['y'], y)
        if error_x == 0 and error_y == 0 and error == 0:
            self.positions['valid_cnt'] += 1

    def append_beam_position_data(self, data, i):
        '''Extract position data from the pre-calculated stat data group'''
        # every append operation on an np array requires reallocation
        # of memory, so maybe we should try to not do all these appends
        try:
            assert(i in [0, 1])
        except AssertionError:
            logger.error('Too many shots detected for beam position analysis.')
            return

        self.positions['x{}'.format(i)] = np.append(
            self.positions['x{}'.format(i)],
            data['X{}'.format(i)][()]
        )
        self.positions['y{}'.format(i)] = np.append(
            self.positions['y{}'.format(i)],
            data['Y{}'.format(i)][()]
        )

        if self.enable_TemperatureCorrection:
            self.positions['Xcorrection']=data['Xcorrection']
            self.positions['Ycorrection']=data['Ycorrection']
        else:
            self.positions['Xcorrection']=0
            self.positions['Ycorrection']=0

        if i == 1:
            if self.invert_TemperatureCorrection_X:
                self.positions['x'] = self.positions['x1'] - self.positions['x0'] - self.positions['Xcorrection']
            else:
                self.positions['x'] = self.positions['x1'] - self.positions['x0'] + self.positions['Xcorrection']
            if self.invert_TemperatureCorrection_Y:
                self.positions['y'] = self.positions['y1'] - self.positions['y0'] - self.positions['Ycorrection']
            else:
                self.positions['y'] = self.positions['y1'] - self.positions['y0'] + self.positions['Ycorrection']
            self.positions['valid_cnt'] += 1
            # print(self.positions)


    def analyzeMeasurement(self, measResults, iterResults, expResults):
        if self.enable:
            # check that the data exists and it is valid

            for i, path in enumerate(self.positions_paths):
                if path in measResults:
                    data = measResults[path]
                    # if the data is a raw image we have to process it
                    if isinstance(data, h5py.Dataset) and len(data.shape) == 2:
                        self.calc_beam_position(data.value)
                    # if the data is alreay processed, check if it is valid
                    elif self.meas_error_paths[i] in measResults:
                        if measResults[self.meas_error_paths[i]].value == 0:
                            self.append_beam_position_data(data, i)
                        else:
                            logger.error('Position measurements at `{}` are not valid.'.format(path))
                    else:
                        msg = """
                            Positions found in measurementResults[{}],
                             but format didn't match expectations.
                        """
                        logger.error(msg.format(path))
                else:
                    logger.error("Unable to find positions in measurementResults[{}].".format(path))


    def savetohdf5(self, iterationResults):
        for key in self.position_iter_stat:
            iterationResults[self.iter_analysis_path+key] = self.position_iter_stat[key]

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

        cutoff=200 # last 200 samples.
        xs = self.positions['x']
        ys = self.positions['y']

        # We will use only last chunck of samples for beam position calculation.
        num_of_samples=min(len(xs),cutoff)
        x = np.nanmedian(xs[-num_of_samples:])
        sigma_x = np.nanstd(xs[-num_of_samples:])
        y = np.nanmedian(ys[-num_of_samples:])
        sigma_y = np.nanstd(ys[-num_of_samples:])
        # Sometimes shots can be in the wrong order

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

            x = np.nanmean(xs_fixed)
            sigma_x = np.nanstd(xs_fixed)
            y = np.nanmean(ys_fixed)
            sigma_y = np.nanstd(ys_fixed)

        self.position_iter_stat['x'] = x
        self.position_iter_stat['sigma_x'] = sigma_x
        self.position_iter_stat['y'] = y
        self.position_iter_stat['sigma_y'] = sigma_y
        # calculate the error signal
        error_x = (x - self.setpoint_X) * self.calibration_X
        self.position_iter_stat['error_x'] = error_x
        error_y = (y - self.setpoint_Y) * self.calibration_Y
        self.position_iter_stat['error_y'] = error_y

        # print self.position_iter_stat
        # apply pi filter
        self.ts = time.time()
        self.int_error_X = self.pi_filter(error_x, self.int_error_X)
        self.int_error_Y = self.pi_filter(error_y, self.int_error_Y)
        self.error_ts = self.ts  # set new timestamp, which will be used for next pi_filter call.
        self.position_iter_stat['ctrl_x'] = self.int_error_X
        self.position_iter_stat['ctrl_y'] = self.int_error_Y

    def pi_filter(self, new_err, old_ctrl):
        """Calculate and return a new error signal for control"""
        #print 'ts:{}'.format(self.ts)
        dt = (self.ts - self.error_ts)/3600.0  # in hours
        #print 'dt:{}'.format(dt)
        a = 1./((self.tau_h/dt) + 1)
        int_error = a*new_err + (1-a)*old_ctrl
        err_to_return = int_error*self.k_i + new_err*self.k_p
        # if PI filter is asked to out nan, it would rather outputs 0 so it wouldn't change
        #independent variables
        if err_to_return is np.nan:
            return 0
        else:
            return err_to_return


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

            msg = ("Moving actuator {} to position: {:.3f}, "
                   "error: {:.3f}, delta: {:.3f}")

            logger.info("old X value: "
                        "{}".format(self.actuator_variable_X.currentValue))
            self.updateIndependentVariableDelta(
                self.actuator_variable_X,

                self.actuator_X.current_position - self.position_iter_stat['ctrl_x']

            )
            logger.info(msg.format(
                'X',
                self.actuator_variable_X.currentValue,

                self.position_iter_stat['error_x'],
                self.position_iter_stat['ctrl_x']

            ))

            logger.info("old Y value: "
                        "{}".format(self.actuator_variable_Y.currentValue))
            self.updateIndependentVariableDelta(
                self.actuator_variable_Y,
                self.actuator_Y.current_position - self.position_iter_stat['error_y']
            )
            logger.info(msg.format(
                'Y',
                self.actuator_variable_Y.currentValue,

                self.position_iter_stat['error_y'],
                self.position_iter_stat['ctrl_y']

            ))
        else:
            logger.warning("Detected that actuator position is being stepped. Feedback is turned off.")

    def updateIndependentVariableDelta(self, ivar, new_value):
        ivar.valueList = ivar.valueList.astype('float')
        ivar.valueList[0] = new_value
        ivar.currentValue = ivar.valueList[0]
        ivar.function = str(ivar.currentValue)
        ivar.set_gui({'currentValueStr': str(ivar.currentValue)})


    def gaussian(self, x, c1, mu1, sigma1, B):
        res = c1 * np.exp(-(x - mu1)**2.0 / (2.0 * sigma1**2.0)) + B
        return res

    def gaussianfit(self, data, center_guess, sigma_guess, axis):
        error = 0
        data_1d = np.sum(data, axis=axis)  # check if the axis correct
        leng = range(0, len(data_1d))
        [max_signal, bg] = [np.max(data_1d), np.min(data_1d)]
        try:
            fit = curve_fit(
                self.gaussian, leng, data_1d,
                [max_signal, center_guess, sigma_guess, bg]
            )
            gaussian_center = fit[0][1]
        except RuntimeError:
            gaussian_center = np.NaN
            error = 1
        return gaussian_center, error

    def centroid_calc(self, data):
        percentile = 95
        threshold = np.percentile(data, percentile)  # Set threshold based on the percentile
        # Mask pixels having brightness less than given threshold
        thresholdmask = data > threshold
        # Apply dilation-erosion to exclude possible noise
        openingmask = binary_opening(thresholdmask)
        temp = np.ma.array(data, mask=np.invert(openingmask))
        temp2 = temp.filled(0)
        if threshold > np.max(temp2):  # if there is no signal, assign NaN
            [COM_Y, COM_X] = [np.nan, np.nan]
        else:
            [COM_Y, COM_X] = measurements.center_of_mass(temp2)  # Center of mass.
        return [COM_X, COM_Y]

