
"""These are the waveform functions for the Rubidium project.

This file is not imported to CsPy. You'll have to copy-paste into the built-in editor of functional waveform definition.

ExpMode
0: Normal experiments
1: Laser continuously on. Shutters and coils are driven same as normal experiments.
2: Continuosly loading a MOT. Watch out for coil temperatures!

"""


import exp_functional_waveforms.functional_waveforms_rb as Rb

HSDIO = experiment.LabView.HSDIO.add_transition
<<<<<<< HEAD
HSDIO_repeat = experiment.LabView.HSDIO.add_repeat
=======
>>>>>>> RbDev3
AO = experiment.LabView.AnalogOutput.add_transition
DO = experiment.LabView.DAQmxDO.add_transition
label = experiment.functional_waveforms_graph.label

exp = Rb.Rb(HSDIO, AO, DO, label)
###########################################################################
<<<<<<< HEAD
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
            [1, 0, 1]
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

#def FORTdrop(t,duration):

###########################################################################
# Main Block
=======

>>>>>>> RbDev3
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
    exp.pointgrey_trigger_switch.profile(0,'off')
<<<<<<< HEAD
    exp.pointgrey2_trigger_switch.profile(0,'off')
    #exp.pointgrey_trigger_switch.profile(t1_PGcamera,'on')
    #exp.pointgrey_trigger_switch.profile(t1_PGcamera+2,'off')
    exp.pointgrey_trigger_switch.profile(t2_PGcamera,'on')
    exp.pointgrey_trigger_switch.profile(t2_PGcamera+2,'off')
    exp.pointgrey2_trigger_switch.profile(t1_PGcamera,'on')
    exp.pointgrey2_trigger_switch.profile(t1_PGcamera+2,'off')
    #exp.pointgrey2_trigger_switch.profile(t2_PGcamera,'on')
    #exp.pointgrey2_trigger_switch.profile(t2_PGcamera+2,'off')
=======
    exp.pointgrey_trigger_switch.profile(t1_PGcamera,'on')
    exp.pointgrey_trigger_switch.profile(t1_PGcamera+2,'off')
    exp.pointgrey_trigger_switch.profile(t2_PGcamera,'on')
    exp.pointgrey_trigger_switch.profile(t2_PGcamera+2,'off')
>>>>>>> RbDev3
    exp.FORT_NE_trigger_switch.profile(0,'off')
    exp.FORT_NE_trigger_switch.profile(170,'on')
    exp.FORT_NE_trigger_switch.profile(175,'off')
    exp.ryd780a_aom_switch.profile(0,'off')
    exp.ryd780a_dds.profile(0,'off')
    exp.red_pointing_dds.profile(0,'off')
    exp.red_pointing_aom_switch.profile(0,'off')
    exp.ryd780a_aom_switch.profile(10,'on')
    exp.ryd780a_dds.profile(10,'r2')
    exp.red_pointing_dds.profile(10,'r2')
    exp.red_pointing_aom_switch.profile(10,'on')
    exp.ryd780a_aom_switch.profile(15,'off')
    exp.ryd780a_dds.profile(15,'off')
    exp.red_pointing_dds.profile(15,'off')
    exp.red_pointing_aom_switch.profile(15,'off')
    # Ryd 780a noise eater trigger
    exp.ryd780A_NE_trigger_switch.profile(0,'off')
    exp.ryd780A_NE_trigger_switch.profile(10,'on')
    exp.ryd780A_NE_trigger_switch.profile(15,'off')

    exp.MOT_scope_trigger_switch.profile(0,'off')
    exp.MOT_scope_trigger_switch.profile(140,'on')
    exp.MOT_scope_trigger_switch.profile(145,'off')

    exp.scope_trigger_switch.profile(170,'on')
    exp.scope_trigger_switch.profile(171,'off')
    exp.fort_aom_switch.profile(0,'off')
    exp.op_dds.profile(0,'off')
    exp.op_aom_switch.profile(0,'off')
    exp.hf_aom_switch.profile(0,'on')
    exp.mot_3d_x_shutter_switch.profile(0,'off')
    exp.mot_3d_y_shutter_switch.profile(0,'on')
    exp.mot_3d_z1_shutter_switch.profile(0,'off')
    exp.microwave_switch.profile(0,'off')
<<<<<<< HEAD

=======
>>>>>>> RbDev3
    exp.microwave_dds.profile(0,'off')
    exp.repumper_shutter_switch.profile(0,'off')
    exp.ground_aom_switch.profile(0,'off') #### dd
    exp.ryd780a_aom_switch.profile(0,'off')
    exp.ryd780a_dds.profile(0,'off')
    exp.red_pointing_dds.profile(0,'off')
    exp.red_pointing_aom_switch.profile(0,'off')
    # For pointgrey shot.
<<<<<<< HEAD
    raman(t1_PGcamera,t_PG_exposure,'PG')
=======
    exp.red_pointing_dds.profile(t2_PGcamera-0.5,'PG')
    exp.red_pointing_dds.profile(t2_PGcamera+t_PG_exposure,'off')

    exp.red_pointing_aom_switch.profile(t2_PGcamera,'on')
    exp.red_pointing_aom_switch.profile(t2_PGcamera+t_PG_exposure,'off')
    exp.ground_aom_switch.profile(t2_PGcamera,'on')
    exp.ground_aom_switch.profile(t2_PGcamera+t_PG_exposure,'off')


>>>>>>> RbDev3

    ## 2D MOT Loading Phase

    exp.mot_3d_dds.profile(0,'MOT')
    exp.fort_dds.profile(0,'off')
    exp.mot_2d_dds.profile(0,'on')
    exp.mot_aom_switch.profile(0,'on')
    exp.mot_2d_aom_switch.profile(0,'on')

    ## 3D MOT Loading Phase
    exp.mot_2d_dds.profile(t_2DMOT_loading,'off') # turn off 2D MOT light and quadrupole fields
    exp.mot_2d_aom_switch.profile(t_2DMOT_loading,'off')
    AO(t_2DMOT_loading+5,0,0)
    AO(t_2DMOT_loading+5,1,0)

    ## FORT Transfer Phase
    exp.fort_aom_switch.profile(t_FORT_loading,'on')
    exp.fort_dds.profile(t_FORT_loading,'on')

    ## Fall off Phase
    AO(110,2,coil_driver_polarity*-0.30) #X
    AO(110,3,coil_driver_polarity*-0.49) #Y
    AO(110,4,0) #Z
    exp.mot_aom_switch.profile(110,'off')
    exp.hf_aom_switch.profile(110,'off') #####
<<<<<<< HEAD
    AO(110,7,0)
=======
>>>>>>> RbDev3

    ## Readout Phase
    AO(25+110,2,coil_driver_polarity*shimX_RO) #X
    AO(25+110,3,coil_driver_polarity*shimY_RO) #Y
    AO(25+110,4,coil_driver_polarity*shimZ_RO) #Z
    exp.mot_3d_dds.profile(140,'RO')
    exp.camera.take_shot(140)
    t_start=140
<<<<<<< HEAD
    readout(t_start,5)
    t_end=t_start+t_readoutduration
=======
    #t_end=140+exp.camera.pulse_length
    t_end=t_start+t_readoutduration
    t_pulsewidth=0.001*0.4
    t_period=0.001*0.8
    for i in range(int(round((t_end-t_start)/t_period))):
        exp.mot_aom_switch.profile(t_start+i*t_period,'off')
        exp.mot_aom_switch.profile(t_start+i*t_period+t_pulsewidth,'on')

    for i in range(int(round((t_end-t_start)/t_period))):
        exp.fort_aom_switch.profile(t_start+i*t_period,'off')
        exp.fort_aom_switch.profile(t_start+i*t_period+t_pulsewidth,'on')

    exp.mot_aom_switch.profile(t_end,'off')
>>>>>>> RbDev3
    AO(t_start,7,10)
    exp.hf_aom_switch.profile(t_start,'on')
    exp.hf_aom_switch.profile(t_end+0.2,'off') ###
    AO(t_end+0.2,7,0)
<<<<<<< HEAD
   # prepareF1(t_start,10)
=======
>>>>>>> RbDev3

    ## Optical Pumping Phase

    AO(150,2,coil_driver_polarity*shimX_OP) #X
    AO(150,3,coil_driver_polarity*shimY_OP) #Y
    AO(150,4,coil_driver_polarity*shimZ_OP) #Z
<<<<<<< HEAD
    AO(150,7,0) # repumper attenuator. repumper turned off.
=======
    AO(150,7,10) # repumper attenuator. temperorary on
>>>>>>> RbDev3

    t_start=160
    t_end=t_start+t_op+t_depump
    AO(t_start,7,10)
    AO(t_start+t_op,7,0)

    exp.op_dds.profile(t_start,'on')
<<<<<<< HEAD
    exp.op_dds.profile(t_end,'off')
    exp.hf_aom_switch.profile(t_start,'on')
    exp.hf_aom_switch.profile(t_start+t_op,'off')
    AO(t_start,7,10)
    AO(t_start+t_op,7,0)
    opticalpumping(t_start,t_end-t_start)
=======
    exp.op_aom_switch.profile(t_start,'on')
    exp.op_aom_switch.profile(t_start+t_op,'off')
    exp.op_dds.profile(t_end,'off')
    exp.hf_aom_switch.profile(t_start,'on')
    exp.hf_aom_switch.profile(t_start+t_op,'off')

    t_offset=-0.001*0.5
    t_op_pulsewidth=0.001*0.5
    t_fort_pulsewidth=0.001*0.5
    t_period=0.001*1
    for i in range(int(round((t_end-t_start)/t_period))):
        exp.op_aom_switch.profile(t_start+i*t_period,'on')
        exp.op_aom_switch.profile(t_start+i*t_period+t_op_pulsewidth,'off')

    for i in range(int(round((t_end-t_start)/t_period))):
        exp.fort_aom_switch.profile(t_start+i*t_period+t_offset,'off')
        exp.fort_aom_switch.profile(t_start+i*t_period+t_fort_pulsewidth+t_offset,'on')
>>>>>>> RbDev3

    exp.mot_3d_x_shutter_switch.profile(t_x_shutter_open,'on')
    exp.mot_3d_x_shutter_switch.profile(t_x_shutter_close,'off')
    exp.mot_3d_y_shutter_switch.profile(t_y_shutter_open,'off')
    exp.mot_3d_y_shutter_switch.profile(t_y_shutter_close,'on')
    exp.mot_3d_z1_shutter_switch.profile(t_z1_shutter_open,'on')
    exp.mot_3d_z1_shutter_switch.profile(t_z1_shutter_close,'off')

<<<<<<< HEAD
    ## Science Phase 170 - 175 ms. t_science=170
    raman(t_science,t_raman,'r2')

    exp.microwave_dds.profile(t_science,'on')
    exp.microwave_switch.profile(t_science,'on')
    exp.microwave_dds.profile(t_science+t_microwave,'off')
    exp.microwave_switch.profile(t_science+t_microwave,'off')

    exp.microwave_dds.profile(t_science+t_microwave+t_gap,'on')
    exp.microwave_switch.profile(t_science+t_microwave+t_gap,'on')
    exp.microwave_dds.profile(t_science+t_microwave+t_gap+t_microwave,'off')
    exp.microwave_switch.profile(t_science+t_microwave+t_gap+t_microwave,'off')
=======
    ## Science Phase 170 - 175 ms

    #exp.ground_aom_switch.profile(170,'on')
    #exp.ground_aom_switch.profile(170+t_raman,'on')
    #exp.red_pointing_aom_switch.profile(170,'on')
    #exp.red_pointing_aom_switch.profile(170+t_raman,'off')
    #exp.red_pointing_dds.profile(170,'r2')
    #exp.red_pointing_dds.profile(170+t_raman,'off')

    exp.microwave_dds.profile(170,'on')
    exp.microwave_switch.profile(170,'on')
    exp.microwave_dds.profile(170+t_microwave,'off')
    exp.microwave_switch.profile(170+t_microwave,'off')

    #exp.microwave_dds.profile(170+t_microwave+t_gap,'on')
    #exp.microwave_switch.profile(170+t_microwave+t_gap,'on')
    #exp.microwave_dds.profile(170+t_microwave+t_gap+t_microwave,'off')
    #exp.microwave_switch.profile(170+t_microwave+t_gap+t_microwave,'off')
>>>>>>> RbDev3

    #t_start=170+t_microwave
    #t_end=t_start+t_gap#t_Ryd780A
    #exp.red_pointing_dds.profile(t_start,'r2')
    #exp.red_pointing_dds.profile(t_end,'r2')

    #exp.ryd780a_dds.profile(t_start,'r2')
    #exp.ryd780a_dds.profile(t_end,'off')

    #exp.red_pointing_aom_switch.profile(t_start,'on')
    #exp.red_pointing_aom_switch.profile(t_end,'off')

    #exp.ryd780a_aom_switch.profile(t_start,'on')
    #exp.ryd780a_aom_switch.profile(t_end,'off')

    #exp.ground_aom_switch.profile(175,'off')
    exp.red_pointing_dds.profile(175,'off')
    exp.red_pointing_aom_switch.profile(175,'off')
    #t_pulsewidth=0.001*1
    #t_period=0.001*5
    #for i in range(int(round((t_end-t_start)/t_period))):
    #    exp.ryd780a_aom_switch.profile(t_start+i*t_period,'on')
    #    exp.ryd780a_aom_switch.profile(t_start+i*t_period+t_pulsewidth,'off')

    #for i in range(int(round((t_end-t_start)/t_period))):
    #    exp.fort_aom_switch.profile(t_start+i*t_period,'off')
    #    exp.fort_aom_switch.profile(t_start+i*t_period+t_pulsewidth,'on')

    exp.blue_pointing_dds.profile(0,'off')
    exp.blue_pointing_aom_switch.profile(0,'off')
    exp.blue_pointing_dds.profile(t_blueon,'r2')
    exp.blue_pointing_aom_switch.profile(t_blueon,'on')
    exp.blue_pointing_dds.profile(t_blueoff,'off')
    exp.blue_pointing_aom_switch.profile(t_blueoff,'off')

    ## Blow-away Phase 176ms

    AO(175,0,coil_driver_polarity*-0.1)
    AO(175,1,coil_driver_polarity*0.1)
    AO(175,2, coil_driver_polarity*shimX_BA) #X
    AO(175,3,coil_driver_polarity*shimY_BA) #Y
    AO(175,4,coil_driver_polarity*shimZ_BA) #Z

    t_start=176
    t_end=t_start+t_BA
    exp.mot_3d_dds.profile(t_start,'Blowaway')
    exp.fort_dds.profile(t_start,'Blowaway')
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
<<<<<<< HEAD
    #t_readout_2nd=195
=======
    t_readout_2nd=195
>>>>>>> RbDev3

    exp.mot_3d_dds.profile(t_readout_2nd,'RO')
    exp.camera.take_shot(t_readout_2nd)
    t_start=t_readout_2nd
<<<<<<< HEAD
    readout(t_start,5)
    t_end=t_start+t_readoutduration
=======
    t_end=t_readout_2nd+exp.camera.pulse_length
    t_pulsewidth=0.001*0.4
    t_period=0.001*0.8
    for i in range(int(round((t_end-t_start)/t_period))):
        exp.mot_aom_switch.profile(t_start+i*t_period,'off')
        exp.mot_aom_switch.profile(t_start+i*t_period+t_pulsewidth,'on')

    for i in range(int(round((t_end-t_start)/t_period))):
        exp.fort_aom_switch.profile(t_start+i*t_period,'off')
        exp.fort_aom_switch.profile(t_start+i*t_period+t_pulsewidth,'on')
    exp.mot_aom_switch.profile(t_readout_2nd+exp.camera.pulse_length,'off')
>>>>>>> RbDev3
    AO(t_readout_2nd,7,10) # Turn on repumper. Sets rf attenuator voltage to 10V
    exp.hf_aom_switch.profile(t_readout_2nd,'on')
    exp.hf_aom_switch.profile(t_readout_2nd+exp.camera.pulse_length,'off')
    AO(t_readout_2nd+exp.camera.pulse_length,7,0)

<<<<<<< HEAD
    #exp.fort_aom_switch.profile(t_readout_2nd+exp.camera.pulse_length,'off')
=======
    exp.fort_aom_switch.profile(t_readout_2nd+exp.camera.pulse_length,'off')
>>>>>>> RbDev3
    exp.fort_dds.profile(t_readout_2nd+exp.camera.pulse_length,'off')


    ## Blue imaging
    t_start_blue_imaging=205
<<<<<<< HEAD
    t_blue_exposure=2
=======
    t_blue_exposure=0.02
>>>>>>> RbDev3

    exp.blue_pointing_dds.profile(t_start_blue_imaging,'r2')
    exp.blue_pointing_aom_switch.profile(t_start_blue_imaging,'on')
    exp.blue_pointing_dds.profile(t_start_blue_imaging+t_blue_exposure,'off')
    exp.blue_pointing_aom_switch.profile(t_start_blue_imaging+t_blue_exposure,'off')
    exp.camera.pulse_length=t_blue_exposure # Changes HSDIO pulse width to control exposure
    t_readout_3rd=205
    exp.camera.take_shot(t_readout_3rd)
<<<<<<< HEAD
    exp.ryd780a_aom_switch.profile(t2_PGcamera,'on')
    exp.ryd780a_dds.profile(t2_PGcamera,'r2')
=======
    #exp.ryd780a_aom_switch.profile(t2_PGcamera,'on')
    #exp.ryd780a_dds.profile(t2_PGcamera,'r2')
>>>>>>> RbDev3


    ############################## End of normal experiment #######################################################


elif ExpMode==1:
    ####### Laser Cw mode (expmode code 1) #############
    ## Coil currents are same as actual experiment cycle to keep thermal loads as close as possible.
    ## If you need continuous MOT loading, go to expmode code 2
    # Camera will not take any pictures to prevent accidental damage due to CW lasers on.

    ## Initilization
    for i in range(5):
        AO(0,i,0)

    AO(0,5,coil_driver_polarity*-2.2)
    AO(0,6,coil_driver_polarity*2.8)
    AO(0,0,coil_driver_polarity*1.5)
    AO(0,1,coil_driver_polarity*1.5)
    AO(0,7,10)
    exp.pointgrey_trigger_switch.profile(0,'off')
    exp.pointgrey_trigger_switch.profile(t1_PGcamera,'on')
    exp.pointgrey_trigger_switch.profile(t1_PGcamera+2,'off')
    exp.pointgrey_trigger_switch.profile(t2_PGcamera,'on')
    exp.pointgrey_trigger_switch.profile(t2_PGcamera+2,'off')
    exp.FORT_NE_trigger_switch.profile(0,'off')
    exp.FORT_NE_trigger_switch.profile(170,'on')
    exp.FORT_NE_trigger_switch.profile(175,'off')
    #exp.ryd780a_aom_switch.profile(0,'off')
    #exp.ryd780a_dds.profile(0,'off')
    #exp.red_pointing_dds.profile(0,'off')
    #exp.red_pointing_aom_switch.profile(0,'off')
    exp.ryd780a_aom_switch.profile(0,'on')
    exp.ryd780a_dds.profile(0,'r2')
    exp.red_pointing_dds.profile(0,'r2')
    exp.red_pointing_aom_switch.profile(0,'on')
    #exp.ryd780a_aom_switch.profile(15,'off')
    #exp.ryd780a_dds.profile(15,'off')
    #exp.red_pointing_dds.profile(15,'off')
    #exp.red_pointing_aom_switch.profile(15,'off')
    # Ryd 780a noise eater trigger
    exp.ryd780A_NE_trigger_switch.profile(0,'off')
    exp.ryd780A_NE_trigger_switch.profile(10,'on')
    exp.ryd780A_NE_trigger_switch.profile(15,'off')

    exp.scope_trigger_switch.profile(170,'on')
    exp.scope_trigger_switch.profile(171,'off')

    exp.fort_aom_switch.profile(0,'on')
    exp.fort_dds.profile(0,'on')
    exp.op_dds.profile(0,'on')
    exp.op_aom_switch.profile(0,'on')
    exp.hf_aom_switch.profile(0,'on')
    exp.microwave_switch.profile(0,'on')
    exp.microwave_dds.profile(0,'on')
    exp.repumper_shutter_switch.profile(0,'on')
    exp.ground_aom_switch.profile(0,'on')
#    exp.ground_aom_switch.profile(155,'off')
    exp.mot_3d_dds.profile(0,'MOT')
    exp.mot_2d_dds.profile(0,'on')
    exp.mot_aom_switch.profile(0,'on')
    exp.mot_2d_aom_switch.profile(0,'on')
#    exp.red_pointing_dds.profile(0,'r2')
#    exp.red_pointing_aom_switch.profile(0,'on')
#    exp.ryd780a_aom_switch.profile(0,'on')
#    exp.ryd780a_dds.profile(0,'r2')
    exp.blue_pointing_dds.profile(0,'r2')
    exp.blue_pointing_aom_switch.profile(0,'on')
    exp.mot_3d_x_shutter_switch.profile(0,'off')
    exp.mot_3d_y_shutter_switch.profile(0,'on')
    exp.mot_3d_z1_shutter_switch.profile(0,'off')


    ## 2D MOT Loading Phase
    AO(0,2,coil_driver_polarity*-0.33) #X
    AO(0,3,coil_driver_polarity*-0.17) #Y
    AO(0,4,coil_driver_polarity*0.0075) #Z


    ## 3D MOT Loading Phase
    AO(60,0,0)
    AO(60,1,0)

    ## FORT Transfer Phase


    ## Fall off Phase
    AO(110,2,coil_driver_polarity*-0.30) #X
    AO(110,3,coil_driver_polarity*-0.49) #Y
    AO(110,4,0) #Z

    ## Readout Phase
    AO(25+110,2,coil_driver_polarity*-0.30) #X
    AO(25+110,3,coil_driver_polarity*-0.50) #Y
    AO(25+110,4,coil_driver_polarity*-0.015) #Z
    #exp.mot_3d_dds.profile(140,'RO')
    exp.camera.take_shot(140)
    AO(150,2,coil_driver_polarity*-0.27) #X
    AO(150,3,coil_driver_polarity*-0.48) #Y
    AO(150,4,coil_driver_polarity*-0.25) #Z
<<<<<<< HEAD
    t_start=140
    readout(t_start,5)
=======


>>>>>>> RbDev3
    ## Optical Pumping Phase
    #AO(150,7,0)
    #AO(160,7,10)
    #AO(165,7,0)

    #exp.mot_3d_x_shutter_switch.profile(t_x_shutter_open,'on')
    #exp.mot_3d_x_shutter_switch.profile(t_x_shutter_close,'off')
    #exp.mot_3d_y_shutter_switch.profile(t_y_shutter_open,'off')
    #exp.mot_3d_y_shutter_switch.profile(t_y_shutter_close,'on')
    #exp.mot_3d_z1_shutter_switch.profile(t_z1_shutter_open,'on')
    #exp.mot_3d_z1_shutter_switch.profile(t_z1_shutter_close,'off')

    ## Science Phase 170 - 175 ms

    ## Blow-away Phase 176ms

    AO(175,0,coil_driver_polarity*-0.1)
    AO(175,1,coil_driver_polarity*0.1)
    AO(175,2, coil_driver_polarity*-0.371) #X
    AO(175,3,coil_driver_polarity*-0.553) #Y
    AO(175,4,coil_driver_polarity*-0.0518) #Z

    ## Readout Phase
    AO(180,0,0) # turn off quadrupole fields
    AO(180,1,0)
    AO(180,2, coil_driver_polarity*-0.30) #X
    AO(180,3, coil_driver_polarity*-0.50) #Y
    AO(180,4, coil_driver_polarity*-0.015) #Z
    t_readout_2nd=195

    exp.camera.take_shot(t_readout_2nd)

    #AO(t_readout_2nd,7,10) # Turn on repumper. Sets rf attenuator voltage to 10V
    #AO(t_readout_2nd+exp.camera.pulse_length,7,0)


    ## Blue imaging

    t_readout_3rd=205
    exp.camera.take_shot(t_readout_3rd)

    ## End of expmode 1

elif ExpMode==2:
    ####### Continous MOT loading mode (expmode code 2) #############
    # Camera will take pictures
    AO(0,0,coil_driver_polarity*I_Q1)
    AO(0,1,coil_driver_polarity*I_Q2)
    AO(0,2,coil_driver_polarity*ShimX_Loading) #X
    AO(0,3,coil_driver_polarity*ShimY_Loading) #Y
    AO(0,4,coil_driver_polarity*ShimZ_Loading) #Z
    AO(0,5,coil_driver_polarity*-2.2)
    AO(0,6,coil_driver_polarity*2.8)
    AO(0,7,10)

#  AO(180,0,coil_driver_polarity*I_Q1*0.9)
#  AO(180,1,coil_driver_polarity*I_Q2*0.9)
    AO(200,0,coil_driver_polarity*I_Q1)
    AO(200,1,coil_driver_polarity*I_Q2)
    AO(200,2,coil_driver_polarity*ShimX_Loading) #X
    AO(200,3,coil_driver_polarity*ShimY_Loading) #Y
    AO(200,4,coil_driver_polarity*ShimZ_Loading) #Z
    AO(200,5,coil_driver_polarity*-2.2)
    AO(200,6,coil_driver_polarity*2.8)
    AO(200,7,10)

    exp.fort_aom_switch.profile(0,'off')
    exp.fort_dds.profile(0,'off') ####
    exp.MOT_scope_trigger_switch.profile(0,'off')
    exp.MOT_scope_trigger_switch.profile(100,'on')
    exp.MOT_scope_trigger_switch.profile(101,'off')
    exp.op_dds.profile(0,'off')
    exp.op_aom_switch.profile(0,'off')
    exp.hf_aom_switch.profile(0,'on')
    exp.microwave_switch.profile(0,'off')
    exp.microwave_dds.profile(0,'on')
    exp.repumper_shutter_switch.profile(0,'on')
    exp.ground_aom_switch.profile(0,'on') ##
    exp.mot_3d_dds.profile(0,'MOT')
    exp.mot_2d_dds.profile(0,'on')
    exp.mot_aom_switch.profile(0,'on')
    exp.mot_2d_aom_switch.profile(0,'on')
    exp.red_pointing_dds.profile(0,'off')
    exp.red_pointing_aom_switch.profile(0,'off')
    exp.ryd780a_aom_switch.profile(0,'on')
    exp.ryd780a_dds.profile(0,'r2')

    exp.blue_pointing_dds.profile(0,'off')
    exp.blue_pointing_aom_switch.profile(0,'off')
    exp.blue_pointing_dds.profile(140,'r2')
    exp.blue_pointing_aom_switch.profile(140,'on')
    exp.blue_pointing_dds.profile(140.1,'off')
    exp.blue_pointing_aom_switch.profile(140.1,'off')

    exp.mot_3d_x_shutter_switch.profile(0,'off')
    exp.mot_3d_y_shutter_switch.profile(0,'on')
    exp.mot_3d_z1_shutter_switch.profile(0,'off')

    exp.camera.pulse_length=10
    exp.camera.take_shot(140)
    t_start=140
    t_end=140+exp.camera.pulse_length
    t_pulsewidth=0.001*0.4
    t_period=0.001*0.8
<<<<<<< HEAD
    image_FORT=True
=======
    image_FORT=False
>>>>>>> RbDev3
    if image_FORT:
        exp.fort_dds.profile(t_start,'on') ####
        for i in range(int(round((t_end-t_start)/t_period))):
            exp.mot_aom_switch.profile(t_start+i*t_period,'off')
            exp.mot_aom_switch.profile(t_start+i*t_period+t_pulsewidth,'on')

        for i in range(int(round((t_end-t_start)/t_period))):
            exp.fort_aom_switch.profile(t_start+i*t_period,'off')
            exp.fort_aom_switch.profile(t_start+i*t_period+t_pulsewidth,'on')

        exp.fort_aom_switch.profile(t_end,'off')
        exp.fort_dds.profile(t_end,'off') ####
        exp.mot_aom_switch.profile(t_end,'on')

    exp.pointgrey_trigger_switch.profile(0,'off')
    exp.pointgrey_trigger_switch.profile(t1_PGcamera,'on')
    exp.pointgrey_trigger_switch.profile(t1_PGcamera+2,'off')
    exp.pointgrey_trigger_switch.profile(t2_PGcamera,'on')
    exp.pointgrey_trigger_switch.profile(t2_PGcamera+2,'off')
    exp.FORT_NE_trigger_switch.profile(0,'off')
    exp.FORT_NE_trigger_switch.profile(170,'on')
    exp.FORT_NE_trigger_switch.profile(171,'off')
    exp.scope_trigger_switch.profile(170,'on')
    exp.scope_trigger_switch.profile(171,'off')
    exp.red_pointing_dds.profile(t2_PGcamera-0.5,'PG')
    exp.red_pointing_dds.profile(t2_PGcamera+t_PG_exposure,'off')
    exp.red_pointing_aom_switch.profile(t2_PGcamera,'on')
    exp.red_pointing_aom_switch.profile(t2_PGcamera+t_PG_exposure,'off')
    exp.ground_aom_switch.profile(t2_PGcamera,'on')
    exp.ground_aom_switch.profile(t2_PGcamera+t_PG_exposure,'off')
    exp.fort_aom_switch.profile(t2_PGcamera,'off')
    exp.fort_aom_switch.profile(t2_PGcamera+t_PG_exposure,'on')


    ## End of expmode 2
elif ExpMode==3:
    ####### Laser CW mode, except 780. (variation of expmode code 1) #############
    ## Coil currents are same as actual experiment cycle to keep thermal loads as close as possible.
    ## To capture beam positions onto Blackfly camera
    # Camera will not take any pictures to prevent accidental damage due to CW lasers on.

    ## Initilization
    for i in range(5):
        AO(0,i,0)

    AO(0,5,coil_driver_polarity*-2.2)
    AO(0,6,coil_driver_polarity*2.8)
    AO(0,0,coil_driver_polarity*I_Q1)
    AO(0,1,coil_driver_polarity*I_Q2)

    AO(0,7,10)
    exp.pointgrey_trigger_switch.profile(0,'off')
    exp.pointgrey_trigger_switch.profile(t1_PGcamera,'on')
    exp.pointgrey_trigger_switch.profile(t1_PGcamera+2,'off')
    exp.pointgrey_trigger_switch.profile(t2_PGcamera,'on')
    exp.pointgrey_trigger_switch.profile(t2_PGcamera+2,'off')
    exp.FORT_NE_trigger_switch.profile(0,'off')
    exp.FORT_NE_trigger_switch.profile(170,'on')
    exp.FORT_NE_trigger_switch.profile(171,'off')
    exp.scope_trigger_switch.profile(170,'on')
    exp.scope_trigger_switch.profile(171,'off')
    # For pointgrey shot.
    exp.red_pointing_dds.profile(t2_PGcamera-0.5,'PG')
    exp.red_pointing_dds.profile(t2_PGcamera+t_PG_exposure,'off')

    exp.red_pointing_aom_switch.profile(t2_PGcamera,'on')
    exp.red_pointing_aom_switch.profile(t2_PGcamera+t_PG_exposure,'off')
    exp.ground_aom_switch.profile(t2_PGcamera,'on')
    exp.ground_aom_switch.profile(t2_PGcamera+t_PG_exposure,'off')

    exp.fort_aom_switch.profile(0,'off')
    exp.fort_dds.profile(0,'off')
    ## FORT Transfer Phase
    exp.fort_aom_switch.profile(t_FORT_loading,'on')
    exp.fort_dds.profile(t_FORT_loading,'on')

    exp.op_dds.profile(0,'on')
    exp.op_aom_switch.profile(0,'on')
    exp.hf_aom_switch.profile(0,'on')
    exp.microwave_switch.profile(0,'on')
    exp.microwave_dds.profile(0,'on')
    exp.repumper_shutter_switch.profile(0,'on')
    exp.ground_aom_switch.profile(0,'on')
#    exp.ground_aom_switch.profile(155,'off')
    exp.mot_3d_dds.profile(0,'MOT')
    exp.mot_2d_dds.profile(0,'on')
    exp.mot_aom_switch.profile(0,'on')
    exp.mot_2d_aom_switch.profile(0,'on')
    exp.red_pointing_dds.profile(0,'r2')
    exp.red_pointing_aom_switch.profile(0,'on')
    exp.ryd780a_aom_switch.profile(0,'on')
    exp.ryd780a_dds.profile(0,'r2')
    exp.blue_pointing_dds.profile(0,'r2')
    exp.blue_pointing_aom_switch.profile(0,'on')
    exp.mot_3d_x_shutter_switch.profile(0,'off')
    exp.mot_3d_y_shutter_switch.profile(0,'on')
    exp.mot_3d_z1_shutter_switch.profile(0,'off')


    ## 2D MOT Loading Phase
    AO(0,2,coil_driver_polarity*-0.33) #X
    AO(0,3,coil_driver_polarity*-0.17) #Y
    AO(0,4,coil_driver_polarity*0.0075) #Z


    ## 3D MOT Loading Phase
    AO(60,0,0)
    AO(60,1,0)

    ## FORT Transfer Phase


    ## Fall off Phase
    AO(110,2,coil_driver_polarity*-0.30) #X
    AO(110,3,coil_driver_polarity*-0.49) #Y
    AO(110,4,0) #Z

    ## Readout Phase
    AO(25+110,2,coil_driver_polarity*-0.30) #X
    AO(25+110,3,coil_driver_polarity*-0.50) #Y
    AO(25+110,4,coil_driver_polarity*-0.015) #Z
    #exp.mot_3d_dds.profile(140,'RO')
    exp.camera.take_shot(140)
    AO(150,2,coil_driver_polarity*-0.27) #X
    AO(150,3,coil_driver_polarity*-0.48) #Y
    AO(150,4,coil_driver_polarity*-0.25) #Z


    ## Optical Pumping Phase
    #AO(150,7,0)
    #AO(160,7,10)
    #AO(165,7,0)

    #exp.mot_3d_x_shutter_switch.profile(t_x_shutter_open,'on')
    #exp.mot_3d_x_shutter_switch.profile(t_x_shutter_close,'off')
    #exp.mot_3d_y_shutter_switch.profile(t_y_shutter_open,'off')
    #exp.mot_3d_y_shutter_switch.profile(t_y_shutter_close,'on')
    #exp.mot_3d_z1_shutter_switch.profile(t_z1_shutter_open,'on')
    #exp.mot_3d_z1_shutter_switch.profile(t_z1_shutter_close,'off')

    ## Science Phase 170 - 175 ms

    ## Blow-away Phase 176ms

    AO(175,0,coil_driver_polarity*-0.1)
    AO(175,1,coil_driver_polarity*0.1)
    AO(175,2, coil_driver_polarity*-0.371) #X
    AO(175,3,coil_driver_polarity*-0.553) #Y
    AO(175,4,coil_driver_polarity*-0.0518) #Z

    ## Readout Phase
    AO(180,0,0) # turn off quadrupole fields
    AO(180,1,0)
    AO(180,2, coil_driver_polarity*-0.30) #X
    AO(180,3, coil_driver_polarity*-0.50) #Y
    AO(180,4, coil_driver_polarity*-0.015) #Z
    t_readout_2nd=195

    exp.camera.take_shot(t_readout_2nd)

    #AO(t_readout_2nd,7,10) # Turn on repumper. Sets rf attenuator voltage to 10V
    #AO(t_readout_2nd+exp.camera.pulse_length,7,0)


    ## Blue imaging

    t_readout_3rd=205
    exp.camera.take_shot(t_readout_3rd)

    ## End of expmode 3

##### For aligning blue side optics. Exp mode 4 ######
elif ExpMode==4:
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
    exp.pointgrey_trigger_switch.profile(0,'off')
    exp.pointgrey_trigger_switch.profile(t1_PGcamera,'on')
    exp.pointgrey_trigger_switch.profile(t1_PGcamera+2,'off')
    exp.pointgrey_trigger_switch.profile(t2_PGcamera,'on')
    exp.pointgrey_trigger_switch.profile(t2_PGcamera+2,'off')
    exp.FORT_NE_trigger_switch.profile(0,'off')
    exp.FORT_NE_trigger_switch.profile(170,'on')
    exp.FORT_NE_trigger_switch.profile(175,'off')
    exp.ryd780a_aom_switch.profile(0,'off')
    exp.ryd780a_dds.profile(0,'off')
    exp.red_pointing_dds.profile(0,'off')
    exp.red_pointing_aom_switch.profile(0,'off')
    exp.ryd780a_aom_switch.profile(10,'on')
    exp.ryd780a_dds.profile(10,'r2')
    exp.red_pointing_dds.profile(10,'r2')
    exp.red_pointing_aom_switch.profile(10,'on')
    exp.ryd780a_aom_switch.profile(15,'off')
    exp.ryd780a_dds.profile(15,'off')
    exp.red_pointing_dds.profile(15,'off')
    exp.red_pointing_aom_switch.profile(15,'off')
    # Ryd 780a noise eater trigger
    exp.ryd780A_NE_trigger_switch.profile(0,'off')
    exp.ryd780A_NE_trigger_switch.profile(10,'on')
    exp.ryd780A_NE_trigger_switch.profile(15,'off')

    exp.MOT_scope_trigger_switch.profile(0,'off')
    exp.MOT_scope_trigger_switch.profile(100,'on')
    exp.MOT_scope_trigger_switch.profile(101,'off')

    exp.scope_trigger_switch.profile(170,'on')
    exp.scope_trigger_switch.profile(171,'off')
    exp.fort_aom_switch.profile(0,'off')
    exp.op_dds.profile(0,'off')
    exp.op_aom_switch.profile(0,'off')
    exp.hf_aom_switch.profile(0,'on')
    exp.mot_3d_x_shutter_switch.profile(0,'off')
    exp.mot_3d_y_shutter_switch.profile(0,'on')
    exp.mot_3d_z1_shutter_switch.profile(0,'off')
    exp.microwave_switch.profile(0,'off')
    exp.microwave_dds.profile(0,'off')
    exp.repumper_shutter_switch.profile(0,'off')
    exp.ground_aom_switch.profile(0,'off') #### dd
    exp.ryd780a_aom_switch.profile(0,'off')
    exp.ryd780a_dds.profile(0,'off')
    exp.red_pointing_dds.profile(0,'off')
    exp.red_pointing_aom_switch.profile(0,'off')
    # For pointgrey shot.
    exp.red_pointing_dds.profile(t2_PGcamera-0.5,'PG')
    exp.red_pointing_dds.profile(t2_PGcamera+t_PG_exposure,'off')

    exp.red_pointing_aom_switch.profile(t2_PGcamera,'on')
    exp.red_pointing_aom_switch.profile(t2_PGcamera+t_PG_exposure,'off')
    exp.ground_aom_switch.profile(t2_PGcamera,'on')
    exp.ground_aom_switch.profile(t2_PGcamera+t_PG_exposure,'off')



    ## 2D MOT Loading Phase

    exp.mot_3d_dds.profile(0,'MOT')
    exp.fort_dds.profile(0,'off')
    exp.mot_2d_dds.profile(0,'on')
    exp.mot_aom_switch.profile(0,'on')
    exp.mot_2d_aom_switch.profile(0,'on')

    ## 3D MOT Loading Phase
    exp.mot_2d_dds.profile(t_2DMOT_loading,'off') # turn off 2D MOT light and quadrupole fields
    exp.mot_2d_aom_switch.profile(t_2DMOT_loading,'off')
    AO(t_2DMOT_loading+5,0,0)
    AO(t_2DMOT_loading+5,1,0)

    ## FORT Transfer Phase
    exp.fort_aom_switch.profile(t_FORT_loading,'on')
    exp.fort_dds.profile(t_FORT_loading,'on')

    ## Fall off Phase
    AO(110,2,coil_driver_polarity*-0.30) #X
    AO(110,3,coil_driver_polarity*-0.49) #Y
    AO(110,4,0) #Z
    exp.mot_aom_switch.profile(110,'off')
    exp.hf_aom_switch.profile(110,'off') #####

    ## Readout Phase
    AO(25+110,2,coil_driver_polarity*shimX_RO) #X
    AO(25+110,3,coil_driver_polarity*shimY_RO) #Y
    AO(25+110,4,coil_driver_polarity*shimZ_RO) #Z
    exp.mot_3d_dds.profile(140,'RO')
    #exp.camera.take_shot(140)
    t_start=140
    t_end=140+exp.camera.pulse_length
    t_pulsewidth=0.001*0.4
    t_period=0.001*0.8
    for i in range(int(round((t_end-t_start)/t_period))):
        exp.mot_aom_switch.profile(t_start+i*t_period,'off')
        exp.mot_aom_switch.profile(t_start+i*t_period+t_pulsewidth,'on')

    for i in range(int(round((t_end-t_start)/t_period))):
        exp.fort_aom_switch.profile(t_start+i*t_period,'off')
        exp.fort_aom_switch.profile(t_start+i*t_period+t_pulsewidth,'on')

    exp.mot_aom_switch.profile(t_end,'off')
    AO(140,7,10)
    exp.hf_aom_switch.profile(140,'on')
    exp.hf_aom_switch.profile(145.2,'off') ###
    AO(145.2,7,0)

    ## Optical Pumping Phase

    AO(150,2,coil_driver_polarity*shimX_OP) #X
    AO(150,3,coil_driver_polarity*shimY_OP) #Y
    AO(150,4,coil_driver_polarity*shimZ_OP) #Z
    AO(150,7,10) # repumper attenuator. temperorary on

    t_start=160
    t_end=t_start+t_op+t_depump
    AO(t_start,7,10)
    AO(t_start+t_op,7,0)

    exp.op_dds.profile(t_start,'on')
    exp.op_aom_switch.profile(t_start,'on')
    exp.op_aom_switch.profile(t_start+t_op,'off')
    exp.op_dds.profile(t_end,'off')
    exp.hf_aom_switch.profile(t_start,'on')
    exp.hf_aom_switch.profile(t_start+t_op,'off')

    t_offset=-0.001*0.5
    t_op_pulsewidth=0.001*0.5
    t_fort_pulsewidth=0.001*0.5
    t_period=0.001*1
    for i in range(int(round((t_end-t_start)/t_period))):
        exp.op_aom_switch.profile(t_start+i*t_period,'on')
        exp.op_aom_switch.profile(t_start+i*t_period+t_op_pulsewidth,'off')

    for i in range(int(round((t_end-t_start)/t_period))):
        exp.fort_aom_switch.profile(t_start+i*t_period+t_offset,'off')
        exp.fort_aom_switch.profile(t_start+i*t_period+t_fort_pulsewidth+t_offset,'on')

    exp.mot_3d_x_shutter_switch.profile(t_x_shutter_open,'on')
    exp.mot_3d_x_shutter_switch.profile(t_x_shutter_close,'off')
    exp.mot_3d_y_shutter_switch.profile(t_y_shutter_open,'off')
    exp.mot_3d_y_shutter_switch.profile(t_y_shutter_close,'on')
    exp.mot_3d_z1_shutter_switch.profile(t_z1_shutter_open,'on')
    exp.mot_3d_z1_shutter_switch.profile(t_z1_shutter_close,'off')

    ## Science Phase 170 - 175 ms

    #exp.ground_aom_switch.profile(170,'on')
    #exp.ground_aom_switch.profile(170+t_raman,'on')
    #exp.red_pointing_aom_switch.profile(170,'on')
    #exp.red_pointing_aom_switch.profile(170+t_raman,'off')
    #exp.red_pointing_dds.profile(170,'r2')
    #exp.red_pointing_dds.profile(170+t_raman,'off')

    exp.microwave_dds.profile(170,'on')
    exp.microwave_dds.profile(170+t_microwave,'off')
    exp.microwave_switch.profile(170,'on')
    exp.microwave_switch.profile(170+t_microwave,'off')

    #exp.microwave_dds.profile(170+t_microwave+t_gap,'on')
    #exp.microwave_switch.profile(170+t_microwave+t_gap,'on')
    #exp.microwave_dds.profile(170+t_microwave+t_gap+t_microwave,'off')
    #exp.microwave_switch.profile(170+t_microwave+t_gap+t_microwave,'off')

    t_start=170+t_microwave
    t_end=t_start+t_gap#t_Ryd780A
    exp.red_pointing_dds.profile(t_start,'r2')
    exp.red_pointing_dds.profile(t_end,'r2')

    exp.ryd780a_dds.profile(t_start,'r2')
    exp.ryd780a_dds.profile(t_end,'off')

    exp.red_pointing_aom_switch.profile(t_start,'on')
    exp.red_pointing_aom_switch.profile(t_end,'off')

    exp.ryd780a_aom_switch.profile(t_start,'on')
    exp.ryd780a_aom_switch.profile(t_end,'off')

    t_start=170+t_microwave+t_gap
    t_end=t_start+t_microwave
    exp.microwave_dds.profile(t_start,'on')
    exp.microwave_dds.profile(t_end,'off')
    exp.microwave_switch.profile(t_start,'on')
    exp.microwave_switch.profile(t_end,'off')


    exp.ground_aom_switch.profile(175,'off')
    exp.red_pointing_dds.profile(175,'off')
    exp.red_pointing_aom_switch.profile(175,'off')
    #t_pulsewidth=0.001*1
    #t_period=0.001*5
    #for i in range(int(round((t_end-t_start)/t_period))):
    #    exp.ryd780a_aom_switch.profile(t_start+i*t_period,'on')
    #    exp.ryd780a_aom_switch.profile(t_start+i*t_period+t_pulsewidth,'off')

    #for i in range(int(round((t_end-t_start)/t_period))):
    #    exp.fort_aom_switch.profile(t_start+i*t_period,'off')
    #    exp.fort_aom_switch.profile(t_start+i*t_period+t_pulsewidth,'on')

    exp.blue_pointing_dds.profile(0,'off')
    exp.blue_pointing_aom_switch.profile(0,'off')
    exp.blue_pointing_dds.profile(t_blueon,'r2')
    exp.blue_pointing_aom_switch.profile(t_blueon,'on')
    exp.blue_pointing_dds.profile(t_blueoff,'off')
    exp.blue_pointing_aom_switch.profile(t_blueoff,'off')

    ## Blow-away Phase 176ms

    AO(175,0,coil_driver_polarity*-0.1)
    AO(175,1,coil_driver_polarity*0.1)
    AO(175,2, coil_driver_polarity*shimX_BA) #X
    AO(175,3,coil_driver_polarity*shimY_BA) #Y
    AO(175,4,coil_driver_polarity*shimZ_BA) #Z

    t_start=176
    t_end=t_start+t_BA
    exp.mot_3d_dds.profile(t_start,'Blowaway')
    exp.fort_dds.profile(t_start,'Blowaway')
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
    #exp.camera.take_shot(t_readout_2nd)
    t_start=t_readout_2nd
    t_end=t_readout_2nd+exp.camera.pulse_length
    t_pulsewidth=0.001*0.4
    t_period=0.001*0.8
    for i in range(int(round((t_end-t_start)/t_period))):
        exp.mot_aom_switch.profile(t_start+i*t_period,'off')
        exp.mot_aom_switch.profile(t_start+i*t_period+t_pulsewidth,'on')

    for i in range(int(round((t_end-t_start)/t_period))):
        exp.fort_aom_switch.profile(t_start+i*t_period,'off')
        exp.fort_aom_switch.profile(t_start+i*t_period+t_pulsewidth,'on')
    exp.mot_aom_switch.profile(t_readout_2nd+exp.camera.pulse_length,'off')
    AO(t_readout_2nd,7,10) # Turn on repumper. Sets rf attenuator voltage to 10V
    exp.hf_aom_switch.profile(t_readout_2nd,'on')
    exp.hf_aom_switch.profile(t_readout_2nd+exp.camera.pulse_length,'off')
    AO(t_readout_2nd+exp.camera.pulse_length,7,0)

    exp.fort_aom_switch.profile(t_readout_2nd+exp.camera.pulse_length,'off')
    exp.fort_dds.profile(t_readout_2nd+exp.camera.pulse_length,'off')


    ## Blue imaging
    t_start_blue_imaging=205
    t_blue_exposure=0.002

    exp.blue_pointing_dds.profile(t_start_blue_imaging,'r2')
    exp.blue_pointing_aom_switch.profile(t_start_blue_imaging,'on')
    exp.blue_pointing_dds.profile(t_start_blue_imaging+t_blue_exposure,'off')
    exp.blue_pointing_aom_switch.profile(t_start_blue_imaging+t_blue_exposure,'off')
    exp.camera.pulse_length=t_blue_exposure # Changes HSDIO pulse width to control exposure
    t_readout_3rd=205
    exp.camera.take_shot(t_readout_3rd)
    #exp.ryd780a_aom_switch.profile(t2_PGcamera,'on')
    #exp.ryd780a_dds.profile(t2_PGcamera,'r2')


    ############################## End of mode 4,  blue aligning experiment #######################################################


else:
    print "Undefined Experiment mode : {}".format(ExpMode)
