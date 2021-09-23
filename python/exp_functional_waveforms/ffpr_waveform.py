"""

The waveform functions for the FFPR Rubidium project to be used as a template for fiber cavity experiments.
The baseline experiment here is based on Garrett's conveyor_ram_expt_v3 for ARTIQ.
Set ExpMode to 0 to use this.

This file is not imported to CsPy. You'll have to load it up in the functional waveforms window.

ExpMode
0: Normal experiments
1: Time-of-flight MOT temperature measurements
2: Continuously loading a MOT. Watch out for coil temperatures!
'off': set all DDS profiles to off
"""

import exp_functional_waveforms.functional_waveforms_ffpr as Rb
from exp_functional_waveforms.functional_waveforms_ffpr import conveyor_back_aom_switch_chan, conveyor_front_aom_switch_chan, xfer852_aom_switch_chan

HSDIO = experiment.LabView.HSDIO.add_transition
HSDIO_repeat = experiment.LabView.HSDIO.add_repeat
AO = experiment.LabView.AnalogOutput.add_transition
DO = experiment.LabView.DAQmxDO.add_transition
label = experiment.functional_waveforms_graph.label

exp = Rb.Rb(HSDIO, AO, DO, label)

"""
*******************************************************************************
FUNCTION DECLARATIONS AND GLOBAL DEFINITIONS

Includes Rb's functions for conveyor_front_aom pulses, fluorescent readout, optical 
pumping, incoherent and coherent Rydberg excitation, etc.
*******************************************************************************
"""

# TODO: CHANGE FORT REFERENCES TO CONVEYOR FRONT AND BACK REFERENCES. PROBABLY NEED ANOTHER SWITCH DEFINED.
# this means all chopped functions will now need to chop both conveyors, unless we have a switch that can toggle
# two channels

# Analog output channels
quadrupole1 = 0
quadrupole2 = 1
shimcoil_3DX = 2
shimcoil_3DY = 3
shimcoil_3DZ = 4
repumper_VCA = 5 # controls a VCA

def everything_off():
    """turns off all, AO, DDS, and Switch channels"""
    ao_channels = [quadrupole1, quadrupole2, shimcoil_3DX, shimcoil_3DY, shimcoil_3DZ, repumper_VCA]
    for chan in ao_channels:
        AO(0, chan, 0)
        AO(1, chan, 0)
        # needs at least one transition, else nidaqmx.task.timing.samp_clk_timing freaks out in instr. server

    # TODO: this doesn't work. not sure why. nothing prints here either
    # for rf_sig in dir(exp):
    #     if hasattr(rf_sig, 'profile'):
    #         try:
    #             getattr(rf_sig, 'profile')(0, 'off')
    #             logger.info("turning off {}".format(rf_sig.__class__.__name__()))
    #         except:
    #             logger.warning("{} has no 'off' profile, but it should!".format(type(rf_sig)))

def chop_readout(channels, phases, profiles, period):
    """Add a single cycle of a chopping pattern """
    if len(channels) != len(phases) or len(channels) != len(profiles):
        "Chop function requries equal length lists of channels and phases"
        raise PauseError

    def chop_function(t):
        # TODO: check that profiles are grey coded!!!!!!!!
        for i, c in enumerate(channels):
            # set up initial state
            init_state = profiles[i][0]
            msg = "ch[{}]: t({}) = {}"
            # print(msg.format(c, 0, init_state))
            HSDIO(t, c, init_state)
            # now change state at phase list
            for j, p in enumerate(phases[i]):
                if p > 1 or p < 0:
                    print
                    "chop_dds function expects phases to be within 0<p<1"
                    raise ValueError
                # put in initial value for the cycle
                # put in transition
                # print(msg.format(c, p, profiles[i][j + 1]))
                HSDIO(t + (p * period), c, profiles[i][j + 1])
        return t + period

    return chop_function

# TODO: readout function needs modifying for chopping both conveyors
def readout(t, duration, period_ms, profile=None):
    """ Image atom in FORT or do polarization gradient cooling.
        'profile': optional to set specific phases. Most options override
         period_ms! Options: 'PGC500kHz','PGC1MHz','RO1MHz'
    """
    # Note that camera trigger is not included here. Exposure control needs to be done indepdently
    # Also magnetic field control is done sepearately.

    # NOTE: there is an overall phase difference between MOT and FORT pulses
    # which changes with the RO_chop_period, so if you change the period, check
    # that the pulses aren't overlapping on the scope.

    label(t, 'readout')

    if profile is None:  # default: assumes 1.25 MHz chop period
        period = period_ms
        # optimal at 1.25 MHz chop period
        # phases = [[0.16, 0.38], [0.60, 0.91]]  # wide FORT, narrow MOT #changed CY 20200810 using [0, 1, 0],  # MOT: off,on,off
        phases = [[0.14, 0.38], [0.65, 0.98]]
        # phases = [[0.2, 0.48], [0.51, 0.92]]   #testing 08232019
        profiles = [
            # [0, 1, 0],  # MOT: off,on,off
            [1, 1, 1],  # MOT: off,on,off
            [1, 0, 1]  # FORT: on,off,on
        ]
    elif profile is 'RO1MHz':
        period = 0.001
        phases = [[0.6, 0.99], [0.05, 0.6]]
        profiles = [
            [1, 0, 1]
            , [0, 1, 0]
        ]
    elif profile is 'PGC500kHz':
        period = 0.002
        offgap = 3 * 26.24e-9 / (period * 1e-3)  # 3 gamma between MOT off, FORT on
        # phases = [[0.55, 0.99-offgap], [0.275, 0.82]]
        phases = [[0.19, 0.78], [0.66, 0.95]]
        profiles = [
            [0, 1, 0]
            , [0, 1, 0]
        ]
    elif profile is 'PGC800kHz':
        period = 0.0015
        #period = alignment_loop
        offgap = 3 * 26.24e-9 / (period * 1e-3)  # 3 gamma between MOT off, FORT on
        phases = [[0.29, 0.88], [0.66, 0.95]]
        profiles = [
            [1, 1, 1]
            , [0, 1, 0]
        ]
        # phases = [[0.6, 0.99], [0.1, 0.77]]
        # profiles = [
        #     [1, 0, 1]
        #     , [0, 1, 0]
        # ]
    elif profile is 'PGC1250kHz':
        period = 0.0008
        offgap = 3 * 26.24e-9 / (period * 1e-3)  # 3 gamma between MOT off, FORT on
        phases = [[0.26, 0.48], [0.56, 0.99]]  # wide FORT, narrow MOT
        profiles = [
            [1, 0, 1]
            , [0, 1, 0]
        ]

    cycles = int(duration / period)
    # print("cycles")
    # print(cycles)
    label(t + period, 'readout c1')
    label(t + cycles * period / 2, 'readout half')
    # print(t + cycles * period / 2)
    channels = [my_MOT_SW_channel, my_FORT_SW_channel]

    t = HSDIO_repeat(t, chop_readout(channels, phases, profiles, period),
                     cycles)
    return t


def chopped_blowaway(t_start, t_end, t_period,
                     t_pulsewidth):  # ,profileFORT='on',profileMOT='Blowaway',labl='blowaway'):
    """
    The blow-away phase in which the MOT and FORT are alternately chopped
    Args:
        't_start': time to start in ms from cycle trigger
        't_end': time to stop in ms from cycle trigger
        't_period': chop period in ms
        't_pulsewidth': pulse width in ms. offset between MOT and FORT controlled by
            independent variable t_BA_offset
        'labl': the label to be used in the functional waveforms graph that doesn't actually work 2020.11.13
    Return:
        'func' the HSDIO_repeat function we built here
    """
    # TODO: This is similar enough to the chopped readout function to merit defining a generic mot pulse function

    if t_BA > 0:
        label(t_start, "Blowaway")  # for functional waveforms graph

        # set up the pulse switching parameters
        channels = [my_MOT_SW_channel, my_FORT_SW_channel]
        profiles = [
            [1, 0, 1],  # MOT on, MOT off, MOT on
            [0, 1, 0]  # FORT off, FORT on, FORT off
        ]

        # convert BA offset to a phase profile
        phi_fudge = 0.07  # difference between MOT and FORT start
        phi0_MOT = t_BA_offset / t_period + phi_fudge
        phi1_MOT = phi0_MOT + t_pulsewidth / t_period
        phi0_FORT = t_BA_offset / t_period
        phi1_FORT = phi0_FORT + (1 - t_pulsewidth / t_period)  # + phi_fudge

        phases = [
            [phi0_MOT, phi1_MOT],  # pulse starting phase, ending phase
            [phi0_FORT, phi1_FORT]
        ]

        cycles = int(round((t_end - t_start) / t_period))

        func = HSDIO_repeat(t_start, chop_readout(channels, phases, profiles, t_period), cycles)
        return func


def opticalpumping(t, duration):
    """Optical pumping to the clock state."""
    # Note that camera trigger is not included here. Exposure control needs to be done indepdently
    # Also magnetic field control is done sepearately.
    if duration > 0:
        label(t, 'OP')
        # chop FORT and MOT out of phase
        cycles = int(duration * 1000 * op_chop_freq_MHz)
        period_ms = 0.001 / op_chop_freq_MHz
        label(t + period_ms, 'OP c1')
        label(t + cycles * period_ms / 2, 'OP half')
        print(t + cycles * period_ms / 2)
        channels = [op_aom_switch_chan, my_FORT_SW_channel]
        # phases = [[0.3, 0.6], [0.1, 0.6]]
        phases = [[0.60, 0.90], [0.1, 0.6]]
        profiles = [
            [1, 0, 1],  # OP on is 0. off is 1
            [1, 0, 1]  # FORT chopping: 1 , 0 , 1, no chopping : 1 1 1
        ]
        t = HSDIO_repeat(t, chop_readout(channels, phases, profiles, period_ms), cycles)
    else:
        print("non-zero duration is required. this repeat function will do nothing")
    return t

#TODO see whether this or the original function was used, delete the others
def opticalpumping2(t, duration):
    """Optical pumping to the clock state."""
    # Note that camera trigger is not included here. Exposure control needs to be done indepdently
    # Also magnetic field control is done sepearately.
    if duration > 0:
        label(t, 'OP')
        # chop FORT and MOT out of phase
        cycles = int(duration * 1000 * op_chop_freq_MHz)
        period_ms = 0.001 / op_chop_freq_MHz
        label(t + period_ms, 'OP c1')
        label(t + cycles * period_ms / 2, 'OP half')
        print(t + cycles * period_ms / 2)
        channels = [ryd480_pointing_aom_switch_chan, my_FORT_SW_channel]
        phases = [[0.3, 0.6], [0.1, 0.6]]
        profiles = [
            [0, 1, 0],  # 780B on is 1. off is 0
            [1, 0, 1]  # FORT chopping: 1 , 0 , 1, no chopping : 1 1 1
        ]
        t = HSDIO_repeat(t, chop_readout(channels, phases, profiles, period_ms), cycles)
    else:
        print("non-zero duration is required. this repeat function will do nothing")
    return t


# TODO use conveyor dds functions instead
def prepareF1(t, duration):
    """This function will leave MOT light on without repumper so atoms are depopulated from F=2 and pumped into F=1"""
    if t > 0 and duration > 0:  # make sure timings are valid
        exp.fort_aom_switch.profile(t, 'on')
        exp.fort_aom_switch.profile(t + duration, 'on')
        exp.fort_dds.profile(t, 'on')
        exp.fort_dds.profile(t + duration, 'on')
        exp.cooling_aom_dds.profile(t, 'RO')
        exp.cooling_aom_switch.profile(t, 'on')
        exp.cooling_aom_switch.profile(t + duration, 'off')
        exp.repumper_aom_switch.profile(t, 'off')
        AO(t, repumper_VCA, 0)
    else:
        print
        "make sure your timings are valid"


# TODO use conveyor dds functions instead
def FORTdrop(t, duration):
    """ This function will turn off the 1064 FORT for the given duration and back on afterwards"""
    if t > 0 and duration > 0:  # make sure timings are valid
        exp.fort_aom_switch.profile(t, 'off')
        exp.fort_aom_switch.profile(t + duration, 'on')
        exp.fort_dds.profile(t, 'off')
        exp.fort_dds.profile(t + duration, 'on')

# TODO copy Rydberg functions from rb_waveform.py and define Rydberg DDS and switch channels in functional_waveforms_ffpr.py

"""
*******************************************************************************
# Main Block
# Setting timing sequences for an experiment.
# For diagnostics purpose, sequences are low level coded.
*******************************************************************************
"""

t = 0  # the experiment time in ms. increment throughout the waveform.

exp.camera.pulse_length = t_exposure  # Changes HSDIO pulse width to control exposure

# Abstractized experiment control

## For normal experiment
if ExpMode == 0:

    # The first argument of every function below is the time which the action should occur in ms wrt to the time the
    # experiment trigger is received by the AnalogInput. The waveform here is only loosely laid out in chronological
    # order, so the time of each action is given as an independent variable or explicitly, rather than simply passing
    # the variable 't' and incrementing it throughout. We may want to change this later.

    # turn on the critical fiber and xfer cavity signals
    # TODO

    t_coil_turn_on = 8 # time to wait for coils to stabilize. can probably be shorter than this.

    # turn on coils and repumper VCA
    AO(0, quadrupole1, coil_driver_polarity * I_Q1)
    AO(0, quadrupole2, coil_driver_polarity * I_Q2)
    AO(0, shimcoil_3DX, coil_driver_polarity * ShimX_Loading)  # X
    AO(0, shimcoil_3DY, coil_driver_polarity * ShimY_Loading)  # Y
    AO(0, shimcoil_3DZ, coil_driver_polarity * ShimZ_Loading)  # Z
    AO(0, repumper, loading_RP_V)

    # shutter initialization. shutters help with background, especially during Rydberg experiments
    exp.mot_3d_x_shutter_switch.profile(0, 'on')
    exp.mot_3d_y_shutter_switch.profile(0, 'on')
    exp.mot_3d_z1_shutter_switch.profile(0, 'on')
    exp.mot_3d_z2_shutter_switch.profile(0, 'on')  # TODO: this might be unused.
    exp.repumper_shutter_switch.profile(0,
                                        'on')  # TODO: i don't recall having a RP specific shutter installed -- check this

    # turn on conveyor aoms and leave them on. use switches to block RF outside experiment time.
    # profile switching activates the RAM sequence to move the atoms
    exp.conveyor_front_aom_dds.profile(t, 'on')
    exp.conveyor_back_aom_dds.profile(t, 'on')
    exp.conveyor_front_aom_switch.profile(t, 'off')
    exp.conveyor_back_aom_switch.profile(t, 'off')

    # pulse on conveyor aoms briefly to check power levels. NE = Noise Eater, aka Thorlabs Motorized Rotators
    exp.FORT_NE_trigger_switch.profile(0, 'off')
    exp.FORT_NE_trigger_switch.profile(t_NE_FORT_trigger_start, 'on')
    exp.FORT_NE_trigger_switch.profile(t_NE_FORT_trigger_end, 'off')
    exp.conveyor_front_aom_switch.profile(1, 'off')
    exp.conveyor_back_aom_switch.profile(1, 'off')

    # UV pulse
    exp.UV_trigger_switch.profile(0, 'off')
    exp.UV_trigger_switch.profile(0.1, 'on')
    exp.UV_trigger_switch.profile(0.1 + t_UVpulse, 'off')

    # for viewing the MOT beam photodiode signals on an oscilloscope. useful for debugging
    exp.MOT_scope_trigger_switch.profile(0, 'off')
    exp.MOT_scope_trigger_switch.profile(140, 'on')
    exp.MOT_scope_trigger_switch.profile(145, 'off')

    # another trigger. might not need this
    exp.scope_trigger_switch.profile(140, 'on')
    exp.scope_trigger_switch.profile(141, 'off')

    # take a shot of the MOT
    exp.camera.pulse_length = 5  # t_MOT_imaging_exposure # Changes HSDIO pulse width to control exposure
    t_readout_MOT = 95
    exp.camera.take_shot(t_readout_MOT)

    # set MOT turn off and FORT turn off times
    t_loading_extension = 20
    exp.mot_aom_switch.profile(t_3DMOT_cutoff + t_loading_extension, 'off')
    exp.repumper_aom_switch.profile(t_3DMOT_cutoff + t_loading_extension, 'off')  #####
    # AO(130, repumper_VCA, 10) # time should reference the MOT cutoff. check this.
    exp.fort_dds.profile(t_3DMOT_cutoff + t_loading_extension, 'on')

    # turn on conveyor AOMS for loading atoms from MOT
    exp.conveyor_front_aom_switch.profile(t_FORT_loading, 'on')
    exp.conveyor_back_aom_switch.profile(t_FORT_loading, 'on')

    # Camera shot 1: fluorescence image of atoms in the dipole trap
    t_shot1 = t_FORT_loading + 60 # the shot start time. takes a while to load atoms?
    exp.fort_dds.profile(t_shot1, 'on')
    exp.cooling_aom_dds.profile(t_shot1, 'RO')
    AO(t_shot1 - t_coil_turn_on, shimcoil_3DX, coil_driver_polarity * shimX_RO)
    AO(t_shot1 - t_coil_turn_on, shimcoil_3DY, coil_driver_polarity * shimY_RO)
    AO(t_shot1 - t_coil_turn_on, shimcoil_3DZ, coil_driver_polarity * shimZ_RO)
    exp.camera.pulse_length = t_exposure_1st_atomshot
    AO(t_shot1, repumper, loading_RP_V)
    readout(t_shot1, t_readoutduration, RO_chop_period)
    exp.camera.take_shot(t_shot1)
    t_end_shot1 = t_shot1 + t_readoutduration
    AO(t_shot, repumper_VCA, loading_RP_V)
    exp.mot_aom_switch.profile(t_end_shot1 + 0.001, 'off')
    exp.repumper_aom_switch.profile(t_shot1, 'on')
    AO(t_end_shot + 0.05, repumper, 0)
    exp.conveyor_front_aom_switch.profile(t_end_shot1, 'on')
    exp.conveyor_back_aom_switch.profile(t_end_shot1, 'on')

    if t_PGC_duration > 0:
        pass # no PGC for now. do later.

    # move the atoms into the cavity and back
    # this is one waveform in RAM per channel for both directions, so the time between the end of the move in and start
    # of move out needs to be set in the waveform defined in the DDS window.
    # TODO

    # mock parameters for dry run of this waveform without cavity probing.
    t_in_cavity = 2
    t_conveyor_ramp = 1

    t_cavity_duration = 2*t_conveyor_ramp + t_in_cavity

    # Camera shot 2: fluorescence image of atoms in the dipole trap
    t_shot2 = t_cavity_duration + t_PGC_duration + t_end_shot1
    exp.conveyor_front_aom_switch.profile(t_shot, 'on')
    exp.cooling_aom_dds.profile(t_shot, 'RO')
    AO(t_shot2 - t_coil_turn_on, shimcoil_3DX, coil_driver_polarity * shimX_RO)
    AO(t_shot2 - t_coil_turn_on, shimcoil_3DY, coil_driver_polarity * shimY_RO)
    AO(t_shot2 - t_coil_turn_on, shimcoil_3DZ, coil_driver_polarity * shimZ_RO)
    exp.camera.pulse_length = t_exposure_1st_atomshot
    AO(t_shot2, repumper, loading_RP_V)
    readout(t_shot2, t_readoutduration, RO_chop_period)
    exp.camera.take_shot(t_shot2)
    t_end_shot2 = t_shot2 + t_readoutduration
    AO(t_shot2, repumper, loading_RP_V)
    exp.mot_aom_switch.profile(t_end_shot2 + 0.001, 'off')
    exp.repumper_aom_switch.profile(t_shot2, 'on')
    AO(t_end_shot2 + 0.05, repumper_VCA, 0)
    exp.conveyor_front_aom_switch.profile(t_end_shot2, 'on')
    exp.conveyor_back_aom_switch.profile(t_end_shot2, 'on')

    ############################## End of normal experiment #######################################################

## Turn everything on. Sometimes useful for diagnostics
elif ExpMode == 'on':

    ####### Continous MOT loading mode (expmode code 2) #############
    # FORT is also on.
    # Camera will take pictures

    ## for DDS test
    # exp.xfer_cav_offset_dds.profile(0, 'r3')  # this is off
    exp.xfer_cav_offset_dds.profile(171-.0005, 'off')  # on
    # exp.xfer_cav_offset_dds.profile(171.0005, 'r3')  # this is off

    ## Initilization
    AO(0, quadrupole1, coil_driver_polarity * I_Q1)
    AO(0, quadrupole2, coil_driver_polarity * I_Q2)
    AO(0, shimcoil_3DX, coil_driver_polarity * ShimX_Loading)
    AO(0, shimcoil_3DY, coil_driver_polarity * ShimY_Loading)
    AO(0, shimcoil_3DZ, coil_driver_polarity * ShimZ_Loading)
    # AO(0,shimcoil_3DX,coil_driver_polarity*shimX_RO) #X
    # AO(0,shimcoil_3DY,coil_driver_polarity*shimY_RO) #Y
    # AO(0,shimcoil_3DZ,coil_driver_polarity*shimZ_RO) #Z
    AO(0, repumper_VCA, loading_RP_V)
    # for i in range(20):
    #     AO(i*10,quadrupole1,coil_driver_polarity*I_Q1*((2000-(i*10))/2000))
    #     AO(i*10,quadrupole2,coil_driver_polarity*I_Q2*((2000-(i*10))/2000))
    # for i in range(20):
    #     AO(i*10+200,quadrupole1,coil_driver_polarity*I_Q1*((1800+(i*10))/2000))
    #     AO(i*10+200,quadrupole2,coil_driver_polarity*I_Q2*((1800+(i*10))/2000))
    AO(100, quadrupole1, coil_driver_polarity * I_Q1)
    AO(100, quadrupole2, coil_driver_polarity * I_Q2)
    AO(100, shimcoil_3DX, coil_driver_polarity * ShimX_Loading)  # X
    AO(100, shimcoil_3DY, coil_driver_polarity * ShimY_Loading)  # Y
    AO(100, shimcoil_3DZ, coil_driver_polarity * ShimZ_Loading)  # Z
    # AO(0,shimcoil_3DX,coil_driver_polarity*shimX_RO) #X
    # AO(0,shimcoil_3DY,coil_driver_polarity*shimY_RO) #Y
    # AO(0,shimcoil_3DZ,coil_driver_polarity*shimZ_RO) #Z
    # AO(0,repumper_VCA,loading_RP_V)

    # looking for molasses
    # AO(0,quadrupole1,coil_driver_polarity*I_Q1*0)
    # AO(0,quadrupole2,coil_driver_polarity*I_Q2*0)
    # AO(0,shimcoil_3DX,coil_driver_polarity*shimX_RO) #X
    # AO(0,shimcoil_3DY,coil_driver_polarity*shimY_RO) #Y
    # AO(0,shimcoil_3DZ,coil_driver_polarity*shimZ_RO) #Z
    # # AO(0,shimcoil_3DX,coil_driver_polarity*shimX_RO) #X
    # # AO(0,shimcoil_3DY,coil_driver_polarity*shimY_RO) #Y
    # # AO(0,shimcoil_3DZ,coil_driver_polarity*shimZ_RO) #Z
    # AO(0,repumper_VCA,10)
    # # for i in range(20):
    # #     AO(i*10,quadrupole1,coil_driver_polarity*I_Q1*((2000-(i*10))/2000))
    # #     AO(i*10,quadrupole2,coil_driver_polarity*I_Q2*((2000-(i*10))/2000))
    # # for i in range(20):
    # #     AO(i*10+200,quadrupole1,coil_driver_polarity*I_Q1*((1800+(i*10))/2000))
    # #     AO(i*10+200,quadrupole2,coil_driver_polarity*I_Q2*((1800+(i*10))/2000))
    # AO(100,quadrupole1,coil_driver_polarity*I_Q1*0)
    # AO(100,quadrupole2,coil_driver_polarity*I_Q2*0)
    # AO(100,shimcoil_3DX,coil_driver_polarity*shimX_RO) #X
    # AO(100,shimcoil_3DY,coil_driver_polarity*shimY_RO) #Y
    # AO(100,shimcoil_3DZ,coil_driver_polarity*shimZ_RO) #Z
    # # AO(0,shimcoil_3DX,coil_driver_polarity*shimX_RO) #X
    # # AO(0,shimcoil_3DY,coil_driver_polarity*shimY_RO) #Y
    # # AO(0,shimcoil_3DZ,coil_driver_polarity*shimZ_RO) #Z
    # AO(100,repumper_VCA,10)

    exp.raman_aom_switch.profile(0, 'on')
    # exp.raman_aom_switch.profile(0,'off') #### dd
    exp.ryd780a_aom_switch.profile(0, 'on')
    # exp.ryd780a_dds.profile(0, 'r2')
    exp.ryd480_pointing_aom_switch.profile(0, 'on')
    exp.ryd480_pointing_aom_dds.profile(0, 'r2')
    # exp.xfer852_aom_dds.profile(0, 'r2')
    exp.xfer852_aom_switch.profile(0, 'on')
    # to turn blue off, please uncomment
    # exp.xfer_cav_offset_dds.profile(0,'off')
    # exp.xfer_cav_offset_switch.profile(0,'off')

    # to turn blue on all the time
    # exp.xfer_cav_offset_dds.profile(0, 'r2')
    # exp.xfer_cav_offset_switch.profile(0, 'on')

    exp.fort_aom_switch.profile(0, 'off')
    exp.fort_dds.profile(0, 'off')
    #
    # exp.fort_aom_switch.profile(0,'on')
    # exp.fort_dds.profile(0,'on')

    exp.MOT_scope_trigger_switch.profile(0, 'off')

    exp.mot_3d_z2_shutter_switch.profile(0, 'on')  # switched polarity
    # **** these were commented out July - 8/22 ****
    # exp.mot_3d_x_shutter_switch.profile(t_x_shutter_open,'off')
    # exp.mot_3d_x_shutter_switch.profile(t_x_shutter_close,'on')
    # exp.mot_3d_y_shutter_switch.profile(t_y_shutter_open,'off')
    # exp.mot_3d_y_shutter_switch.profile(t_y_shutter_close,'on')
    # exp.mot_3d_z1_shutter_switch.profile(t_z1_shutter_open,'off')
    # exp.mot_3d_z1_shutter_switch.profile(t_z1_shutter_close,'on')
    # # ****
    exp.scope_trigger_switch.profile(170, 'on')
    exp.scope_trigger_switch.profile(171, 'off')
    exp.op_dds.profile(0, 'on')
    exp.op_aom_switch.profile(0, 'on')
    exp.repumper_aom_switch.profile(0, 'on')
    exp.mot_3d_x_shutter_switch.profile(0, 'on')
    exp.mot_3d_y_shutter_switch.profile(0, 'on')
    exp.mot_3d_z1_shutter_switch.profile(0, 'on')
    exp.repumper_shutter_switch.profile(0, 'on')
    exp.conveyor_front_aom_switch.profile(0, 'on')
    exp.conveyor_front_aom_dds.profile(0, 'on')
    # exp.conveyor_front_aom_switch.profile(0,'off')
    # exp.conveyor_front_aom_dds.profile(0,'off')

    ## 2D MOT Loading Phase
    exp.cooling_aom_dds.profile(0, 'MOT')  # 'PGC')
    #    exp.fort_dds.profile(0,'off')
    exp.cooling_aom_switch.profile(0, 'on')

    t_start = 50
    exp.camera.take_shot(t_start)

    t_readout_2nd = 110
    exp.camera.take_shot(t_readout_2nd)

    ## Blue imaging
    # Blue480(t_start_blue_imaging,t_blue_exposure,'off')
    # exp.camera.pulse_length=t_blue_exposure # Changes HSDIO pulse width to control exposure
    t_readout_3rd = 170
    exp.camera.take_shot(t_readout_3rd)
    # exp.ryd780a_aom_switch.profile(t2_PGcamera,'on')
    # exp.ryd780a_dds.profile(t2_PGcamera,'r2')

############################## End of mode 2,  Shutter calibration #######################################################

elif ExpMode == 'off':

    ####### Turn all signals off, except MOT aoms #############
    # i have not yet carefully checked that i didn't miss something - PH 2021.04.13

    ao_channels = [quadrupole1, quadrupole2, shimcoil_3DX, shimcoil_3DY, shimcoil_3DZ, repumper_VCA]
    for chan in ao_channels:
        AO(0, chan, 0)
        AO(1, chan, 0)
        # needs at least one transition, else nidaqmx.task.timing.samp_clk_timing freaks out in instr. server

    # TODO: this doesn't work. not sure why. nothing prints here either
    # for rf_sig in dir(exp):
    #     if hasattr(rf_sig, 'profile'):
    #         try:
    #             getattr(rf_sig, 'profile')(0, 'off')
    #             logger.info("turning off {}".format(rf_sig.__class__.__name__()))
    #         except:
    #             logger.warning("{} has no 'off' profile, but it should!".format(type(rf_sig)))

    exp.raman_aom_switch.profile(0, 'off')
    # exp.ryd780_aom_switch.profile(0, 'off') # TODO define switch
    exp.ryd480_pointing_aom_switch.profile(0, 'off')
    exp.ryd480_pointing_aom_dds.profile(0, 'off')
    exp.xfer852_aom_dds.profile(0, 'off')
    exp.xfer852_aom_switch.profile(0, 'off')
    exp.xfer_cav_offset_dds.profile(0,'off')
    exp.xfer_cav_offset_switch.profile(0,'off')
    exp.xfer_cav_offset_dds.profile(0, 'off')
    exp.xfer_cav_offset_switch.profile(0, 'off')
    exp.fort_aom_switch.profile(0, 'off')
    # exp.fort_dds.profile(0, 'off')
    exp.fort_aom_switch.profile(0,'off')
    exp.MOT_scope_trigger_switch.profile(0, 'off')
    exp.mot_3d_z2_shutter_switch.profile(0, 'off')  # switched polarity
    exp.op_dds.profile(0, 'off')
    exp.op_aom_switch.profile(0, 'off')
    exp.repumper_aom_switch.profile(0, 'off')
    exp.mot_3d_x_shutter_switch.profile(0, 'off')
    exp.mot_3d_y_shutter_switch.profile(0, 'off')
    exp.mot_3d_z1_shutter_switch.profile(0, 'off')
    exp.repumper_shutter_switch.profile(0, 'off')
    exp.conveyor_front_aom_switch.profile(0, 'off')
    exp.conveyor_front_aom_dds.profile(0, 'off')
    exp.cooling_aom_dds.profile(0, 'MOT') # we don't have an "off" profile yet :P
    exp.cooling_aom_switch.profile(0, 'off')

    # mot aoms on only
    # exp.cooling_aom_switch.profile(t, 'on')
    # exp.repumper_aom_switch.profile(0, 'on')

else:
    print
    "Undefined Experiment mode : {}".format(ExpMode)
