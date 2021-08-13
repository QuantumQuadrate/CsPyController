"""HPSignalGenerator.py
Part of the AQuA Cesium Controller software package

author=Juan Bohorquez
created=2019-10-15
modified>=2019-10-15

This class holds a python wrapper for the GPIB functions of the HP8648B signal generator as well as a few functions to
facilitate it's use within the Hybrid experiment
"""

from __future__ import division
__author__ = 'Juan Bohorquez'
import logging
import pyvisa as visa
import numpy as np
import time
import threading
from atom.api import Bool, Int, Float, Str, Typed, Member, observe, Atom
from enaml.application import deferred_call
from instrument_property import Prop, BoolProp, IntProp, FloatProp, StrProp, ListProp
from cs_instruments import Instrument
from cs_errors import PauseError

logger = logging.getLogger(__name__)


class VisaError(Exception):
    """
    Error to deal with PyVISA Errors
    """
    def __init__(self, msg):
        """
        :param msg: Message tied to this particular instance of the error
        """
        self.msg = msg

    def __str__(self):
        return repr(self.msg)


class DevGPIBError(Exception):
    """
    Error to deal with GPIB Errors from the device
    """
    def __init__(self, msg):
        """
        :param msg: Message tied to this particular instance of the error
        """
        self.msg = msg

    def __str__(self):
        return repr(self.msg)


class DevFrontPanelError(Exception):
    """
    Error to deal with Front Panel Errors from the device
    """

    def __init__(self, msg):
        """
        :param msg: Message tied to this particular instance of the error
        """
        self.msg = msg

    def __str__(self):
        return repr(self.msg)


class HP8648B:
    """
    Wrapper class to deal with connecting to the HP8648B signal generator, and making use of it's functionality.

    Communication is based on GPIB, using PyVisa with the NIVISA backend
    """

    unit_fac = {"MHZ": 1.0e6, "KHZ": 1.0e3, "HZ":1.0}

    def __init__(self, address, verbose=False):
        """
        Initializes communication with device.
        :param address: String, GPIB address of device
        :param verbose: should this class be annoyingly verbose
        """

        self.dev_stat = None
        self.visa_stat = None
        self.stat = 0
        self.query = None
        self.verbose = verbose
        self.frequency = None
        self.power = None
        self.ref_freq = None
        self.ref_pow = None
        self.output_status = None
        self.freq_ref_stat = None
        self.pow_ref_stat = None

        self.address = address
        self.rm = visa.ResourceManager()

        logger.debug("Connecting to device at address {}; Found Resources {}".format(address, self.rm.list_resources()))
        if self.address in self.rm.list_resources():
            self.inst = self.rm.open_resource(address)
        else:
            self.inst = None
            msg = "Device Unavailable : '{}' is not in list_resources {}. Try Again"
            logger.error(msg.format(address, self.rm.list_resources()))
        try:
            assert self.inst is not None
        except AssertionError:
            raise AssertionError

    # --- Some Error Handling functions --------------------------------------------------------------------------------

    def dev_chk(self, clr=True):
        """
        Queries device to ask it's status, returns parsed string containing said info.
        :param clr : Boolean, should the status and event registers on the device be cleared?
        :return: dev_stat : tuple, (int, string) device status code followed by device status string
        """

        self.frequency = self.inst.query("FREQ:CW?")
        self.power = self.inst.query("POW:AMPL?")
        dev_ret = self.inst.query("SYST:ERR?")
        dev_stat = dev_ret.split(',')
        dev_stat[1] = dev_stat[1].split(";")[0]
        dev_stat[1] = dev_stat[1][1:]
        if clr:
            self.clear()
        return dev_stat

    def vis_chk(self):
        """
        Checks the status of the VISA connection's most recent communication. If device connection was opened and no
        command has been sent this will throw an error...
        :return: visa_stat : StatsCode object per PyVISA
        """
        visa_stat = self.inst.last_status
        return visa_stat

    def stat_check(self, command=None, chk=False, visa_stat = None, dev_stat = None):
        """
        Checks the status of the  device after command was sent, raising errors and warnings based of chk.

        :param command: String, GPIB command to send to rf device
        :param chk: boolean, if command unsuccessful, raise error?

        :return: stat, 0 if good, 1 if something has gone wrong
        :return: msg, message attached to current status
        """
        if visa_stat is None:
            visa_stat = self.vis_chk()
        if dev_stat is None:
            dev_stat = self.dev_chk()

        self.visa_stat = visa_stat
        self.dev_stat = dev_stat

        msg = "Visa Status : {}, {}\n Device Status = {}, {}"
        msg = msg.format(visa_stat.value, visa_stat.name, dev_stat[0], dev_stat[1])
        if command is not None:
            msg = "Command sent '{}'\n {}".format(command, msg)

        # Verify status of device
        self.stat = 0
        if visa_stat.value is not 0:
            self.stat = 1
            if chk:
                logger.error("Error from VISA: " + msg)
                raise PauseError(msg)
            else:
                logger.warning("Warning from VISA: " + msg)
        # Messages < 0 are GPIB errors
        if int(dev_stat[0]) < 0:
            self.stat = 1
            if chk:
                logger.error("Error from GPIB: " + msg)
                raise PauseError(msg)
            else:
                logger.warning("Warning from GPIB: " + msg)
        # Some messages > 0 are front panel errors. A few are not errors but messages related to memory copying. I don't
        # intend to use this functionality so I'll just treat them as errors.
        elif int(dev_stat[0]) > 0:
            self.stat = 1
            if chk:
                logger.error("Error from Front Panel " + msg)
                raise PauseError(msg)
            else:
                logger.warning("Warning from Front Panel " + msg)

        if self.verbose:
            logger.info(msg)
        else:
            logger.debug(msg)

        return self.stat, msg

    def write_chk(self, command, chk=False):
        """
        Function that writes to the connected instrument and automatically checks the device's status through PyVISA s
        status returned, potentially shutting off operation in case of a failure.
        :param command : String, GPIB command to send to rf device
        :param chk : boolean, if command unsuccessful, raise error?

        :return: stat, 0 if good, 1 if something has gone wrong
        :return msg, message attached to current status
        """
        ret = self.inst.write(command)

        return self.stat_check(command, chk, visa_stat=ret[1])

    def query_chk(self, command, chk=False):
        """
        Function that queries the connected instrument and automatically checks the device's status through PyVISA
        status and internal status, potentially shutting off operation in case of a failure.
        writes result of query to self.query

        :param command : String, GPIB command to send to rf device
        :param chk : boolean, if command unsuccessful, raise error?

        :return: stat, 0 if good, 1 if something has gone wrong
        :return msg, message attached to current status
        """
        self.query = self.inst.query(command)

        return self.stat_check(command, chk)

    # -- Device interface wrapping functions to make this feel more like python than basic. ----------------------------
    def clear(self):
        """
        Clears status and event registers
        """
        self.inst.write("*CLS")

    def reset(self):
        """
        Resets the signal generator to a default state (see SCPI Command reference)

        :return: stat, 0 if good, 1 if something has gone wrong
        :return msg, message attached to current status
        """
        return self.write_chk("*RST", chk=True)

    def identity(self):
        """
        Returns the instrument's identity
        :return: identity: string
        """
        self.query_chk("*IDN?", chk=True)
        return self.query

    def self_test(self):
        """
        Executes instrument self-test

        :return: string, self test result
        """
        self.query_chk("*TST?", chk=True)
        return self.query

    def inst_wait(self):
        """
        Instrument waits until previous commands are completed
        :return: stat, 0 if good, 1 if something has gone wrong
        :return msg, message attached to current status
        """
        return self.write_chk("*WAI", chk=True)

    # -- setters -------------------------------------------------------------------------------------------------------
    def set_freq(self, value, units):
        """
        Sets the output RF frequency of the HP 8648 Signal generator.
        :param value: positive float, representing frequency. Device has maximum of 10Hz resolution
        :param units: string, may be "MHZ", "KHZ", or "HZ"

        :return: stat, 0 if good, 1 if something has gone wrong
        :return msg, message attached to current status
        """

        value = abs(value)

        assert units in self.unit_fac.keys()

        # Fulfill up to 10 Hz precision criteria
        fq = value*self.unit_fac[units]
        fq = round(fq/10.0)*10.0
        value = fq/self.unit_fac[units]

        # Fulfill up to 9 digits criteria
        valstr = repr(value)
        if len(valstr) > 10:
            valstr = valstr[:10]

        cmd = "FREQ:CW {} {}".format(valstr, units)
        self.frequency = value*self.unit_fac[units]
        return self.write_chk(cmd, chk=True)

    def set_ref_freq(self, value, units):
        """
        Writes the reference RF frequency of the HP 8648 Signal generator to "Non-Volatile Memory"

        :param value: Float, up to 10 Hz resolution
        :param units: Frequency unit. May be "MHZ", "KHZ", "HZ"

        :return: stat, 0 if good, 1 if something has gone wrong
        :return msg, message attached to current status
        """

        value = abs(value)

        assert units in self.unit_fac.keys()

        # Fulfill up to 10 Hz precision criteria
        fq = value*self.unit_fac[units]
        fq = round(fq/10.0)*10.0
        value = fq/self.unit_fac[units]

        # Fulfill up to 9 digits criteria
        valstr = repr(value)
        if len(valstr) > 10:
            valstr = valstr[:10]

        cmd = "FREQ:REF {} {}".format(valstr, units)
        self.ref_freq = value*self.unit_fac[units]
        return self.write_chk(cmd, chk=True)

    def set_power(self, value):
        """
        Sets power at output of the HP 8648 Signal generator.
        Requirement that value string may be up to 4 digits long plus a sign if applicable, or have a maximum resolution
        of 0.1dB, 0.001 mV, or 0.01uV.

        I have to be honest, I don't know what the difference between MV and MVEMF and the like is. I'm doing my best...
        This Currently only implements dB and dBm functionality. If you need mV/uV etc you'll have to add it yourself.

        :param value: float, power in dBm (dB if in reference mode)

        :return: stat, 0 if good, 1 if something has gone wrong
        :return msg, message attached to current status
        """

        # fulfil up to 0.1dB(m) resolution criteria
        value = round(value, 1)

        # fulfil up to 4 digits plus a sign criteria
        valbf = abs(value)
        valstr = repr(valbf)
        vallst = valstr.split('.')
        whole_dig = len(vallst[0])
        sgn = "-" if value < 0 else ""
        if whole_dig > 4:
            msg = "Entirely too many digits. {} dBm is too big or small to be a sensible power".format(value)
            raise PauseError(msg)
        if whole_dig == 4:
            valstr = repr(int(round(value)))
        if whole_dig < 4:
            valstr = sgn + vallst[0] + "." + vallst[1][0]

        unit = "DBM"  # Hardcoded for now
        cmd = "POW:AMPL {} {}".format(valstr, unit)
        self.power = value
        return self.write_chk(cmd, chk=True)

    def set_ref_power(self, value):
        """
        Writes reference power of the HP 8648 Signal generator to "Non-Volatile Memory"
        Requirement that value string may be up to 4 digits long plus a sign if applicable, or have a maximum resolution
        of 0.1dB, 0.001 mV, or 0.01uV.

        I have to be honest, I don't know what the difference between MV and MVEMF and the like is. I'm doing my best...
        This Currently only implements dB and dBm functionality. If you need mV/uV etc you'll have to add it yourself.

        :param value: float, power in dBm (dB if in reference mode)

        :return: stat, 0 if good, 1 if something has gone wrong
        :return msg, message attached to current status
        """

        # fulfil up to 0.1dB(m) resolution criteria
        value = round(value, 1)

        # fulfil up to 4 digits plus a sign criteria
        valbf = abs(value)
        valstr = repr(valbf)
        vallst = valstr.split('.')
        whole_dig = len(vallst[0])
        sgn = "-" if value < 0 else ""
        if whole_dig > 4:
            msg = "Entirely too many digits. {} dBm is too big or small to be a sensible power".format(value)
            raise PauseError(msg)
        if whole_dig == 4:
            valstr = repr(int(round(value)))
        if whole_dig < 4:
            valstr = sgn + vallst[0] + "." + vallst[1][0]

        unit = "DBM"  # Hardcoded for now
        cmd = "POW:REF {} {}".format(valstr, unit)
        self.ref_pow = value
        return self.write_chk(cmd, chk=True)

    def set_output_stat(self, state):
        """
        Turns RF power on/off
        :param state: Boolean, True = turn on, False = turn off

        :return: stat, 0 if good, 1 if something has gone wrong
        :return msg, message attached to current status
        """

        st = "ON" if state else "OFF"
        cmd = "OUTP:STAT {}".format(st)
        self.output_status = state
        return self.write_chk(cmd, chk=True)

    def set_pow_ref_stat(self, state):
        """
        Turns power reference mode on or off. On makes all amplitude changes relative to reference
        :param state: Boolean, True = turn on, False = turn off

        :return: stat, 0 if good, 1 if something has gone wrong
        :return msg, message attached to current status
        """

        st = "ON" if state else "OFF"
        cmd = "POW:REF:STAT {}".format(st)
        self.pow_ref_stat = state
        return self.write_chk(cmd, chk=True)

    def set_freq_ref_stat(self, state):
        """
        Turns frequency reference mode on or off. On makes all frequency changes relative to reference
        :param state: Boolean, True = turn on, False = turn off

        :return: stat, 0 if good, 1 if something has gone wrong
        :return msg, message attached to current status
        """

        st = "ON" if state else "OFF"
        cmd = "FREQ:REF:STAT {}".format(st)
        self.freq_ref_stat = state
        return self.write_chk(cmd, chk=True)

    # -- getters -------------------------------------------------------------------------------------------------------
    def get_freq(self, units="HZ"):
        """
        Reads output RF frequency
        :param: string, units to give frequency. units must be "MHZ", "KZ", or "HZ"
        :return: float, output frequency in <units>
        """

        self.query_chk("FREQ:CW?", chk=True)
        self.frequency = float(self.query)

        return self.frequency/self.unit_fac[units]

    def get_ref_freq(self, units="HZ"):
        """
        Reads reference RF frequency from memory
        :param: string, units to give frequency. units must be "MHZ", "KZ", or "HZ"
        :return: float, reference frequency in Hz
        """

        self.query_chk("FREQ:REF?", chk=True)
        self.ref_freq = float(self.query)
        return self.ref_freq/self.unit_fac[units]

    def get_ref_freq_stat(self):
        """
        Reads reference RF frequency mode status
        :return: boolean, reference frequency status (True, False) : frequency reference mode (on, off)
        """

        self.query_chk("FREQ:REF:STAT?", chk=True)
        self.freq_ref_stat = bool(self.query)

        return self.freq_ref_stat

    def get_pow(self):
        """
        Reads output RF amplitude in dBM
        :return: float, output power in dBm
        """

        self.query_chk("POW:AMPL?", chk=True)
        self.power = float(self.query)
        return self.power

    def get_ref_pow(self):
        """
        Reads reference RF power from memory
        :return: float, reference power in dBm
        """

        self.query_chk("POW:REF?", chk=True)
        self.ref_pow = float(self.query)
        return self.ref_pow

    def get_ref_pow_stat(self):
        """
        Reads reference RF power mode status
        :return: boolean, reference power status (True, False) : power reference mode (on, off)
        """

        self.query_chk("FREQ:REF:STAT?", chk=True)
        self.pow_ref_stat = bool(self.query)
        return self.pow_ref_stat

    def get_output_stat(self):
        """
        Reads rf output status.
        :return: boolean, rf output status (True, False) : output (on, off)
        """
        self.query_chk("OUTP:STAT?")
        self.output_status = bool(self.query)
        logger.info(self.output_status)
        return self.output_status

    def close(self):
        """
        Closes connection to Device
        """
        self.inst.close()

    def step_freq(self, value, units):
        """
        Steps the output frequency by amount specified by <value> <units>
        :param value: Float, desired frequency step value
        :param units: String, desired frequency step units, can be "MHZ", "KHZ", or "HZ"

        :return: stat, 0 if good, 1 if something has gone wrong
        :return msg, message attached to current status
        """
        assert units in self.unit_fac.keys()

        self.get_freq(units)
        freq_c = self.frequency/self.unit_fac[units]
        freq_t = freq_c+value
        return self.set_freq(freq_t, units)

    def step_freq_adiabat(self, value, units, step=0.1, t_wait=None):
        """
        Steps the output frequency to value in discrete steps of size <step> MHZ. Starts from self.frequency ends
        as <value> <units>. For reference, when t_wait = None, each step takes roughly 100ms. This
        :param value: Float, Value of desired end frequency
        :param units: String, unit of desired end frequency. Can be "MHZ", "KHZ", "HZ"
        :param step: Float, discrete step size in MHZ
        :param t_wait: Float, (S) wait time in between sending discrete step commands. If None, no waiting, time scale
                            of steps is set by GPIB communication time

        :return: stat, 0 if good, 1 if something has gone wrong
        :return msg, message attached to current status
        """

        assert units in self.unit_fac.keys()

        f_i = self.get_freq(units)
        f_f = value
        f_step = step*self.unit_fac["MHZ"]/self.unit_fac[units]

        if f_i > f_f:
            sgn = -1
        else:
            sgn = 1
        f_list = np.arange(f_i, f_f, sgn*f_step)
        logger.debug(f_list)
        for frequency in f_list:
            self.set_freq(frequency, units)
            time.sleep(t_wait)

        fc = self.get_freq(units)
        if fc != value and fc-value <= step*self.unit_fac["MHZ"]/self.unit_fac[units]:
            self.set_freq(value, units)
        return self.stat_check()


class RydHP(Instrument):
    version = '2019.10.15'

    frequency = Member()
    freq_step = Member()
    power = Member()
    RF_on = Bool()
    keep_locked = Bool(True)
    enable = Bool(False)

#    freq_ref_on = Bool()
#    pow_ref_on = Bool()
#    ref_freq = Float()
#    ref_pow = Float()
    visa_stat = Int()
    gen_stat = Int()

    addr = Member()

    gen = Member()

    def __init__(self, name, experiment, description='HP8648B Signal Generator'):
        super(RydHP, self).__init__(name, experiment, description)
        self.frequency = FloatProp('frequency', experiment, 'Output Frequency (MHz)', '0')
        self.freq_step = FloatProp('freq_step', experiment, 'Frequency Step when attempting to keep lock (MHz)', '0.1')
        self.power = FloatProp('power', experiment, 'Output Power (dBm)', '0')
#        self.RF_on = BoolProp('RF_on', experiment, 'RF output state (on/off)', 'True')
#        self.freq_ref_on = BoolProp('freq_ref_on', experiment, 'Frequency Reference mode (on/off)', 'False')
#        self.pow_ref_on = BoolProp('pow_ref_on', experiment, 'Power Reference Mode (on/off)', 'False')
#        self.ref_freq = FloatProp('ref_freq', experiment, 'Reference Frequency (MHz)', '0')
#        self.ref_pow = FloatProp('ref_pow', experiment, 'Reference Power (dBm)', '0')

        # self.visa_stat = IntProp('visa_stat', experiment, 'NI Visa status code', '0')
        # self.gen_stat = IntProp('generator status', experiment, 'RF generator status code', '0')

        self.addr = StrProp('addr', experiment, 'GPIB address of Generator', '\'GPIB1::20::INSTR\'')

        self.properties += ['frequency', 'power', 'RF_on', 'freq_step']# 'freq_ref_on', 'pow_ref_on', 'ref_freq', 'ref_pow']

    def initialize(self):
        if self.enable and not self.isInitialized:
            if self.gen is not None:
                try:
                    self.gen.close()
                except AttributeError:
                    logger.warning("AttributeError raised when closing Gen. Issue with NoneType?")
                del self.gen
            logger.info("Instantiating Generator")
            try:
                self.gen = HP8648B(address=self.addr.value)
                logger.info("Generator : {}".format(self.gen.address))
                self.isInitialized = True
            except AssertionError:
                self.isInitialized = False
                self.enable = False

    def start(self):
        self.isDone = True

    def update(self):
        # logger.info("Updating, Fc = {} MHz, Fs = {} MHz".format(self.gen.get_freq("MHZ"), self.frequency.value))
        if not self.isInitialized:
            self.initialize()
        if not self.enable:
            return
        if self.keep_locked:
            # logger.info("Sweeping Frequency")
            if self.frequency.value != self.gen.get_freq("MHZ"):
                logger.info("Sweeping Frequency from {} MHz to {} MHz".format(self.gen.get_freq("MHZ"), self.frequency.value))
                self.gen.step_freq_adiabat(self.frequency.value, "MHZ", step=self.freq_step.value, t_wait=0.2)
                logger.info("Sweep Complete: F_current = {} MHz, F_set = {} MHz".format(self.gen.get_freq("MHZ"), self.frequency.value))
        else:
            if self.frequency.value != self.gen.get_freq("MHZ"):
                logger.info("Jumping Frequency from {} MHz to {} MHz".format(self.gen.get_freq("MHZ"), self.frequency.value))
                self.gen.set_freq(self.frequency.value, "MHZ")

        if self.power.value != self.gen.get_pow():
            logger.info("Jumping Power from {} dBm to {} dBm".format(self.gen.get_pow(), self.power.value))
            self.gen.set_power(self.power.value)

    def output_toggle(self):
        #logger.info( self.isInitialized
        if self.isInitialized:
            self.gen.set_output_stat(not self.gen.get_output_stat())
            self.RF_on = self.gen.get_output_stat()

    def close_connection(self):
        self.isInitialized = False
        self.gen.close()