"""These are the waveform functions for the Rb project.
They define the operation of the HSDIO, AO and DAQmxDO outputs.
Use the functions HSDIO(time, channel, state), DO(time, channel, state), AO(time, channel, voltage) and label(time, text).
The user should ensure that all waveform functions take in the start time as the first parameter,
and return the end time.
In order to use this class in the experiment does something like:
------------------------------------------------------------------
import exp_functional_waveforms.functional_waveforms_rb as Rb
HSDIO = experiment.LabView.HSDIO.add_transition
AO = experiment.LabView.AnalogOutput.add_transition
DO = experiment.LabView.DAQmxDO.add_transition
label = experiment.functional_waveforms_graph.label
print 'yo'
exp = Rb.Rb(HSDIO, AO, DO, label)
print 'yolo'
t = 0 # start time
# turn the mot on
exp.mot_aom_switch.profile(t, 'on')
t=60
# turn the mot off
exp.mot_aom_switch.profile(t, 'off')
------------------------------------------------------------------
"""


from dds import DDS
from switch import Switch
from camera import Camera

'''I think these constants need to be defined here so that they can be
overwritten at the global scope.
'''
################################################################################
# Example DDS Profile ##########################################################
################################################################################
# ex_dds_pinout = (-1,2,5) # pins on the HDSIO to toggle DDS pins. -1: not in use
# ex_dds_profiles = {
#   'ex1' = (0,0,1) # pin 5 outputs high, dds sees 4 in grey code
# }

################################################################################
# Adruino DDS Profile ##########################################################
################################################################################
test_dds_pinout = (-1,-1,-1) #
test_dds_profiles = {
  'test1' : (0,0,0) # only the last pin high
}

################################################################################
# 3D MOT DDS SETUP #############################################################
################################################################################
mot_3d_dds_pinout = (0,1,2)
mot_3d_dds_profiles = {
    'MOT' : (0,0,0),#  (pin2, pin1, pin0)
    'PGC' : (0,0,1),
    'Blowaway' : (0,1,0),
    'RO' : (0,1,1),
    'PGC2' : (1,0,0),
    'GM': (1,1,0)  # coming soon? O__o
}

################################################################################
# FORT DDS SETUP ################################################################
################################################################################
fort_dds_pinout = (-1,3,4) # -1 indicates pins that are not being used
fort_dds_profiles = {
    'on' : (0,0,0),
    'off' : (0,0,1),
    'science' : (0,1,0),
    'low' : (0,1,1)
}
################################################################################
# 2D MOT DDS SETUP ################################################################
################################################################################
mot_2d_dds_pinout = (-1,-1,5) # -1 indicates pins that are not being used
mot_2d_dds_profiles = {
    'on' : (0,0,0),
    'off' : (0,0,1)
}
################################################################################
# OP DDS SETUP ################################################################
################################################################################
op_dds_pinout = (-1,-1,6) # -1 indicates pins that are not being used
op_dds_profiles = {
    'on' : (0,0,0),
    'off' : (0,0,1)
}
################################################################################
# Microwave DDS SETUP ################################################################
################################################################################
microwave_dds_pinout = (-1,28,29) # -1 indicates pins that are not being used. (P2, P1, P0)
microwave_dds_profiles = {
    'off' : (0,0,0),
    'on' : (0,0,1),
}

################################################################################
# Ryd 780A DDS SETUP ################################################################
################################################################################
ryd780a_dds_pinout = (-1,30,31) # -1 indicates pins that are not being used
ryd780a_dds_profiles = {
    'off' : (0,0,0),
    'r1' : (0,0,1),
    'r2' : (0,1,0),
    'PG' : (0,1,1)
}

################################################################################
# Ryd 780B DDS SETUP ################################################################
################################################################################
ryd780b_dds_pinout = (-1,34,33) # -1 indicates pins that are not being used
ryd780b_dds_profiles = {
    'off' : (0,0,0),
    'r1' : (0,0,1),
    'r2' : (0,1,0),
    'r3' : (0,1,1)
}
################################################################################
# Red pointing AOM DDS SETUP ################################################################
################################################################################
red_pointing_dds_pinout = (-1,24,25) # -1 indicates pins that are not being used
red_pointing_dds_profiles = {
    'off' : (0,0,0),
    'addressing' : (0,0,1),
    'r2' : (0,1,0),
    'PG' : (0,1,1)
}
################################################################################
# Blue pointing AOM DDS SETUP ################################################################
################################################################################
blue_pointing_dds_pinout = (-1,26,27) # -1 indicates pins that are not being used
blue_pointing_dds_profiles = {
    'off' : (0,0,0),
    'r1' : (0,0,1),
    'r2' : (0,1,0),
    'r3' : (0,1,1)
}

################################################################################
# 3D MOT AOM SWITCH SETUP #########################################################
################################################################################
mot_aom_switch_chan = 7
# this is the default profile, we dont have to pass it in if we dont want to
mot_aom_switch_profile = {'on':1, 'off':0}
# timing delay parameter
mot_aom_switch_delay = 0

################################################################################
# FORT AOM SWITCH SETUP ########################################################
################################################################################
fort_aom_switch_chan = 8
# this is the default profile, we dont have to pass it in if we dont want to
fort_aom_switch_profile = {'on':1, 'off':0}
# timing delay parameter
fort_aom_switch_delay = 0

################################################################################
# 2D MOT AOM SWITCH SETUP ########################################################
################################################################################
mot_2d_aom_switch_chan = 9
# this is the default profile, we dont have to pass it in if we dont want to
mot_2d_aom_switch_profile = {'on':1, 'off':0}
# timing delay parameter
mot_2d_aom_switch_delay = 0

################################################################################
# OP AOM SWITCH SETUP ########################################################
################################################################################
op_aom_switch_chan = 10
# this is the default profile, we dont have to pass it in if we dont want to
op_aom_switch_profile = {'on':0, 'off':1}
# timing delay parameter
op_aom_switch_delay = 0

################################################################################
# HF Repumper AOM SWITCH SETUP ##########################################################
################################################################################
hf_aom_switch_chan = 11
# this is the default profile, we dont have to pass it in if we dont want to
hf_aom_switch_profile = {'on':0, 'off':1}
# timing delay parameter
hf_aom_switch_delay = 0

################################################################################
# 3D MOT X Shutter SWITCH SETUP ##########################################################
################################################################################
mot_3d_x_shutter_switch_chan = 12
# this is the default profile, we dont have to pass it in if we dont want to
mot_3d_x_shutter_switch_profile = {'on':1, 'off':0}
# timing delay parameter
mot_3d_x_shutter_switch_delay = 0

################################################################################
# 3D MOT Y Shutter SWITCH SETUP ##########################################################
################################################################################
mot_3d_y_shutter_switch_chan = 13
# this is the default profile, we dont have to pass it in if we dont want to
mot_3d_y_shutter_switch_profile = {'off':1, 'on':0}
# timing delay parameter
mot_3d_y_shutter_switch_delay = 0

################################################################################
# 3D MOT Z1 Shutter SWITCH SETUP ##########################################################
################################################################################
mot_3d_z1_shutter_switch_chan = 14
# this is the default profile, we dont have to pass it in if we dont want to
mot_3d_z1_shutter_switch_profile = {'on':1, 'off':0}
# timing delay parameter
mot_3d_z1_shutter_switch_delay = 0

################################################################################
# 3D MOT Z2 Shutter SWITCH SETUP ##########################################################
################################################################################
mot_3d_z2_shutter_switch_chan = 15
# this is the default profile, we dont have to pass it in if we dont want to
mot_3d_z2_shutter_switch_profile = {'on':1, 'off':0}
# timing delay parameter
mot_3d_z2_shutter_switch_delay = 0

################################################################################
# Repumper Shutter SWITCH SETUP ##########################################################
################################################################################
repumper_shutter_switch_chan = 16
# this is the default profile, we dont have to pass it in if we dont want to
repumper_shutter_switch_profile = {'on':1, 'off':0}
# timing delay parameter
repumper_shutter_switch_delay = 0


################################################################################
# microwave SWITCH SETUP ##########################################################
################################################################################
microwave_switch_chan = 18
# this is the default profile, we dont have to pass it in if we dont want to
microwave_switch_profile = {'on':0, 'off':1}
# timing delay parameter
microwave_switch_delay = 0

################################################################################
# Ground Raman AOM SWITCH SETUP ##########################################################
################################################################################
ground_aom_switch_chan = 19
# this is the default profile, we dont have to pass it in if we dont want to
ground_aom_switch_profile = {'on':1, 'off':0}
# timing delay parameter
ground_aom_switch_delay = 0

################################################################################
# ANDOR EMCCD CAMERA SETUP #####################################################
################################################################################
andor_trigger_chan = 20
# this is the default profile, we dont have to pass it in if we dont want to
andor_trigger_profile = {'on':1, 'off':0}
# timing delay parameter
andor_trigger_delay = 0

################################################################################
# Ryd 780A AOM SWITCH SETUP ##########################################################
################################################################################
ryd780a_aom_switch_chan = 21
# this is the default profile, we dont have to pass it in if we dont want to
ryd780a_aom_switch_profile = {'on':1, 'off':0}
# timing delay parameter
ryd780a_aom_switch_delay = 0
################################################################################
# Ryd 780B AOM SWITCH SETUP ##########################################################
################################################################################
ryd780b_aom_switch_chan = 32
# this is the default profile, we dont have to pass it in if we dont want to
ryd780b_aom_switch_profile = {'on':1, 'off':0}
# timing delay parameter
ryd780b_aom_switch_delay = 0

################################################################################
# Red Pointing AOM SWITCH SETUP ##########################################################
################################################################################
red_pointing_aom_switch_chan = 22
# this is the default profile, we dont have to pass it in if we dont want to
red_pointing_aom_switch_profile = {'on':1, 'off':0}
# timing delay parameter
red_pointing_aom_switch_delay = 0

################################################################################
# Blue Pointing AOM SWITCH SETUP ##########################################################
################################################################################
blue_pointing_aom_switch_chan = 23
# this is the default profile, we dont have to pass it in if we dont want to
blue_pointing_aom_switch_profile = {'on':1, 'off':0}
# timing delay parameter
blue_pointing_aom_switch_delay = 0

################################################################################
# 3DMOT Scope Trigger SETUP ###############################################
################################################################################
MOT_scope_trigger_chan = 44
# this is the default profile, we dont have to pass it in if we dont want to
MOT_scope_trigger_profile = {'on':1, 'off':0} # Does this work?
# timing delay parameter
MOT_scope_trigger_delay = 0


################################################################################
# FORT Scope Trigger SETUP ###############################################
################################################################################
scope_trigger_chan = 45
# this is the default profile, we dont have to pass it in if we dont want to
scope_trigger_profile = {'on':1, 'off':0} # Does this work?
# timing delay parameter
scope_trigger_delay = 0

################################################################################
# Pointgrey camera no.1 Trigger SETUP ###############################################
################################################################################
pointgrey_trigger_chan = 46
# this is the default profile, we dont have to pass it in if we dont want to
pointgrey_trigger_profile = {'on':1, 'off':0} # Does this work?
# timing delay parameter
pointgrey_trigger_delay = 0

################################################################################
# FORT Noise eater Trigger SETUP ###############################################
################################################################################
FORT_NE_trigger_chan = 47
# this is the default profile, we dont have to pass it in if we dont want to
FORT_NE_trigger_profile = {'on':1, 'off':0} # Does this work?
# timing delay parameter
FORT_NE_trigger_delay = 0

################################################################################
# rydberg 780A Noise eater Trigger SETUP ###############################################
################################################################################
ryd780A_NE_trigger_chan = 48
# this is the default profile, we dont have to pass it in if we dont want to
ryd780A_NE_trigger_profile = {'on':1, 'off':0} # Does this work?
# timing delay parameter
ryd780A_NE_trigger_delay = 0

################################################################################
# FORT Pulse Generator Trigger SETUP ###############################################
################################################################################
FORT_PG_trigger_chan = 50
# this is the default profile, we dont have to pass it in if we dont want to
FORT_PG_trigger_profile = {'on':1, 'off':0}
# timing delay parameter
FORT_PG_trigger_delay = 0

################################################################################
# FORT Switch1 Trigger SETUP ###############################################
################################################################################
FORT_SW1_trigger_chan = 51
# this is the default profile, we dont have to pass it in if we dont want to
FORT_SW1_trigger_profile = {'on':1, 'off':0}
# timing delay parameter
FORT_SW1_trigger_delay = 0

################################################################################
# FORT Switch2 Trigger SETUP ###############################################
################################################################################
FORT_SW2_trigger_chan = 52
# this is the default profile, we dont have to pass it in if we dont want to
FORT_SW2_trigger_profile = {'on':1, 'off':0}
# timing delay parameter
FORT_SW2_trigger_delay = 0

################################################################################
# Pointgrey camera no.2 Trigger SETUP ###############################################
################################################################################
pointgrey2_trigger_chan = 53 # 53 - 32 = 21
# this is the default profile, we dont have to pass it in if we dont want to
pointgrey2_trigger_profile = {'on':1, 'off':0} # Does this work?
# timing delay parameter
pointgrey2_trigger_delay = 0

################################################################################
# UV LIAD SETUP ###############################################
################################################################################
UV_trigger_chan = 57 # 57 - 32 = 25
# this is the default profile, we dont have to pass it in if we dont want to
UV_trigger_profile = {'on':1, 'off':0} # Does this work?
# timing delay parameter
UV_trigger_delay = 0


################################################################################
################################################################################
################################################################################
class Rb(object):
    '''holds all of the experiment's standard functional waveforms
    I need to be able to pass in the hardware classes, so a class is convenient
    '''

    def __init__(self, HSDIO, AO, DO, label):

        # DDS 1. declare dds channels. Up to four.
        self.mot_3d_dds = DDS(HSDIO, mot_3d_dds_pinout, mot_3d_dds_profiles)
        self.fort_dds = DDS(HSDIO, fort_dds_pinout, fort_dds_profiles)
        self.mot_2d_dds = DDS(HSDIO, mot_2d_dds_pinout, mot_2d_dds_profiles)
        self.op_dds = DDS(HSDIO, op_dds_pinout, op_dds_profiles)

        # DDS .. 2?
        #self.ryd780b_dds_dds = DDS(HSDIO, ryd780b_dds_pinout, ryd780b_dds_profiles)
        self.red_pointing_dds = DDS(HSDIO, red_pointing_dds_pinout, red_pointing_dds_profiles)
        self.blue_pointing_dds = DDS(HSDIO, blue_pointing_dds_pinout, blue_pointing_dds_profiles)
        self.microwave_dds = DDS(HSDIO, microwave_dds_pinout, microwave_dds_profiles)
        self.ryd780a_dds = DDS(HSDIO, ryd780a_dds_pinout, ryd780a_dds_profiles)

        # 3rd DDS - but how to we bind this to a particular DDS???
        self.ryd780b_dds = DDS(HSDIO, ryd780b_dds_pinout, ryd780b_dds_profiles)
        #self.blue_pointing_dds = DDS(HSDIO, blue_pointing_dds_pinout, blue_pointing_dds_profiles)
        #self.microwave_dds = DDS(HSDIO, microwave_dds_pinout, microwave_dds_profiles)
        #self.ryd780a_dds = DDS(HSDIO, ryd780a_dds_pinout, ryd780a_dds_profiles)

        # Arduino DDS (v. "1.5")
        self.test_dds = DDS(HSDIO, test_dds_pinout, test_dds_profiles)

        # declare switches

        self.mot_aom_switch = Switch(
            HSDIO,
            mot_aom_switch_chan,
            profiles=mot_aom_switch_profile,
            delay=mot_aom_switch_delay
        )

        self.fort_aom_switch = Switch(
            HSDIO,
            fort_aom_switch_chan,
            profiles=fort_aom_switch_profile,
            delay=fort_aom_switch_delay
        )

        self.mot_2d_aom_switch = Switch(
            HSDIO,
            mot_2d_aom_switch_chan,
            profiles=mot_2d_aom_switch_profile,
            delay=mot_2d_aom_switch_delay
        )

        self.op_aom_switch = Switch(
            HSDIO,
            op_aom_switch_chan,
            profiles=op_aom_switch_profile,
            delay=op_aom_switch_delay
        )

        self.hf_aom_switch = Switch(
            HSDIO,
            hf_aom_switch_chan,
            profiles=hf_aom_switch_profile,
            delay=hf_aom_switch_delay
        )

        self.mot_3d_x_shutter_switch = Switch(
            HSDIO,
            mot_3d_x_shutter_switch_chan,
            profiles=mot_3d_x_shutter_switch_profile,
            delay=mot_3d_x_shutter_switch_delay
        )


        self.mot_3d_y_shutter_switch = Switch(
            HSDIO,
            mot_3d_y_shutter_switch_chan,
            profiles=mot_3d_y_shutter_switch_profile,
            delay=mot_3d_y_shutter_switch_delay
        )

        self.mot_3d_z1_shutter_switch = Switch(
            HSDIO,
            mot_3d_z1_shutter_switch_chan,
            profiles=mot_3d_z1_shutter_switch_profile,
            delay=mot_3d_z1_shutter_switch_delay
        )

        self.mot_3d_z2_shutter_switch = Switch(
            HSDIO,
            mot_3d_z2_shutter_switch_chan,
            profiles=mot_3d_z2_shutter_switch_profile,
            delay=mot_3d_z2_shutter_switch_delay
        )

        self.repumper_shutter_switch = Switch(
            HSDIO,
            repumper_shutter_switch_chan,
            profiles=repumper_shutter_switch_profile,
            delay=repumper_shutter_switch_delay
        )


        self.microwave_switch = Switch(
            HSDIO,
            microwave_switch_chan,
            profiles=microwave_switch_profile,
            delay=microwave_switch_delay
        )

        self.camera = Camera(
            HSDIO=HSDIO,
            channel=andor_trigger_chan,
            delay=andor_trigger_delay,
            pulse_length=5 # in millisecond. this can be overwrttten in functional waveform window
        )
        self.PGcamera = Camera( # Pointgret camera, standard trigger control
            HSDIO=HSDIO,
            channel=pointgrey_trigger_chan,
            delay=pointgrey_trigger_delay,
            pulse_length=1 # in millisecond. this can be overwrttten in functional waveform window
        )
        self.PGcamera2 = Camera( # Pointgret camera, standard trigger control
            HSDIO=HSDIO,
            channel=pointgrey2_trigger_chan,
            delay=pointgrey2_trigger_delay,
            pulse_length=1 # in millisecond. this can be overwrttten in functional waveform window
        )
        self.red_pointing_aom_switch = Switch(
            HSDIO,
            red_pointing_aom_switch_chan,
            profiles=red_pointing_aom_switch_profile,
            delay=red_pointing_aom_switch_delay
        )

        self.blue_pointing_aom_switch = Switch(
            HSDIO,
            blue_pointing_aom_switch_chan,
            profiles=blue_pointing_aom_switch_profile,
            delay=blue_pointing_aom_switch_delay
        )

        self.ryd780a_aom_switch = Switch(
            HSDIO,
            ryd780a_aom_switch_chan,
            profiles=ryd780a_aom_switch_profile,
            delay=ryd780a_aom_switch_delay
        )
        self.ryd780b_aom_switch = Switch(
            HSDIO,
            ryd780b_aom_switch_chan,
            profiles=ryd780b_aom_switch_profile,
            delay=ryd780b_aom_switch_delay
        )
        self.ground_aom_switch = Switch(
            HSDIO,
            ground_aom_switch_chan,
            profiles=ground_aom_switch_profile,
            delay=ground_aom_switch_delay
        )

        self.MOT_scope_trigger_switch = Switch(
            HSDIO,
            MOT_scope_trigger_chan,
            profiles=MOT_scope_trigger_profile,
            delay=MOT_scope_trigger_delay
        )

        self.scope_trigger_switch = Switch(
            HSDIO,
            scope_trigger_chan,
            profiles=scope_trigger_profile,
            delay=scope_trigger_delay
        )

        self.pointgrey_trigger_switch = Switch(
            HSDIO,
            pointgrey_trigger_chan,
            profiles=pointgrey_trigger_profile,
            delay=pointgrey_trigger_delay
        )
        self.pointgrey2_trigger_switch = Switch(
            HSDIO,
            pointgrey2_trigger_chan,
            profiles=pointgrey2_trigger_profile,
            delay=pointgrey2_trigger_delay
        )
        self.FORT_NE_trigger_switch = Switch(
            HSDIO,
            FORT_NE_trigger_chan,
            profiles=FORT_NE_trigger_profile,
            delay=FORT_NE_trigger_delay
        )

        self.ryd780A_NE_trigger_switch = Switch(
            HSDIO,
            ryd780A_NE_trigger_chan,
            profiles=ryd780A_NE_trigger_profile,
            delay=ryd780A_NE_trigger_delay
        )

        self.UV_trigger_switch = Switch(
            HSDIO,
            UV_trigger_chan,
            profiles=UV_trigger_profile,
            delay=UV_trigger_delay
        )
