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
# 3D MOT DDS SETUP ################################################################
################################################################################
mot_3d_dds_pinout = (0,1,2)
mot_3d_dds_profiles = {
    'MOT' : (0,0,0),
    'off' : (0,0,1),
    'Blowaway' : (0,1,0),
    'RO' : (0,1,1)
}

################################################################################
# FORT DDS SETUP ################################################################
################################################################################
fort_dds_pinout = (-1,3,4) # -1 indicates pins that are not being used
fort_dds_profiles = {
    'on' : (0,0,0),
    'off' : (0,0,1),
    'Blowaway' : (0,1,0),
    'RO' : (0,1,1)
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
# MOT AOM SWITCH SETUP #########################################################
################################################################################
mot_aom_switch_chan = 7
# this is the default profile, we dont have to pass it in if we dont want to
mot_aom_switch_profile = {'on':1, 'off':0}
# timing delay parameter
mot_aom_switch_delay = 0

################################################################################
# HF AOM SWITCH SETUP ##########################################################
################################################################################
hf_aom_switch_chan = 11
# this is the default profile, we dont have to pass it in if we dont want to
hf_aom_switch_profile = {'on':1, 'off':0}
# timing delay parameter
hf_aom_switch_delay = 0

################################################################################
# FORT AOM SWITCH SETUP ########################################################
################################################################################
fort_aom_switch_chan = 8
# this is the default profile, we dont have to pass it in if we dont want to
fort_aom_switch_profile = {'on':1, 'off':0}
# timing delay parameter
fort_aom_switch_delay = 0

################################################################################
# ANDOR EMCCD CAMERA SETUP #####################################################
################################################################################
andor_trigger_chan = 20
# this is the default profile, we dont have to pass it in if we dont want to
andor_trigger_profile = {'on':1, 'off':0}
# timing delay parameter
andor_trigger_delay = 0

################################################################################
################################################################################
################################################################################
class Rb(object):
    '''holds all of the experiment's standard functional waveforms
    I need to be able to pass in the hardware classes, so a class is convenient
    '''

    def __init__(self, HSDIO, AO, DO, label):
        self.mot_3d_dds = DDS(HSDIO, mot_3d_dds_pinout, mot_3d_dds_profiles)
        self.fort_dds = DDS(HSDIO, fort_dds_pinout, fort_dds_profiles)
        self.mot_2d_dds = DDS(HSDIO, mot_2d_dds_pinout, mot_2d_dds_profiles)
        self.op_dds = DDS(HSDIO, op_dds_pinout, op_dds_profiles)

        self.mot_aom_switch = Switch(
            HSDIO,
            mot_aom_switch_chan,
            profiles=mot_aom_switch_profile,
            delay=mot_aom_switch_delay
        )

        self.hf_aom_switch = Switch(
            HSDIO,
            hf_aom_switch_chan,
            profiles=hf_aom_switch_profile,
            delay=hf_aom_switch_delay
        )

        self.fort_aom_switch = Switch(
            HSDIO,
            fort_aom_switch_chan,
            profiles=fort_aom_switch_profile,
            delay=fort_aom_switch_delay
        )

        self.camera = Camera(
            HSDIO,
            andor_trigger_chan
        )

#    def mot_dds(self):
#        return
#
#    def mot_aom_switch(self, t, profile):
#        return self.mot_aom_switch.profile(t, profile)
#
#    def hf_aom_switch(self, t, profile):
#        return self.hf_aom_switch.profile(t, profile)
#
#    def fort_aom_switch(self):
#        return self.fort_aom_switch.profile(t, profile)
#
#    def andor_take_shot(self):
#        return self.camera.take_shot(t)
