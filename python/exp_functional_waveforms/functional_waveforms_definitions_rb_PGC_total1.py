
"""These are the waveform functions for the Rubidium project.

This file is not imported to CsPy. You'll have to copy-paste into the built-in editor of functional waveform definition.

ExpMode
0: Normal experiments
1: Laser continuously on. Shutters and coils are driven same as normal experiments.
2: Continuosly loading a MOT. Watch out for coil temperatures!

"""


import exp_functional_waveforms.functional_waveforms_rb as Rb

HSDIO = experiment.LabView.HSDIO.add_transition
HSDIO_repeat = experiment.LabView.HSDIO.add_repeat
AO = experiment.LabView.AnalogOutput.add_transition
DO = experiment.LabView.DAQmxDO.add_transition
label = experiment.functional_waveforms_graph.label

exp = Rb.Rb(HSDIO, AO, DO, label)
###########################################################################
# Definition Block

def chop_readout(channels, phases, profiles, period):
    """Add a single cycle of a chopping pattern """
    if len(channels) != len(phases) or len(channels) != len(profiles):
        print "Chop function requries equal length lists of channels and phases"
        raise PauseError

    def chop_function(t):
        # TODO: check that profiles are grey coded!!!!!!!!
        print t
        for i, c in enumerate(channels):
            # set up initial state
            init_state = profiles[i][0]
            msg = "ch[{}]: t({}) = {}"
            #print(msg.format(c, 0, init_state))
            HSDIO(t, c, init_state)
            # now change state at phase list
            for j, p in enumerate(phases[i]):
                if p > 1 or p < 0:
                    print "chop_dds function expects phases to be within 0<p<1"
                    raise ValueError
                # put in initial value for the cycle
                # put in transition
                #print(msg.format(c, p, profiles[i][j + 1]))
                HSDIO(t + (p * period), c, profiles[i][j + 1])
        return t + period

    return chop_function


def readout(t,duration):
    """Image atom in FORT."""
    # Note that camera trigger is not included here. Exposure control needs to be done indepdently
    # Also magnetic field control is done sepearately.

    label(t, 'readout')
    # chop FORT and MOT out of phase
    cycles = int(duration*1000*readout_chop_freq_MHz)
    period_ms = 0.001/readout_chop_freq_MHz
    label(t + period_ms, 'readout c1')
    label(t + cycles*period_ms/2, 'readout half')
    print(t + cycles*period_ms/2)
    channels = [my_MOT_SW_channel, my_FORT_SW_channel]
    #phases = [[0.18, 0.4], [0.49, 0.96]] #original
    phases = [[0.18, 0.4], [0.59, 0.9]] # wide Best so far
    #phases = [[0.18, 0.49],[0.69, 0.91]] # wide  REVERSE
    # phases = [[0.18, 0.4], [0.59+t_gap, 0.9-t_gap]] # wide
    # phases = [[0.18, 0.4], [0.59+t_gap, 0.9+t_gap]] # wide, but change overall phase

    # phases = [[0.76, 0.98], [0.17, 0.8]] #narrow
    # phases = [[0.6, 0.98], [0.17, 0.8]] #narrow wider mot
    #phases = [[0.5,0.9], [0.18, 0.6]]
    profiles = [
        [0, 1, 0],
        [1, 0, 1]
    ] # Normal
    # profiles = [
    #     [1, 0, 1]
    #     ,[0, 1, 0]
    # ]
    t = HSDIO_repeat(t, chop_readout(channels, phases, profiles, period_ms), cycles)
    return t
def readout2(t,duration):
    """Image atom in FORT."""
    # Note that camera trigger is not included here. Exposure control needs to be done indepdently
    # Also magnetic field control is done sepearately.

    label(t, 'readout')
    # chop FORT and MOT out of phase
    cycles = int(duration/RO_chop_period)
    period_ms = RO_chop_period
    label(t + period_ms, 'readout c1')
    label(t + cycles*period_ms/2, 'readout half')
    print(t + cycles*period_ms/2)
    channels = [my_MOT_SW_channel,my_FORT_SW_channel]
    #phases = [ [0.49, 0.96]]
    #phases = [[0.2, 0.9]]
    phases = [[0.18, 0.49],[0.69, 0.91]]
    profiles = [
        [1, 0, 1]
        ,[0, 1, 0]
    ]
    # profiles = [
    #     [1, 0, 1]
    # ]
    # profiles = [
    # [1, 0, 1]
    # ]
    # channels = [3]
    # phases = [ [0.49, 0.96]]
    # profiles = [
    #     [1, 0, 1]
    # ]
    t = HSDIO_repeat(t, chop_readout(channels, phases, profiles, period_ms), cycles)
    return t
def readout3(t,duration):
    """Image atom in FORT."""
    # Note that camera trigger is not included here. Exposure control needs to be done indepdently
    # Also magnetic field control is done sepearately.

    label(t, 'readout')
    # chop FORT and MOT out of phase
    cycles = int(duration*1000*readout_chop_freq_MHz)
    period_ms = 0.001/readout_chop_freq_MHz
    label(t + period_ms, 'readout c1')
    label(t + cycles*period_ms/2, 'readout half')
    print(t + cycles*period_ms/2)
    channels = [my_MOT_SW_channel, my_FORT_SW_channel]
    phases = [[0.18, 0.4], [0.59, 0.9]]
    #phases = [[0.5,0.9], [0.18, 0.6]]
    profiles = [
        [0, 1, 0],
        [1, 0, 1]
    ]
    t = HSDIO_repeat(t, chop_readout(channels, phases, profiles, period_ms), cycles)
    return t

def readout4(t,duration): # slightly thinner thicc FORT pulses
    """Image atom in FORT."""
    # Note that camera trigger is not included here. Exposure control needs to be done indepdently
    # Also magnetic field control is done sepearately.

    label(t, 'readout')
    # chop FORT and MOT out of phase
    cycles = int(duration*1000*readout_chop_freq_MHz)
    period_ms = 0.001/readout_chop_freq_MHz
    label(t + period_ms, 'readout c1')
    label(t + cycles*period_ms/2, 'readout half')
    print(t + cycles*period_ms/2)
    channels = [my_MOT_SW_channel, my_FORT_SW_channel]
    phases = [[0.18, 0.4], [0.52, 0.96]]
    profiles = [
        [0, 1, 0],
        [1, 0, 1]
    ]
    t = HSDIO_repeat(t, chop_readout(channels, phases, profiles, period_ms), cycles)
    return t

def opticalpumping(t,duration):
    """Optical pumping to the clock state."""
    # Note that camera trigger is not included here. Exposure control needs to be done indepdently
    # Also magnetic field control is done sepearately.
    if duration>0:
        label(t, 'OP')
        # chop FORT and MOT out of phase
        cycles = int(duration*1000*op_chop_freq_MHz)
        period_ms = 0.001/op_chop_freq_MHz
        label(t + period_ms, 'OP c1')
        label(t + cycles*period_ms/2, 'OP half')
        print(t + cycles*period_ms/2)
        channels = [op_aom_switch_chan, my_FORT_SW_channel]
        phases = [[0.3, 0.6], [0.1, 0.6]]
        profiles = [
            [1, 0, 1], # OP on is 0. off is 1
            [1, 0, 1]  # FORT chopping: 1 , 0 , 1, no chopping : 1 1 1
        ]
        t = HSDIO_repeat(t, chop_readout(channels, phases, profiles, period_ms), cycles)
    else:
        print("non-zero duration is required. this repeat function will do nothing")
    return t
def opticalpumping2(t,duration):
    """Optical pumping to the clock state."""
    # Note that camera trigger is not included here. Exposure control needs to be done indepdently
    # Also magnetic field control is done sepearately.
    if duration>0:
        label(t, 'OP')
        # chop FORT and MOT out of phase
        cycles = int(duration*1000*op_chop_freq_MHz)
        period_ms = 0.001/op_chop_freq_MHz
        label(t + period_ms, 'OP c1')
        label(t + cycles*period_ms/2, 'OP half')
        print(t + cycles*period_ms/2)
        channels = [ryd780b_aom_switch_chan, my_FORT_SW_channel]
        phases = [[0.3, 0.6], [0.1, 0.6]]
        profiles = [
            [0, 1, 0], # 780B on is 1. off is 0
            [1, 0, 1]  # FORT chopping: 1 , 0 , 1, no chopping : 1 1 1
        ]
        t = HSDIO_repeat(t, chop_readout(channels, phases, profiles, period_ms), cycles)
    else:
        print("non-zero duration is required. this repeat function will do nothing")
    return t
def raman(t,duration,pointing_profile):
    """Raman beam control to drive ground hyperfine clock transition |2,0> <-> |1,0> """
    if t>0 and duration >0: #make sure timings are valid
        exp.ground_aom_switch.profile(t,'on')
        exp.ground_aom_switch.profile(t+duration,'off')
        exp.red_pointing_aom_switch.profile(t,'on')
        #exp.red_pointing_aom_switch.profile(t+duration,'off')
        exp.red_pointing_dds.profile(t,pointing_profile) # point to the target_region. example 'r2'
        exp.red_pointing_dds.profile(t+duration,'off')
    else:
        print "make sure your timings are valid"

def prepareF1(t,duration):
    """This function will leave MOT light on without repumper so atoms are depopulated from F=2 and pumped into F=1"""
    if t>0 and duration >0: #make sure timings are valid
        exp.fort_aom_switch.profile(t,'on')
        exp.fort_aom_switch.profile(t+duration,'on')
        exp.fort_dds.profile(t,'on')
        exp.fort_dds.profile(t+duration,'on')
        exp.mot_3d_dds.profile(t,'RO')
        exp.mot_aom_switch.profile(t,'on')
        exp.mot_aom_switch.profile(t+duration,'off')
        exp.hf_aom_switch.profile(t,'off')
        AO(t,7,0)
    else:
        print "make sure your timings are valid"

def FORTdrop(t,duration):
    """ This function will turn off the 1064 FORT for the given duration and back on afterwards"""
    if t>0 and duration >0: #make sure timings are valid
        exp.fort_aom_switch.profile(t,'off')
        exp.fort_aom_switch.profile(t+duration,'on')
        exp.fort_dds.profile(t,'off')
        exp.fort_dds.profile(t+duration,'on')
#    else:
        #print "make sure your timings are valid"

def MicrowaveRamsey(t_start,t_gap,t_piover2):
    """ Creates two pi/2 pulses separated by t_gap. First pulse starts at t_start"""
    if t_start>=0 and t_piover2 >0 and t_gap>=0: #make sure timings are valid
        exp.microwave_dds.profile(t_start,'on')
        exp.microwave_switch.profile(t_start,'on')
        exp.microwave_dds.profile(t_start+t_piover2,'off')
        exp.microwave_switch.profile(t_start+t_piover2,'off')
        exp.microwave_dds.profile(t_start+t_piover2+t_gap,'on')
        exp.microwave_switch.profile(t_start+t_piover2+t_gap,'on')
        exp.microwave_dds.profile(t_start+t_piover2+t_gap+t_piover2,'off')
        exp.microwave_switch.profile(t_start+t_piover2+t_gap+t_piover2,'off')

def SpinEcho(t_start,t_gap,t_piover2):
    """ Creates two pi/2 pulses separated by (t_gap+2*t_piover2). First pulse starts at t_start"""
    if t_start>=0 and t_piover2 >0 and t_gap>=0: #make sure timings are valid
        # First pi/2 pulse
        exp.microwave_dds.profile(t_start,'on')
        exp.microwave_switch.profile(t_start,'on')
        exp.microwave_dds.profile(t_start+t_piover2,'off')
        exp.microwave_switch.profile(t_start+t_piover2,'off')
        # Pi pulse in between
        exp.microwave_dds.profile(t_start+t_piover2+t_gap/2.0,'on')
        exp.microwave_switch.profile(t_start+t_piover2+t_gap/2.0,'on')
        exp.microwave_dds.profile(t_start+3.0*t_piover2+t_gap/2.0,'off')
        exp.microwave_switch.profile(t_start+3.0*t_piover2+t_gap/2.0,'off')


        exp.microwave_dds.profile(t_start+3.0*t_piover2+t_gap,'on')
        exp.microwave_switch.profile(t_start+3.0*t_piover2+t_gap,'on')
        exp.microwave_dds.profile(t_start+4.0*t_piover2+t_gap,'off')
        exp.microwave_switch.profile(t_start+4.0*t_piover2+t_gap,'off')

def Microwave(t,duration):
    if t>=0 and duration>0: #make sure timings are valid
        exp.microwave_dds.profile(t,'on')
        exp.microwave_switch.profile(t,'on')
        exp.microwave_dds.profile(t+duration,'off')
        exp.microwave_switch.profile(t+duration,'off')

def Ryd780A(t,duration,pointing_profile,intensity_profile): # region_profile example: 'r2'
    if t>=0 and duration>0: #make sure timings are valid
        exp.red_pointing_dds.profile(t,pointing_profile)
        exp.red_pointing_dds.profile(t+duration,'off')
        exp.ryd780a_dds.profile(t,intensity_profile)
        exp.ryd780a_dds.profile(t+duration,'off')
        exp.red_pointing_aom_switch.profile(t,'on')
        #exp.red_pointing_aom_switch.profile(t+duration,'off')
        exp.ryd780a_aom_switch.profile(t,'on')
        exp.ryd780a_aom_switch.profile(t+duration,'off')

def Ryd780B(t,duration,pointing_profile,intensity_profile): # region_profile example: 'r2'
    if t>=0 and duration>0: #make sure timings are valid
        exp.red_pointing_dds.profile(t,pointing_profile)
        exp.red_pointing_dds.profile(t+duration,'off')
        exp.ryd780b_dds.profile(t,intensity_profile)
        exp.ryd780b_dds.profile(t+duration,'off')
        exp.red_pointing_aom_switch.profile(t,'on')
        #exp.red_pointing_aom_switch.profile(t+duration,'off')
        exp.ryd780b_aom_switch.profile(t,'on')
        exp.ryd780b_aom_switch.profile(t+duration,'off')

def Ryd780A_leadtime(t,t_leadtime,duration,pointing_profile,intensity_profile): # region_profile example: 'r2'
    if t>=0 and duration>0: #make sure timings are valid
        exp.red_pointing_dds.profile(t-t_leadtime,pointing_profile)
        exp.red_pointing_dds.profile(t+duration,'off')
        exp.ryd780a_dds.profile(t-t_leadtime,intensity_profile)
        exp.ryd780a_dds.profile(t+duration,'off')
        exp.red_pointing_aom_switch.profile(t-t_leadtime,'on')
        #exp.red_pointing_aom_switch.profile(t+duration,'off')
        exp.ryd780a_aom_switch.profile(t,'on')
        exp.ryd780a_aom_switch.profile(t+duration,'off')


def Ryd780A_pulsed(t, cycle_time, pointing_profile, intensity_profile, pulse_ontime, num_of_pulses): # region_profile example: 'r2'
    t_red_delay=0.950*0.001
    if t>=0: #make sure timings are valid
        for i in range(0,num_of_pulses):
            exp.red_pointing_dds.profile(t+t_red_delay+i*cycle_time,pointing_profile)
            exp.red_pointing_dds.profile(t+t_red_delay+pulse_ontime+i*cycle_time,'off')
            exp.ryd780a_dds.profile(t+t_red_delay+i*cycle_time,intensity_profile)
            exp.ryd780a_dds.profile(t+t_red_delay+pulse_ontime+i*cycle_time,'off')
            exp.red_pointing_aom_switch.profile(t+t_red_delay+i*cycle_time,'on')
            exp.red_pointing_aom_switch.profile(t+t_red_delay+pulse_ontime+i*cycle_time,'off')
            exp.ryd780a_aom_switch.profile(t+t_red_delay+i*cycle_time,'on')
            exp.ryd780a_aom_switch.profile(t+t_red_delay+pulse_ontime+i*cycle_time,'off')
            exp.fort_aom_switch.profile(t+i*cycle_time,'off')
            exp.fort_aom_switch.profile(t+pulse_ontime+i*cycle_time,'on')

def Ryd780A_Ramsey(t_start, t_gap, t_piover2, pointing_profile, intensity_profile):
    if t_start>=0 and t_piover2 >0 and t_gap>=0: #make sure timings are valid
        t_leadtime=0.005
        exp.red_pointing_dds.profile(t_start-t_leadtime,pointing_profile)
        exp.ryd780a_dds.profile(t_start-t_leadtime,intensity_profile)
        exp.red_pointing_aom_switch.profile(t_start-t_leadtime,'on')

        exp.ryd780a_aom_switch.profile(t_start,'on')
        exp.ryd780a_aom_switch.profile(t_start+t_piover2,'off')
        exp.ryd780a_aom_switch.profile(t_start+t_piover2+t_gap,'on')
        exp.ryd780a_aom_switch.profile(t_start+t_piover2+t_gap+t_piover2,'off')

        exp.red_pointing_dds.profile(t_start+t_piover2+t_gap+t_piover2,'off')
        exp.ryd780a_dds.profile(t_start+t_piover2+t_gap+t_piover2,'off')
        exp.red_pointing_aom_switch.profile(t_start+t_piover2+t_gap+t_piover2,'off')

def MicrowaveRamsey_and_780A(t_start, t_gap, t_piover2, pointing_profile, intensity_profile):
    """ Creates two pi/2 pulses separated by t_gap. First pulse starts at t_start"""
    if t_start>=0 and t_piover2 >0 and t_gap>=0: #make sure timings are valid
        exp.microwave_dds.profile(t_start,'on')
        exp.microwave_switch.profile(t_start,'on')
        exp.microwave_dds.profile(t_start+t_piover2,'off')
        exp.microwave_switch.profile(t_start+t_piover2,'off')
        Ryd780A(t_start+t_piover2,t_gap,pointing_profile,intensity_profile)
        exp.microwave_dds.profile(t_start+t_piover2+t_gap,'on')
        exp.microwave_switch.profile(t_start+t_piover2+t_gap,'on')
        exp.microwave_dds.profile(t_start+t_piover2+t_gap+t_piover2,'off')
        exp.microwave_switch.profile(t_start+t_piover2+t_gap+t_piover2,'off')
def MicrowaveRamsey_and_780B(t_start, t_gap, t_piover2, pointing_profile, intensity_profile):
    """ Creates two pi/2 pulses separated by t_gap. First pulse starts at t_start"""
    if t_start>=0 and t_piover2 >0 and t_gap>=0: #make sure timings are valid
        exp.microwave_dds.profile(t_start,'on')
        exp.microwave_switch.profile(t_start,'on')
        exp.microwave_dds.profile(t_start+t_piover2,'off')
        exp.microwave_switch.profile(t_start+t_piover2,'off')
        Ryd780B(t_start+t_piover2,t_gap,pointing_profile,intensity_profile)
        exp.microwave_dds.profile(t_start+t_piover2+t_gap,'on')
        exp.microwave_switch.profile(t_start+t_piover2+t_gap,'on')
        exp.microwave_dds.profile(t_start+t_piover2+t_gap+t_piover2,'off')
        exp.microwave_switch.profile(t_start+t_piover2+t_gap+t_piover2,'off')
def RamanRamsey(t_start, t_gap, t_piover2, pointing_profile, intensity_profile):
    """ Creates two pi/2 pulses separated by t_gap. First pulse starts at t_start"""
    if t_start>=0 and t_piover2 >0 and t_gap>=0: #make sure timings are valid
        exp.ground_aom_switch.profile(t_start,'on')
        exp.ground_aom_switch.profile(t_start+t_piover2,'off')
        exp.red_pointing_aom_switch.profile(t_start,'on')
        #exp.red_pointing_aom_switch.profile(t+duration,'off')
        exp.red_pointing_dds.profile(t_start,pointing_profile) # point to the target_region. example 'r2'
        exp.red_pointing_dds.profile(t_start+2*t_piover2+t_gap*1.05,'off')
        exp.ground_aom_switch.profile(t_start+t_piover2+t_gap,'on')
        exp.ground_aom_switch.profile(t_start+t_piover2+t_gap+t_piover2,'off')
def Blue480(t, duration, pointing_profile):
    exp.blue_pointing_dds.profile(t, pointing_profile)
    exp.blue_pointing_aom_switch.profile(t, 'on')
    exp.blue_pointing_dds.profile(t+duration,'off')
    #exp.blue_pointing_aom_switch.profile(t+duration,'off')

###########################################################################
# Main Block
# Setting timing sequences for an experiment.
# For diagnostics purpose, sequences are low level coded.
############
t=0

exp.camera.pulse_length=t_exposure # Changes HSDIO pulse width to control exposure

# Abstractized experiment control

##### For Normal Experiment ######
if ExpMode==0:
## Initilization
    #for i in range(5):
    #    AO(0,i,0)
    AO(0,0,coil_driver_polarity*I_Q1)
    AO(0,1,coil_driver_polarity*I_Q2)
    AO(0,2,coil_driver_polarity*ShimX_Loading) #X
    AO(0,3,coil_driver_polarity*ShimY_Loading) #Y
    AO(0,4,coil_driver_polarity*ShimZ_Loading) #Z
    AO(0,5,coil_driver_polarity*-2.2)
    AO(0,6,coil_driver_polarity*2.8)
    AO(0,7,10)
    # For pointgrey shot.
    exp.pointgrey_trigger_switch.profile(0,'off')
    exp.pointgrey_trigger_switch.profile(t1_PGcamera,'on')
    exp.pointgrey_trigger_switch.profile(t1_PGcamera+t_PG_triggerduration,'off')
    #Ryd780A(t1_PGcamera,t_PG_triggerduration,'PG','PG')
    #Ryd780B(t1_PGcamera,t_PG_triggerduration,'PG','r3')
    # Ryd780B(t_science,t_gap,'PG','r3')
    exp.ground_aom_switch.profile(0,'off')
    exp.ground_aom_switch.profile(t1_PGcamera+0.4*t_PG_triggerduration,'on')
    exp.ground_aom_switch.profile(t1_PGcamera+0.5*t_PG_triggerduration,'off')
    #raman(t1_PGcamera,t_PG_triggerduration*0.5,'PG')
    ##
        ##turn on raman for diagnostic purposes

    #exp.ground_aom_switch.profile(0,'off') #### dd
    ##
    # FORT is turned on for short period of time for imaging.
    exp.pointgrey_trigger_switch.profile(t2_PGcamera,'on')
    exp.pointgrey_trigger_switch.profile(t2_PGcamera+t_PG_triggerduration,'off')
    # if (t2_PGcamera+t_PG_FORT_ontime)<=t_FORT_loading:
    exp.fort_aom_switch.profile(t2_PGcamera,'on')
    exp.fort_dds.profile(t2_PGcamera,'on')
    exp.fort_aom_switch.profile(t2_PGcamera+t_PG_FORT_ontime,'off')
    exp.fort_dds.profile(t2_PGcamera+t_PG_FORT_ontime,'off')
    # else:
    #     logger.info("FORT image is taken after FORT transfer. Things may conflict")
    exp.FORT_NE_trigger_switch.profile(0,'off')
    exp.FORT_NE_trigger_switch.profile(t_NE_FORT_trigger_start,'on')
    exp.FORT_NE_trigger_switch.profile(t_NE_FORT_trigger_end,'off')
    # exp.ryd780a_aom_switch.profile(0,'off')
    # exp.ryd780a_dds.profile(0,'off')
    # exp.ryd780b_aom_switch.profile(0,'off')
    # exp.ryd780b_dds.profile(0,'off')
    # Ryd780A(10,170,'r2','r2')
    exp.ryd780a_aom_switch.profile(0,'on')
    exp.ryd780a_dds.profile(0,'r2')
    #exp.ryd780b_aom_switch.profile(0,'on')
    #exp.ryd780b_aom_switch.profile(0,'on')
    #exp.ryd780b_dds.profile(0,'r2')
    ## Turning this on intentinally
    exp.red_pointing_dds.profile(0,'off')
    #exp.red_pointing_aom_switch.profile(0,'off')
    exp.red_pointing_aom_switch.profile(0,'on')
    # Ryd 780a noise eater part
    exp.ryd780A_NE_trigger_switch.profile(0,'off')
    exp.ryd780A_NE_trigger_switch.profile(10,'on')
    exp.ryd780A_NE_trigger_switch.profile(15,'off')
    #Ryd780A(10,3,'r2','r2')
    # exp.ryd780b_aom_switch.profile(10,'on')
    # exp.ryd780b_dds.profile(10,'r2')
    # exp.ryd780b_aom_switch.profile(11,'off')
    # exp.ryd780b_dds.profile(11,'off')

    # UV switching
    exp.UV_trigger_switch.profile(0,'off')
    exp.UV_trigger_switch.profile(0.1,'on')
    exp.UV_trigger_switch.profile(0.1+t_UVpulse,'off')
    exp.MOT_scope_trigger_switch.profile(0,'off')
    exp.MOT_scope_trigger_switch.profile(140,'on')
    exp.MOT_scope_trigger_switch.profile(145,'off')
    exp.blue_pointing_dds.profile(0,'off')
    exp.blue_pointing_aom_switch.profile(0,'on')
    #exp.blue_pointing_aom_switch.profile(0,'off')

    # exp.scope_trigger_switch.profile(270,'on')
    # exp.scope_trigger_switch.profile(271,'off')
    exp.scope_trigger_switch.profile(140,'on')
    exp.scope_trigger_switch.profile(141,'off')
    exp.fort_aom_switch.profile(0,'off')
    exp.fort_dds.profile(0,'off')
    exp.op_dds.profile(0,'off')
    exp.op_aom_switch.profile(0,'off')
    exp.hf_aom_switch.profile(0,'on')
    exp.mot_3d_x_shutter_switch.profile(0,'on')
    exp.mot_3d_y_shutter_switch.profile(0,'on')
    exp.mot_3d_z1_shutter_switch.profile(0,'on')
    exp.repumper_shutter_switch.profile(0,'on')
    exp.mot_3d_z2_shutter_switch.profile(0,'on')
    exp.microwave_switch.profile(0,'off')
    exp.microwave_dds.profile(0,'off')

    ## 2D MOT Loading Phase
    exp.mot_3d_dds.profile(0,'MOT')
    exp.fort_dds.profile(0,'off')
    exp.mot_2d_dds.profile(0,'on')
    exp.mot_aom_switch.profile(0,'on')
    exp.mot_2d_aom_switch.profile(0,'on')
    #raman laser pulse for #
    exp.ground_aom_switch.profile(15,'on')
    exp.red_pointing_dds.profile(14,'r2')
    exp.red_pointing_aom_switch.profile(15,'on')
    #exp.red_pointing_aom_switch.profile(16,'off')
    exp.ground_aom_switch.profile(16,'off')
    exp.red_pointing_dds.profile(16,'off')
    ## 3D MOT Loading Phase
    exp.mot_2d_dds.profile(t_2DMOT_loading,'off') # turn off 2D MOT light
    exp.mot_2d_aom_switch.profile(t_2DMOT_loading,'off')
    exp.mot_3d_z2_shutter_switch.profile(t_2DMOT_loading,'off')# 2dmot shutters

    ## FORT Transfer Phase
    exp.fort_aom_switch.profile(t_FORT_loading,'on')
    exp.fort_dds.profile(t_FORT_loading,'on')
    # exp.fort_aom_switch.profile(t_3DMOT_cutoff-5,'on')
    # exp.fort_dds.profile(t_3DMOT_cutoff-5,'on')
    exp.camera.pulse_length=5#t_MOT_imaging_exposure # Changes HSDIO pulse width to control exposure
    t_readout_MOT=95
    exp.camera.take_shot(t_readout_MOT)
    exp.mot_3d_dds.profile(t_2DMOT_loading,'PGC')
    # AO(t_2DMOT_loading+5,0,0) # turns off quadrupole fields
    # AO(t_2DMOT_loading+5,1,0)
    AO(t_2DMOT_loading,0,0) # turns off quadrupole fields
    AO(t_2DMOT_loading,1,0)
    AO(t_2DMOT_loading,2,coil_driver_polarity*shimX_PGC) #X
    AO(t_2DMOT_loading,3,coil_driver_polarity*shimY_PGC) #Y
    AO(t_2DMOT_loading,4,coil_driver_polarity*shimZ_PGC) #Z
    # exp.mot_aom_switch.profile(t_2DMOT_loading-0.002,'off')
    # exp.mot_aom_switch.profile(t_2DMOT_loading+0.500,'on')
    ## Fall off Phase
    # AO(t_3DMOT_cutoff,2,coil_driver_polarity*-0.30) #X
    # AO(t_3DMOT_cutoff,3,coil_driver_polarity*-0.49) #Y
    # AO(t_3DMOT_cutoff,4,0) #Z
    # AO(t_3DMOT_cutoff,2,coil_driver_polarity*FOshimx) #X
    # AO(t_3DMOT_cutoff,3,coil_driver_polarity*FOshimy) #Y
    # AO(t_3DMOT_cutoff,4,FOshimz) #Z
    # AO(t_2DMOT_loading+5,2,coil_driver_polarity*shimX_RO) #X
    # AO(t_2DMOT_loading+5,3,coil_driver_polarity*shimY_RO) #Y
    # AO(t_2DMOT_loading+5,4,coil_driver_polarity*shimZ_RO) #Z
    exp.mot_aom_switch.profile(t_3DMOT_cutoff,'off')
    #exp.fort_dds.profile(111,'on')
    exp.hf_aom_switch.profile(t_3DMOT_cutoff,'off') #####
    AO(t_3DMOT_cutoff,7,0)

    ## Readout Phase, nominally from 140-145 ms
    # AO(130,2,coil_driver_polarity*shimX_PGC) #X
    # AO(130,3,coil_driver_polarity*shimY_PGC) #Y
    # AO(130,4,coil_driver_polarity*shimZ_PGC) #Z
    t_start=140
    t_end=t_start+t_readoutduration
    exp.camera.pulse_length=t_exposure_1st_atomshot # Changes HSDIO pulse width to control exposure
    exp.camera.take_shot(t_start-6)
    exp.fort_dds.profile(t_start,'low')
    exp.mot_3d_dds.profile(t_start,'PGC')
    exp.fort_aom_switch.profile(t_start-0.001,'off')
    readout2(t_start,t_readoutduration)
    exp.fort_aom_switch.profile(t_start+t_readoutduration+0.0012,'on')
    exp.fort_dds.profile(t_start+t_readoutduration+0.001,'on')
    exp.mot_aom_switch.profile(t_end+0.001,'off')
    AO(t_start,7,10) # Reumper VCA
    AO(t_end+0.2,7,0)

    #Polarization Gradient Cooling (PGC) phase, nominally from 145-150 ms
    #Doing chopping
    extension = 10
    # if t_PGC_duration>0:
    #     AO(145.2,2,coil_driver_polarity*shimX_PGC) #X PGC
    #     AO(145.2,3,coil_driver_polarity*shimY_PGC) #Y PGC
    #     AO(145.2,4,coil_driver_polarity*shimZ_PGC) #Z PGC
    #     # exp.mot_3d_x_shutter_switch.profile(150,'off')
    #     # exp.mot_3d_x_shutter_switch.profile(270,'on')
    #     # exp.mot_3d_y_shutter_switch.profile(150,'off')
    #     # exp.mot_3d_y_shutter_switch.profile(270,'on')
    #     # exp.mot_3d_z1_shutter_switch.profile(150,'off')
    #     # exp.mot_3d_z1_shutter_switch.profile(270,'on')
    #     # AO(165,2,coil_driver_polarity*shimX_RO) #X
    #     # AO(165,3,coil_driver_polarity*shimY_RO) #Y
    #     # AO(165,4,coil_driver_polarity*shimZ_RO) #Z
    #     t_start=170
    #     t_end=t_start+t_PGC_duration
    #     # exp.camera.pulse_length=t_exposure_1st_atomshot # Changes HSDIO pulse width to control exposure
    #     # exp.camera.take_shot(t_start)
    #     exp.fort_dds.profile(t_start,'low')
    #     # exp.fort_dds.profile(t_start,'low')
    #     # exp.fort_dds.profile(t_end+5,'on')
    #     exp.mot_3d_dds.profile(t_start,'PGC')
    #     # exp.mot_3d_dds.profile(t_start,'Blowaway')
    #     #exp.fort_dds.profile(t_start+3*t_PGC_duration/4,'science') # lowered FORT during PGC
    #     #exp.fort_dds.profile(t_end+0.1,'on')
    #     exp.fort_aom_switch.profile(t_start-0.001,'off')
    #     readout2(t_start,t_PGC_duration)
    #     exp.fort_aom_switch.profile(t_start+t_PGC_duration+0.0012,'on')
    #     exp.fort_dds.profile(t_start+t_PGC_duration+0.001,'on')
    #     # exp.mot_aom_switch.profile(t_start,'off')
    #     exp.mot_aom_switch.profile(t_end+0.001,'off')
    #     AO(t_start,7,10) # Reumper VCA
    #     AO(t_end+0.2,7,0)
        # exp.hf_aom_switch.profile(t_start,'on')
        # exp.hf_aom_switch.profile(t_end+0.2,'off') ###
    # exp.mot_aom_switch.profile(170+t_PGC_duration+0.005,'off')
    # if only chopping FORT, e.g. for trap frequency measurement
    # exp.mot_3d_x_shutter_switch.profile(t_x_shutter_open,'off')
    # exp.mot_3d_x_shutter_switch.profile(t_x_shutter_close+extension,'on')
    # exp.mot_3d_y_shutter_switch.profile(t_y_shutter_open,'off')
    # exp.mot_3d_y_shutter_switch.profile(t_y_shutter_close+extension,'on')
    # exp.mot_3d_z1_shutter_switch.profile(t_z1_shutter_open,'off')
    # exp.mot_3d_z1_shutter_switch.profile(t_z1_shutter_close+extension,'on')
    #exp.mot_aom_switch.profile(159.9,'off')
    # t_start=160
    # t_end=t_start+t_PGC_duration

    #for FORT trap frequency (parametric heating) measurement:
    # if t_PGC_duration>0:
    #     readout2(t_start,t_PGC_duration)
    # exp.fort_dds.profile(t_end+0.1,'on')
    # if t_PGC_duration>0:
    #     timesteps = 1/(RO_chopfreq*1000)
    #     numsteps = t_PGC_duration/timesteps
    #     for x in range(0,int(numsteps)):
    #         exp.fort_dds.profile(t_start+x*timesteps,'science')
    #         exp.fort_dds.profile(t_start+x*timesteps+timesteps/2,'on')

    ## Optical Pumping Phase
    # AO(155,2,coil_driver_polarity*shimX_OP) #X
    # AO(155,3,coil_driver_polarity*shimY_OP) #Y
    # AO(155,4,coil_driver_polarity*shimZ_OP) #Z
    # AO(155,7,0) # repumper attenuator. repumper turned off.

    # AO(157,2,coil_driver_polarity*shimX_OP) #X
    # AO(157,3,coil_driver_polarity*shimY_OP) #Y
    # AO(157,4,coil_driver_polarity*shimZ_OP) #Z
    # AO(157,7,0) # repumper attenuator. repumper turned off.
    #
    # t_start=160
    # t_end=t_start+t_op+t_depump
    # # t_start=170-t_op-t_depump
    # # t_end=170
    # # AO(t_start,7,10)
    # # AO(t_start+t_op,7,0)
    # #exp.fort_dds.profile(t_start,'science')
    #
    # exp.op_dds.profile(t_start,'on')
    # exp.op_dds.profile(t_end,'off')
    # exp.hf_aom_switch.profile(t_start,'on')
    # exp.hf_aom_switch.profile(t_start+t_op,'off')
    # AO(t_start,7,10)
    # AO(t_start+t_op,7,0)
    # # exp.camera.pulse_length=t_op # Changes HSDIO pulse width to control exposure
    # # exp.camera.take_shot(t_start)
    # opticalpumping(t_start,t_end-t_start)


    # exp.ryd780b_dds.profile(t_start,'r2')
    # exp.red_pointing_dds.profile(t_start,'r2')
    # exp.red_pointing_dds.profile(t_end,'off')
    # exp.ryd780b_dds.profile(t_end,'off')
    # exp.op_dds.profile(t_start,'off')
    # #exp.op_dds.profile(t_end,'off')
    # #Ryd780B(t_start,t_end-t_start,'r2','r2')
    # exp.hf_aom_switch.profile(t_start,'on')
    # exp.hf_aom_switch.profile(t_end-t_depump,'off')
    # opticalpumping2(t_start,t_end-t_start)
    #
    # AO(165,2,coil_driver_polarity*shimX_SCI) #X
    # AO(165,3,coil_driver_polarity*shimY_SCI) #Y
    # AO(165,4,coil_driver_polarity*shimZ_SCI) #Z
    # exp.mot_3d_x_shutter_switch.profile(t_x_shutter_open,'off')
    # exp.mot_3d_x_shutter_switch.profile(t_x_shutter_close,'on')
    # exp.mot_3d_y_shutter_switch.profile(t_y_shutter_open,'off')
    # exp.mot_3d_y_shutter_switch.profile(t_y_shutter_close,'on')
    # exp.mot_3d_z1_shutter_switch.profile(t_z1_shutter_open,'off')
    # exp.mot_3d_z1_shutter_switch.profile(t_z1_shutter_close,'on')
 # for specific purposes
    # Microwave(t_science+extension-4,t_microwave)
    #
    # # Science Phase 170 - 175 ms. t_science=170
    # AO(t_science+extension-3,2,coil_driver_polarity*shimX_PGC) #X PGC
    # AO(t_science+extension-3,3,coil_driver_polarity*shimY_PGC) #Y PGC
    # AO(t_science+extension-3,4,coil_driver_polarity*shimZ_PGC) #Z PGC
    # reduce FORT trap depth during science phase
    # exp.fort_dds.profile(t_science,'science')
    # exp.fort_dds.profile(t_science+5,'on')
    #RamanRamsey(t_science, t_gap, t_raman, 'addressing', 'r2')
    #raman(t_science+0.001,t_raman,'r2')
    #FORTdrop(t_science+0.001, t_FORTdrop)
    ##FORTdrop(t_science+t_microwave, t_FORTdrop)
    #MicrowaveRamsey(t_science,t_gap,t_microwavepiover2)
    #MicrowaveRamsey_and_780A(t_science, t_gap, t_microwavepiover2, 'addressing', 'r2')
    #MicrowaveRamsey_and_780B(t_science, t_gap, t_microwavepiover2, 'addressing', 'r2')
    #Ryd780B(t_science,t_gap,'PG','r3')
    # Ryd780B(t_science,t_gap,'addressing','r3')
    #SpinEcho(t_science,t_gap,t_microwavepiover2)
    #Microwave(t_science+extension,t_microwave)
   ##Microwave(t_science,t_microwave) # Microwave for Ryd780B
    #Ryd780A(t_science+0.001,t_Ryd780A,'r2','r2')
    ##Ryd780B(t_science+t_microwave+0.001,t_Ryd780B,'r2','r2')
    #Ryd780A(t_science-0.005,0.1,'r2','r2')
    #Ryd780A_pulsed(t, cycle_time, pointing_profile, intensity_profile, pulse_ontime, num_of_pulses): # region_profile example: 'r2'
    #Ryd780A_pulsed(t_science, 0.01, 'r2', 'r2', 0.0008, 6)
    #Ryd780A_Ramsey(t_science, t_Rydberg_gap, t_Ryd780A_piover2, 'r2', 'r2')
    #Ryd780A_leadtime(t_science,0.005,t_Ryd780A,'r2','r2')

    #Blue480(t_science, t_blueon,'r2')
    #Microwave(t_science+t_FORTdrop+0.001,1) # Rydberg killing microwave pulse.
    #Blue480(1,200,'r2')


    # exp.red_pointing_dds.profile(175,'off')
    # exp.red_pointing_aom_switch.profile(175,'off')
    # #exp.red_pointing_aom_switch.profile(175,'on')
    #
    ## Blow-away Phase 176ms
    FORTdrop(170+extension, t_FORTdrop)
    AO(175+extension,0,coil_driver_polarity*-0.1)
    AO(175+extension,1,coil_driver_polarity*0.1)
    AO(175+extension,2, coil_driver_polarity*shimX_BA) #X
    AO(175+extension,3,coil_driver_polarity*shimY_BA) #Y
    AO(175+extension,4,coil_driver_polarity*shimZ_BA) #Z

    t_start=176+extension
    t_end=t_start+t_BA
    exp.fort_dds.profile(t_start,'on')
    exp.mot_3d_dds.profile(t_start,'Blowaway')
    t_pulsewidth=0.001*2
    t_period=0.001*4
    for i in range(int(round((t_end-t_start)/t_period))):
        exp.mot_aom_switch.profile(t_start+i*t_period+t_BA_offset,'on')
        exp.mot_aom_switch.profile(t_start+i*t_period+t_pulsewidth+t_BA_offset,'off')

    for i in range(int(round((t_end-t_start)/t_period))):
        exp.fort_aom_switch.profile(t_start+i*t_period,'off')
        exp.fort_aom_switch.profile(t_start+i*t_period+t_pulsewidth,'on')

    exp.fort_dds.profile(t_end,'on')


    ## Readout Phase
    AO(180+extension,0,0) # turn off quadrupole fields
    AO(180+extension,1,0)
    AO(180+extension,2, coil_driver_polarity*shimX_RO) #X
    AO(180+extension,3, coil_driver_polarity*shimY_RO) #Y
    AO(180+extension,4, coil_driver_polarity*shimZ_RO) #Z
    t_readout_2nd=195+extension
    t_start=t_readout_2nd
    exp.fort_dds.profile(t_start,'on')
    exp.mot_3d_dds.profile(t_start,'RO')
    exp.camera.pulse_length=t_exposure
    exp.camera.take_shot(t_start)
    readout(t_start,t_readoutduration)
    t_end=t_start+t_readoutduration
    #exp.mot_aom_switch.profile(t_end+0.001,'off') ###
    AO(t_start,7,10) # Turn on repumper. Sets rf attenuator voltage to 10V
    exp.hf_aom_switch.profile(t_start,'on')
    exp.hf_aom_switch.profile(t_start+exp.camera.pulse_length,'off')
    AO(t_start+exp.camera.pulse_length,7,0)
    #Trying to see if making it the same as above affects the timing
    #exp.hf_aom_switch.profile(t_end,'off')
    #AO(t_end,7,0)

    #exp.fort_aom_switch.profile(t_readout_2nd+exp.camera.pulse_length,'off')
    exp.fort_dds.profile(t_readout_2nd+exp.camera.pulse_length,'off')

    ## Blue imaging
    # Blue480(t_start_blue_imaging,t_blue_exposure,'r2')

    exp.camera.pulse_length=t_blue_exposure # Changes HSDIO pulse width to control exposure
    t_readout_3rd=205+extension
    exp.camera.take_shot(t_readout_3rd + extension)

    ############################## End of normal experiment #######################################################


elif ExpMode==1:
    ####### Laser Cw mode (expmode code 1) #############
    ## Coil currents are same as actual experiment cycle to keep thermal loads as close as possible.
    ## If you need continuous MOT loading, go to expmode code 2
    # Camera will not take any pictures to prevent accidental damage due to CW lasers on.
    #print "Not Implemented"
    ## Initilization
        #for i in range(5):
        #    AO(0,i,0)
        AO(0,0,coil_driver_polarity*I_Q1)
        AO(0,1,coil_driver_polarity*I_Q2)
        AO(0,2,coil_driver_polarity*ShimX_Loading) #X
        AO(0,3,coil_driver_polarity*ShimY_Loading) #Y
        AO(0,4,coil_driver_polarity*ShimZ_Loading) #Z
        AO(0,5,coil_driver_polarity*-2.2)
        AO(0,6,coil_driver_polarity*2.8)
        AO(0,7,10)

        # UV switching
        exp.UV_trigger_switch.profile(0,'off')
        exp.UV_trigger_switch.profile(0.1,'on')
        exp.UV_trigger_switch.profile(0.1+1500,'off')
        #define MOT scope drigger to be off
        exp.MOT_scope_trigger_switch.profile(0,'off')
        #define unneeded dds profiles
        exp.blue_pointing_dds.profile(0,'off')
        exp.blue_pointing_aom_switch.profile(0,'on')
        #exp.blue_pointing_aom_switch.profile(0,'off')
        exp.scope_trigger_switch.profile(140,'on')
        exp.scope_trigger_switch.profile(141,'off')
        exp.fort_aom_switch.profile(0,'off')
        exp.fort_dds.profile(0,'off')
        exp.op_dds.profile(0,'off')
        exp.op_aom_switch.profile(0,'off')
        exp.hf_aom_switch.profile(0,'on')
        exp.microwave_switch.profile(0,'off')
        exp.microwave_dds.profile(0,'off')

        #open mot shutters
        exp.mot_3d_x_shutter_switch.profile(0,'on')
        exp.mot_3d_y_shutter_switch.profile(0,'on')
        exp.mot_3d_z1_shutter_switch.profile(0,'on')
        exp.mot_3d_z2_shutter_switch.profile(0,'on')#switched polarity
        exp.repumper_shutter_switch.profile(0,'on')

        ## 2D MOT Loading Phase
        exp.mot_3d_dds.profile(0,'MOT')
        exp.mot_2d_dds.profile(0,'on')
        exp.mot_aom_switch.profile(0,'on')
        exp.mot_2d_aom_switch.profile(0,'on')

        ## 3D MOT Loading Phase
        motoff = 2000
        # turn off 2D MOT light 1 full second early and close shutters
        exp.mot_2d_dds.profile(motoff-500,'off')
        exp.mot_2d_aom_switch.profile(motoff-500,'off')
        exp.mot_3d_z2_shutter_switch.profile(motoff-500,'off')
        #early mot image
        exp.camera.pulse_length=0.2#t_MOT_imaging_exposure # Changes HSDIO pulse width to control exposure
        t_readout_MOT=1995
        exp.camera.take_shot(t_readout_MOT)
        AO(motoff,0,0) # turns off quadrupole fields
        AO(motoff,1,0)
        exp.mot_aom_switch.profile(motoff+5,'off')
        #exp.mot_3d_dds.profile(motoff,'PGC')
        exp.hf_aom_switch.profile(motoff+5,'off') #####
        #AO(motoff,7,0)
        cameratime = motoff+0.004
        exp.MOT_scope_trigger_switch.profile(cameratime,'on')
        exp.MOT_scope_trigger_switch.profile(cameratime+3,'off')
        exp.camera.pulse_length=0.2#t_MOT_imaging_exposure # Changes HSDIO pulse width to control exposure
        # exp.camera.take_shot(cameratime+t_gap)
        exp.camera.take_shot(cameratime-0.02)


        # exp.mot_aom_switch.profile(motoff+t_gap,'on')
        # exp.mot_3d_dds.profile(motoff,'PGC')
        # exp.hf_aom_switch.profile(motoff+t_gap,'on') #####
        # AO(motoff+t_gap,7,10)
        # exp.mot_aom_switch.profile(motoff+t_gap+0.2,'off')
        # exp.hf_aom_switch.profile(motoff+t_gap+0.2,'off') #####
        # AO(motoff+t_gap+0.2,7,0)

    ## End of expmode 1

elif ExpMode==2:
    ####### Continous MOT loading mode (expmode code 2) #############
    # FORT is also on.
    # Camera will take pictures

    ## Initilization
        AO(0,0,coil_driver_polarity*I_Q1)
        AO(0,1,coil_driver_polarity*I_Q2)
        AO(0,2,coil_driver_polarity*ShimX_Loading) #X
        AO(0,3,coil_driver_polarity*ShimY_Loading) #Y
        AO(0,4,coil_driver_polarity*ShimZ_Loading) #Z
        # AO(0,2,coil_driver_polarity*shimX_RO) #X
        # AO(0,3,coil_driver_polarity*shimY_RO) #Y
        # AO(0,4,coil_driver_polarity*shimZ_RO) #Z
        AO(0,5,coil_driver_polarity*-2.2)
        AO(0,6,coil_driver_polarity*2.8)
        AO(0,7,10)
        # for i in range(20):
        #     AO(i*10,0,coil_driver_polarity*I_Q1*((2000-(i*10))/2000))
        #     AO(i*10,1,coil_driver_polarity*I_Q2*((2000-(i*10))/2000))
        # for i in range(20):
        #     AO(i*10+200,0,coil_driver_polarity*I_Q1*((1800+(i*10))/2000))
        #     AO(i*10+200,1,coil_driver_polarity*I_Q2*((1800+(i*10))/2000))
        AO(100,0,coil_driver_polarity*I_Q1)
        AO(100,1,coil_driver_polarity*I_Q2)
        AO(100,2,coil_driver_polarity*ShimX_Loading) #X
        AO(100,3,coil_driver_polarity*ShimY_Loading) #Y
        AO(100,4,coil_driver_polarity*ShimZ_Loading) #Z
        # AO(0,2,coil_driver_polarity*shimX_RO) #X
        # AO(0,3,coil_driver_polarity*shimY_RO) #Y
        # AO(0,4,coil_driver_polarity*shimZ_RO) #Z
        AO(100,5,coil_driver_polarity*-2.2)
        AO(100,6,coil_driver_polarity*2.8)
        AO(100,7,10)

        #looking for molassis
        # AO(0,0,coil_driver_polarity*I_Q1*0)
        # AO(0,1,coil_driver_polarity*I_Q2*0)
        # AO(0,2,coil_driver_polarity*shimX_RO) #X
        # AO(0,3,coil_driver_polarity*shimY_RO) #Y
        # AO(0,4,coil_driver_polarity*shimZ_RO) #Z
        # # AO(0,2,coil_driver_polarity*shimX_RO) #X
        # # AO(0,3,coil_driver_polarity*shimY_RO) #Y
        # # AO(0,4,coil_driver_polarity*shimZ_RO) #Z
        # AO(0,5,coil_driver_polarity*-2.2)
        # AO(0,6,coil_driver_polarity*2.8)
        # AO(0,7,10)
        # # for i in range(20):
        # #     AO(i*10,0,coil_driver_polarity*I_Q1*((2000-(i*10))/2000))
        # #     AO(i*10,1,coil_driver_polarity*I_Q2*((2000-(i*10))/2000))
        # # for i in range(20):
        # #     AO(i*10+200,0,coil_driver_polarity*I_Q1*((1800+(i*10))/2000))
        # #     AO(i*10+200,1,coil_driver_polarity*I_Q2*((1800+(i*10))/2000))
        # AO(100,0,coil_driver_polarity*I_Q1*0)
        # AO(100,1,coil_driver_polarity*I_Q2*0)
        # AO(100,2,coil_driver_polarity*shimX_RO) #X
        # AO(100,3,coil_driver_polarity*shimY_RO) #Y
        # AO(100,4,coil_driver_polarity*shimZ_RO) #Z
        # # AO(0,2,coil_driver_polarity*shimX_RO) #X
        # # AO(0,3,coil_driver_polarity*shimY_RO) #Y
        # # AO(0,4,coil_driver_polarity*shimZ_RO) #Z
        # AO(100,5,coil_driver_polarity*-2.2)
        # AO(100,6,coil_driver_polarity*2.8)
        # AO(100,7,10)

        exp.ground_aom_switch.profile(0,'on')
        #exp.ground_aom_switch.profile(0,'off') #### dd
        exp.ryd780a_aom_switch.profile(0,'on')
        exp.ryd780a_dds.profile(0,'r2')
        exp.ryd780b_aom_switch.profile(0,'on')
        exp.ryd780b_dds.profile(0,'r2')
        exp.red_pointing_dds.profile(0,'r2')
        exp.red_pointing_aom_switch.profile(0,'on')
        # to turn blue off, please uncomment
        # exp.blue_pointing_dds.profile(0,'off')
        # exp.blue_pointing_aom_switch.profile(0,'off')

        # to turn blue on all the time
        exp.blue_pointing_dds.profile(0,'r2')
        exp.blue_pointing_aom_switch.profile(0,'on')

        exp.fort_aom_switch.profile(0,'on')
        exp.fort_dds.profile(0,'on')

        exp.MOT_scope_trigger_switch.profile(0,'off')
        exp.MOT_scope_trigger_switch.profile(140,'on')
        exp.MOT_scope_trigger_switch.profile(145,'off')
        exp.mot_3d_z2_shutter_switch.profile(0,'on')#switched polarity
        # exp.mot_3d_x_shutter_switch.profile(t_x_shutter_open,'off')
        # exp.mot_3d_x_shutter_switch.profile(t_x_shutter_close,'on')
        # exp.mot_3d_y_shutter_switch.profile(t_y_shutter_open,'off')
        # exp.mot_3d_y_shutter_switch.profile(t_y_shutter_close,'on')
        # exp.mot_3d_z1_shutter_switch.profile(t_z1_shutter_open,'off')
        # exp.mot_3d_z1_shutter_switch.profile(t_z1_shutter_close,'on')
        exp.scope_trigger_switch.profile(170,'on')
        exp.scope_trigger_switch.profile(171,'off')
        exp.op_dds.profile(0,'on')
        exp.op_aom_switch.profile(0,'on')
        exp.hf_aom_switch.profile(0,'on')
        exp.mot_3d_x_shutter_switch.profile(0,'on')
        exp.mot_3d_y_shutter_switch.profile(0,'on')
        exp.mot_3d_z1_shutter_switch.profile(0,'on')
        exp.repumper_shutter_switch.profile(0,'on')
        exp.microwave_switch.profile(0,'on')
        exp.microwave_dds.profile(0,'on')
        # exp.microwave_switch.profile(0,'off')
        # exp.microwave_dds.profile(0,'off')

        ## 2D MOT Loading Phase
        exp.mot_3d_dds.profile(0,'MOT')
    #    exp.fort_dds.profile(0,'off')
        exp.mot_2d_dds.profile(0,'on')
        exp.mot_aom_switch.profile(0,'on')
        exp.mot_2d_aom_switch.profile(0,'on')

        t_start=50
        exp.camera.take_shot(t_start)

        t_readout_2nd=110
        exp.camera.take_shot(t_readout_2nd)

        ## Blue imaging
        #Blue480(t_start_blue_imaging,t_blue_exposure,'off')
        # exp.camera.pulse_length=t_blue_exposure # Changes HSDIO pulse width to control exposure
        t_readout_3rd=170
        exp.camera.take_shot(t_readout_3rd)
        # exp.ryd780a_aom_switch.profile(t2_PGcamera,'on')
        # exp.ryd780a_dds.profile(t2_PGcamera,'r2')

    ############################## End of mode 2,  Shutter calibration #######################################################

else:
    print "Undefined Experiment mode : {}".format(ExpMode)
