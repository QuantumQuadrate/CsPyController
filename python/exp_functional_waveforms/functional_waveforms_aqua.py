"""These are the waveform functions for the AQuA project.
They define the operation of the HSDIO, AO and DAQmxDO outputs.
Use the functions HSDIO(time, channel, state), DO(time, channel, state), AO(time, channel, voltage) and label(time, text).
The user should ensure that all waveform functions take in the start time as the first parameter,
and return the end time.
"""

HSDIO = experiment.LabView.HSDIO.add_transition
AO = experiment.LabView.AnalogOutput.add_transition
DO = experiment.LabView.DAQmxDO.add_transition
label = experiment.functional_waveforms_graph.label

class DDS(object):
    """This class represents a single DDS channel controlled by one or more HSDIO channels.
    This class does NOT communicate directly with the DDS box, that is taken care of in the DDS.py file.
    This class only manipulates the HSDIO channels which switch the current HSDIO profile.
    It takes care of grey coding the profile changes.
    This class only works properly if all calls to a particular instance are done sequentially, but that is the expected situation for a single DDS channel.
    In other words, the sequencing for a DDS() object must be done monotonically."""
    
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
            if old_bit != new_bit:
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
MOT = DDS(0, (32, 33, 34), {'MOT':(0,0,0), 'PGC in MOT':(1,0,0), 'off':(0,1,0), 'monitor':(0,0,1), 'readout':(1,1,0), 'light assisted collisions':(1,0,1), 'Blowaway':(0,1,1), 'PGC in traps':(1,1,1)}).profile
repump = DDS(0, (35,), {'on':(0,), 'off':(1,)}).profile
SHG780 = DDS(0, (0,), {'on':(1 if all780off else 0,), 'off':(1,)}).profile
#old setting; Verdi780 is used to control the rf switch of the Verdi 780 line AOM
#Verdi780 = DDS(0, (1,), {'on':(0 if all780off else 1,), 'off':(0,)}).profile
#new tentative setting; Verdi780 is applied to control the dds profile of Sprout 780 line
Verdi780 = DDS(0, (1,), {'on':(1 if all780off else 0,), 'off':(1,)}).profile
# two DDS channels are controlled by the same pins for uwave DDS, so we double up on the profiles here:
uwave_DDS = DDS(0, (4, 5, 6), {'global':(0,0,0), 'control site, with phase':(1,0,0), 'target site, CNOT phase':(0,1,0), 'global, parity phase':(1,1,0), 'target site, with phase':(0,0,1), 'control site, CNOT phase':(1,0,1),'global phase':(0,1,1),
                                                      'a':(1,0,0), 'b':(0,1,0), 'c':(1,1,0), 'd':(0,0,1), 'e':(1,0,1), 'f':(0,1,1), 'g':(1,1,1)}).profile
scanner459_1 = DDS(0, (12,13,14), {'off':(0,0,0), 'a':(1,0,0), 'b':(0,1,0), 'c':(1,1,0), 'd':(0,0,1), 'e':(1,0,1), 'f':(0,1,1), 'g':(1,1,1)}).profile
scanner459_2 = DDS(0, (15,16,17), {'off':(0,0,0), 'a':(1,0,0), 'b':(0,1,0), 'c':(1,1,0), 'd':(0,0,1), 'e':(1,0,1), 'f':(0,1,1), 'g':(1,1,1)}).profile
scanner1038_1 = DDS(0, (20,21,22), {'off':(0,0,0), 'a':(1,0,0), 'b':(0,1,0), 'c':(1,1,0), 'd':(0,0,1), 'e':(1,0,1), 'f':(0,1,1), 'g':(1,1,1)}).profile
scanner1038_2 = DDS(0, (23,24,25), {'off':(0,0,0), 'a':(1,0,0), 'b':(0,1,0), 'c':(1,1,0), 'd':(0,0,1), 'e':(1,0,1), 'f':(0,1,1), 'g':(1,1,1)}).profile
Rydberg459A = DDS(0, (10,11,28), {'off':(0,0,0), 'a':(1,0,0), 'b':(0,1,0), 'c':(1,1,0), 'd':(0,0,1), 'e':(1,0,1), 'f':(0,1,1), 'g':(1,1,1)}).profile
#Rydberg1038 = DDS(0, (18,19), {'off':(0,0), 'on':(1,0), 'low power':(0,1)}).profile
MOT_intermediary_a = DDS(0, (46,47,48), {'MOT':(0,0,0), 'PGC in MOT':(1,0,0), 'off':(0,1,0), 'monitor':(0,0,1), 'readout':(1,1,0), 'light assisted collisions':(1,0,1), 'Blowaway':(0,1,1), 'PGC in traps':(1,1,1)}).profile
MOT_intermediary_b = DDS(0, (49,50,51), {'MOT':(0,0,0), 'PGC in MOT':(1,0,0), 'off':(0,1,0), 'monitor':(0,0,1), 'readout':(1,1,0), 'light assisted collisions':(1,0,1), 'Blowaway':(0,1,1), 'PGC in traps':(1,1,1)}).profile

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
MOT2D_shutter = switch(36, {'on':0, 'off':1}).profile
MOT3D_shutter = switch(37, {'on':0, 'off':1}).profile  # MOT3D_shutter = switch(37, {'on':0, 'off':1}).profile
repump_shutter = switch(38, {'on':0, 'off':1}).profile
blowaway_shutter = switch(52, {'on':0, 'off':1}).profile #switch(49, {'on':0, 'off':1}).profile; temporarily disabled.
OP = switch(40, {'on':1, 'off':0}).profile
OP_repump = switch(41, {'on':1, 'off':0}).profile
uwave_select = switch(3, {'DDS ch.3':1, 'DDS ch.4':0}).profile
uwave_switch = switch(8, {'on':1, 'off':0}).profile
Raman459 = switch(9, {'on':1, 'off':0}).profile
blowaway = switch(42, {'on':1, 'off':0}).profile
slow_noise_eater_trigger1 = switch(43, {'on':0, 'off':1}).profile
slow_noise_eater_trigger2 = switch(44, {'on':1, 'off':0}).profile
oscilloscope_trigger_Rydberg = switch(26, {'on':1, 'off':0}).profile
PointGrey_Trigger = switch(45, {'on':0, 'off':1}).profile

# direct switching functionality of the DDS controls when necessary
#Rydberg459A_bit0 = switch(10, {'on':1, 'off':0}).profile
#Rydberg459A_bit1 = switch(11, {'on':1, 'off':0}).profile
#Rydberg459A_bit2 = switch(28, {'on':1, 'off':0}).profile
Rydberg1038_bit0 = switch(18, {'on':1, 'off':0}).profile  #'on':1, 'off':0
Rydberg1038_bit1 = switch(19, {'on':1, 'off':0}).profile  #'on':1, 'off':0

### Create a special Hamamatsu class so we can keep track of when the last shot was
class Hamamatsu_class(switch):
    """A special case of switch that also keeps track of when the last shot was."""

    def __init__(self, t, channel):
        super(Hamamatsu_class, self).__init__(channel, {'open':1, 'closed':0})
        self.last_shot = t

Hamamatsu = Hamamatsu_class(0, 39)

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

    #AO(t, 5, 2)  # for AO testing purpose, set AO channel 5 to a static output.

    return t

def DCNE_trigger_1(t):
    """ The once-per-measurement trigger for the DC Noise Eaters.  Goes low for 1 ms.
    This is an active low trigger.  Trigger 2 (HSDIO ch 27) is active high."""
    slow_noise_eater_trigger1(t, 'on')
    t += 1
    slow_noise_eater_trigger1(t, 'off')

def PTGrey_trigger(t):
    """ The once-per-measurement trigger for the DC Noise Eaters.  Goes low for 1 ms.
    This is an active low trigger.  Trigger 2 (HSDIO ch 45) is active high."""
    PointGrey_Trigger(t, 'on')
    t +=1
    PointGrey_Trigger(t, 'off')
    


def MOT_loading(t):
    """Load atoms from the 2D vapor beam"""

    label(t, 'MOT loading')

    # turn on the MOT, repump and traps, everything else is off
    if background:
        t1_0 = MOT(t, 'off')
        t1_a = MOT_intermediary_a(t, 'off')
        t1_b = MOT_intermediary_b(t, 'off')
        t2 = repump(t, 'off')
        t3 = MOT2D_shutter(t, 'off')
    else:
        t1_0 = MOT(t, 'MOT')
        t1_a = MOT_intermediary_a(t, 'MOT')
        t1_b = MOT_intermediary_b(t, 'MOT')
        t2 = repump(t, 'on')
        t3 = MOT2D_shutter(t, 'on')
    t4 = MOT3D_shutter(t, 'on')
    t5 = SHG780(t, 'on')
    t6 = Verdi780(t, 'on')
    #t5 = SHG780(t, 'off')
    #t6 = Verdi780(t, 'off')
    
    
    t = max(t1_0, t1_a, t1_b, t2, t3, t4, t5, t6)
    

    # turn off the 780 traps

    t1 = SHG780(t + trap_on_time_during_loading, 'off')
    t2 = Verdi780(t + trap_on_time_during_loading, 'off')
    
    # turn off the 2D MOT
    t3 = MOT2D_shutter(t + MOT_2D_time, 'off')
    
    # end sequence
    t4 = t + MOT_loading_time
    
    t = max(t1, t2, t3, t4)
    
    return t
    
def MOT_loading_with_compressing(t, compress_time = MOT_compress_time):
    """Load atoms from the 2D vapor beam into the 3D MOT, with MOT concentration
     at last."""

    label(t, 'MOT loading')

    # turn on the MOT, repump and traps, everything else is off
    if background:
        t1_0 = MOT(t, 'off')
        t1_a = MOT_intermediary_a(t, 'off')
        t1_b = MOT_intermediary_b(t, 'off')
        t2 = repump(t, 'off')
        t3 = MOT2D_shutter(t, 'off')
    else:
        t1_0 = MOT(t, 'MOT')
        t1_a = MOT_intermediary_a(t, 'MOT')
        t1_b = MOT_intermediary_b(t, 'MOT')
        t2 = repump(t, 'on')
        t3 = MOT2D_shutter(t, 'on')
    t4 = MOT3D_shutter(t, 'on')
    t5 = SHG780(t, 'on')
    t6 = Verdi780(t, 'on')
    
    t = max(t1_0, t1_a, t1_b, t2, t3, t4, t5, t6)
    

    # turn off the 780 traps

    t1 = SHG780(t + trap_on_time_during_loading, 'off')
    t2 = Verdi780(t + trap_on_time_during_loading, 'off')
    
    # turn off the 2D MOT
    t3 = MOT2D_shutter(t + MOT_2D_time, 'off')
    


    # take into consideration the MOT compressing time
    if compress_time < MOT_loading_time:
        t4_a = t + MOT_loading_time - compress_time
        t4_b = t + MOT_loading_time - compress_time
        t4_c = t + MOT_loading_time - compress_time
        t4_d = t + MOT_loading_time - compress_time
    else:
        t4_a = t
        t4_b = t
        t4_c = t
        t4_d = t
        
    label(t4_a, 'MOT compressing')
    print t4_a
    
    gradient_current_value = magnetic_fields[0,0] 
    shim25_current_value = magnetic_fields[1, 0]
    shim36_current_value = magnetic_fields[2, 0]
    shimV_current_value = magnetic_fields[3, 0] 
    print shim25_current_value

    for step in range(20): 
        # work on the AO channel for gradient coils to adiabatically compress the MOT to achieve concentration, with 10 steps.
        # channel 0 is the channel for the gradient coil.
        field_strength_grad = gradient_current_value+step*grad_compress_value/19
        field_strength_25 = shim25_current_value+step*shim25_compress_value/19
        field_strength_36 = shim36_current_value+step*shim36_compress_value/19
        field_strength_V = shimV_current_value+step*shimV_compress_value/19
        AO(t4_a, 0, field_strength_grad)    
        AO(t4_a, 1, field_strength_25)    
        AO(t4_a, 2, field_strength_36)    
        AO(t4_a, 3, field_strength_V)    
        #wait until the AO switching is finished(>0.05 ms, since AO is driven at max 20kilo clock frequency)
        t4_a += compress_time/20
        #for debugging process
        #print field_strength
    
    # end sequence
    t4_e = t + MOT_loading_time
    
    t = max(t1, t2, t3, t4_e)
    
    return t

def PGC_in_MOT(t):
    """Polarization gradient cooling in the MOT."""

    label(t, 'PGC in MOT')

    # calculate when the end of the sequence will come
    t1 = t+PGC_1_time

    # switch to PGC phase
    if not background:
        t_0 = MOT(t, 'PGC in MOT')
        t_a = MOT_intermediary_a(t, 'PGC in MOT')
        t_b = MOT_intermediary_b(t, 'PGC in MOT')
        
        t = max(t_0, t_a, t_b)
        
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

    t1 = MOT(t, 'off')  # only need to turn off the main switching AO of MOT cooling light
    t2 = repump(t, 'off')
    t = max(t1,t2)
    
    # let the MOT drop away
    t += MOT_drop_time
    
    return t

def light_assisted_collisions(t):
    """Time to allow light assisted collisions eliminate the occurrence of more than 1 atom per trap."""
    
    label(t, 'pre-readout')

    if not background:
        t1_0 = MOT(t, 'light assisted collisions')
        t1_a = MOT_intermediary_a(t, 'light assisted collisions')
        t1_b = MOT_intermediary_b(t, 'light assisted collisions')
        t2 = repump(t, 'on')
        t = max(t1_0, t1_a, t1_b, t2)
    
    # wait for light assisted collisions to eliminate twos, threes, etc, from the traps.
    t += Pre_Readout_Time
    
    return t

def PGC_in_traps(t):
    """Polarization gradient cooling in the single atom traps."""

    label(t, 'PGC in traps')

    if not background:
        t1_0 = MOT(t, 'PGC in traps')
        t1_a = MOT_intermediary_a(t, 'PGC in traps')
        t1_b = MOT_intermediary_b(t, 'PGC in traps')
        t2 = repump(t, 'on')
        t = max(t1_0, t1_a, t1_b, t2)

    # wait for atoms to cool
    t += PGC_2_time

    return t

def readout(t, MOT_light_on = True, repump_light_on = True, camera_shutter_open = True):
    """Take a picture."""

    label(t, 'readout')
    
    if MOT_light_on:
        MOT(t, 'readout')
        MOT_intermediary_a(t, 'readout')
        MOT_intermediary_b(t, 'readout')
    else:
        MOT(t, 'off')
        MOT_intermediary_a(t, 'off')
        MOT_intermediary_b(t, 'off')
    if repump_light_on:
        repump(t, 'on')
    else:
        repump(t, 'off')
    # comment out for real experiment
    #repump(t, 'off')
    if camera_shutter_open:
        Hamamatsu.profile(t, 'open')
    
    # leave the shutter open for the exposure time
    t += Readout_time
    Hamamatsu.last_camera_shot = t
    Hamamatsu.profile(t, 'closed')

    # turn off the readout light
    t1_0 = MOT(t, 'off')
    t1_a = MOT_intermediary_a(t, 'off')
    t1_b = MOT_intermediary_b(t, 'off')
    t2 = repump(t, 'off')
    t = max(t1_0, t1_a, t1_b, t2)
   
    return t

def close_shutters(t):
    """Close the MOT shutters to prevent state mixing."""

    label(t, 'close shutters')

    # start the shutters closing
    MOT(t, 'off')
    MOT3D_shutter(t, 'off')
    repump(t, 'off')
    repump_shutter(t, 'off')
    
    # open shutter for blow away light
    blowaway_shutter(t, 'on')

    # wait until they are fully closed
    t += close_shutter_time

    return t

def open_3D_shutters(t):
    """Open the MOT shutters again so we can take a picture."""

    label(t, 'open shutters')

    # start the shutters opening
    MOT3D_shutter(t, 'on')
    repump_shutter(t, 'on')

    # close shutter for blow away light
    blowaway_shutter(t, 'off')
    
    # wait until they are fully open (this could use it's own time, not necessarily the same as the close_shutter_time)
    t += close_shutter_time

    return t

def OP_magnetic_fields(t):
    """Turn on a bias field and wait until the field stabilizes."""
    
    #turn on the op repumper light
    OP_repump(t, 'on')

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
    
    # old method of turning off
    t1 = OP(t, 'off')
    t2 = OP_repump(t, 'off')
    t = max(t1,t2)

    # new method of turning off
    #t = OP(t, 'off')
    #t = OP_repump(t, 'off')

    return t

def OP_depump(t):
    """Use just the OP beam without repumping.
    Since the F=4, mF=0 state is dark to this, the transference to F=3 can be used to measure how good the previous
    optical pumping was."""

    label(t, 'OP depump')

    # turn on the OP, with no OP repumper
    OP_repump(t, 'off')
    OP(t, 'on')

    # turn off the OP
    t += depumping_894_time
    t = OP(t, 'off')

    return t

def Rydberg_magnetic_fields(t, Ramping=False):
    """Set the magnetic shims to the RYD settings and wait until they stabilize.
        Ramping is the switch to turn on/off the adiabatic magnetic field change functionality.
        Currently, because the AO is set at 20kHz and the Rydberg magnetic waiting time is set at 0.52ms, a safe choice of the ramping steps is 10,
        which means we have effectively introduced Rydberg magnetic waiting time.
    """
    # Table of magnetic field settings (an identical translation of what's defined in the dependent variables).  Rows are gradient, x25, x36, vert, x14.  Columns are:
    profiles = {'MOT':0, 'PGC in MOT':1, 'readout':2, '685':3, 'optical pumping':4, 'Rydberg':5, 'light assisted collisions':6,
                'gradient only':7, 'x1_4 only':8, 'x2_5 only':9, 'x3_6 only':10, 'vertical only':11, 'off':12}
    
    label(t, 'Rydberg Magnetic Fields')
    print t
   
    if Ramping:
        # display info message
        print 'Magnetic field switching: adiabatic type'
        #go through all the ramping steps
        for step in range(10): 
                #go through each AO channel           
                # for each AO channel (rows of the magnetic field matrix)
                for channel, fields in enumerate(magnetic_fields):
                    # switch to the field defined by the column of the magnetic fields matrix selected by 'profile'
                    # ramping from optical pumping magnetic field setting to the Rydberg magnetic field setting
                    AO(t, channel,((9-step)*fields[profiles['optical pumping']] + step*fields[profiles['Rydberg']])/9)    
                #wait until the AO switching is finished(0.05 ms, since AO is driven at max 20kilo clock frequency)
                t += 0.05
                #for debugging process
                #print ((9-step)*fields[profiles['optical pumping']] + step*fields[profiles['Rydberg']])/9
        t += 0.25  # wait a little more until the AO finally settles.
    else:
        # display info message
        print 'Magnetic field switching: jump type'
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

def uwave_global_phase(t, duration):
    """Perform a global X rotation using microwaves.
    duration: the length of the pulse
   the phase is controller by the parameter 'parity_phase' for now. """

    # switch the microwave DDS profile, the choice is typically 'global, parity phase';  'control site, CNOT phase' is used for testing purpose.
    t = uwave_DDS(t, 'global, parity phase')
    #t = uwave_DDS(t, 'control site, CNOT phase')

    #wait for uwave DDS to switch
    t += 0.0001
    
    # turn on microwave pulse
    t = uwave_switch(t, 'on')

    # turn off microwave pulse
    t += duration
    t = uwave_switch(t, 'off')

    return t

def uwave_pi_global(t):
    """Perform a global X gate (X pi rotation)"""
    label(t, 'uwave pi global')
    t = uwave_global(t, uwave_pi_time_global)
    return t
    
def uwave_pi_global_phase(t):
    """Perform a global X gate (X pi rotation)"""
    label(t, 'uwave pi global')
    t = uwave_global_phase(t, uwave_pi_time_global)
    return t

def uwave_pi_by_2_global(t):
    """Perform a global X pi/2 rotation."""
    label(t, 'uwave pi/2 global')
    t = uwave_global(t, uwave_pi2_time_global)
    return t

def uwave_pi_by_2_global_phase(t):
    """Perform a global X pi/2 rotation."""
    label(t, 'uwave pi/2 global phase')
    t = uwave_global_phase(t, uwave_pi2_time_global)
    return t

def uwave_global_control_phase(t, duration):
    """Perform a global X rotation using microwaves.
    duration: the length of the pulse
   the phase is controller by the parameter 'det_control_phase' for now. """

    # switch the microwave DDS profile, the choice is typically 'control site, with phase'.
    t = uwave_DDS(t, 'control site, with phase')
    #wait for uwave DDS to switch
    t += 0.0001
    # turn on microwave pulse
    t = uwave_switch(t, 'on')
    # turn off microwave pulse
    t += duration
    t = uwave_switch(t, 'off')
    return t

def uwave_pi2_global_control_phase(t):
    """Perform a global X gate (X pi rotation)"""
    label(t, 'uwave pi global control phase')
    t = uwave_global_control_phase(t, uwave_pi2_time_global)
    return t
    

def uwave_global_control_CNOT_phase(t, duration):
    """Perform a global X rotation using microwaves.
    duration: the length of the pulse
   the phase is controller by the parameter 'det_target_phase' for now. """

    # switch the microwave DDS profile, the choice is typically 'target site, with phase'.
    t = uwave_DDS(t, 'control site, CNOT phase')
    #wait for uwave DDS to switch
    t += 0.0001
    # turn on microwave pulse
    t = uwave_switch(t, 'on')
    # turn off microwave pulse
    t += duration
    t = uwave_switch(t, 'off')
    return t

def uwave_pi2_global_control_CNOT_phase(t):
    """Perform a global X gate (X pi rotation)"""
    label(t, 'uwave pi/2 global target phase')
    t = uwave_global_control_CNOT_phase(t, uwave_pi2_time_global)
    return t


def uwave_clifford_global(t, index):
    """Perform a global clifford gate with index."""
    #index is defined as in the supplemental material of PRL 114.100503 with zero index
    gate_time = clifford_times[index]
    if gate_time[2]>0:
        t = uwave_global(t, gate_time[2]*uwave_pi2_time_global)
    if gate_time[1]>0:
        t =  uwave_global_phase(t, gate_time[1]*uwave_pi2_time_global)
        t += 0.0001
    if gate_time[0]>0:
        t = uwave_global(t, gate_time[0]*uwave_pi2_time_global)
    return t

def divert_459_scanners(t, site='e'):
    """ direct the 459 scanners to designated position.
    The purpose of this waveform is to divert the 459 scanners outside the area of interest when no 459 Ryd A laser or 459 ac Stark shift laser is in need.
    Therefore, the issue of stray 459 light can be safely dealt with.
    """
    #switch 459 scanners to site
    t2 = scanner459_1(t, site)
    t3 = scanner459_2(t, site)
    #wait for the 459 scanners to complete switching behavior
    t2 += Ryd459_scanner1_delay
    t3 += Ryd459_scanner2_delay
    t = max(t2, t3)    
    
    return t

def mute_459_scanners(t):
    """ mute the 459 scanners to avoid stray 459 Raman light, by setting the corresponding DDS profiles to 'off'; only supposed to apply within a few tens of ms.
    The purpose of this waveform is to kick the 459 scanners outside the area of interest when no 459 Ryd A laser or 459 ac Stark shift laser is in need.
    Therefore, the issue of stray 459 light can be safely dealt with.
    """
    #switch 459 scanners to 'off'
    t2 = scanner459_1(t, 'off')
    t3 = scanner459_2(t, 'off')
    #wait for the 459 scanners to complete switching behavior
    t2 += Ryd459_scanner1_delay
    t3 += Ryd459_scanner2_delay
    t = max(t2, t3)    
    
    return t
    
def uwave_wStark_empty(t, site, duration, do_uwave=True):
    """ a 'shift in' type uwave operation on the specified site for a uwave pulse time of duration
    site: the DDS profile to use, i.e. 'a', 'b', or 'c'
    duration: the length of the pulse
    """

    #select channel3 before everything
    uwave_select(t, 'DDS ch.3')
    
    #switch to the designated microwave DDS profile
    t1 = uwave_DDS(t, site)
    #switch 459 scanners to site
    t2 = scanner459_1(t, site)
    t3 = scanner459_2(t, site)
    #wait for the 459 scanners to complete switching behavior
    t2 += Ryd459_scanner1_delay
    t3 += Ryd459_scanner2_delay
    t = max(t1, t2, t3)
    
    #turn on 459 Raman laser and wait for an interval until the AOM is fully on.
    Raman459(t, 'off')
    t += Ryd459A_on_delay
    
    #turn on microwaves
    if do_uwave is True:
        uwave_switch(t, 'on')

    #pulse interaction
    t += duration

    #turn off pulse nicely    
    t = uwave_switch(t, 'off')
    t = Raman459(t, 'off')
    uwave_select(t, 'DDS ch.4')
    t+=Ryd459A_off_delay

    return t
    
def uwave_wStark_control_phase_empty(t, site, duration, do_uwave=True):
    """Perform an X rotation on the control site with a phase offset.
    This assumes the microwaves are tuned off resonance, so the 459 'Raman' light will shift the light into resonance on the target site only..
    duration: defines the length of the pulse
    """

    # switch the microwave DDS profile
    t1 = uwave_DDS(t, 'control site, CNOT phase')
    # switch the scanners to the control site
    t2 = scanner459_1(t, site)
    t3 = scanner459_2(t, site)
    # wait for scanners to switch
    t2 += Ryd459_scanner1_delay
    t3 += Ryd459_scanner2_delay
    t = max(t1, t2, t3)

    #turn on 459 Raman laser and wait for an interval until the AOM is fully on.
    Raman459(t, 'off')
    t += Ryd459A_on_delay
    
    #turn on microwaves
    if do_uwave is True:
        uwave_switch(t, 'on')

    # turn off pulse nicely
    t += duration
    t = uwave_switch(t, 'off')
    t = Raman459(t, 'off')
    t+=Ryd459A_off_delay

    # Don't turn 459 scanners to off here.  Save time by only doing it after the last pulse.

    return t
    
def uwave_wStark(t, site, duration):
    """ a 'shift in' type uwave operation on the specified site for a uwave pulse time of duration
    site: the DDS profile to use, i.e. 'a', 'b', or 'c'
    duration: the length of the pulse
    """

    #select channel3 before everything
    uwave_select(t, 'DDS ch.3')
    
    #switch to the designated microwave DDS profile
    t1 = uwave_DDS(t, site)
    #switch 459 scanners to site
    t2 = scanner459_1(t, site)
    t3 = scanner459_2(t, site)
    #wait for the 459 scanners to complete switching behavior
    t2 += Ryd459_scanner1_delay
    t3 += Ryd459_scanner2_delay
    t = max(t1, t2, t3)
    
    #turn on 459 Raman laser and wait for an interval until the AOM is fully on.
    Raman459(t, 'on')
    t += Ryd459A_on_delay
    
    #turn on microwaves
    uwave_switch(t, 'on')

    #pulse interaction
    t += duration

    #turn off pulse nicely    
    t = uwave_switch(t, 'off')
    t = Raman459(t, 'off')
    uwave_select(t, 'DDS ch.4')
    t+=Ryd459A_off_delay

    return t


def uwave_wStark_control_phase(t, site, duration):
    """Perform an X rotation on the control site with a phase offset.
    phase control variable: det_control_phase
    This assumes the microwaves are tuned off resonance, so the 459 'Raman' light will shift the light into resonance on the target site only..
    duration: defines the length of the pulse
    """

    # switch the microwave DDS profile
    t1 = uwave_DDS(t, 'control site, CNOT phase')
    # switch the scanners to the control site
    t2 = scanner459_1(t, site)
    t3 = scanner459_2(t, site)
    # wait for scanners to switch
    t2 += Ryd459_scanner1_delay
    t3 += Ryd459_scanner2_delay
    t = max(t1, t2, t3)

    #turn on 459 Raman laser and wait for an interval until the AOM is fully on.
    Raman459(t, 'on')
    t += Ryd459A_on_delay
    
    #turn on microwaves
    uwave_switch(t, 'on')

    # turn off pulse nicely
    t += duration
    t = uwave_switch(t, 'off')
    t = Raman459(t, 'off')
    t+=Ryd459A_off_delay

    # Don't turn 459 scanners to off here.  Save time by only doing it after the last pulse.

    return t
    

def uwave_wStark_target_phase(t, site, duration):
    """The name suggests that the 459 Raman laser is shinning on the target site. This waveform can either be used as in shift-in or shift-out type operations. Right now, shift-out type.
    Perform an X rotation on the target site with a phase offset.
    phase control variable: det_target_phase
    This assumes the microwaves are tuned off resonance, so the 459 'Raman' light will shift the light into resonance on the target site only..
    duration: defines the length of the pulse
    """

    # switch the microwave DDS profile
    t1 = uwave_DDS(t, 'target site, with phase')
    # switch the scanners to target site
    t2 = scanner459_1(t, site)
    t3 = scanner459_2(t, site)
    # wait for scanners to switch
    t2 += Ryd459_scanner1_delay
    t3 += Ryd459_scanner2_delay
    t = max(t1, t2, t3)

    #turn on 459 Raman laser and wait for an interval until the AOM is fully on.
    Raman459(t, 'on')
    t += Ryd459A_on_delay
    
    #turn on microwaves
    uwave_switch(t, 'on')

    # turn off pulse
    t += duration
    t = Raman459(t, 'off')
    t = uwave_switch(t, 'off')

    # Don't turn 459 scanners to off here.  Save time by only doing it after the last pulse.

    return t
    
def uwave_wStark_control_phase_ver2(t, site, duration):
    """The name suggests that the 459 Raman laser is shinning on the control site. This waveform can either be used as in shift-in or shift-out type operations.    
    Perform an X rotation on the control site with a phase offset.
    This assumes the microwaves are tuned off resonance, so the 459 'Raman' light will shift the light into resonance on the target site only..
    duration: defines the length of the pulse
    """

    # switch the microwave DDS profile
    t1 = uwave_DDS(t, 'control site, with phase')
    # switch the scanners to the control site
    t2 = scanner459_1(t, site)
    t3 = scanner459_2(t, site)
    # wait for scanners to switch
    t2 += Ryd459_scanner1_delay
    t3 += Ryd459_scanner2_delay
    t = max(t1, t2, t3)

    #turn on 459 Raman laser and wait for an interval until the AOM is fully on.
    Raman459(t, 'on')
    t += Ryd459A_on_delay
    
    #turn on microwaves
    uwave_switch(t, 'on')

    # turn off pulse nicely
    t += duration
    t = uwave_switch(t, 'off')
    t = Raman459(t, 'off')
    t+=Ryd459A_off_delay

    # Don't turn 459 scanners to off here.  Save time by only doing it after the last pulse.

    return t
    
    
def Raman459_pulse(t, site, duration):
    """ shine 459 Raman light pulse for the time of duration onto specified site
    site: the DDS profile to use, i.e. 'a', 'b', or 'c'
    """

    #switch 459 scanners to site
    t1 = scanner459_1(t, site)
    t2 = scanner459_2(t, site)
    #wait for the 459 scanners to complete switching behavior
    t1 += Ryd459_scanner1_delay
    t2 += Ryd459_scanner2_delay
    t = max(t1, t2)
    
    #turn on 459 light    
    Raman459(t, 'on')
    t += Ryd459A_on_delay

    #pulse interaction
    t += duration    

    #turn off pulse nicely    
    t = Raman459(t, 'off')    
    t+=Ryd459A_off_delay

    return t
    
    
def scanners_off(t):
    """Turn the 459 scanners off.  This function is used so we don't have to turn the scanners off after the 1st
    microwave pulse in the Cz waveform."""

    #wait a little bit more time before switching off the scanners.
    t+=Ryd1038_scanners_off_extra_delay

    # scanners back to off
    t1 = scanner459_1(t, 'off')
    t2 = scanner459_2(t, 'off')
    t3 = scanner1038_1(t, 'off')
    t4 = scanner1038_2(t, 'off')
    # wait for scanners to switch
    t1 += Ryd459_scanner1_delay
    t2 += Ryd459_scanner2_delay
    t3 += Ryd1038_scanner1_delay
    t4 += Ryd1038_scanner2_delay
    t = max(t1,t2,t3,t4)

    return t

def do_blowaway(t):
    """Remove any atoms in F=4."""

    label(t, 'blowaway')

    # 1 us delay to account for variation of timing on HSDIO 1 and 2; not explicit because of the close_shutter_tim3
    t += .010

    # magnetic field switching waiting time 100 us; not explicit because of the close_shutter_tim3
    #t+=0.1

    # switch to readout fields
    t = set_magnetic_fields(t, 'readout')

    # magnetic field switching waiting time 200 us;
    t+=0.2
    
    # wait for the shutter to open
    #t+=close_shutter_time

    # do a blowaway pulse
    t1_0 = MOT(t, 'Blowaway')
    t1_a = MOT_intermediary_a(t, 'Blowaway')
    t1_b = MOT_intermediary_b(t, 'Blowaway')
    t = max(t1_0, t1_a, t1_b)
    
    t += blow_away_time
    
    t1_0 = MOT(t, 'off')
    t1_a = MOT_intermediary_a(t, 'off')
    t1_b = MOT_intermediary_b(t, 'off')
    t = max(t1_0, t1_a, t1_b)
    
    return t

def camera_delay(t):
    """Wait until 31 ms after the previous camera shot."""

    label(t, 'camera delay')

    # If we have already waited 31 ms doing other operations, then just proceed.
    # Otherwise, wait until 31 ms after the last shot

    return max(t, Hamamatsu.last_shot + delay_between_camera_shots)

def slow_noise_eater(t, RydA_switch_AO_DCNE_site=None):
    """Turn on the lasers one by one, so we can get the readings of their power."""

    label(t, 'noise eater')

    # turn everything off, and pointing the scanners to site 8.
    t = max(MOT(t, 'off'),
            repump(t, 'off'),
            Verdi780(t, 'off'),
            SHG780(t, 'off'),
            scanner459_1(t, 'e'),
            scanner459_2(t, 'e'),
            scanner1038_1(t, 'e'),
            scanner1038_2(t, 'e')
            )

    # wait for scanners to switch
    t += max(Ryd459_scanner1_delay, Ryd459_scanner2_delay)

    # set the time for each pulse
    dt = slow_noise_eater_laser_time
    dt2 = 0.5  # off for 0.5 ms
    dt3 = 0.005  # noise eater trigger delay, to ensure laser has turned on
    
    # 'Raman' 459 (samples [1,2])
    Raman459(t, 'on')
    slow_noise_eater_trigger2(t+dt3, 'on')
    t += dt
    Raman459(t, 'off')
    slow_noise_eater_trigger2(t, 'off')
    t += dt2

    # Rydberg 459A (samples [5,6])
    # the value is recorded when the scanner is pointing to site 8
    if RydA_switch_AO_DCNE_site is None:
        Rydberg459A(t, 'e')
    else:
        Rydberg459A(t, RydA_switch_AO_DCNE_site)
    slow_noise_eater_trigger2(t+dt3, 'on')
    t += dt
    Rydberg459A(t, 'off')
    slow_noise_eater_trigger2(t, 'off')
    # turn the 459 scanner to off
    scanner459_1(t, 'off')
    scanner459_2(t, 'off')
    t += dt2
    
    # Rydberg 1038 (samples [9,10])
    Rydberg1038_bit0(t, 'on')
    t += DDS_profile_delay
    Rydberg1038_bit1(t, 'on')
    slow_noise_eater_trigger2(t+dt3, 'on')
    t += dt
    Rydberg1038_bit0(t, 'off')
    t += DDS_profile_delay
    Rydberg1038_bit1(t, 'off')
    slow_noise_eater_trigger2(t, 'off')
    t += dt2
    
    # MOT (samples [13,14])
    MOT(t,'monitor')
    MOT_intermediary_a(t, 'monitor')
    MOT_intermediary_b(t, 'monitor')
    t += dt
    MOT(t, 'off')
    MOT_intermediary_a(t, 'off')
    MOT_intermediary_b(t, 'off')
    t += dt2
    
    # repump (samples [17,18])
    repump(t, 'on')
    t += dt
    repump(t, 'off')
    t += dt2
    
    # OP  (samples [21,22])
    OP(t, 'on')
    t += dt
    OP(t, 'off')
    t += dt2
    
    # OP repump (samples [25,26])
    OP_repump(t, 'on')
    t += dt
    OP_repump(t, 'off')
    t += dt2
    
    # blowaway (samples [29,30])
    blowaway(t, 'on')
    t += dt
    blowaway(t, 'off')
    t += dt2
    
    # 780 SHG (samples [33,34])
    SHG780(t, 'on')
    t += dt
    SHG780(t, 'off')
    t += dt2
    
    # 780 Verdi TiSapph (samples [37,38])
    Verdi780(t, 'on')
    t += dt
    Verdi780(t, 'off')
    t += dt2
    
    # 2D MOT (samples [61,62])
    # open 2D shutter and wait 10 ms
    t = open_2D_shutter(t, wait=True)
    # measure 2D MOT
    t += dt
    
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

def open_2D_shutter(t, wait=False):
    """Reopen the 2D MOT shutter.  If wait==True, then wait 10 ms for shutter to open."""

    label(t, 'open 2D shutter')

    # turn on the MOT, repump and traps, everything else is off
    if background:
        MOT2D_shutter(t, 'off')
    else:
        MOT2D_shutter(t, 'on')
        if wait:
            t += 10

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
        MOT_intermediary_a(t, 'MOT')
        MOT_intermediary_b(t, 'MOT')
        repump(t, 'on')
        MOT2D_shutter(t, 'on')
        # turn on OP light and OP repumper
        OP(t, 'on')
        OP_repump(t, 'on')        
    MOT3D_shutter(t, 'on')
    SHG780(t, 'on')
    Verdi780(t, 'on')
    blowaway_shutter(t, 'off')  # ensure the shutter for blow away light is off
    Raman459(t, 'on') # turn on Raman laser
    #Rydberg459A(t, 'e')#turn on Rydberg 459 A laser in the profile e
  
    t = uwave_DDS(t, 'global') # restore the uwave control DDS to rightful initial place
    
    # if you want to turn a specific channel on or off during idle, just do this here:
    #HSDIO(t, 3, 1)  # e.g. turn on channel 3

    return t    


def camera_noise_no_loading(t):
    """It is a standalone version of a complete experimental waveform whose sole purpose is to test the camera noise, 
    where the usual MOT loading stage is completely omitted. The motivation: 1. no atoms at all in theory (at least only
    the background atoms); 2. saving the time cost for one measurement.
    """
    DCNE_trigger_1(t)
    
    # turn on traps
    SHG780(t, 'on')
    Verdi780(t+Verdi_on_delay, 'on')
    
    #set the magnetic field as the usual 
    t = set_magnetic_fields(t, 'readout')
    t += 0.5
    t = readout(t, MOT_light_on = True, repump_light_on = True, camera_shutter_open = True)
    
    # 10 us delay to account for variation of HSDIO cards 1 and 2
    t += .010
    
    #take the second image
    t = camera_delay(t)
    t = readout(t, MOT_light_on = True, repump_light_on = True, camera_shutter_open = True)
    
    #finishing up stuff
    t = slow_noise_eater(t)
    t = idle(t)
    
    return t
    
def before_experiment_catalysis_loading(t):
    """Plays the same role as before_experiment(), but with the light assisted collision mechanism built in to enhance the loading process.
    """
   
    DCNE_trigger_1(t)

    # normal MOT loading
    t = set_magnetic_fields(t, 'MOT')
    t = MOT_loading(t)

    # PGC in MOT
    t = set_magnetic_fields(t, 'PGC in MOT')
    t = MOT(t, 'PGC in MOT')
    t += trap_780_delay_for_PGC_1
    
    # population re-distribution by MOT light
    t = repump(t, 'off')  # turn off repump light
    t = MOT(t, 'MOT')  # turn on MOT light
    t += ppl_redist_time
    
    # turn on traps
    SHG780(t, 'on')
    Verdi780(t+Verdi_on_delay, 'on')
    
    ## old-fashioned cooling in traps and pre-readout stage
    #t = set_magnetic_fields(t, 'light assisted collisions')
    #MOT(t, 'light assisted collisions')
    ## turn on OP light
    ##OP(t, 'on')
    #t += Pre_Readout_Time
    ##t = OP(t, 'off')
    ##MOT(t, 'off')

    # light assisted collisions while cooling in traps
    t = set_magnetic_fields(t, 'light assisted collisions')
    t = repump(t, 'on')  # turn on repump light
    MOT(t, 'light assisted collisions')
    # turn on OP light
    OP(t, 'on')
    t = t+catalysis_pulse_time
    OP(t, 'off')
    t =  t + max(0, Pre_Readout_Time - catalysis_pulse_time)
    #t = OP(t, 'off')
    #MOT(t, 'off')

    # continue as normal
    t = set_magnetic_fields(t, 'readout')
    t += 0.5
    t = PGC_in_traps(t)
    t = readout(t)
    t = PGC_in_traps(t)
    t = close_shutters(t)
    t = OP_magnetic_fields(t)
    t = optical_pumping(t)
    oscilloscope_trigger_Rydberg(t,'on')
    # 10 us delay to account for variation of HSDIO cards 1 and 2
    t += .010
    return t
    
def before_experiment_lookforaqua(t):
    """Plays the same role as before_experiment(), but with a different purpose: trying to find the atoms at low loading rate.
     Speical techniques have been applied which might not be necessarily suitable for daily operation under normal loading condition.
    Currently does not use any OP light.
    """
   
    DCNE_trigger_1(t)
    PTGrey_trigger(t)

    # normal MOT loading
    t = set_magnetic_fields(t, 'MOT')
    t = MOT_loading(t)

    # PGC in MOT & turn on traps
    t = set_magnetic_fields(t, 'PGC in MOT')
    t = MOT(t, 'PGC in MOT')
    SHG780(t, 'on')
    Verdi780(t+Verdi_on_delay, 'on')
    t += trap_780_delay_for_PGC_1
    
    # light assisted collisions while cooling in traps, pre-readout stage    
    #t = set_magnetic_fields(t, 'light assisted collisions')
    #MOT(t, 'light assisted collisions')
    # turn on OP light
    #OP(t, 'on')
    #t += Pre_Readout_Time
    #t = OP(t, 'off')
    #MOT(t, 'off')

    # continue as normal
    t = set_magnetic_fields(t, 'readout')
    t += 0.5
    t = PGC_in_traps(t)
    t = readout(t)
    t = PGC_in_traps(t)
    t = close_shutters(t)
    t = OP_magnetic_fields(t)
    t = optical_pumping(t)
    oscilloscope_trigger_Rydberg(t,'on')
    # 10 us delay to account for variation of HSDIO cards 1 and 2
    t += .010
    return t
    
def before_experiment_compressMOT(t):
    """Plays the same role as before_experiment(), but with additional MOT compressing operations.     
    Currently does not use any OP light.
    """
   
    DCNE_trigger_1(t)

    # normal MOT loading
    t = set_magnetic_fields(t, 'MOT')
    t = MOT_loading_with_compressing(t, compress_time = MOT_compress_time)

    # PGC in MOT & turn on traps
    t = set_magnetic_fields(t, 'PGC in MOT')
    t = PGC_in_MOT(t)
    t = set_magnetic_fields(t, 'light assisted collisions')
    t = MOT_drop(t)
    
    #t = light_assisted_collisions(t)

    # continue as normal
    t = set_magnetic_fields(t, 'readout')
    t += 0.5
    t = PGC_in_traps(t)
    t = readout(t)
    t = PGC_in_traps(t)
    t = close_shutters(t)
    t = OP_magnetic_fields(t)
    t = optical_pumping(t)
    oscilloscope_trigger_Rydberg(t,'on')
    # 10 us delay to account for variation of HSDIO cards 1 and 2
    t += .010
    return t

def before_experiment(t):
    """All the steps to get atoms initialized for an experiment."""
    DCNE_trigger_1(t)
    PTGrey_trigger(t)
    t = set_magnetic_fields(t, 'MOT')
    t = MOT_loading(t)
    t = set_magnetic_fields(t, 'PGC in MOT')
    t = PGC_in_MOT(t)
    t = set_magnetic_fields(t, 'light assisted collisions')
    t = MOT_drop(t)
    #t = light_assisted_collisions(t)
    t = set_magnetic_fields(t, 'readout')
    t = PGC_in_traps(t)
    t = readout(t)
    t = PGC_in_traps(t)
    t = close_shutters(t)
    t = OP_magnetic_fields(t)
    t = optical_pumping(t)
    oscilloscope_trigger_Rydberg(t,'on')
    # 10 us delay to account for variation of HSDIO cards 1 and 2
    t += .010
    return t

def after_experiment(t, RydA_switch_AO_DCNE_site=None):
    """All the steps to readout after an experiment.
    Note: Does not include blowaway."""

    oscilloscope_trigger_Rydberg(t,'off')
    # magnetic field switching waiting time 200 us.
    t += 0.2
    t = set_magnetic_fields(t, 'readout')    
    t = open_3D_shutters(t)
        
    t = camera_delay(t)
    t = readout(t)
    #t = PGC_in_traps(t)
    t = set_magnetic_fields(t, 'MOT')
    
    t = slow_noise_eater(t, RydA_switch_AO_DCNE_site=RydA_switch_AO_DCNE_site)
    #t = magnetic_field_monitor(t)
    #t = set_magnetic_fields(t, 'MOT')
    t = idle(t)
    return t

def Rydberg_pulse(t, time459, time1038, site, do459=True, do1038=True):
    """Do a Rydberg pulse on one site.  This waveform is used inside the Rydberg and Cz waveforms.
    It is used do eliminate repetition, but it is not sufficient on its own because it does not switch the scanners
    or traps.
    time459: how long the 459 light is on (not including delays)
    time1038 how long the 1038 light is on (not including delays)
    site: a string directing the 459 switch DDS to the correct profile (e.g. 'a', b', etc.)
    """
    on_delay = Ryd1038_on_delay - Ryd459A_on_delay
    off_delay = Ryd459A_off_delay - Ryd1038_off_delay
    # Rydberg light on
    if do459: 
        if (site == 'd') or (site == 'a') or (site == 'b'):
            Rydberg459A(t+on_delay, site)
        else:
            Rydberg459A(t+on_delay-DDS_profile_delay, site)
    if do1038: 
        if site == 'a':
            Rydberg1038_bit1(t, 'on')
        elif site == 'b':
            Rydberg1038_bit0(t, 'on')
        else:
            Rydberg1038_bit1(t, 'on')
    # Rydberg light off
    if do459: 
        Rydberg459A(t+time459 + off_delay, 'off')
    if do1038: 
        if site == 'a':
            Rydberg1038_bit1(t+time1038, 'off')
        elif site == 'b':
            Rydberg1038_bit0(t+time1038, 'off')
        else:
            Rydberg1038_bit1(t+time1038, 'off')
    # set the time to after 459 and 1038 have both ended
    t += max(time459, time1038)
    return t

def Rydberg(t, site, time459, time1038, do459=True, do1038=True, traps_off=True):
    """Do a Rydberg pulse on a single site.  Choose the site by passing in a string 'site' (e.g. 'site 1', 'site 2',
    etc.) that will select the appropriate DDS profile.
    time459: how long the 459 light is on (not including delays)
    time1038 how long the 1038 light is on (not including delays)
    site: a string directing the 459 switch DDS to the correct profile (e.g. 'a', b', etc.)
    """

    label(t, 'Rydberg '+str(sites[site]))
    
    #for debugging purpose
    print t

    # scanners to correct site
    if do459:
        scanner459_1(t, site)
        scanner459_2(t, site)    
    
    if do1038:
        scanner1038_1(t, site)
        scanner1038_2(t, site)

    # timing relative to the start of the pulse
    # calculate which of these delays is the longest, so we wait as little time as possible before excitation
    t1 = max(Ryd459A_on_delay, Ryd459_scanner1_delay, Ryd459_scanner2_delay) if do459 else 0
    t2 = max(Ryd1038_on_delay, Ryd1038_scanner1_delay, Ryd1038_scanner2_delay) if do1038 else 0
    t3 = max(trap780top_off_delay, trap780bottom_off_delay)
    t += max(t1, t2, t3)
    
    if traps_off:
        # 780 traps off
        SHG780(t-trap780top_off_delay, 'off')
        Verdi780(t-trap780bottom_off_delay, 'off')

    ### pi pulse ###
    t = Rydberg_pulse(t, time459, time1038, site, do459, do1038)

    # wait until both 459 and 1038 are both really off
    t += delay_before_switching

    # scanners off
    t = scanners_off(t)

    if traps_off:
        # 780 traps on
        SHG780(t+trap780top_on_delay, 'on')
        Verdi780(t+trap780bottom_on_delay, 'on')
    
        # wait until the traps are really back on
        t += delay_after_excitation_pulse

    return t

def Rydberg_pi(t, site, do459=True, do1038=True, traps_off=True):
    """Does a Rydberg pi pulse on one or several site.
    If traps_off=True (default) then the traps turn off for each pulse, but turn back on between pulses.  If traps_off=False then the traps are always on.
    """
    label(t, 'Rydberg Pi on site'+site)
    t_pulse = rydberg_RFE_pi_time[sites[site]]  # used for both 459 and 1038 pulse time
    return  Rydberg(t, site, t_pulse, t_pulse, do459, do1038, traps_off)

def Rydberg_pi_multiple(t, site_list, do459=True, do1038=True, traps_off=True):
    """ Waveform to run two consecutive Rydberg pulses on two sites. Separated by 2.5 ms to avoid Rydberg blockade behavior."""    
    t = Rydberg_magnetic_fields(t, Ramping=True)    
    for i,site in enumerate(site_list):
        t = Rydberg_pi(t, site, do459=do459, do1038=do1038, traps_off=traps_off)
        t = divert_459_scanners(t, site = 'e')
        if i != len(site_list)-1:
            t+= 2.5                 
    return t

def Rydberg_2pi(t, site, do459=True, do1038=True, traps_off=True):
    return  Rydberg(t, site, rydberg_RFE_2pi_time[sites[site]], rydberg_RFE_2pi_time[sites[site]],do459, do1038, traps_off)

def Rydberg_pi2(t, site, do459=True, do1038=True, traps_off=True):
    return  Rydberg(t, site, rydberg_RFE_pi2_time[sites[site]],rydberg_RFE_pi2_time[sites[site]], do459, do1038, traps_off)



def Cz(t, control, target, traps_off=True, do_1st_pulse=True, do_2nd_pulse=True, do_3rd_pulse=True):
    """Perform a Cz gate between two sites.
    This is a pi Rydberg pulse on the control site, a 2*pi Rydberg pulse on the target site, and a pi Rydberg pulse on
    the control site again.
    'control' and 'target' parameters are strings that direct the DDS profiles to the correct sites (e.g. 'a', 'b', 'c', etc).
    traps_off: If True (default) then the traps are turned off during the Rydberg pulses.  If False, the traps are always on.
    do_1st_pulse:  If True (default) the first pi pulse on the control is done.  If False, the first pulse on the control is not done, but the appropriate amount of time is allowed to pass.
    do_2nd_pulse:  If True (default) the 2pi pulse on the target is done.  If False, the 2pi pulse on the target is not done, althought the appropriate amount of time is allowed to pass.  So False does a pi-gap-pi experiment.
    do_3rd_pulse:  If True (default) the last pi pulse on the control is done.  If False, the last pulse on the control is not done, but the appropriate amount of time is allowed to pass.
    """

    label(t, 'Cz')

    #for debugging purpose
    print t

    # scanners to control site
    scanner459_1(t, control)
    scanner459_2(t, control)
    scanner1038_1(t, control)
    scanner1038_2(t, control)

    # timing relative to the start of the pulse
    # calculate which of these delays is the longest, so we wait as little time as possible before excitation
    #t1 = max(Ryd459A_on_delay, Ryd459_scanner1_delay, Ryd459_scanner2_delay)
    #t2 = max (Ryd1038_on_delay, Ryd1038_scanner1_delay, Ryd1038_scanner2_delay)
    switching_delay = max(Ryd459A_on_delay, Ryd1038_on_delay, delay_after_switching)
    t3 = max(trap780top_off_delay, trap780bottom_off_delay)
    t += max(switching_delay, t3)
    
    if traps_off:
        # 780 traps off
        SHG780(t-trap780top_off_delay, 'off')
        Verdi780(t-trap780bottom_off_delay, 'off')
    
    ### pi pulse on control site ###
    t = Rydberg_pulse(t, rydberg_RFE_pi_time[sites[control]], rydberg_RFE_pi_time[sites[control]], control, do459=do_1st_pulse, do1038=do_1st_pulse)
    
    # wait until both 459 and 1038 are really off
    t += delay_before_switching
    
    #scanners to target site
    scanner459_1(t, target)
    scanner459_2(t, target)
    scanner1038_1(t, target)
    scanner1038_2(t, target)

    # time it takes to fully switch sites
    t += switching_delay

    ### 2*pi pulse on target site ###
    t = Rydberg_pulse(t, rydberg_RFE_2pi_time[sites[target]], rydberg_RFE_2pi_time[sites[target]], target, do459=do_2nd_pulse, do1038=do_2nd_pulse)

    # wait until both 459 and 1038 are both really off
    t += delay_before_switching

    # scanners to control site
    scanner459_1(t, control)
    scanner459_2(t, control)
    scanner1038_1(t, control)
    scanner1038_2(t, control)

    # time it takes to fully switch sites
    t += switching_delay

    ### pi pulse on control site ###
    t = Rydberg_pulse(t, rydberg_RFE_pi_time[sites[control]], rydberg_RFE_pi_time[sites[control]], control, do459=do_3rd_pulse, do1038=do_3rd_pulse)
    
    # wait until both 459 and 1038 are both really off
    t += delay_before_switching

    # scanners off
    t = scanners_off(t)

    if traps_off:
        # 780 traps on
        SHG780(t+trap780top_on_delay, 'on')
        Verdi780(t+trap780bottom_on_delay, 'on')
    
        # wait until the traps are really back on
        t += delay_after_excitation_pulse

    return t

### different experiments ###

def state_F3(t):
    """Do state prep into F=3.  A high signal is expected."""    
    t = Rydberg_magnetic_fields(t, Ramping=True)    
    t = uwave_pi_global(t)    
    t = do_blowaway(t)
    return t

def state_F4(t):
    """Do state prep into F=4.  A low signal is expected."""
    t = do_blowaway(t)
    return t

def optimize_traps(t):
    """Use a trap drop, but no blowaway, so we can optimize the trap loading and retention."""
    t = Rydberg_magnetic_fields(t)
    t = trap_drop(t)
    return t


def state_choice(t, control, target, state):
    """Perform a microwave rotation on 0, 1 or 2 qubits, depending on the value of state.
    state:  0: |00>, 1:|X0>, 2:|0X>, and 3:|XX>
    control and target: strings that indicate the profiles to use for each site, i.e. 'a', 'b', 'c'
    """

    # Perform the appropriate microwave pulse
    if state==0:
        t = no_op(t)
    elif state==1:
        t = uwave_wStark(t, control, uwave_pi_time[sites[control]])
    elif state==2:
        t = uwave_wStark(t, target, uwave_pi_time[sites[target]])
    elif state==3:
        t = uwave_pi_global(t)
    return t
    
def state_choice_local_shiftout(t, control, target, state):
    """Perform a microwave rotation on 0, 1 or 2 qubits, depending on the value of state.
    state:  0: |00>, 1:|X0>, 2:|0X>, and 3:|XX>
    control and target: strings that indicate the profiles to use for each site, i.e. 'control' and 'target', as defined in the constants strings tab; DO NOT use 'a'  'b' names here!!!
    what's NEW? now, even the microwave frequency is customized locally; shift-out type.
    """

    # Perform the appropriate microwave pulse
    if state==0:
        t = uwave_wStark_target_phase(t, control, uwave_pi_time[sites[target]])
        t += uwave_local_delay_time #extra 200ns of gap time to avoid error
        t = uwave_wStark_control_phase(t, target, uwave_pi_time[sites[control]])
    elif state==1:
        t = uwave_wStark_control_phase(t, target, uwave_pi_time[sites[control]])
    elif state==2:
        t = uwave_wStark_target_phase(t, control, uwave_pi_time[sites[target]])
    elif state==3:
        t = no_op(t)
    return t

def state_choice_prepare(t, control, target, state):
    """Perform a microwave rotation on 0, 1 or 2 qubits, depending on the value of state.
    Shift out method. Prepare the input states for a gate, based upon the result of the previous optical pumping.
    assuming everything starts at F=4:  0: |00>, 1:|X0>, 2:|0X>, and 3:|XX>
    control and target: strings that indicate the profiles to use for each site, i.e. 'a', 'b', 'c'
    """

    # Perform the appropriate microwave pulse
    if state==3:
        t = no_op(t)
    elif state==2:
        t = uwave_wStark(t, control, uwave_pi_time[sites[target]])
    elif state==1:
        t = uwave_wStark(t, target, uwave_pi_time[sites[control]])
    elif state==0:
        t = uwave_pi_global(t)
    return t
    
def state_choice_detect(t, control, target, state):
    """Perform a microwave rotation on 0, 1 or 2 qubits, depending on the value of state.
    Shift out method. Detect the output states from a gate.
    state:  0: |00>, 1:|X0>, 2:|0X>, and 3:|XX>
    control and target: strings that indicate the profiles to use for each site, i.e. 'a', 'b', 'c'
    """

    # Perform the appropriate microwave pulse
    if state==0:
        t = no_op(t)
    elif state==1:
        t = uwave_wStark(t, control, uwave_pi_time[sites[target]])
    elif state==2:
        t = uwave_wStark(t, target, uwave_pi_time[sites[control]])
    elif state==3:
        t = uwave_pi_global(t)
    return t
    
def state_choice_detect_phase(t, control, target, input_state, state_det):
    """Perform a microwave rotation on 0, 1 or 2 qubits, depending on the value of state.
    Shift out method. Detect the output states from a gate.
    state:  0: |00>, 1:|X0>, 2:|0X>, and 3:|XX>
    control and target: strings that indicate the profiles to use for each site, i.e. 'a', 'b', 'c'
    """

    # Perform the appropriate microwave pulse
    if state_det==0:
        t = no_op(t)
    elif state_det==1:
        t = uwave_wStark_control_phase_ver2(t, control, uwave_pi_time[sites[target]])
    elif state_det==2:
        t = uwave_wStark_target_phase(t, target, uwave_pi_time[sites[control]])
    elif state_det==3:
        t = uwave_pi_global_phase(t)
    return t

def state_prep(t, control, target, state):
    """Prepare different state |11>, |01>, |10>, and |00> depending on the value of state, which should be stepped
    in the independent variables.
    control and target: strings that indicate the profiles to use for each site, i.e. 'a', 'b', 'c'
    """

    # Switch to Rydberg fields, unless we're just going to do a no_op.
    #if state != 0:
        #t = Rydberg_magnetic_fields(t)

    # switch to Rydberg magnetic field settings no matter what
    t = Rydberg_magnetic_fields(t, Ramping = True)
    
    # perform the appropriate microwave pulse to prepare the two-qubit states, in the shift-out type.
    t = state_choice_prepare(t, control, target, state)
    
    t = do_blowaway(t)
    
    return t
    
def state_prep_local_shiftout(t, control, target, state):
    """Prepare different state |11>, |01>, |10>, and |00> depending on the value of state, which should be stepped
    in the independent variables.
    control and target: strings that indicate the profiles to use for each site, i.e. 'a', 'b', 'c', however, the control and target site specification must agree with the global codename defined in the constants tab.
    """
    # switch to Rydberg magnetic field settings no matter what
    t = Rydberg_magnetic_fields(t, Ramping = True)
    
    # perform the appropriate microwave pulse
    t = state_choice_local_shiftout(t, control, target, state)
    
    t = do_blowaway(t)
    
    return t
    
def ac_Stark_laser_test(t, site, duration, do_uwave_first=True, is_empty=False):
    """A waveform to check what is wrong with the ac Stark shift laser.
    First pump everything into |0>; then apply uwave+ac Stark shift laser onto the specified site for given duration amount of time.
    """
    # switch to Rydberg magnetic field settings no matter what
    t = Rydberg_magnetic_fields(t, Ramping = True)
    
    if do_uwave_first is True:
        t = uwave_pi_global(t)
    
    # apply uwave+ac Stark shift laser; empty form
    if is_empty is True:
        t = uwave_wStark_empty(t, site, duration, False)    
    else:
        t = uwave_wStark(t, site, duration)
        
    # point the scanner to somewhere else, without triggering on the uwave.
    t = uwave_wStark_empty(t, 'c', 0.006, False) 
        
    t = do_blowaway(t)
    
    return t
    
def CNOT_empty(t,control, target, input_state, state_det, traps_off=True, do_uwave=True, do_1st_pulse=True, do_2nd_pulse=True, do_3rd_pulse=True):
    """Performs an empty CNOT waveform (i.e. without the 459 Raman laser, and the Rydberg lasers can be turned off too)
    And the microwave pi/2 pulse time is controlled by the uwave_pi2_time_global
    """
    t = Rydberg_magnetic_fields(t, Ramping=True)
    
    t = state_choice_prepare(t, control, target, input_state)
    t = uwave_wStark_empty(t, control, uwave_pi2_time_global, do_uwave=do_uwave)
    t = Cz(t, control, target, traps_off=traps_off, do_1st_pulse=do_1st_pulse, do_2nd_pulse=do_2nd_pulse, do_3rd_pulse=do_3rd_pulse)
    t = uwave_wStark_control_phase_empty(t, control, uwave_pi2_time_global, do_uwave=do_uwave)   
    t = state_choice_detect(t, control, target, state_det)

    t = do_blowaway(t)
    
    return t

def CNOT(t,control, target, input_state, state_det, traps_off=True, do_1st_pulse=True, do_2nd_pulse=True, do_3rd_pulse=True):
    """Performs a CNOT gate.
    input_state: prepare one of four states |11>, |01>, |10>, |00>"""
    
    t = Rydberg_magnetic_fields(t)
    
    t = state_choice(t, control, target, input_state)
    t = uwave_wStark(t, target, uwave_pi2_time[sites[target]])
    t = Cz(t, control, target, traps_off=traps_off, do_1st_pulse=do_1st_pulse, do_2nd_pulse=do_2nd_pulse, do_3rd_pulse=do_3rd_pulse)
    t = uwave_wStark_target_pi2_phase(t, target)
    # readout one of four states |00>, |10>, |01>, |11> as a high-high signal
    t = state_choice(t, control, target, state_det)

    t = do_blowaway(t)

    return t

def CNOT_shiftout(t,control, target, input_state, state_det, traps_off=True, do_1st_pulse=True, do_2nd_pulse=True, do_3rd_pulse=True):
    """Performs a CNOT gate on two sites by shift out method.
    input_state: prepare one of four states |11>, |01>, |10>, |00>"""
    
    t = Rydberg_magnetic_fields(t, Ramping=True)
    
    t = state_choice_prepare(t, control, target, input_state)
    t = uwave_wStark(t, control, uwave_pi2_time[sites[target]])
    t = Cz(t, control, target, traps_off=traps_off, do_1st_pulse=do_1st_pulse, do_2nd_pulse=do_2nd_pulse, do_3rd_pulse=do_3rd_pulse)
    t = uwave_wStark_control_phase(t, control, uwave_pi2_time[sites[target]])   
    t = state_choice_detect(t, control, target, state_det)
    
    t = divert_459_scanners(t, site = 'e')

    t = do_blowaway(t)

    return t
    
def CNOT_shiftout_with_detect_phase(t,control, target, input_state, state_det, traps_off=True, do_1st_pulse=True, do_2nd_pulse=True, do_3rd_pulse=True):
    """Performs a CNOT gate on two sites by shift out method.
    input_state: prepare one of four states |11>, |01>, |10>, |00>"""
    
    t = Rydberg_magnetic_fields(t, Ramping=True)
    
    t = state_choice_prepare(t, control, target, input_state)
    t = uwave_wStark(t, control, uwave_pi2_time[sites[target]])
    t = Cz(t, control, target, traps_off=traps_off, do_1st_pulse=do_1st_pulse, do_2nd_pulse=do_2nd_pulse, do_3rd_pulse=do_3rd_pulse)
    t = uwave_wStark_control_phase(t, control, uwave_pi2_time[sites[target]])   
    t = state_choice_detect_phase(t, control, target, input_state, state_det)

    t = do_blowaway(t)

    return t

def CNOT_phase_target(t,control, target, traps_off=True):
    """Performs a CNOT phase measurement on the target site.
    control: The DDS profile label of the control site (i.e. 'a', 'b', 'c')
    target: The DDS profile label of the target site (i.e. 'a', 'b', 'c')
    traps_off:  If True (default) then the traps go off during the gate.  If False, the traps are always on.
    """
        
    t = Rydberg_magnetic_fields(t)
    
    t = uwave_wStark(t, control, uwave_pi2_time[sites[target]])
    t = Cz(t, control, target, traps_off=traps_off)
    t = uwave_wStark_control_phase(t, control, uwave_pi2_time[sites[target]])

    t = do_blowaway(t)

    return t

def CNOT_phase_control(t,control, target, traps_off=True):
    """Performs a CNOT phase measurement on the control site.
    control: The DDS profile label of the control site (i.e. 'a', 'b', 'c')
    target: The DDS profile label of the target site (i.e. 'a', 'b', 'c')
    traps_off:  If True (default) then the traps go off during the gate.  If False, the traps are always on.
    """
        
    t = Rydberg_magnetic_fields(t)
    
    t = uwave_wStark(t, target, uwave_pi2_time[sites[control]])
    t = Cz(t, control, target, traps_off=traps_off)
    t = uwave_wStark_target_phase(t, target, uwave_pi2_time[sites[control]])

    t = do_blowaway(t)

    return t
    
def Oracle_imprint_phase(t, control, target, oracle_state, traps_off=True, laser_on = True):
    """Performs the oracle operation for the 2-qubit Grover search algorithm.
    The labeling strategy of the oracle_state is the same as the input_state
    """
    #waveform as written in the notes
    t = state_choice_prepare(t, control, target, state=oracle_state)    
    t += HSDIO_switching_delay
    t = Cz(t, control, target, traps_off=traps_off, do_1st_pulse=laser_on, do_2nd_pulse=laser_on, do_3rd_pulse=laser_on)
    t += HSDIO_switching_delay
    t = Raman459_pulse(t, site=target, duration=phaseshift_duration_A1)
    t += HSDIO_switching_delay
    t = Raman459_pulse(t, site=control, duration=phaseshift_duration_A2)
    t += HSDIO_switching_delay
    t = state_choice_prepare(t, control, target, state=oracle_state)
    
    return t 
    
def Inversion_about_mean_phase(t, control, target, traps_off=True, laser_on = True):
    """Performs the inversion about mean for the 2-qubit Grover search algorithm.
    In this version, the second microwave pi/2 pulse carries a phase, which can be used to cancel the overall accumulated phase if necessary.
    """
    t = uwave_pi_by_2_global(t)
    t += HSDIO_switching_delay
    t = Cz(t, control, target, traps_off=traps_off, do_1st_pulse=laser_on, do_2nd_pulse=laser_on, do_3rd_pulse=laser_on)
    t += HSDIO_switching_delay
    t = Raman459_pulse(t, site=target, duration=phaseshift_duration_B1)
    t += HSDIO_switching_delay
    t = Raman459_pulse(t, site=control, duration=phaseshift_duration_B2)
    t += HSDIO_switching_delay
    t = uwave_pi_by_2_global_phase(t)
    return t
    
def Grover_2qubit_phaseA(t, control, target, oracle_state, state_det, traps_off=True, laser_on = True):
    """Look for the proper phase correction needed in the Oracle_imprint_phase part. For the sake of safety, try both the two cases:
    oracle_state: 3 & state_det: 3, oracle_state: 0 & state_det: 0.
    """
    t = Rydberg_magnetic_fields(t, Ramping=True)    
    t = uwave_pi_by_2_global(t)
    t = Oracle_imprint_phase(t, control, target, oracle_state, traps_off=traps_off, laser_on = laser_on)
    t += HSDIO_switching_delay
    t = uwave_pi_by_2_global(t)
    t = state_choice_detect(t, control, target, state_det)
    
    t = do_blowaway(t)
    return t
    
def Grover_2qubit_shiftout(t, control, target, oracle_state, state_det, traps_off=True, laser_on = True):
    """Performs a 2-qubit Grover search with the simplified circuit diagram. The microwave local operations are in the shift out type.
    HSDIO_switching_delay is necessary or otherwise the transitions between sub-waveforms would be too fast.
    """
    t = Rydberg_magnetic_fields(t, Ramping=True)
    
    t = uwave_pi_by_2_global(t)
    t = Oracle_imprint_phase(t, control, target, oracle_state, traps_off=traps_off, laser_on = laser_on)
    t += HSDIO_switching_delay
    t = Inversion_about_mean_phase(t, control, target, traps_off=traps_off, laser_on = laser_on)
    t += HSDIO_switching_delay
    t = state_choice_detect(t, control, target, state_det)
    
    t = do_blowaway(t)
    return t

def RydbergRamsey(t, site, gap_time, do459=True, do1038=True, traps_off=True):
    """Perform a Rydberg Ramsey experiment on a single site: Rydberg pi/2 pulse -> gap time -> Rydberg pi/2 pulse.
    site:  the specified site in the form e.g. 'site 37';
    traps_off:  True to shut off the 780 traps during the pulse.  False to leave the traps always on.
    """
    label(t, 'Rydberg Ramsey on'+str(sites[site]))
    
    t = Rydberg_magnetic_fields(t, Ramping=True)    

    # scanners to correct site
    if do459:
        scanner459_1(t, site)
        scanner459_2(t, site)
    if do1038:
        scanner1038_1(t, site)
        scanner1038_2(t, site)
    
    #assign the pi/2 pulse time    
    time459 = rydberg_RFE_pi_time[sites[site]]/2
    time1038= rydberg_RFE_pi_time[sites[site]]/2   

    # timing relative to the start of the pulse
    # calculate which of these delays is the longest, so we wait as little time as possible before excitation
    t1 = max(Ryd459A_on_delay, Ryd459_scanner1_delay, Ryd459_scanner2_delay) if do459 else 0
    t2 = max(Ryd1038_on_delay, Ryd1038_scanner1_delay, Ryd1038_scanner2_delay) if do1038 else 0
    t3 = max(trap780top_off_delay, trap780bottom_off_delay)
    t += max(t1, t2, t3)
    
    if traps_off:
        # 780 traps off
        SHG780(t-trap780top_off_delay, 'off')
        Verdi780(t-trap780bottom_off_delay, 'off')

    ### pi/2 pulse ###
    t = Rydberg_pulse(t, time459, time1038, site, do459, do1038)

    # wait until both 459 and 1038 are both really off
    t += delay_before_switching
    
    # wait for the gap time
    t += gap_time
    
    ### pi/2 pulse ###
    t = Rydberg_pulse(t, time459, time1038, site, do459, do1038)
    
    # wait until both 459 and 1038 are both really off
    t += delay_before_switching

    # scanners off
    t = scanners_off(t)

    if traps_off:
        # 780 traps on
        SHG780(t+trap780top_on_delay, 'on')
        Verdi780(t+trap780bottom_on_delay, 'on')
    
        # wait until the traps are really back on
        t += delay_after_excitation_pulse

    # this delay was added to prevent the "HSDIO buffer underrun error" which happens if we try to do too many small pulses too quickly
    # we got this error when doing three Rydberg(t) operations in a row
    # it may be possible to make this delay shorter or instead put it somewhere else
    t += .001

    return t

def Ground_459A_Ramsey(t, site_list, duration=None):
    """Perform a 459 RydA light Ramsey experiment by doing a 459 pulse sandwiched by two microwave pi/2 pulses.
    site_list:  a list of profiles in the form e.g. ['a','b',...]
    duration: the length of each pulse.  If not specified, the site specific rydberg_A_459_pi_time will be used
    """
    
    t = Rydberg_magnetic_fields(t, Ramping=True)
    t = uwave_pi_by_2_global(t)
    
    print t
    
    if duration is None:
        for site in site_list:
            t = Rydberg(t, site, rydberg_A_459_pi_time[sites[site]], rydberg_A_459_pi_time[sites[site]], do459=True, do1038=False, traps_off=False)
            
            # this delay was added to prevent the "HSDIO buffer underrun error" which happens if we try to do too many small pulses too quickly
            # we got this error when doing three Rydberg(t) operations in a row
            t += HSDIO_switching_delay
    else:
        for site in site_list:
            t = Rydberg(t, site, duration, duration, do459=True, do1038=False, traps_off=False)
            # this delay was added to prevent the "HSDIO buffer underrun error" which happens if we try to do too many small pulses too quickly
            # we got this error when doing three Rydberg(t) operations in a row
            t += HSDIO_switching_delay

    print t
    
    t = uwave_pi_by_2_global(t)
    
    t = do_blowaway(t)
    
    return t

def Ground_459Raman_Ramsey(t, site_list, duration):
    """Perform a 459 Raman light Ramsey experiment by doing a 459 pulse sandwiched by two microwave pi/2 pulses.
    site_list:  a list of profiles in the form e.g. ['site 1', 'site 37']
    duration: the length of each pulse
    """

    t = Rydberg_magnetic_fields(t, Ramping=True)
    t = uwave_pi_by_2_global(t)
    if duration is None:
        for site in site_list:
            t =Raman459_pulse(t, site, raman_459_pi_time[sites[site]])
    else:
        for site in site_list:
            t = Raman459_pulse(t, site, duration)
    t = uwave_pi_by_2_global(t)
    
    # tell the scanners to point the Raman laser to somewhere else
    t = divert_459_scanners(t, site = 'e')

    t = do_blowaway(t)

    return t

def Ground_Rydberg_Stark_Echo_Ramsey(t, site_list, duration=None):
    """Perform a 459 RydA light Ramsey experiment by doing a 459 pulse sandwiched by two microwave pi/2 pulses.
    site_list:  a list of profiles in the form e.g. ['a','b',...]
    duration: the length of each pulse.  If not specified, the site specific rydberg_A_459_pi_time will be used
    """
    
    t = Rydberg_magnetic_fields(t, Ramping=True)
    t = uwave_pi_by_2_global(t)
    
    if duration is None:
        for site in site_list:
            t = Rydberg(t, site, rydberg_A_459_pi_time[sites[site]], rydberg_A_459_pi_time[sites[site]], do459=True, do1038=False, traps_off=True)
            
            # this delay was added to prevent the "HSDIO buffer underrun error" which happens if we try to do too many small pulses too quickly
            # we got this error when doing three Rydberg(t) operations in a row
            t += HSDIO_switching_delay
    else:
        for site in site_list:
            t = Rydberg(t, site, duration, duration, do459=True, do1038=False, traps_off=True)
            # this delay was added to prevent the "HSDIO buffer underrun error" which happens if we try to do too many small pulses too quickly
            # we got this error when doing three Rydberg(t) operations in a row
            t += HSDIO_switching_delay

    t = uwave_pi_global(t) 

    if duration is None:
        for site in site_list:
            t = Rydberg(t, site, rydberg_A_459_pi_time[sites[site]], rydberg_A_459_pi_time[sites[site]], do459=True, do1038=False, traps_off=True)
            
            # this delay was added to prevent the "HSDIO buffer underrun error" which happens if we try to do too many small pulses too quickly
            # we got this error when doing three Rydberg(t) operations in a row
            t += HSDIO_switching_delay
    else:
        for site in site_list:
            t = Rydberg(t, site, duration, duration, do459=True, do1038=False, traps_off=True)
            # this delay was added to prevent the "HSDIO buffer underrun error" which happens if we try to do too many small pulses too quickly
            # we got this error when doing three Rydberg(t) operations in a row
            t += HSDIO_switching_delay

    t = uwave_pi_by_2_global_phase(t)
    
    t = do_blowaway(t)

    return t

def uwave_shiftin_sites(t, site_list, duration=None):
    """Do shift-in type uwave operations on all 7 pre-assigned sites, with the hlep of 459 Raman laser
    site_list:  a list of profiles in the form e.g. ['site 1', 'site 37']
    duration: the length of each pulse.  If not specified, the site specific uwave_pi_time will be used
    """

    t = Rydberg_magnetic_fields(t)
    if duration is None:
        for site in site_list:
            t = uwave_wStark(t, site, uwave_pi_time[sites[site]])
    else:
        for site in site_list:
            t = uwave_wStark(t, site, duration)
            
    t = divert_459_scanners(t, site = 'e')

    t = do_blowaway(t)

    return t
    
def uwave_shiftin_pi(t, site_list, duration=None):
    """Do shift-in type uwave operations on up to 7 pre-assigned sites, with the hlep of 459 Raman laser.
    This version applies a global pi pulse first therefore every other site shall be high in retention.
    site_list:  a list of profiles in the form e.g. ['site 1', 'site 37']
    duration: the length of each pulse.  If not specified, the site specific uwave_pi_time will be used
    """

    t = Rydberg_magnetic_fields(t, Ramping=True)
    t = uwave_pi_global(t)
    if duration is None:
        for site in site_list:
            t = uwave_wStark(t, site, uwave_pi_time[sites[site]])
    else:
        for site in site_list:
            t = uwave_wStark(t, site, duration)
            
    t = divert_459_scanners(t, site = 'e')

    t = do_blowaway(t)

    return t
    
def uwave_shiftout(t, site1, site2, duration=None):
    """Do shift-out type uwave operations on site1, with the hlep of 459 Raman laser.
    site1: the site that is doing uwave operation.
    site2: the site that is shifted out of resonance of uwave.    
    duration: the length of each pulse.  If not specified, the site specific uwave_pi_time will be used
    """

    t = Rydberg_magnetic_fields(t)

    label(t, 'uwave')

    if duration is None:        
        t = uwave_wStark(t, site2, uwave_pi_time[sites[site1]])        
    else:
        t = uwave_wStark(t, site2, duration)     

    t = do_blowaway(t)

    return t

def OP_optimize(t):
    t = OP_depump(t)
    t = do_blowaway(t)
    return(t)

def optimize_0_1(t):
    """Switch between doing a pi pulse and no pi pulse, so you can optimize the high-low signal.  Includes an OP depumping and trap drop."""
    t = OP_depump(t)
    t = Rydberg_magnetic_fields(t)
    if state==3:
        t = uwave_pi_global(t)
    t = trap_drop(t)
    t = do_blowaway(t)
    return(t)

def background_only(t):
    """All the steps to get atoms initialized for an experiment."""
    set_magnetic_fields(t, 'MOT')
    SHG780(t, 'on')
    Verdi780(t, 'on')
    MOT(t, 'off')
    repump(t, 'off')
    MOT2D_shutter(t, 'off')
    MOT3D_shutter(t, 'on')

    t = readout(t)
    t = camera_delay(t)
    t = readout(t)

    return t

def ground_T2(t):
    """ T2 experiment on the two ground hyperfine states"""

    t = Rydberg_magnetic_fields(t, Ramping=True)
    t = uwave_pi_by_2_global(t)
    t += T2_delay
    t = uwave_pi_by_2_global_phase(t)
    t = do_blowaway(t)
  
    return t

def ground_T2_orthodox(t):
    """ T2 experiment on the two ground hyperfine states"""
    
    t = Rydberg_magnetic_fields(t, Ramping=True)
    t = uwave_pi_by_2_global(t)
    t += T2_delay
    t = uwave_pi_by_2_global(t)
    t = do_blowaway(t)
    
    return t

def ground_T2_local(t, control, target):
    """ T2 experiment on the two ground hyperfine states of a qubit, on a local single site which is the target site.
    Local addressing is realized via shift out method: 459 Raman laser is used to tune the control site out of resonance.    
    """

    t = Rydberg_magnetic_fields(t, Ramping=True)
    t = uwave_wStark(t, control, uwave_pi2_time[sites[target]])
    t += T2_delay            
    t = uwave_wStark_control_phase(t, control, uwave_pi2_time[sites[target]])   
    t = do_blowaway(t)
  
    return t



def ground_T2_sandwich(t, site):
    """ T2 experiment on the two ground hyperfine states globally, across the array.
    However, during the gap time, the Rydberg lasers are shining on the specified site.
    Trap is always on.
    """

    t = Rydberg_magnetic_fields(t)
    t = uwave_pi_by_2_global(t)
    
    # scanners to the specified site
    scanner459_1(t, site)
    scanner459_2(t, site)
    scanner1038_1(t, site)
    scanner1038_2(t, site)

    # timing relative to the start of the pulse
    # calculate which of these delays is the longest, so we wait as little time as possible before excitation
    #t1 = max(Ryd459A_on_delay, Ryd459_scanner1_delay, Ryd459_scanner2_delay)
    #t2 = max (Ryd1038_on_delay, Ryd1038_scanner1_delay, Ryd1038_scanner2_delay)
    switching_delay = max(Ryd459A_on_delay, Ryd1038_on_delay, delay_after_switching)
    t3 = max(trap780top_off_delay, trap780bottom_off_delay)
    t += max(switching_delay, t3)
    
    ### pi pulse on control site ###
    t = Rydberg_pulse(t, rydberg_RFE_pi_time[sites[site]], rydberg_RFE_pi_time[sites[site]], site, do459=True, do1038=True)
    #t+= rydberg_RFE_pi_time[sites[site]]
    
    # wait until both 459 and 1038 are really off
    t += delay_before_switching
    
    # uwave T2 gap time
    t += T2_delay
    
    t = uwave_pi_by_2_global_phase(t)
    t = do_blowaway(t)
  
    return t

def trapdrop_T2(t):
    """T2 experiment with a trap drop, to simulate CNOT."""
    t = uwave_pi_by_2_global(t)
    t = trap_drop(t)
    t += T2_delay
    t = uwave_pi_by_2_global_phase(t)
    t = do_blowaway(t)
  
    return t

def Ryd459A_on(t):
    """A convenience function to turn on the 459 light."""
    scanner459_1(t, 'site 1')
    scanner459_2(t, 'site 1')
    Rydberg459A(t, 'site 1')
    #SHG780(t, 'off')-
    #Verdi780(t, 'off')
    return t

def randomized_benchmarking_global(t):
    """Randomized Benchmarking with a random sequence of number 0 to 23 entered into dependent variables and truncation lengths entered into the independent variables tab."""    
    t = Rydberg_magnetic_fields(t, Ramping=True)    
    for temp in range(0, truncations[iteration_num]):
        t = uwave_clifford_global(t, matrix_list[temp])
    t = uwave_clifford_global(t, corrective_cliffords[iteration_num])
    t = uwave_pi_global(t)
    t = do_blowaway(t)
    return t


def uwave_wStark_clifford_global(t, site, site_phase, index):
    """Perform a global clifford gate with index."""
    #index is defined as in the supplemental material of PRL 114.100503 with zero index
    gate_time = clifford_times[index]
    if gate_time[2]>0:
        # switch the microwave DDS profile
        t = uwave_DDS(t, site)
        # turn on microwave pulse
        t = uwave_switch(t, 'on')
        # turn off microwave pulse
        t += gate_time[2]*uwave_pi2_time[sites[site]] 
        t = uwave_switch(t, 'off')

    if gate_time[1]>0:
        # switch the microwave DDS profile
        t = uwave_DDS(t, site_phase)
        # turn on microwave pulse
        t=uwave_switch(t, 'on')
        # turn off microwave pulse
        t += gate_time[1]*uwave_pi2_time[sites[site]] 
        t = uwave_switch(t, 'off')

    if gate_time[0]>0:
        # switch the microwave DDS profile
        t = uwave_DDS(t, site)
        # turn on microwave pulse
        t=uwave_switch(t, 'on')
        # turn off microwave pulse
        t += gate_time[0]*uwave_pi2_time[sites[site]] 
        t = uwave_switch(t, 'off')

    return t

def uwave_wStark_RB(t, site, site_phase):
    """ a 'shift in' type uwave operation on the specified site for a uwave randomized benchmarking
    site: the DDS profile to use, i.e. 'a', 'b', or 'c'
    duration: the length of the pulse
    """
    
    #switch to the designated microwave DDS profile
    t1 = uwave_DDS(t, site)
    #switch 459 scanners to site
    t2 = scanner459_1(t, site)
    t3 = scanner459_2(t, site)
    #wait for the 459 scanners to complete switching behavior
    t2 += Ryd459_scanner1_delay
    t3 += Ryd459_scanner2_delay
    t = max(t1, t2, t3)
    
    #turn on 459 Raman laser and wait for an interval until the AOM is fully on.
    Raman459(t, 'on')
    t += Ryd459A_on_delay

    for temp in range(0, truncations[iteration_num]):
        t = uwave_wStark_clifford_global(t, site, site_phase, matrix_list[temp])

    t = uwave_wStark_clifford_global(t, site, site_phase, corrective_cliffords[iteration_num])
    #turn off pulse nicely    
    t = Raman459(t, 'off')
    uwave_select(t, 'DDS ch.4')
    t+=Ryd459A_off_delay

    return t


def randomized_benchmarking_local_shiftin(t, site_list):
    """Do shift-in type uwave operations on up to 7 pre-assigned sites, with the help of 459 Raman laser.
    This version applies a global pi pulse first therefore every other site shall be high in retention.
    site_list:  a list of profiles in the form e.g. ['site 1', 'site 37']
    duration: the length of each pulse.  If not specified, the site specific uwave_pi_time will be used
    """

    t = Rydberg_magnetic_fields(t, Ramping=True)
    t = uwave_pi_global(t)
    #select channel3 before everything
    uwave_select(t, 'DDS ch.3')
    for temp in range(0, len(site_list), 2):
        t = uwave_wStark_RB(t, site_list[temp], site_list[temp+1])
    t = divert_459_scanners(t, site = 'e')
    t = do_blowaway(t)

    return t

def Ground_1038_Ramsey(t, site_list, duration=None):
    """Perform a 459 RydA light Ramsey experiment by doing a 459 pulse sandwiched by two microwave pi/2 pulses.
    site_list:  a list of profiles in the form e.g. ['a','b',...]
    duration: the length of each pulse.  If not specified, the site specific rydberg_A_459_pi_time will be used
    """
    
    t = Rydberg_magnetic_fields(t, Ramping=True)
    t = uwave_pi_by_2_global(t)

    for site in site_list:
        t = Rydberg(t, site, duration, duration, do459=False, do1038=True, traps_off=True)
            # this delay was added to prevent the "HSDIO buffer underrun error" which happens if we try to do too many small pulses too quickly
            # we got this error when doing three Rydberg(t) operations in a row
        t += HSDIO_switching_delay
    t = uwave_pi_by_2_global(t)
    
    t = do_blowaway(t)
    return t

def uwave_raman_clifford_local(t, site_list, index):
    """Perform a local clifford gate with index."""
    #index is defined as in the supplemental material of PRL 114.100503 with zero index
    gate_time = clifford_times[index]

    if gate_time[2] == 1:
        t = uwave_pi_by_2_global(t)
        for site in site_list:
            t = Raman459_pulse(t, site, raman_459_pi2_time[sites[site]])
        t = divert_459_scanners(t, site = 'e')
        t =uwave_pi2_global_control_CNOT_phase(t)
    elif gate_time[2] == -1:
        t = uwave_pi2_global_control_CNOT_phase(t)
        for site in site_list:
            t = Raman459_pulse(t, site, raman_459_pi2_time[sites[site]])
        t = divert_459_scanners(t, site = 'e')
        t = uwave_pi_by_2_global(t)
    elif gate_time[2] == 2:
        t = uwave_pi_by_2_global(t)
        for site in site_list:
            t = Raman459_pulse(t, site, raman_459_pi_time[sites[site]])
        t = divert_459_scanners(t, site = 'e')
        t =uwave_pi2_global_control_CNOT_phase(t)
    elif gate_time[2] == -2:
        t = uwave_pi2_global_control_CNOT_phase(t)
        for site in site_list:
            t = Raman459_pulse(t, site, raman_459_pi_time[sites[site]])
        t = divert_459_scanners(t, site = 'e')
        t = uwave_pi_by_2_global(t)

    t = uwave_DDS(t, 'global')
    t += 0.0001
    t = uwave_DDS(t, 'control site, with phase')
    t += 0.0001


    if gate_time[1] == 1:
        t = uwave_pi_by_2_global_phase(t)
        for site in site_list:
            t = Raman459_pulse(t, site, raman_459_pi2_time[sites[site]])
        t = divert_459_scanners(t, site = 'e')
        t =  uwave_pi2_global_control_phase(t)
    elif gate_time[1] == -1:
        t = uwave_pi2_global_control_phase(t)
        for site in site_list:
            t = Raman459_pulse(t, site,raman_459_pi2_time[sites[site]])
        t = divert_459_scanners(t, site = 'e')
        t = uwave_pi_by_2_global_phase(t)
    elif gate_time[1] == 2:
        t = uwave_pi_by_2_global_phase(t)
        for site in site_list:
            t = Raman459_pulse(t, site,raman_459_pi_time[sites[site]])
        t = divert_459_scanners(t, site = 'e')
        t = uwave_pi2_global_control_phase(t)
    elif gate_time[1] == -2:
        t =  uwave_pi2_global_control_phase(t)
        for site in site_list:
            t = Raman459_pulse(t, site,raman_459_pi_time[sites[site]])
        t = divert_459_scanners(t, site = 'e')
        t = uwave_pi_by_2_global_phase(t)

    t = uwave_DDS(t,  'control site, with phase')
    t += 0.0001
    t = uwave_DDS(t,'global')
    t += 0.0001

    if gate_time[0] == 1:
        t = uwave_pi_by_2_global(t)
        for site in site_list:
            t = Raman459_pulse(t, site, raman_459_pi2_time[sites[site]])
        t = divert_459_scanners(t, site = 'e')
        t =uwave_pi2_global_control_CNOT_phase(t)
    elif gate_time[0] == -1:
        t = uwave_pi2_global_control_CNOT_phase(t)
        for site in site_list:
            t = Raman459_pulse(t, site, raman_459_pi2_time[sites[site]])
        t = divert_459_scanners(t, site = 'e')
        t = uwave_pi_by_2_global(t)
    elif gate_time[0] == 2:
        t = uwave_pi_by_2_global(t)
        for site in site_list:
            t = Raman459_pulse(t, site, raman_459_pi_time[sites[site]])
        t = divert_459_scanners(t, site = 'e')
        t =uwave_pi2_global_control_CNOT_phase(t)
    elif gate_time[0] == -2:
        t = uwave_pi2_global_control_CNOT_phase(t)
        for site in site_list:
            t = Raman459_pulse(t, site, raman_459_pi_time[sites[site]])
        t = divert_459_scanners(t, site = 'e')
        t = uwave_pi_by_2_global(t)

    return t

def randomized_benchmarking_local_raman(t, site_list):
    """Do shift-in type uwave operations on up to 7 pre-assigned sites, with the help of 459 Raman laser.
    This version applies a global pi pulse first therefore every other site shall be high in retention.
    site_list:  a list of profiles in the form e.g. ['site 1', 'site 37']
    duration: the length of each pulse.  If not specified, the site specific uwave_pi_time will be used
    """

    t = Rydberg_magnetic_fields(t, Ramping=True)
    t = uwave_pi_global(t)
    for temp in range(0, truncations[iteration_num]):
        t = uwave_raman_clifford_local(t, site_list, matrix_list[temp])
    t = uwave_raman_clifford_local(t, site_list, corrective_cliffords[iteration_num])   
    t = divert_459_scanners(t, site = 'e')
    t = do_blowaway(t)

    return t

def zero_order_1038_pulse(t, site, time1038):
    """Do a Rydberg pulse on a single site.  Choose the site by passing in a string 'site' (e.g. 'site 1', 'site 2',
    etc.) that will select the appropriate DDS profile.
    time459: how long the 459 light is on (not including delays)
    time1038 how long the 1038 light is on (not including delays)
    site: a string directing the 459 switch DDS to the correct profile (e.g. 'a', b', etc.)
    """

    label(t, 'Rydberg '+str(sites[site]))
    
    #for debugging purpose
    print t

    scanner1038_1(t, site)
    scanner1038_2(t, site)

    t += time1038

    # scanners off
    t = scanners_off(t)

    return t


def Ground_1038_Raman(t, site_list, duration=None):
    """Perform a Raman gate with the zero order of the 1038  Rydberg laser light.
    site_list:  a list of profiles in the form e.g. ['a','b',...]
    duration: the length of each pulse.  If not specified, the site specific rydberg_1038_pi_time will be used
    """

    t = Rydberg_magnetic_fields(t, Ramping=True)
    #t = uwave_pi_by_2_global(t)
    if duration is None:
        for site in site_list:
            t = zero_order_1038_pulse(t, site, rydberg_1038_pi_time[sites[site]])
            
            # this delay was added to prevent the "HSDIO buffer underrun error" which happens if we try to do too many small pulses too quickly
            # we got this error when doing three Rydberg(t) operations in a row
            t += HSDIO_switching_delay
    else:
        for site in site_list:
            t = zero_order_1038_pulse(t, site, duration)
            # this delay was added to prevent the "HSDIO buffer underrun error" which happens if we try to do too many small pulses too quickly
            # we got this error when doing three Rydberg(t) operations in a row
            t += HSDIO_switching_delay     
    t = uwave_pi_global(t)
    t = do_blowaway(t)
    return t


    ### The above are all just definitions.  Specify the waveforms to actually run below. ###

t = 0


t = before_experiment(t)
#t = before_experiment_lookforaqua(t)
#t = before_experiment_compressMOT(t)
#t = before_experiment_catalysis_loading(t)



#t = trap_drop(t)
#t = state_F4(t)

#t = state_F3(t)
t+=time

#t = uwave_shiftin_pi(t, site_list=['a','b','d'], duration=uwave_time_local)
#t = uwave_shiftin_sites(t, ['a','b','c','d','e','f','g'], time)
#t = uwave_shiftout(t,'b','d', time)
#t= ground_T2(t)
#t= ground_T2_orthodox(t)
#t = Ground_459A_Ramsey(t, ['b'], duration=time)
#t = Ground_459A_Ramsey(t, ['a','b','d'])
#t = Ground_1038_Ramsey(t, ['b','d'], duration=3000)
#t = CNOT_phase_target(t, 'd', 'e', traps_off=False)
#t= CNOT_shiftout(t, 'd', 'e', input_state, state_det, traps_off=False, do_1st_pulse=False, do_2nd_pulse=False, do_3rd_pulse=False)
#t = RydbergRamsey(t, 'b', gap_time, do459=True, do1038=True, traps_off=True)
#t = ground_T2_local(t, control='a', target='b')
#t = ground_T2_sandwich(t, site = 'e')

#t = Ground_1038_Raman(t, ['b'], duration=time)

#t = OP_optimize(t)
#t = OP_depump(t)
#t = optical_pumping(t)
#t = do_blowaway(t)

#t = Ground_Rydberg_Stark_Echo_Ramsey(t, ['b'])

#t = randomized_benchmarking_global(t)
#t = randomized_benchmarking_local_shiftin(t, ['a','b'])
#t = randomized_benchmarking_local_raman(t, ['a'])

# pi-gap-pi experiment via CZ waveform
#t = Rydberg_magnetic_fields(t, Ramping=True)
#t = Cz(t, 'a', 'b', traps_off=True, do_1st_pulse=True, do_2nd_pulse=False, do_3rd_pulse=True)

# pi-gap-pi experiment via RydbergRamsey waveform
#t = RydbergRamsey(t, 'a', gap_time, do459=True, do1038=True, traps_off=True)

#t= CNOT_empty(t, 'b', 'a', input_state, state_det, traps_off=True, do_uwave=True, do_1st_pulse=False, do_2nd_pulse=False, do_3rd_pulse=False)

#t = Ground_459Raman_Ramsey(t, ['a'], time)
#t = Ground_459A_Ramsey(t, ['b'], duration=time)
#t = Rydberg_pi_multiple(t, ['a','b'], traps_off=True)
#t = Rydberg_pi_multiple(t, ['b','b','b','b','b'], traps_off=True)

#t = state_prep(t, 'a', 'b', input_state) #shift-out type!

#t = ac_Stark_laser_test(t, 'b', uwave_pi_time_global, do_uwave_first=True, is_empty=False)
#t = state_prep_local_shiftout(t, 'b', 'a', input_state)

#t = Cz(t, 'a', 'b', traps_off=True)
#t= CNOT_shiftout(t, 'a', 'b', input_state, state_det, traps_off=True, do_1st_pulse=True, do_2nd_pulse=True, do_3rd_pulse=True)

#t= CNOT_shiftout_with_detect_phase(t, 'a', 'd', input_state, state_det, traps_off=True, do_1st_pulse=True, do_2nd_pulse=True, do_3rd_pulse=True)

#t = Grover_2qubit_phaseA(t, 'a','b', oracle_state, state_det, traps_off=True, laser_on = True)
#t = Grover_2qubit_shiftout(t, 'a', 'b', oracle_state, state_det, traps_off=True, laser_on = True)

t = after_experiment(t, RydA_switch_AO_DCNE_site=None)
