"""These are the waveform functions for the AQuA project.
They define the operation of the HSDIO, AO and DAQmxDO outputs.
Use the functions HSDIO(time, channel, state), DO(time, channel, state), AO(time, channel, voltage) and label(time, text).
The user should ensure that all waveform functions take in the start time as the first parameter,
and return the end time.
"""

# reset the time
t = 0

HSDIO = experiment.LabView.HSDIO.add_transition
AO = experiment.LabView.AnalogOutput.add_transition
DO = experiment.LabView.DAQmxDO.add_transition
label = experiment.functional_waveforms_graph.label

class DDS(object):
    """This class represents a single DDS channel controlled by one or more HSDIO channels.
    This class does NOT communicate directly with the DDS box, that is taken care of in the DDS.py file.
    This class only manipulates the HSDIO channels which switch the current HSDIO profile.
    It takes care of grey coding the profile changes.
    This class only works properly if all calls to a particular instance are done sequentially, but that is the expected situation for a single DDS channel."""
    
    def __init__(self, t, channels, profiles=None):
        """Create a new DDS channel.
        channels: a list of the HSDIO channels corresponding to the DDS bits.  e.g. (0, 1, 18)
        profile:  a dict using profile names as keys to look up the bit settings.  e.g. {"MOT": (0,0,0), "OFF": (1,0,0)}
        """
        
        self.channels = channels
        self.profiles = profiles
        
        # keep track of the state
        self.bits = [False, False, False]
        # keep track of the last time a bit was changed, to see if we need to add a DDS delay
        # assume that a bit was changed immediately before this, to be conservative
        self.last_change = t
    
    def initialize(self, t, new_bits):
        """Sets the state.  Unlike set(), this function sets every bit, regardless of its current state."""
        # set the state in the HSDIO, adding a delay between each bit setting if necessary
        for channel, new_bit in zip(self.channels, new_bits):
            t = self.delay(t)
            HSDIO(t, channel, new_bit)
        # keep track that the bits have all been set
        self.bits = new_bits
        return t
    
    def delay(self, t):
        """Add a DDS delay if it is needed, and update the last_change parameter."""

        if t <= (self.last_change + DDS_profile_delay):
            t += DDS_profile_delay
        # update the last_change parameter
        self.last_change = t
        return t
    
    def set(self, t, new_bits):
        """Sets the state.  Only bits that need to be flipped are flipped.  Grey coding is automatic.
        new_bits: the state we want to set"""

        # go through the bits one at a time
        for channel, old_bit, new_bit in zip(self.channels, self.bits, new_bits):
            # check to see if the bit needs to be changed
            if old_bit != new_bits:
                # delay if we recently changed another bit
                t = self.delay(t)
                HSDIO(t, channel, new_bit)
        # keep track that the bits have all been set
        self.bits = new_bits
        return t
     
    def profile(self, t, profile):
        """Switch to a specific profile by looking up the name in the stored dict."""
        return self.set(t, self.profiles[profile])

### set up the DDS channels to use the DDS class for grey coding ###
# Alias the the profile() method of each of these instances, for convenience.
MOT = DDS(t, (0, 1, 18), {'MOT':(0,0,0), 'PGC in MOT':(1,0,0), 'off':(0,1,0), 'readout':(1,1,0), 'light assisted collisions':(1,0,1), 'off 2':(0,1,1), 'PGC in traps':(1,1,1)}).profile
repump = DDS(t, (2,), {'on':(0,), 'off':(1,)}).profile
SHG780 = DDS(t, (12,), {'on':(1 if all780off else 0,), 'off':(1,)}).profile
Verdi780 = DDS(t, (3,), {'on':(0 if all780off else 1,), 'off':(0,)}).profile
uwave_DDS = DDS(t, (14, 10, 28), {'global':(0,0,0), 'site 1 0 phase':(1,0,0), 'site 2 CNOT phase':(0,1,0), 'global parity phase':(1,1,0), 'site 2 0 phase':(0,0,1), 'site 1 CNOT phase':(1,0,1)}).profile
scanner459_1 = DDS(t, (16, 17), {'off':(0,0), 'site 1':(1,0), 'site 2':(0,1), 'site 3':(1,1)}).profile
scanner459_2 = DDS(t, (19, 20), {'off':(0,0), 'site 1':(1,0), 'site 2':(0,1), 'site 3':(1,1)}).profile
scanner1038_1 = DDS(t, (22,), {'site 1':(0,), 'site 2':(1,)}).profile
scanner1038_2 = DDS(t, (23,), {'site 1':(0,), 'site 2':(1,)}).profile
Rydberg459A = DDS(t, (24, 31), {'off':(0,0), 'site 1':(1,0), 'site 2':(0,1), 'site 3':(1,1)}).profile
Rydberg1038 = DDS(t, (21,29), {'off':(0,0), 'on':(1,0), 'low power':(0,1)}).profile

class switch(object):
    """A single HSDIO channel that controls a switch.  Unlike DDS(), this does not use any grey coding or delays."""
    
    def __init__(self, channel, profiles=None):
        """
        channel: the HSDIO channel that controls this device
        profiles: a dict of profile settings, e.g {'on':1, 'off':2}
        """
        self.channel = channel
        self.profiles = profiles
    
    def profile(self, t, profile):
        """Set the HSDIO channel to the requested state"""
        HSDIO(t, self.channel, self.profiles[profile])
        return t

### set up the switches that do not need grey coding ###
# Alias the the profile() method of each of these instances, for convenience.
MOT2D_shutter = switch(4, {'on':0, 'off':1}).profile
MOT3D_shutter = switch(9, {'on':0, 'off':1}).profile
repump_shutter = switch(25, {'on':0, 'off':1}).profile
OP = switch(26, {'on':1, 'off':0}).profile
OP_repump = switch(30, {'on':1, 'off':0}).profile
uwave_switch = switch(13, {'on':1, 'off':0}).profile
Raman459 = switch(15, {'on':1, 'off':0}).profile
blowaway = switch(11, {'on':1, 'off':0}).profile
slow_noise_eater_trigger2 = switch(27, {'on':1, 'off':0}).profile

### Create a special Hamamatsu class so we can keep track of when the last shot was
class Hamamatsu_class(switch):
    """A special case of switch that also keeps track of when the last shot was."""

    def __init__(self, t):
        super(Hamamatsu_class, self).__init__(5, {'open':1, 'closed':0})
        self.last_shot = t

Hamamatsu = Hamamatsu_class(t)

#### define the component waveforms that can be mixed and matched to make an experiment ###

def set_magnetic_fields(t, profile):
    """Switch to the magnetic fields of choice, defined by the magnetic fields matrix."""

    # Table of magnetic field settings.  Rows are gradient, x25, x36, vert, x14.  Columns are:
    profiles = {'MOT':0, 'PGC in MOT':1, 'readout':2, '685':3, 'optical pumping':4, 'Rydberg':5, 'light assisted collisions':6,
                'gradient only':7, 'x1_4 only':8, 'x2_5 only':9, 'x3_6 only':10, 'vertical only':11, 'off':12}

    # for each AO channel (rows of the magnetic field matrix)
    for channel, fields in enumerate(magnetic_fields):
        # switch to the field defined by the column of the magnetic fields matrix selected by 'profile'
        AO(t, channel, fields[profiles[profile]])

    return t

def DCNE_trigger_1(t):
    """ The once-per-measurement trigger for the DC Noise Eaters.  Goes low for 1 ms."""
    DO(t, 0, 0)
    t += 1
    DO(t, 0, 1)

def MOT_loading(t):
    """Load atoms from the 2D vapor beam"""

    label(t, 'MOT loading')

    # turn on the MOT, repump and traps, everything else is off
    if background:
        t1 = MOT(t, 'off')
        t2 = repump(t, 'off')
        t3 = MOT2D_shutter(t, 'off')
    else:
        t1 = MOT(t, 'MOT')
        t2 = repump(t, 'on')
        t3 = MOT2D_shutter(t, 'on')
    t4 = MOT3D_shutter(t, 'on')
    t5 = SHG780(t, 'on')
    t6 = Verdi780(t, 'on')
    
    t = max(t1, t2, t3, t4, t5, t6)
    

    # turn off the 780 traps

    t1 = SHG780(t + trap_on_time_during_loading, 'off')
    t2 = Verdi780(t + trap_on_time_during_loading, 'off')
    
    # turn off the 2D MOT
    t3 = MOT2D_shutter(t + MOT_2D_time, 'off')
    
    # end sequence
    t4 = t + MOT_loading_time
    
    t = max(t1, t2, t3, t4)
    
    return t

def PGC_in_MOT(t):
    """Polarization gradient cooling in the MOT."""

    label(t, 'PGC in MOT')

    # calculate when the end of the sequence will come
    t1 = t+PGC_1_time

    # switch to PGC phase
    if not background:
        t = MOT(t, 'PGC in MOT')

    # turn on the traps
    t += trap_780_delay_for_PGC_1
    t_after_SHG = SHG780(t, 'on')
    t_after_Verdi = Verdi780(t, 'on')
    t = max(t_after_SHG, t_after_Verdi)
    
    # end sequence
    t = max(t, t1)
    return t

def MOT_drop(t):
    """After single atom traps are on, let the rest of the MOT fall away."""

    label(t, 'MOT drop')

    t1 = MOT(t, 'off')
    t2 = repump(t, 'off')
    t = max(t1,t2)
    
    # let the MOT drop away
    t += MOT_drop_time
    
    return t

def light_assisted_collisions(t):
    """Time to allow light assisted collisions eliminate the occurrence of more than 1 atom per trap."""
    
    label(t, 'pre-readout')

    if not background:
        t1 = MOT(t, 'light assisted collisions')
        t2 = repump(t, 'on')
        t = max(t1, t2)
    
    # wait for light assisted collisions to eliminate twos, threes, etc, from the traps.
    t += Pre_Readout_Time
    
    return t

def PGC_in_traps(t):
    """Polarization gradient cooling in the single atom traps."""

    label(t, 'PGC in traps')

    if not background:
        t1 = MOT(t, 'PGC in traps')
        t2 = repump(t, 'on')
        t = max(t1, t2)

    # wait for atoms to cool
    t += PGC_2_time

    return t

def readout(t):
    """Take a picture."""

    label(t, 'readout')

    MOT(t, 'readout')
    repump(t, 'on')
    Hamamatsu.profile(t, 'open')

    # leave the shutter open for the exposure time
    t += Readout_time
    Hamamatsu.last_camera_shot = t
    Hamamatsu.profile(t, 'closed')

    return t

def close_shutters(t):
    """Close the MOT shutters to prevent state mixing."""

    label(t, 'close shutters')

    # start the shutters closing
    MOT(t, 'off')
    MOT3D_shutter(t, 'off')
    repump(t, 'off')
    repump_shutter(t, 'off')

    # wait until they are fully closed
    t += close_shutter_time

    return t

def open_3D_shutters(t):
    """Open the MOT shutters again so we can take a picture."""

    label(t, 'open shutters')

    # start the shutters opening
    MOT3D_shutter(t, 'on')
    repump_shutter(t, 'on')

    # wait until they are fully open (this could use it's own time, not necessarily the same as the close_shutter_time)
    t += close_shutter_time

    return t

def OP_magnetic_fields(t):
    """Turn on a bias field and wait until the field stabilizes."""

    t = set_magnetic_fields(t, 'optical pumping')

    # wait until the fields are fully switched
    t += PGC_to_bias_B_field_delay

    return t

def optical_pumping(t):
    """Shuffle atoms until they are in the F=4, mF=0 dark state.  The OP beam is 894 nm linearly polarized F=4 to 4'."""

    label(t, 'optical pumping')

    # turn on the OP and OP repumper
    OP(t, 'on')
    OP_repump(t, 'on')

    # turn off the OP and OP repumper
    t += optical_pumping_time
    OP(t, 'off')
    OP_repump(t, 'off')

    return t

def OP_depump(t):
    """Use just the OP beam without repumping.
    Since the F=4, mF=0 state is dark to this, the transference to F=3 can be used to measure how good the previous
    optical pumping was."""

    label(t, 'OP depump')

    # turn on the OP, with no OP repumper
    OP(t, 'on')
    OP_repump(t, 'off')

    # turn off the OP
    t += depumping_894_time
    OP(t, 'off')

    return t

def Rydberg_magnetic_fields(t):
    """Set the magnetic shims to the RYD settings and wait until they stabilize."""

    t = set_magnetic_fields(t, 'Rydberg')

    # wait until the fields are fully switched
    t += ryd_mag_wait

    return t

def no_op(t):
    """Do nothing for zero time."""
    return t

def uwave_global(t, duration):
    """Perform a global X rotation using microwaves.
    duration: the length of the pulse"""

    # switch the microwave DDS profile
    t = uwave_DDS(t, 'global')

    # turn on microwave pulse
    uwave_switch(t, 'on')

    # turn off microwave pulse
    t += duration
    t = uwave_switch(t, 'off')

    return t

def uwave_pi_global(t):
    """Perform a global X gate (X pi rotation"""
    label(t, 'uwave pi global')
    t = uwave_global(t, microwave_pi_pulse)
    return t

def uwave_pi_by_2_global(t):
    """Perform a global X pi/2 rotation."""
    label(t, 'uwave pi/2 global')
    t = uwave(t, microwave_pi_by_2)
    return t

def uwave_wStark_site1_Raman(t, duration):
    """Perform an X rotation on all sites EXCEPT site 1.
    This assumes the microwaves are tuned to resonance, so the 459 'Raman' light will detune the microwaves.
    """

    # switch the microwave DDS profile
    t1 = uwave_DDS(t, 'site 1 0 phase')
    # switch the scanners to site 1
    t2 = scanner459_1(t, 'site 1')
    t3 = scanner459_2(t, 'site 1')
    # wait for scanners to switch
    t2 += Ryd459_scanner1_delay
    t3 += Ryd459_scanner2_delay
    t = max(t1, t2, t3)

    # turn on microwaves and 459 light
    uwave_switch(t, 'on')
    Raman459(t, 'on')

    # turn off pulse
    t += microwave_pi_pulse
    t = uwave_switch(t, 'off')

    # Don't turn 459 scanners to off here.  Save time by only doing it after the last pulse.

    return t

def uwave_wStark_site1_Pi_Raman(t):
    """An X gate on all sites EXCEPT site 1"""
    label(t, 'uwave pi site ~1')
    t = uwave_wStark_site1_Raman(t, microwave_pi_pulse)
    return t

def uwave_wStark_site1_Pi2_Raman(t):
    """An X pi/2 rotation on all sites EXCEPT site 1"""
    label(t, 'uwave pi/2 site ~1')
    t = uwave_wStark_site1_Raman(t, microwave_pi_by_2)
    return t

def uwave_wStark_site2_Raman(t, duration):
    """Perform an X rotation on all sites EXCEPT site 2.
    This assumes the microwaves are tuned to resonance, so the 459 'Raman' light will detune the microwaves.
    duration: defines the length of the pulse
    """

    # switch the microwave DDS profile
    t1 = uwave_DDS(t, 'site 2 0 phase')
    # switch the scanners to site 2
    t2 = scanner459_1(t, 'site 2')
    t3 = scanner459_2(t, 'site 2')
    # wait for scanners to switch
    t2 += Ryd459_scanner1_delay
    t3 += Ryd459_scanner2_delay
    t = max(t1, t2, t3)

    # turn on microwaves and 459 light
    uwave_switch(t, 'on')
    Raman459(t, 'on')

    # turn off pulse
    t += duration
    t = uwave_switch(t, 'off')

    # Don't turn 459 scanners to off here.  Save time by only doing it after the last pulse.

    return t

def uwave_wStark_site2_Pi_Raman(t):
    """X gate on all sites EXCEPT site 2"""
    label(t, 'uwave pi site ~2')
    t = uwave_wStark_site2_Raman(t, microwave_pi_pulse)
    return t

def uwave_wStark_site2_Pi2_Raman(t):
    """X gate on all sites EXCEPT site 2"""
    label(t, 'uwave pi/2 site ~2')
    t = uwave_wStark_site2_Raman(t, microwave_pi_by_2)
    return t

def uwave_wStark_site2_Raman_phase(t, duration):
    """Perform an X rotation on all sites EXCEPT site 2 with a phase offset.
    This assumes the microwaves are tuned to resonance, so the 459 'Raman' light will detune the microwaves.
    duration: defines the length of the pulse
    """

    # switch the microwave DDS profile
    t1 = uwave_DDS(t, 'site 2 CNOT phase')
    # switch the scanners to site 2
    t2 = scanner459_1(t, 'site 2')
    t3 = scanner459_2(t, 'site 2')
    # wait for scanners to switch
    t2 += Ryd459_scanner1_delay
    t3 += Ryd459_scanner2_delay
    t = max(t1, t2, t3)

    # turn on microwaves and 459 light
    uwave_switch(t, 'on')
    Raman459(t, 'on')

    # turn off pulse
    t += duration
    t = uwave_switch(t, 'off')

    # Don't turn 459 scanners to off here.  Save time by only doing it after the last pulse.

    return t

def uwave_wStark_site2_Pi2_Raman_phase(t):
    label(t, 'uwave pi/2 site ~2 phase')
    t = uwave_wStark_site2_Raman_phase(t, microwave_pi_by_2)
    return t

def scanners459_off(t):
    """Turn the 459 scanners off.  This function is used so we don't have to turn the scanners off after the 1st
    microwave pulse in the Cz waveform."""

    # scanners back to off
    t1 = scanner459_1(t, 'off')
    t2 = scanner459_2(t, 'off')
    # wait for scanners to switch
    t1 += Ryd459_scanner1_delay
    t2 += Ryd459_scanner2_delay

    return t

def do_blowaway(t):
    """Remove any atoms in F=4."""

    label(t, 'blowaway')

    # do a blowaway pulse
    t = blowaway(t, 'on')
    t += blow_away_time
    t = blowaway(t, 'off')

    return t

def camera_delay(t):
    """Wait until 31 ms after the previous camera shot."""

    label(t, 'camera delay')

    # If we have already waited 31 ms doing other operations, then just proceed.
    # Otherwise, wait until 31 ms after the last shot

    return max(t, Hamamatsu.last_shot + delay_between_camera_shots)

def slow_noise_eater(t):
    """Turn on the lasers one by one, so we can get a reading of their power."""

    label(t, 'noise eater')

    # turn everything off
    t = max(MOT(t, 'off'),
            repump(t, 'off'),
            Verdi780(t, 'off'),
            SHG780(t, 'off'),
            scanner459_1(t, 'off'),
            scanner459_2(t, 'off'),
            scanner1038_1(t, 'site 1'),
            scanner1038_2(t, 'site 1')
            )

    # each step will be 2 ms
    dt = slow_noise_eater_laser_time
    dt2 = 0.5  # off for 0.5 ms
    dt3 = 0.005  # noise eater trigger delay, to ensure laser has turned on

    # 'Raman' 459
    Raman459(t, 'on')
    slow_noise_eater_trigger2(t+dt3, 'on')
    t += dt
    Raman459(t, 'off')
    slow_noise_eater_trigger2(t, 'off')
    t += dt2

    # Rydberg 459A
    Rydberg459A(t, 'site 1')
    slow_noise_eater_trigger2(t+dt3, 'on')
    t += dt
    Rydberg459A(t, 'off')
    slow_noise_eater_trigger2(t, 'off')
    # turn the 459 scanner off now
    scanner459_1(t, 'off')
    scanner459_2(t, 'off')
    t += dt2

    # Rydberg 1038
    Rydberg1038(t, 'on')
    slow_noise_eater_trigger2(t+dt3, 'on')
    t += dt
    Rydberg1038(t, 'off')
    slow_noise_eater_trigger2(t, 'off')
    t += dt2

    # MOT
    MOT(t,'MOT')
    t += dt
    MOT(t, 'off')
    t += dt2

    # repump
    repump(t, 'on')
    t += dt
    repump(t, 'off')
    t += dt2

    # OP
    OP(t, 'on')
    t += dt
    OP(t, 'off')
    t += dt2

    # OP repump
    OP_repump(t, 'on')
    t += dt
    OP_repump(t, 'off')
    t += dt2

    # blowaway
    blowaway(t, 'on')
    t += dt
    blowaway(t, 'off')
    t += dt2

    # 780 SHG
    SHG780(t, 'on')
    t += dt
    SHG780(t, 'off')
    t += dt2

    # 780 Verdi TiSapph
    Verdi780(t, 'on')
    t += dt
    Verdi780(t, 'off')
    t += dt2

    # return to MOT loading settings
    if not background:
        MOT(t, 'MOT')
        repump(t, 'on')
        MOT2D_shutter(t, 'on')
        MOT3D_shutter(t, 'on')
    SHG780(t, 'on')
    Verdi780(t, 'on')

    return t

def magnetic_field_monitor(t):
    """Turn on each coil one by one, so we can get a reading of their noise from shot to shot."""

    label(t, 'magnetic field monitor')

    #each step will be 3 ms
    dt = slow_noise_eater_magnetic_time

    set_magnetic_fields(t, 'gradient only')
    t += dt
    set_magnetic_fields(t, 'x1_4 only')
    t += dt
    set_magnetic_fields(t, 'x2_5 only')
    t += dt
    set_magnetic_fields(t, 'x3_6 only')
    t += dt
    set_magnetic_fields(t, 'vertical only')
    t += dt
    set_magnetic_fields(t, 'off')
    t += dt

    return t

def trap_drop(t):
    """Turn off the 780 nm traps for a short period of time.  Usually to check atom temperature."""

    label(t, 'trap drop')

    # traps off
    SHG780(t, 'off')
    Verdi780(t, 'off')

    # wait a short time with the traps off
    t += trap_release_time

    # turn the traps back on
    SHG780(t, 'on')
    Verdi780(t, 'on')

    return t

def open_2D_shutter(t):
    """Reopen the 2D MOT shutter."""

    label(t, 'open 2D shutter')

    # turn on the MOT, repump and traps, everything else is off
    if background:
        MOT2D_shutter(t, 'off')
    else:
        MOT2D_shutter(t, 'on')

    return t


def idle(t):
    """Turn on the MOT to start the loading, and turn on the 780 to stabilize the temperature between measurements.
    These settings will persist until the next measurement starts."""

    label(t, 'idle')

    # turn on the MOT, repump and traps, everything else is off
    if background:
        MOT(t, 'off')
        repump(t, 'off')
        MOT2D_shutter(t, 'off')
    else:
        MOT(t, 'MOT')
        repump(t, 'on')
        MOT2D_shutter(t, 'on')
    MOT3D_shutter(t, 'on')
    SHG780(t, 'on')
    Verdi780(t, 'on')
    
    # if you want to turn a specific channel on or off during idle, just do this here:
    #HSDIO(t, 3, 1)  # e.g. turn on channel 3

    return t

def before_experiment(t):
    """All the steps to get atoms initialized for an experiment."""
    DCNE_trigger_1(t)
    t = set_magnetic_fields(t, 'MOT')
    t = MOT_loading(t)
    t = set_magnetic_fields(t, 'PGC in MOT')
    t = PGC_in_MOT(t)
    t = set_magnetic_fields(t, 'light assisted collisions')
    t = MOT_drop(t)
    t = light_assisted_collisions(t)
    t = set_magnetic_fields(t, 'readout')
    t = PGC_in_traps(t)
    t = readout(t)
    t = PGC_in_traps(t)
    t = close_shutters(t)
    t = OP_magnetic_fields(t)
    t = optical_pumping(t)
    HSDIO(t,34,1)  # oscilloscope trigger on
    return t

def after_experiment(t):
    """All the steps to readout after an experiment.
    Note: Does not include blowaway."""

    HSDIO(t,34,0)  # oscilloscope trigger off
    t = set_magnetic_fields(t, 'readout')
    t = open_3D_shutters(t)
    t = camera_delay(t)
    t = readout(t)
    t = PGC_in_traps(t)
    t = set_magnetic_fields(t, 'MOT')
    t = open_2D_shutter(t)
    t = slow_noise_eater(t)
    #t = magnetic_field_monitor(t)
    #t = set_magnetic_fields(t, 'MOT')
    t = idle(t)
    return t

def Rydberg_pulse(t, time459, time1038, site):
    """Do a Rydberg pulse on one site.  This waveform is used inside the Rydberg and Cz waveforms.
    It is used do eliminate repetition, but it is not sufficient on its own because it does not switch the scanners
    or traps.
    time459: how long the 459 light is on (not including delays)
    time1038 how long the 1038 light is on (not including delays)
    site: a string directing the 459 switch DDS to the correct profile (e.g. 'site 1', 'site 2', etc.)"""

    # Rydberg light on
    Rydberg459A(t-Ryd459A_on_delay, site)
    Rydberg1038(t-Ryd1038_on_delay, 'on')
    # Rydberg light off
    Rydberg459A(t+time459+Ryd459A_off_delay, 'off')
    Rydberg1038(t+time1038+Ryd1038_off_delay, 'off')
    # set the time to after 459 and 1038 have both ended
    t += max(rydberg_A_459_time_control, rydberg_A_1038_time_control)
    return t

def Rydberg(t, site):
    """Do a Rydberg pulse on a single site.  Choose the site by passing in a string 'site' (e.g. 'site 1', 'site 2',
    etc.) that will select the appropriate DDS profile."""

    # scanners to correct site
    scanner459_1(t, site)
    scanner459_2(t, site)
    scanner1038_1(t, site)
    scanner1038_2(t, site)

    # timing relative to the start of the pulse
    # calculate which of these delays is the longest, so we wait as little time as possible before excitation
    t += max(Ryd1038_on_delay, Ryd1038_scanner1_delay, Ryd1038_scanner2_delay,
             Ryd459A_on_delay, Ryd459_scanner1_delay, Ryd459_scanner2_delay,
             trap780top_off_delay, trap780bottom_off_delay)

    # scope trigger on (it's okay if this happens before the beginning of this waveform)
    HSDIO(t-HSDIO2_delay, 34, 1)
    # 780 traps off
    SHG780(t-trap780top_off_delay, 'off')
    Verdi780(t-trap780bottom_off_delay, 'off')

    ### pi pulse ###
    t = Rydberg_pulse(t, rydberg_A_459_time_control, rydberg_A_1038_time_control, site)

    # scope trigger off
    HSDIO(t-HSDIO2_delay, 34, 0)

    # 780 traps on
    SHG780(t+trap780top_on_delay, 'on')
    Verdi780(t+trap780bottom_on_delay, 'on')

    # wait until the traps are really back on
    t += delay_after_excitation_pulse

    # scanners off
    t1 = scanner459_1(t, 'off')
    t2 = scanner459_2(t, 'off')
    # wait for DDS delay if necessary
    t = max(t1, t2)

    return t

def Cz(t, control, target):
    """Perform a Cz gate between two sites.
    This is a pi Rydberg pulse on the control site, a 2*pi Rydberg pulse on the target site, and a pi Rydberg pulse on
    the control site again.
    'control' and 'target' parameters are strings that direct the DDS profiles to the correct sites
    (e.g. 'site 1', 'site 2')."""

    # replaces a 19 x 22 table (418 elements) with

    # scanners to control site
    scanner459_1(t, control)
    scanner459_2(t, control)
    scanner1038_1(t, control)
    scanner1038_2(t, control)

    # timing relative to the start of the pulse
    # calculate which of these delays is the longest, so we wait as little time as possible before excitation
    t += max(Ryd1038_on_delay, Ryd1038_scanner1_delay, Ryd1038_scanner2_delay,
             Ryd459A_on_delay, Ryd459_scanner1_delay, Ryd459_scanner2_delay,
             trap780top_off_delay, trap780bottom_off_delay)

    # scope trigger (it's okay if this happens before the beginning of this waveform)
    HSDIO(t-HSDIO2_delay, 34, 1)
    # 780 traps off
    SHG780(t-trap780top_off_delay, 'off')
    Verdi780(t-trap780bottom_off_delay, 'off')

    ### pi pulse on control site ###
    t = Rydberg_pulse(t, rydberg_A_459_time_control, rydberg_A_1038_time_control, control)

    # scope trigger off
    HSDIO(t-HSDIO2_delay, 34, 0)
    # wait until both 459 and 1038 are really off
    t += delay_before_switching

    # scanners to target site
    scanner459_1(t, target)
    scanner459_2(t, target)
    scanner1038_1(t, target)
    scanner1038_2(t, target)

    # time it takes to fully switch sites
    switching_delay = max(Ryd1038_on_delay, Ryd1038_scanner1_delay, Ryd1038_scanner2_delay,
                          Ryd459A_on_delay, Ryd459_scanner1_delay, Ryd459_scanner2_delay,
                          ) if doGates else 5
    t += switching_delay

    ### 2*pi pulse on target site ###
    t = Rydberg_pulse(t, rydberg_A_459_time_target, rydberg_A_1038_time_target, target)

    # wait until both 459 and 1038 are both really off
    t += delay_before_switching

    # scanners to control site
    scanner459_1(t, control)
    scanner459_2(t, control)
    scanner1038_1(t, control)
    scanner1038_2(t, control)

    t += switching_delay

    ### pi pulse on control site ###
    t = Rydberg_pulse(t, rydberg_A_459_time_control, rydberg_A_1038_time_control, control)

    # 780 traps on
    SHG780(t+trap780top_on_delay, 'on')
    Verdi780(t+trap780bottom_on_delay, 'on')

    # wait until the traps are really back on
    t += delay_after_excitation_pulse

    # scanners off
    t1 = scanner459_1(t, 'off')
    t2 = scanner459_2(t, 'off')
    # wait for DDS delay if necessary
    t = max(t1, t2)

    return t

### different experiments ###

def state_F3(t):
    """Do state prep into F=3.  A high signal is expected."""
    t = Rydberg_magnetic_fields(t)
    t = uwave_pi_global(t)
    t = set_magnetic_fields(t, 'readout')
    t = do_blowaway(t)
    return t

def state_F4(t):
    """Do state prep into F=4.  A low signal is expected."""
    t = set_magnetic_fields(t, 'readout')
    t = do_blowaway(t)
    return t

def optimize_traps(t):
    """Use a trap drop, but no blowaway, so we can optimize the trap loading and retention."""
    t = Rydberg_magnetic_fields(t)
    t = uwave_pi_global(t)
    t = set_magnetic_fields(t, 'readout')
    t = do_blowaway(t)
    return t

def state_prep(t):
    """Prepare different state |11>, |10>, |01>, and |00> depending on the value of state_det, which should be stepped
    in the independent variables."""

    # Switch to Rydberg fields, unless we're just going to do a no_op.
    if state_det != 0:
        t = Rydberg_magnetic_fields(t)
    # Perform the appropriate microwave pulse
    t = [no_op, uwave_wStark_site2_Pi_Raman, uwave_wStark_site1_Pi_Raman, uwave_pi_global][state_det](t)
    # blowaway
    t = set_magnetic_fields(t, 'readout')
    t = do_blowaway(t)
    return t

def CNOT(t):
    # prepare one of four states |11>, |01>, |10>, |00>
    t = [no_op, uwave_wStark_site2_Pi_Raman, uwave_wStark_site1_Pi_Raman, uwave_pi_global][input_state](t)
    t = uwave_wStark_site2_Pi2_Raman(t)
    t = Cz(t, 'site 1', 'site 2')
    t = uwave_wStark_site2_Pi2_Raman_phase(t)
    # readout one of four states |00>, |10>, |01>, |11> as a high-high signal
    t = [no_op, uwave_wStark_site2_Pi_Raman, uwave_wStark_site1_Pi_Raman, uwave_pi_global][state_det](t)
    t = scanners459_off(t)
    # blowaway
    t = set_magnetic_fields(t, 'readout')
    t = do_blowaway(t)
    return t

def Ground459(t):
    """Perform a 459 Ramsey experiment by doing a 459 pulse sandwiched by two microwave pi/2 pulses."""
    t = Rydberg_magnetic_fields(t)
    t = uwave_pi_by_2_global(t)
    t = Rydberg(t, 'site 1')
    t = Rydberg(t, 'site 2')
    t = uwave_pi_by_2_global(t)
    t = scanners459_off(t)
    # blowaway
    t = set_magnetic_fields(t, 'readout')
    t = do_blowaway(t)
    return t

def OP_optimize(t):
    t = OP_depump(t)
    t = set_magnetic_fields(t, 'readout')
    t = do_blowaway(t)
    return(t)

def optimize_0_1(t):
    """Switch between doing a pi pulse and no pi pulse, so you can optimize the high-low signal.  Includes an OP depumping and trap drop."""
    t = OP_depump(t)
    t = Rydberg_magnetic_fields(t)
    if state==3:
        t = uwave_pi_global(t)
    t = trap_drop(t)
    t = set_magnetic_fields(t, 'readout')
    t = do_blowaway(t)
    return(t)

### The above are all just definitions.  Specify the waveforms to actually run below. ###

t = before_experiment(t)
t = optimize_0_1(t)
t = after_experiment(t)
