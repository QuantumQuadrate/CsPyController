
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
    phases = [[0.31, 0.66], [0.2, 0.7]]
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

def raman(t,duration,pointing_profile):
    """Raman beam control to drive ground hyperfine clock transition |2,0> <-> |1,0> """
    if t>0 and duration >0: #make sure timings are valid
        exp.ground_aom_switch.profile(t,'on')
        exp.ground_aom_switch.profile(t+duration,'off')
        exp.red_pointing_aom_switch.profile(t,'on')
        exp.red_pointing_aom_switch.profile(t+duration,'off')
        exp.red_pointing_dds.profile(t,pointing_profile) # point to the target_region. example 'r2'
        exp.red_pointing_dds.profile(t+duration,'off')
    else:
        print "make sure your timings are valid"

def prepareF1(t,duration):
    """This function will leave MOT light on without repumper so atoms are depopulate from F=1 and pumped into F=1"""
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
        exp.red_pointing_aom_switch.profile(t+duration,'off')
        exp.ryd780a_aom_switch.profile(t,'on')
        exp.ryd780a_aom_switch.profile(t+duration,'off')

def Ryd780A_pulsed(t, cycle_time, pointing_profile, intensity_profile, pulse_ontime, num_of_pulses): # region_profile example: 'r2'
    t_red_delay=0.25*0.001
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

def Blue480(t, duration, pointing_profile):
    exp.blue_pointing_dds.profile(t, pointing_profile)
    exp.blue_pointing_aom_switch.profile(t, 'on')
    exp.blue_pointing_dds.profile(t+duration,'off')
    exp.blue_pointing_aom_switch.profile(t+duration,'off')

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
    Ryd780A(t1_PGcamera,t_PG_triggerduration,'PG','PG')
    ##

    ##
    # FORT is turned on for short period of time for imaging.
    exp.pointgrey_trigger_switch.profile(t2_PGcamera,'on')
    exp.pointgrey_trigger_switch.profile(t2_PGcamera+t_PG_triggerduration,'off')
    # if (t2_PGcamera+t_PG_FORT_ontime)<=t_FORT_loading:
    exp.fort_aom_switch.profile(t2_PGcamera,'on')
    exp.fort_dds.profile(t2_PGcamera,'low')
    exp.fort_aom_switch.profile(t2_PGcamera+t_PG_FORT_ontime,'off')
    exp.fort_dds.profile(t2_PGcamera+t_PG_FORT_ontime,'off')
    # else:
    #     logger.info("FORT image is taken after FORT transfer. Things may conflict")
    exp.FORT_NE_trigger_switch.profile(0,'off')
    exp.FORT_NE_trigger_switch.profile(t_NE_FORT_trigger_start,'on')
    exp.FORT_NE_trigger_switch.profile(t_NE_FORT_trigger_end,'off')
    exp.ryd780a_aom_switch.profile(0,'off')
    exp.ryd780a_dds.profile(0,'off')
    exp.red_pointing_dds.profile(0,'off')
    exp.red_pointing_aom_switch.profile(0,'off')
    # Ryd 780a noise eater part
    #Ryd780A(10,170,'r2','r2')
    exp.ryd780A_NE_trigger_switch.profile(0,'off')
    exp.ryd780A_NE_trigger_switch.profile(10,'on')
    exp.ryd780A_NE_trigger_switch.profile(15,'off')
    Ryd780A(10,3,'r2','r2')

    exp.MOT_scope_trigger_switch.profile(0,'off')
    exp.MOT_scope_trigger_switch.profile(140,'on')
    exp.MOT_scope_trigger_switch.profile(145,'off')
    exp.blue_pointing_dds.profile(0,'off')
    exp.blue_pointing_aom_switch.profile(0,'off')

    exp.scope_trigger_switch.profile(170,'on')
    exp.scope_trigger_switch.profile(171,'off')
    exp.fort_aom_switch.profile(0,'off')
    exp.fort_dds.profile(0,'off')
    exp.op_dds.profile(0,'off')
    exp.op_aom_switch.profile(0,'off')
    exp.hf_aom_switch.profile(0,'on')
    exp.mot_3d_x_shutter_switch.profile(0,'on')
    exp.mot_3d_y_shutter_switch.profile(0,'on')
    exp.mot_3d_z1_shutter_switch.profile(0,'on')
    exp.repumper_shutter_switch.profile(0,'on')
    exp.microwave_switch.profile(0,'off')
    exp.microwave_dds.profile(0,'off')
    exp.ground_aom_switch.profile(0,'off') #### dd

    ## 2D MOT Loading Phase
    exp.mot_3d_dds.profile(0,'MOT')
    exp.fort_dds.profile(0,'off')
    exp.mot_2d_dds.profile(0,'on')
    exp.mot_aom_switch.profile(0,'on')
    exp.mot_2d_aom_switch.profile(0,'on')

    ## 3D MOT Loading Phase
    exp.mot_2d_dds.profile(t_2DMOT_loading,'off') # turn off 2D MOT light
    exp.mot_2d_aom_switch.profile(t_2DMOT_loading,'off')

    AO(t_2DMOT_loading+5,0,0) # turns off quadrupole fields
    AO(t_2DMOT_loading+5,1,0)

    ## FORT Transfer Phase
    exp.fort_aom_switch.profile(t_FORT_loading,'on')
    exp.fort_dds.profile(t_FORT_loading,'on')
    exp.camera.pulse_length=5#t_MOT_imaging_exposure # Changes HSDIO pulse width to control exposure
    t_readout_MOT=100
    exp.camera.take_shot(t_readout_MOT)
    exp.camera.pulse_length=t_exposure # Changes HSDIO pulse width to control exposure
    ## Fall off Phase
    AO(t_3DMOT_cutoff,2,coil_driver_polarity*-0.30) #X
    AO(t_3DMOT_cutoff,3,coil_driver_polarity*-0.49) #Y
    AO(t_3DMOT_cutoff,4,0) #Z
    exp.mot_aom_switch.profile(t_3DMOT_cutoff,'off')
    exp.hf_aom_switch.profile(t_3DMOT_cutoff,'off') #####
    AO(t_3DMOT_cutoff,7,0)

    ## Readout Phase, nominally from 140-145 ms
    AO(130,2,coil_driver_polarity*shimX_RO) #X
    AO(130,3,coil_driver_polarity*shimY_RO) #Y
    AO(130,4,coil_driver_polarity*shimZ_RO) #Z
    t_start=140
    t_leadtime=0
    exp.mot_3d_dds.profile(t_start,'RO')
    exp.camera.take_shot(t_start)
    exp.mot_3d_dds.profile(t_start+t_readoutduration,'PGC')
    #readout(t_start,t_leadtime+t_readoutduration)
    readout(t_start,t_leadtime+t_readoutduration+t_PGC_duration)
    t_end=t_start+t_readoutduration+t_leadtime
    AO(t_start,7,10)
    exp.hf_aom_switch.profile(t_start,'on')
    exp.hf_aom_switch.profile(t_end+t_PGC_duration+0.2,'off') ###
    AO(t_end+t_PGC_duration+0.2,7,0)
    prepareF1(t_end+0.3,t_F1prepare)

    #Poliarization Gradient Cooling (PGC) phase, nominally from 145-150 ms
    #Doing chopping

    # t_start=145.3
    # t_end=t_start+t_PGC_duration
    # exp.mot_3d_dds.profile(t_start,'PGC')
    # exp.fort_dds.profile(t_start,'science') # lowered FORT during PGC
    # exp.fort_dds.profile(t_start+4,'on')

    # readout(t_start,t_end)
    # exp.mot_aom_switch.profile(t_start,'on')
    # exp.mot_aom_switch.profile(t_end,'off')
    # AO(t_start,7,10) # Reumper VCA
    # AO(t_end+0.2,7,0)
    # exp.hf_aom_switch.profile(t_start,'on')
    # exp.hf_aom_switch.profile(t_end+0.2,'off') ###

    ## Optical Pumping Phase

    AO(150,2,coil_driver_polarity*shimX_OP) #X
    AO(150,3,coil_driver_polarity*shimY_OP) #Y
    AO(150,4,coil_driver_polarity*shimZ_OP) #Z
    AO(150,7,0) # repumper attenuator. repumper turned off.

    t_start=160
    t_end=t_start+t_op+t_depump
    AO(t_start,7,10)
    AO(t_start+t_op,7,0)

    exp.op_dds.profile(t_start,'on')
    exp.op_dds.profile(t_end,'off')
    exp.hf_aom_switch.profile(t_start,'on')
    exp.hf_aom_switch.profile(t_start+t_op,'off')
    AO(t_start,7,10)
    AO(t_start+t_op,7,0)
    opticalpumping(t_start,t_end-t_start)

    exp.mot_3d_x_shutter_switch.profile(t_x_shutter_open,'off')
    exp.mot_3d_x_shutter_switch.profile(t_x_shutter_close,'on')
    exp.mot_3d_y_shutter_switch.profile(t_y_shutter_open,'off')
    exp.mot_3d_y_shutter_switch.profile(t_y_shutter_close,'on')
    exp.mot_3d_z1_shutter_switch.profile(t_z1_shutter_open,'off')
    exp.mot_3d_z1_shutter_switch.profile(t_z1_shutter_close,'on')

    ## Science Phase 170 - 175 ms. t_science=170

    # reduce FORT trap depth during science phase
    exp.fort_dds.profile(t_science,'science')
    exp.fort_dds.profile(t_science+7,'on')
    #raman(t_science,t_raman,'r2')
    #FORTdrop(t_science-0.001, t_FORTdrop)
    #MicrowaveRamsey(t_science,t_gap,t_microwavepiover2)
    #Microwave(t_science,t_microwave)
    #Ryd780A(t_science,t_Ryd780A,'r2','r2')
    #Ryd780A_pulsed(t, cycle_time, pointing_profile, intensity_profile, pulse_ontime, num_of_pulses): # region_profile example: 'r2'
    #Ryd780A_pulsed(t_science, 0.01, 'r2', 'r2', 0.001, 10)
    #Blue480(t_science-0.001, t_blueon,'r2')
    #Blue480(1,200,'r2')
    MicrowaveRamsey_and_780A(t_science, t_gap, t_microwavepiover2, 'addressing', 'r2')

    exp.red_pointing_dds.profile(175,'off')
    exp.red_pointing_aom_switch.profile(175,'off')

    ## Blow-away Phase 176ms

    AO(175,0,coil_driver_polarity*-0.1)
    AO(175,1,coil_driver_polarity*0.1)
    AO(175,2, coil_driver_polarity*shimX_BA) #X
    AO(175,3,coil_driver_polarity*shimY_BA) #Y
    AO(175,4,coil_driver_polarity*shimZ_BA) #Z

    t_start=176
    t_end=t_start+t_BA
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
    AO(180,0,0) # turn off quadrupole fields
    AO(180,1,0)
    AO(180,2, coil_driver_polarity*shimX_RO) #X
    AO(180,3, coil_driver_polarity*shimY_RO) #Y
    AO(180,4, coil_driver_polarity*shimZ_RO) #Z
    t_readout_2nd=195

    exp.mot_3d_dds.profile(t_readout_2nd,'RO')
    exp.camera.take_shot(t_readout_2nd)
    t_start=t_readout_2nd
    readout(t_start,5)
    t_end=t_start+t_readoutduration
    AO(t_readout_2nd,7,10) # Turn on repumper. Sets rf attenuator voltage to 10V
    exp.hf_aom_switch.profile(t_readout_2nd,'on')
    exp.hf_aom_switch.profile(t_readout_2nd+exp.camera.pulse_length,'off')
    AO(t_readout_2nd+exp.camera.pulse_length,7,0)

    #exp.fort_aom_switch.profile(t_readout_2nd+exp.camera.pulse_length,'off')
    exp.fort_dds.profile(t_readout_2nd+exp.camera.pulse_length,'off')

    ## Blue imaging
    Blue480(t_start_blue_imaging,t_blue_exposure,'r2')

    exp.camera.pulse_length=t_blue_exposure # Changes HSDIO pulse width to control exposure
    t_readout_3rd=205
    exp.camera.take_shot(t_readout_3rd)

    ############################## End of normal experiment #######################################################


elif ExpMode==1:
    ####### Laser Cw mode (expmode code 1) #############
    ## Coil currents are same as actual experiment cycle to keep thermal loads as close as possible.
    ## If you need continuous MOT loading, go to expmode code 2
    # Camera will not take any pictures to prevent accidental damage due to CW lasers on.
    print "Not Implemented"


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
        AO(0,5,coil_driver_polarity*-2.2)
        AO(0,6,coil_driver_polarity*2.8)
        AO(0,7,10)

        AO(100,0,coil_driver_polarity*I_Q1)
        AO(100,1,coil_driver_polarity*I_Q2)
        AO(100,2,coil_driver_polarity*ShimX_Loading) #X
        AO(100,3,coil_driver_polarity*ShimY_Loading) #Y
        AO(100,4,coil_driver_polarity*ShimZ_Loading) #Z
        AO(100,5,coil_driver_polarity*-2.2)
        AO(100,6,coil_driver_polarity*2.8)
        AO(100,7,10)

    #
        exp.ryd780a_aom_switch.profile(0,'on')
        exp.ryd780a_dds.profile(0,'r2')
        exp.red_pointing_dds.profile(0,'r2')
        exp.red_pointing_aom_switch.profile(0,'on')
        exp.blue_pointing_dds.profile(0,'off')
        exp.blue_pointing_aom_switch.profile(0,'off')
        exp.fort_aom_switch.profile(0,'on')
        exp.fort_dds.profile(0,'on')

        exp.MOT_scope_trigger_switch.profile(0,'off')
        exp.MOT_scope_trigger_switch.profile(140,'on')
        exp.MOT_scope_trigger_switch.profile(145,'off')

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
        exp.ground_aom_switch.profile(0,'off') #### dd

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
