"""These are the waveform functions for the Rb  FFPR project.
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
exp.cooling_aom_switch.profile(t, 'on')
t=60
# turn the mot off
exp.cooling_aom_switch.profile(t, 'off')
------------------------------------------------------------------
"""


from dds import DDS
from switch import Switch
from camera import Camera

# TODO: FORT DDS and SWITCH should be renamed for some other use, b/c the HSDIO line is run across the lab to that DDS
# TODO: SWITCHES NEED TO BE DEFINED FOR THE CONVEYOR AND RYDBERG AOMS, AND MICROWAVES.

# softTODO all of these pinouts should be set in a config/json file or a GUI window
# and loaded up whenever the DDS is updated. OR, load this file in the same
# fashion that the experiment waveform is loaded

'''I think these constants need to be defined here so that they can be
overwritten at the global scope.
'''
################################################################################
# Example DDS Profile ##########################################################
#
# these pinouts and profiles are used further down in this file in the Rb class
# where they are used to define DDS or Switch objects
################################################################################
# ex_dds_pinout = (-1,2,5) # pins on the HDSIO to toggle DDS pins. -1: not in use
# ex_dds_profiles = {
#   'ex1' = (0,0,1) # pin 5 outputs high, dds sees 4 in grey code
# }
# what determines what profile this is though? see dds window in CsPy to set it

################################################################################
# DDS 1.5 Test Profile ##########################################################
################################################################################
test_dds_pinout = (-1,-1,-1) # actually hook this up to something
test_dds_profiles = {
  'on' : (0,0,0),
  'off': (0,0,1)
}

################################################################################
# 3D MOT DDS SETUP #############################################################
################################################################################
cooling_aom_dds_pinout = (0,1,2)
cooling_aom_dds_profiles = {
    'MOT' : (0,0,0),#  (pin2, pin1, pin0)
    'PGC' : (0,0,1),
    'Blowaway' : (0,1,0),
    'RO' : (0,1,1),
    'PGC2' : (1,0,0),
    'GM': (1,1,0)  # coming soon? O__o
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
# conveyor_front_aom DDS SETUP ################################################################
################################################################################
conveyor_front_aom_dds_pinout = (-1,28,29) # -1 indicates pins that are not being used. (P2, P1, P0)
conveyor_front_aom_dds_profiles = {
    'off' : (0,0,0),
    'on' : (0,0,1),
}

################################################################################
# Ryd 780 DDS SETUP ################################################################
################################################################################
conveyor_back_aom_dds_pinout = (-1,30,31) # -1 indicates pins that are not being used
conveyor_back_aom_dds_profiles = {
    'off' : (0,0,0),
    'r1' : (0,0,1),
    'r2' : (0,1,0),
    'PG' : (0,1,1)
}

################################################################################
# Ryd 480 DDS SETUP ################################################################
################################################################################
ryd480_pointing_aom_dds_pinout = (-1,34,33) # -1 indicates pins that are not being used
ryd480_pointing_aom_dds_profiles = {
    'off' : (0,0,0),
    'r1' : (0,0,1),
    'r2' : (0,1,0),
    'r3' : (0,1,1)
}

################################################################################
# Xfer cavity offset DDS SETUP ################################################################
################################################################################
xfer_cav_offset_dds_pinout = (-1,26,27) # -1 indicates pins that are not being used
xfer_cav_offset_dds_profiles = {
    'off' : (0,0,0),
    'r1' : (0,0,1),
    'r2' : (0,1,0),
    'r3' : (0,1,1)
}

################################################################################
# 3D MOT AOM SWITCH SETUP #########################################################
################################################################################
cooling_aom_switch_chan = 7
# this is the default profile, we dont have to pass it in if we dont want to
cooling_aom_switch_profile = {'on':1, 'off':0}
# timing delay parameter
cooling_aom_switch_delay = 0

################################################################################
# FORT AOM SWITCH SETUP ########################################################
################################################################################
fort_aom_switch_chan = 8
# this is the default profile, we dont have to pass it in if we dont want to
fort_aom_switch_profile = {'on':1, 'off':0}
# timing delay parameter
fort_aom_switch_delay = 0

################################################################################
# OP AOM SWITCH SETUP ########################################################
################################################################################
op_aom_switch_chan = 10
# this is the default profile, we dont have to pass it in if we dont want to
op_aom_switch_profile = {'on':0, 'off':1}
# timing delay parameter
op_aom_switch_delay = 0

################################################################################
# Repumper AOM SWITCH SETUP ##########################################################
################################################################################
repumper_aom_switch_chan = 11
# this is the default profile, we dont have to pass it in if we dont want to
repumper_aom_switch_profile = {'on':0, 'off':1}
# timing delay parameter
repumper_aom_switch_delay = 0

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
# conveyor_front_aom SWITCH SETUP ##########################################################
################################################################################
conveyor_front_aom_switch_chan = 18
# this is the default profile, we dont have to pass it in if we dont want to
conveyor_front_aom_switch_profile = {'on':0, 'off':1}
# timing delay parameter
conveyor_front_aom_switch_delay = 0

################################################################################
# Raman AOM SWITCH SETUP ##########################################################
################################################################################
raman_aom_switch_chan = 19
# this is the default profile, we dont have to pass it in if we dont want to
raman_aom_switch_profile = {'on':1, 'off':0}
# timing delay parameter
raman_aom_switch_delay = 0

################################################################################
# ANDOR EMCCD CAMERA SETUP #####################################################
################################################################################
andor_trigger_chan = 20
# this is the default profile, we dont have to pass it in if we dont want to
andor_trigger_profile = {'on':1, 'off':0}
# timing delay parameter
andor_trigger_delay = 0

################################################################################
# Conveyor Back AOM SWITCH SETUP ##########################################################
################################################################################
conveyor_back_aom_switch_chan = 21
# this is the default profile, we dont have to pass it in if we dont want to
conveyor_back_aom_switch_profile = {'on':1, 'off':0}
# timing delay parameter
conveyor_back_aom_switch_delay = 0

################################################################################
# 852 AOM SWITCH SETUP ##########################################################
################################################################################
xfer852_aom_switch_chan = 22
# this is the default profile, we dont have to pass it in if we dont want to
xfer852_aom_switch_profile = {'on':1, 'off':0}
# timing delay parameter
xfer852_aom_switch_delay = 0

################################################################################
# Ryd 480 AOM SWITCH SETUP ##########################################################
################################################################################
ryd480_aom_switch_chan = 32
# this is the default profile, we dont have to pass it in if we dont want to
ryd480_aom_switch_profile = {'on':1, 'off':0}
# timing delay parameter
ryd480_aom_switch_delay = 0

################################################################################
# Ryd 480 AOM SWITCH SETUP ##########################################################
################################################################################
ryd480_pointing_aom_switch_chan = 32
# this is the default profile, we dont have to pass it in if we dont want to
ryd480_pointing_aom_switch_profile = {'on':1, 'off':0}
# timing delay parameter
ryd480_pointing_aom_switch_delay = 0

# TODO: probably don't need a switch for this. repurpose as a conveyor switch
################################################################################
# Xfer cavity offset SWITCH SETUP ##########################################################
################################################################################
xfer_cav_offset_switch_chan = 23
# this is the default profile, we dont have to pass it in if we dont want to
xfer_cav_offset_switch_profile = {'on':1, 'off':0}
# timing delay parameter
xfer_cav_offset_switch_delay = 0

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
# rydberg 780 Noise eater Trigger SETUP ###############################################
################################################################################
ryd780_NE_trigger_chan = 48
# this is the default profile, we dont have to pass it in if we dont want to
ryd780_NE_trigger_profile = {'on':1, 'off':0} # Does this work?
# timing delay parameter
ryd780_NE_trigger_delay = 0

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
# Rb class contains the switch, shutter, and camera functions
################################################################################
class Rb(object):
    '''holds all of the experiment's standard functional waveforms
    I need to be able to pass in the hardware classes, so a class is convenient
    '''

    def __init__(self, HSDIO, AO, DO, label):

        # DDS boxes are agnostic to these channel definitions-- you must make sure that the HSDIO channels are
        # connected to the DDS profile pins that you want. The frequency, amplitude, etc for each profile are configured
        # in the DDS window when CsPy is run. Our box numbering scheme is commented below only as a convenience to the 
        # reader.

        # DDS 1. declare dds channels. Up to four.
        self.cooling_aom_dds = DDS(HSDIO, cooling_aom_dds_pinout, cooling_aom_dds_profiles)
        self.op_dds = DDS(HSDIO, op_dds_pinout, op_dds_profiles)

        # DDS 2
        #self.ryd480_pointing_aom_dds_dds = DDS(HSDIO, ryd480_pointing_aom_dds_pinout, ryd480_pointing_aom_dds_profiles)
        self.xfer852_aom_dds = DDS(HSDIO, xfer852_aom_dds_pinout, xfer852_aom_dds_profiles)
        self.xfer_cav_offset_dds = DDS(HSDIO, xfer_cav_offset_dds_pinout, xfer_cav_offset_dds_profiles)
        self.conveyor_front_aom_dds = DDS(HSDIO, conveyor_front_aom_dds_pinout, conveyor_front_aom_dds_profiles)
        self.conveyor_back_aom_dds = DDS(HSDIO, conveyor_back_aom_dds_pinout, conveyor_back_aom_dds_profiles)

        # DDS 3
        # self.ryd480_pointing_aom_dds = DDS(HSDIO, ryd480_pointing_aom_dds_pinout, ryd480_pointing_aom_dds_profiles)
        #self.xfer_cav_offset_dds = DDS(HSDIO, xfer_cav_offset_dds_pinout, xfer_cav_offset_dds_profiles)
        #self.conveyor_front_aom_dds = DDS(HSDIO, conveyor_front_aom_dds_pinout, conveyor_front_aom_dds_profiles)
        #self.conveyor_back_aom_dds = DDS(HSDIO, conveyor_back_aom_dds_pinout, conveyor_back_aom_dds_profiles)

        # Arduino DDS (v. "1.5")
        self.test_dds = DDS(HSDIO, test_dds_pinout, test_dds_profiles)

        self.cooling_aom_switch = Switch(
            HSDIO,
            cooling_aom_switch_chan,
            profiles=cooling_aom_switch_profile,
            delay=cooling_aom_switch_delay
        )

        self.fort_aom_switch = Switch(
            HSDIO,
            fort_aom_switch_chan,
            profiles=fort_aom_switch_profile,
            delay=fort_aom_switch_delay
        )

        self.op_aom_switch = Switch(
            HSDIO,
            op_aom_switch_chan,
            profiles=op_aom_switch_profile,
            delay=op_aom_switch_delay
        )

        self.repumper_aom_switch = Switch(
            HSDIO,
            repumper_aom_switch_chan,
            profiles=repumper_aom_switch_profile,
            delay=repumper_aom_switch_delay
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


        self.conveyor_front_aom_switch = Switch(
            HSDIO,
            conveyor_front_aom_switch_chan,
            profiles=conveyor_front_aom_switch_profile,
            delay=conveyor_front_aom_switch_delay
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

        self.xfer852_aom_switch = Switch(
            HSDIO,
            xfer852_aom_switch_chan,
            profiles=xfer852_aom_switch_profile,
            delay=xfer852_aom_switch_delay
        )

        self.xfer_cav_offset_switch = Switch(
            HSDIO,
            xfer_cav_offset_switch_chan,
            profiles=xfer_cav_offset_switch_profile,
            delay=xfer_cav_offset_switch_delay
        )

        self.conveyor_back_aom_switch = Switch(
            HSDIO,
            conveyor_back_aom_switch_chan,
            profiles=conveyor_back_aom_switch_profile,
            delay=conveyor_back_aom_switch_delay
        )
        self.ryd480_aom_switch = Switch(
            HSDIO,
            ryd480_aom_switch_chan,
            profiles=ryd480_aom_switch_profile,
            delay=ryd480_aom_switch_delay
        )

        self.ryd480_pointing_aom_switch = Switch(
            HSDIO,
            ryd480_pointing_aom_switch_chan,
            profiles=ryd480_pointing_aom_switch_profile,
            delay=ryd480_pointing_aom_switch_delay
        )

        self.raman_aom_switch = Switch(
            HSDIO,
            raman_aom_switch_chan,
            profiles=raman_aom_switch_profile,
            delay=raman_aom_switch_delay
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

        self.ryd780_NE_trigger_switch = Switch(
            HSDIO,
            ryd780_NE_trigger_chan,
            profiles=ryd780_NE_trigger_profile,
            delay=ryd780_NE_trigger_delay
        )


        self.UV_trigger_switch = Switch(
            HSDIO,
            UV_trigger_chan,
            profiles=UV_trigger_profile,
            delay=UV_trigger_delay
        )

