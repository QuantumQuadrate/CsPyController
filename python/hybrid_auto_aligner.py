"""
Communicates with the Hybrid-Auto-Alignment system

hybrid_auto_aligner.py
author = Juan C. Bohorquez
created = 2023-04-13

This largely works to communicate with the auto-aligner. The auto-aligner will send cs.py messages when the beam is
being moved, so data is not stored during movement. This will also serve to set the auto-aligner settings.
"""

import logging
import threading
import numpy as np

from cs_errors import PauseError
from atom.api import Typed, Member, Int, Float, Bool, Str
from cs_instruments import TCP_Instrument
from instrument_property import StrProp, FloatProp, IntProp, BoolProp, Prop
from analysis import Analysis
from TCP import CsClientSock

logger = logging.getLogger(__name__)

__author__ = "Juan C. Bohorquez"


class BeamAlignmentFilter(Analysis):
    """
    This analysis allows the user to drop measurements in an iteration where beam alignment is outside a desired region.
    Must be used in conjunction with the hybrid_auto_aligner.AutoAligner class.
    """
    version = '2023.05.09'
    enable = Bool()
    filter_level = Int()
    max_error = Float()
    beam_avg_x = Float(0)
    beam_avg_y = Float(0)
    avg_time = Int(10)

    def __init__(self, name, experiment, description=''):
        super(BeamAlignmentFilter, self).__init__(name, experiment, description)
        self.properties += ['version', 'enable', 'filter_level', 'max_error', 'avg_time']

    def analyzeMeasurement(self, measurementResults, iterationResults, experimentResults):
        if not self.enable:
            return
        try:
            aligner_enable = self.experiment.AutoAligner.enable
        except AttributeError:
            aligner_enable = False
        if not aligner_enable:
            logger.warning("cannot filter on beam data, AutoAligner is not enabled")
            return

        beam_x = float(measurementResults["data/auto_aligner/last_image/x"][()])
        beam_y = float(measurementResults["data/auto_aligner/last_image/y"][()])

        if self.avg_time > 0:
            r = np.exp(-1/self.avg_time)  # implement a running average as an exponential decay of running average
        else:
            r = 0

        measurement = int(measurementResults.attrs['measurement'])
        self.beam_avg_x = (beam_x+r*self.beam_avg_x*(measurement > 0))/(1+r)
        # zero-out running average at start of iterations
        self.beam_avg_y = (beam_y+r*self.beam_avg_y*(measurement > 0))/(1+r)

        error_x = self.experiment.AutoAligner.control.set_point_x.value-self.beam_avg_x
        error_y = self.experiment.AutoAligner.control.set_point_y.value-self.beam_avg_y

        logger.debug("beam position measured = {}, {}".format(self.beam_avg_x, self.beam_avg_y))
        logger.debug("error signal = {},{}, |e| = {}".format(error_x,error_y,np.sqrt(error_x**2+error_y**2)))

        # compute pythagorean mean beam displacement
        if np.sqrt(error_x**2+error_y**2) > self.max_error:
            logger.warning("beam out of positon, dropping this measurement.\n beam position = {}, {}".format(beam_x, beam_y))
            return max(0, self.filter_level)


class AutoAligner(TCP_Instrument):

    enable_aligner = Member()
    timeout = Member()

    images = Member()
    control = Member()
    motors = Member()
    camera = Member()

    def __init__(self, name, experiment, description):
        super(AutoAligner, self).__init__(name, experiment, description)

        self.enable_aligner = BoolProp("enable_aligner", experiment, "Enable Auto Aligner servo?")
        self.timeout = IntProp("timeout", experiment, "")

        self.images = Images(experiment)
        self.control = Control(experiment)
        self.motors = Motors(experiment)
        self.camera = Camera(experiment)

        self.properties += ["enable_aligner", "timeout", "images", "control", "motors", "camera"]

        self.doNotSendToHardware += ["timeout"]

    def receive(self):
        """
        Receives a message from the aligner
        """

    def openThread(self):
        """
        Opens the connection thread
        """
        thread = threading.Thread(target=self.initialize)
        thread.daemon = True
        thread.start()

    def update(self):
        """
        Run at the start of each new iteration, sets exposed settings
        """
        self.send(self.toHardware())

    def start(self):
        """
        Run at start of each measurement
        """
        self.send('<{}><status><{}/>'.format(self.name, self.name))
        self.parse_results()

    def initialize(self):
        """
        Initializes connection to device, initializes internal device properties
        """
        logger.info("Initializing Device (not a Labview instrument)")
        super(AutoAligner, self).initialize()

    def parse_results(self):
        logger.debug("Query Results = {}".format(self.results))
        pass


# wrapper classes to hold nested data, for nested XML dicts
class Images(Prop):
    """
    Settings related to image saving, analysis
    """
    cutoff = Member()
    path = Member()

    def __init__(self, experiment):
        super(Images, self).__init__("images", experiment, "holds image processing parameters")

        self.cutoff = FloatProp(
            'cutoff',
            experiment,
            'Minimum value not set to zero before computing centroid (camera counts)',
            "0"
        )
        self.path = StrProp('path', experiment, 'Filepath to which beam images will be saved', "")
        self.properties += ["cutoff", "path"]


class Control(Prop):
    """
    Settings related to control loop
    """
    set_point_x = Member()
    set_point_y = Member()
    stability = Member()
    transform = Member()

    def __init__(self, experiment):
        super(Control, self).__init__("control", experiment, "holds control loop parameters")
        self.set_point_x = FloatProp("set_point_x", experiment, "spot set point x-coordinate. In pixels.", "0")
        self.set_point_y = FloatProp("set_point_y", experiment, "spot set point y-coordinate. In pixels.", "0")
        self.stability = FloatProp("stability", experiment, "size of stability region. In pixels.", "1.0")
        self.transform = Transform("transform", experiment)

        self.properties += ["set_point_x", "set_point_y", "stability", "transform"]


class Transform(Prop):
    """
    Transformation Matrix elements for one axis, between motor moves and beam displacement. That is:

    d = M.s

    where s is a vector of motor moves, and d is a vector of the beam displacements those motor moves will cause. M is
    the transfer matrix

    Both horizontal and vertical axes have significant hysteresis. They also show a small coupling to the transverse
    direction (the off-diagonal matrix elements). To solve the hysteresis issue the aligner will split the camera into
    quadrants around the set-point, these quadrants will determine if the beam needs to be moved positively/negatively
    by the motors. The correct matrix elements from the motor-beam transfer matrix will be chosen, that matrix is
    then inverted to compute the motor moves.
    """
    mxx_p = Member()
    mxy_p = Member()
    myx_p = Member()
    myy_p = Member()

    mxx_n = Member()
    mxy_n = Member()
    myx_n = Member()
    myy_n = Member()

    def __init__(self, name, experiment):
        super(Transform, self).__init__(name, experiment, "Matrix mapping beam displacement to motor moves")
        self.mxx_p = FloatProp("mxx_p", experiment, "xx element for positive x motion (pixels/step)", "0")
        self.myx_p = FloatProp("myx_p", experiment, "yx element for positive x motion (pixels/step)", "0")
        self.mxy_p = FloatProp("mxy_p", experiment, "xy element for positive y motion (pixels/step)", "0")
        self.myy_p = FloatProp("myy_p", experiment, "yy element for positive y motion (pixels/step)", "0")

        self.mxx_n = FloatProp("mxx_n", experiment, "xx element for negative x motion (pixels/step)", "0")
        self.myx_n = FloatProp("myx_n", experiment, "yx element for negative x motion (pixels/step)", "0")
        self.mxy_n = FloatProp("mxy_n", experiment, "xy element for negative y motion (pixels/step)", "0")
        self.myy_n = FloatProp("myy_n", experiment, "yy element for negative y motion (pixels/step)", "0")

        self.properties += [
            "mxx_p",
            "mxy_p",
            "myx_p",
            "myy_p",
            "mxx_n",
            "mxy_n",
            "myx_n",
            "myy_n"
        ]


class Motors(Prop):
    """
    Settings related to the PicoMotors
    """
    serial_number = Member()
    x_axis = Member()
    y_axis = Member()

    def __init__(self, experiment):
        super(Motors, self).__init__("motors", experiment, "holds motor parameters")
        self.serial_number = StrProp("serial_number", experiment, "Serial Number of the PicoMotor driver", "")
        self.x_axis = IntProp("x_axis", experiment, "motion axis of the horizontal mirror motor (1-4)", "0")
        self.y_axis = IntProp("y_axis", experiment, "motion axis of the vertical mirror motor (1-4)", "0")

        self.properties += ["serial_number", "x_axis", "y_axis"]


class Camera(Prop):
    """
    Settings related to the Blackfly Camera
    """
    serial_number = Member()
    trigger_delay = Member()
    roi = Member()
    exposure_time = Member()
    gain = Member()
    
    def __init__(self, experiment):
        super(Camera, self).__init__("camera", experiment, "holds camera parameters")
        self.serial_number = StrProp("serial_number", experiment, "Serial Number of the BlackFly camera", "")
        self.trigger_delay = IntProp(
            "trigger_delay",
            experiment,
            "amount of time between trigger signal and start of exposure (us)",
            "0.0"
        )
        self.roi = ROI(experiment)
        self.exposure_time = IntProp("exposure_time", experiment, "Length of image exposure (us)", "0")
        self.gain = IntProp("gain", experiment, "Camera gain (dB)", "0")

        self.properties += ["serial_number", "trigger_delay", "roi", "exposure_time", "gain"]


class ROI(Prop):
    """
    Holds info on the camera ROI
    """
    width = Member()
    height = Member()
    offset_x = Member()
    offset_y = Member()

    def __init__(self, experiment):

        super(ROI, self).__init__("roi", experiment, "holds ROI info")
        self.width = IntProp("width", experiment, "width of camera ROI", "50")
        self.height = IntProp("height", experiment, "height of camera ROI", "50")
        self.offset_x = IntProp("offset_x", experiment, "x-offset of the camera ROI", "0")
        self.offset_y = IntProp("offset_y", experiment, "y-offset of the camera ROI", "0")

        self.properties += ["width", "height", "offset_x", "offset_y"]
