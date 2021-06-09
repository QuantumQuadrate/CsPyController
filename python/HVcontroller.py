from __future__ import division
__author__ = 'Juan Bohorquez'
import logging
import serial
import struct
from atom.api import Bool, Int, Float, Str, Typed, Member, observe, Atom
from enaml.application import deferred_call
from instrument_property import Prop, BoolProp, IntProp, FloatProp, StrProp, ListProp
from cs_instruments import Instrument
from cs_errors import PauseError

logger = logging.getLogger(__name__)

class hvbox:

    # Command characters
    ECHO = 'E'
    SET = 'S'
    READ = 'R'

    # Secondary command characters
    INIT = 'I'
    RESET = 'R'
    UPDATE = 'U'
    CLEAR = 'X'
    OUTPUT = 'O'
    SETCLR = 'C'
    SYNC = 'S'

    TIMEOUT = 1  # s

    def __init__(self, address, n_dac = 3, v_ref_pos=None, v_ref_neg=None):
        """
        :param address: (str) COM port address corresponding to the arduino
        :param n_dac: (int) Number of dac boards being controlled
        :param v_ref_pos: (float or list of float) positive voltage reference(s) being used by dacs.
            if a float, all dacs presumed to us the same positive voltage reference
            if a list, should be of len() = n_dac, index corresponds to board
            defaults to list with values 10.0 with len() = n_dac
        :param v_ref_neg: (float or list of float) negative voltage reference(s) being used by dacs.
            if a float, all dacs presumed to us the same negative voltage reference
            if a list, should be of len() = n_dac, index corresponds to board
            defaults to list with values 0.0 with len() = n_dac
        """
        self.address = address
        self.n_dac = int(n_dac)

        logger.info("Setting positive voltage reference")
        # ensure voltage reference values are valid arrays
        if v_ref_pos is None:
            v_ref_pos = [10.0]*self.n_dac
        if type(v_ref_pos) in [float,int]:
            v_ref_pos = [float(v_ref_pos)]*self.n_dac
        try:
            self.v_ref_pos = [float(ref) for ref in v_ref_pos]
        except (TypeError, ValueError):
            raise TypeError(
                "Reference Voltages must be a float or an int, or a list of floats or ints"
            )

        if v_ref_neg is None:
            v_ref_neg = [10.0] * self.n_dac
        if type(v_ref_neg) in [float, int]:
            v_ref_neg = [float(v_ref_neg)] * self.n_dac
        try:
            self.v_ref_neg = [float(ref) for ref in v_ref_neg]
        except (TypeError, ValueError):
            raise TypeError(
                "Reference Voltages must be a float or an int, or a list of floats or ints"
            )

        self.serial = None
        self.open_connection()

    @property
    def v_ref_pos(self):
        """
        :return: (list) list of floats
        """
        return self._v_ref_pos

    @v_ref_pos.setter
    def v_ref_pos(self, v_ref_pos):
        logger.info("Setting positive voltage reference")
        # ensure voltage reference values are valid arrays
        if v_ref_pos is None:
            v_ref_pos = [10.0]*self.n_dac
        if type(v_ref_pos) in [float,int]:
            v_ref_pos = [float(v_ref_pos)]*self.n_dac
        try:
            self._v_ref_pos = [float(ref) for ref in v_ref_pos]
        except (TypeError, ValueError):
            raise TypeError("Reference Voltages must be a float or an int, or a list of floats or ints")

        self._v_ref_pos = [float(ref) for ref in v_ref_pos]

    @property
    def v_ref_neg(self):
        """
        :return: (list) list of floats
        """
        return self._v_ref_neg

    @v_ref_neg.setter
    def v_ref_neg(self, v_ref_neg):
        # ensure voltage reference values are valid arrays
        if v_ref_neg is None:
            v_ref_neg = [10.0] * self.n_dac
        if type(v_ref_neg) in [float, int]:
            v_ref_neg = [float(v_ref_neg)] * self.n_dac
        try:
            if any([type(ref) not in [float, int] for ref in v_ref_neg]):
                raise ValueError("Reference voltages must be floats or ints")
        except (TypeError, ValueError):
            raise TypeError("Reference Voltages must be a float or an int, or a list of floats or ints")


        self._v_ref_neg = [float(ref) for ref in v_ref_neg]

    def open_connection(self):
        logger.info("Opening Serial Connection")
        self.serial = serial.Serial(self.address, timeout=self.TIMEOUT)
        logger.info("Serial port open : {}".format(self.serial))

    def close_connection(self):
        self.serial.close()

    def volt_to_dac(self, voltage, board):
        """
        Converts desired output voltage to the 20 bit word that is to be written to the DAC. 20 bit
        word is encoded as a 20 bit int.

        :param voltage: voltage output desired from a board
        :param board: int, index of the board's dac value being generated
        :return: int, 20 bit word to be written to 20 bit dac
        """
        v_neg = self.v_ref_neg[board]
        v_pos = self.v_ref_pos[board]
        if voltage < v_neg:
            return 0
        if voltage > v_pos:
            return 2**20 - 1
        return int((voltage-v_neg)*(2**20-1)/(v_pos-v_neg))

    def dac_to_volt(self, word, board):
        """
        Converts 20 bit word (encoded as a 20 bit int) from the DAC into the respective output voltage
        of that DAC.

        :param word: (int) 20 bit word, encoded as an int from 0 to 2**20-1, corresponding to a DAC output
        :param board: int, index of board generating that word
        :return: float, voltage corresponding to the 20 bit word.
        """
        v_neg = self.v_ref_neg[board]
        v_pos = self.v_ref_pos[board]
        return (v_pos - v_neg) * word / (2**20 - 1) + v_neg

    def set_voltage(self, voltage, board):
        """
        Set DAC output register on the board specified to output the voltage specified
        :param board: int, index of board which is having it's output modified
        :param voltage: float, desired output voltage of board
        """
        logger.info("Setting voltage on board {}".format(board))
        word = self.volt_to_dac(voltage, board)
        msg = struct.pack('>ccBLc', self.SET, self.OUTPUT, board, word, '\n')
        self.serial.write(msg)
        logger.debug(self.serial.read(len(msg)))

    def read_voltage(self, board):
        """
        Read the DAC output register of the board specified. If board is greater than the number of
        DACs being controlled, the voltage outputs of all dacs are returned as a list

        :param board: index corresponding to the board to be queried
        :return: voltage(s) stored in the DAC output register addressed, or error code
        """
        msg = struct.pack('>ccBc', self.READ, self.OUTPUT, board, '\n')
        self.serial.write(msg)
        if board < self.n_dac:
            return_msg = self.serial.read(4+1)
            return self.dac_to_volt(struct.unpack('>Lc',return_msg)[0],board)
        else:
            return_msg = self.serial.read(self.n_dac*4+1)
            return [self.dac_to_volt(d, board) for board, d in enumerate(
                    struct.unpack('>LLLc', return_msg)[0:self.n_dac])]

    def read_all(self):
        """
        Reads the voltage output register of all DAC boards
        :return: list of voltages stored in the output registers of all DACs being controlled
        """

        return self.read_voltage(self.n_dac)

    def set_sync(self, voltages):
        """
        Synchronously set DAC output registers.
        Each DAC is set to its own value, and they all update synchronously.

        :param voltages: List of voltages (in volts) of length self.n_dac, in order
        :return: Serial output from Arduino, either echo of command or error code
        """
        if len(voltages) != self.n_dac:
            raise ValueError("Voltage list must be of length n_dac")
        words = [self.volt_to_dac(volt,board) for board, volt in enumerate(voltages)]
        msg = struct.pack(">ccB%dL" % self.n_dac, self.SET, self.SYNC, self.n_dac, *words)
        self.serial.write(msg)
        return self.serial.read(len(msg))

    def setclear(self, voltage, board):
        """
        Set CLR output register (value to pulse when cleared)

        :param voltage: Voltage in volts to set CLR output register to
        :param board: Address of DAC to be addressed
        :return: Serial output from Arduino, either echo of command or error code
        """
        word = self.volt_to_dac(voltage, board)
        msg = struct.pack('>ccBLc', self.SET, self.SETCLR, board, word, '\n')
        self.serial.write(msg)
        return self.serial.read(len(msg))

    def clear(self, board):
        """
        Pulse voltage in CLR register, then return to DAC register voltage.
        Voltage cannot be held at CLR value.

        :param board: Address of DAC to be addressed
        :return: Serial output from Arduino, either echo of command or error code
        """
        msg = struct.pack('>ccBBc', self.SET, self.CLEAR, board, 0, '\n')
        self.serial.write(msg)
        return self.serial.read(len(msg))

    def read_clear(self, board):
        """
        Read CLR output register of addressed DAC

        :param board: Address of DAC to be addressed
        :return: Voltage(s) listed in CLR output register addressed, or error code
        """
        msg = struct.pack('>ccBc', self.READ, self.SETCLR, board, '\n')
        self.serial.write(msg)
        returnmsg = self.serial.read(3 * 4 + 1)
        if board < self.n_dac:
            returnmsg, g = struct.unpack('>Lc', returnmsg)
            return self.dac_to_volt(returnmsg,board)
        else:
            return [self.dac_to_volt(d,board) for boad,d in enumerate(
                struct.unpack('>LLLc', returnmsg)[0:self.n_dac])]

    def initialize(self, board, linear_compensation=0):
        """
        Initialize DAC: Sets linear compensation mode and resets DAC control
        register to value coded into Arduino (Old Labview code uses mode 1)
        Linear Compensation modes: 1: 10-12V, 2: 12-16V, 3: 16-19V, 4: 19-20V, default: 0-10V

        :param board: Address of DAC to be addressed
        :param linear_compensation: Linear compensation mode - see above list
        :return: Serial output from Arduino, either echo of command or error code
        """
        msg = struct.pack('>ccBBc', self.SET, self.INIT, board, linear_compensation, '\n')
        self.serial.write(msg)
        return self.serial.read(len(msg))

    def reset(self, board):
        """
        Reset DAC: Returns DAC to state immediately after powering on
        Control registers are all reset to defaults

        :param board: Address of DAC to be addressed
        :return: Serial output from Arduino, either echo of command or error code
        """
        msg = struct.pack('ccBBc', self.SET, self.RESET, board, 0, '\n')
        self.serial.write(msg)
        return self.serial.read(len(msg))

    def echo(self):
        """
        Asks Arduino to echo a short message (up to 4 characters, set to 'Echo' here)
        Tests serial connection with Arduino.

        :return: Serial output from Arduino, either echo of command or error code
        """
        msg = struct.pack('c4s', self.ECHO, 'cho\n')
        self.serial.write(msg)
        return self.serial.readline()

    def __repr__(self):
        return "hvbox({},{},{}.{})".format(self.address, self.n_dac, self.v_ref_pos, self.v_ref_neg)


class HighVoltageController(Instrument):

    version = '2021.05.29'

    address = Member()
    voltage1 = Member()
    voltage2 = Member()
    voltage3 = Member()

    v_ref_p1 = Member()
    v_ref_p2 = Member()
    v_ref_p3 = Member()

    v_ref_n1 = Member()
    v_ref_n2 = Member()
    v_ref_n3 = Member()

    out_1 = Float()
    out_2 = Float()
    out_3 = Float()

    controller = Member()

    def __init__(self,  name, experiment, description='HV control board'):
        super(HighVoltageController, self).__init__(name, experiment, description)
        self.address = StrProp("address", experiment, "COM port address of Arduino", "'COM1'")
        self.voltage1 = FloatProp("voltage1", experiment, "Voltage output from DAC 1", '0.0')
        self.voltage2 = FloatProp("voltage2", experiment, "Voltage output from DAC 2", '0.0')
        self.voltage3 = FloatProp("voltage3", experiment, "Voltage output from DAC 3", '0.0')

        self.v_ref_p1 = FloatProp("v_ref_p1", experiment, "Positive Voltage Reference for DAC 1", '10')
        self.v_ref_p2 = FloatProp("v_ref_p2", experiment, "Positive Voltage Reference for DAC 2", '10')
        self.v_ref_p3 = FloatProp("v_ref_p3", experiment, "Positive Voltage Reference for DAC 3", '10')
        self.v_ref_n1 = FloatProp("v_ref_n1", experiment, "Negative Voltage Reference for DAC 1", '0')
        self.v_ref_n2 = FloatProp("v_ref_n2", experiment, "Negative Voltage Reference for DAC 2", '0')
        self.v_ref_n3 = FloatProp("v_ref_n3", experiment, "Negative Voltage Reference for DAC 3", '0')

        self.properties += [
            "address",
            "voltage1",
            "voltage2",
            "voltage3",
            "v_ref_p1",
            "v_ref_p2",
            "v_ref_p3",
            "v_ref_n1",
            "v_ref_n2",
            "v_ref_n3"
        ]

    def initialize(self):
        if self.enable and not self.isInitialized:
            if self.controller is not None:
                try:
                    self.controller.close_connection()
                except AttributeError:
                    logger.warning("AttributeError raised when closing controller. Issue with NoneType?")
                del self.controller
            try:
                logger.info("Instantiating HV controller")
                self.controller = hvbox(
                    address=self.address.value,
                    n_dac=3,
                    v_ref_pos=[
                        self.v_ref_p1.value,
                        self.v_ref_p2.value,
                        self.v_ref_p3.value
                    ],
                    v_ref_neg=[
                        self.v_ref_n1.value,
                        self.v_ref_n2.value,
                        self.v_ref_n3.value
                    ]
                )
                logger.info("HV controller : {}".format(repr(self.controller)))
            except TypeError as e:
                logger.warning("Failed to instantiate HV controller. Error : {}".format(e), exc_info=True)
                self.isInitialized = False
                self.enable = False
            else:
                self.isInitialized = True

    def start(self):
        self.isDone = True

    def update(self):
        if not self.isInitialized:
            self.initialize()
        if not self.enable:
            return
        self.controller.set_voltage(self.voltage1.value, 0)
        self.controller.set_voltage(self.voltage2.value, 1)
        self.controller.set_voltage(self.voltage3.value, 2)
        self.out_1, self.out_2, self.out_3 = self.controller.read_all()

