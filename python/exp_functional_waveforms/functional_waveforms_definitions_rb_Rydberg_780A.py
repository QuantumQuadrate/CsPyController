"""These are the waveform functions for the Rubidium project.

This file is not imported to CsPy. You'll have to copy-paste into the built-in editor of fuctional waveform definition, which sucks..


"""


import exp_functional_waveforms.functional_waveforms_rb as Rb

HSDIO = experiment.LabView.HSDIO.add_transition
AO = experiment.LabView.AnalogOutput.add_transition
DO = experiment.LabView.DAQmxDO.add_transition
label = experiment.functional_waveforms_graph.label

exp = Rb.Rb(HSDIO, AO, DO, label)
###########################################################################

# Setting timing sequences for an experiment.
# For diagnostics purpose, sequences are low level coded.
############
t=0
coil_driver_polarity=-1 # -1 flips the polarity. Needed for Matt's coil drivers.
exp.camera.pulse_length=5 # Changes HSDIO pulse width to control exposure
t_x_shutter_open=167
t_x_shutter_close=185 # X shutter seems one-way working.
t_y_shutter_open=166.2
t_y_shutter_close=180.80
t_z1_shutter_open=166
t_z1_shutter_close=175
# Abstractized experiment control

## Initilization
for i in range(5):
    AO(0,i,0)
AO(0,5,coil_driver_polarity*-2.2)
AO(0,6,coil_driver_polarity*2.8)
AO(0,0,coil_driver_polarity*1.5)
AO(0,1,coil_driver_polarity*1.5)
AO(0,7,10)


exp.fort_aom_switch.profile(0,'off')
exp.op_dds.profile(0,'off')
exp.op_aom_switch.profile(0,'off')
exp.hf_aom_switch.profile(0,'on')
exp.mot_3d_x_shutter_switch.profile(0,'off')
exp.mot_3d_y_shutter_switch.profile(0,'on')
exp.mot_3d_z1_shutter_switch.profile(0,'off')
exp.microwave_switch.profile(0,'off')
exp.microwave_dds.profile(0,'off')
exp.repumper_shutter_switch.profile(0,'on')
exp.ground_aom_switch.profile(0,'off')
## 2D MOT Loading Phase
AO(0,2,coil_driver_polarity*-0.33) #X
AO(0,3,coil_driver_polarity*-0.17) #Y
AO(0,4,coil_driver_polarity*0.0075) #Z

exp.mot_3d_dds.profile(0,'MOT')
exp.fort_dds.profile(0,'off')
exp.mot_2d_dds.profile(0,'on')
exp.mot_aom_switch.profile(0,'on')
exp.mot_2d_aom_switch.profile(0,'on')

## 3D MOT Loading Phase
exp.mot_2d_dds.profile(50,'off')
exp.mot_2d_aom_switch.profile(50,'off')
AO(60,0,0)
AO(60,1,0)

## FORT Transfer Phase
exp.fort_dds.profile(40,'on')
exp.fort_aom_switch.profile(40,'on')


## Fall off Phase
AO(110,2,coil_driver_polarity*-0.30) #X
AO(110,3,coil_driver_polarity*-0.49) #Y
AO(110,4,0) #Z
exp.mot_aom_switch.profile(110,'off')
exp.hf_aom_switch.profile(110,'off')

## Readout Phase
AO(25+110,2,coil_driver_polarity*-0.30) #X
AO(25+110,3,coil_driver_polarity*-0.50) #Y
AO(25+110,4,coil_driver_polarity*-0.015) #Z
exp.mot_3d_dds.profile(140,'RO')
exp.camera.take_shot(140)
t_start=140
t_end=140+exp.camera.pulse_length
t_pulsewidth=0.001*0.4
t_period=0.001*0.8
for i in range(int(round((t_end-t_start)/t_period))):
    exp.mot_aom_switch.profile(t_start+i*t_period,'on')
    exp.mot_aom_switch.profile(t_start+i*t_period+t_pulsewidth,'off')

for i in range(int(round((t_end-t_start)/t_period))):
    exp.fort_aom_switch.profile(t_start+i*t_period,'off')
    exp.fort_aom_switch.profile(t_start+i*t_period+t_pulsewidth,'on')

exp.hf_aom_switch.profile(140,'on')
exp.hf_aom_switch.profile(146,'off')

AO(150,2,coil_driver_polarity*-0.27) #X
AO(150,3,coil_driver_polarity*-0.48) #Y
AO(150,4,coil_driver_polarity*-0.25) #Z


## Optical Pumping Phase
AO(150,7,0)
AO(160,7,10)
AO(165,7,0)

t_start=160
t_end=t_start+t_op
exp.op_dds.profile(160,'on')
exp.op_dds.profile(t_end,'off')
exp.hf_aom_switch.profile(160,'on')
exp.hf_aom_switch.profile(t_end,'off')
t_offset=0
t_op_pulsewidth=0.001*0.5
t_fort_pulsewidth=0.001*0.5
t_period=0.001*1
for i in range(int(round((t_end-t_start)/t_period))):
    exp.op_aom_switch.profile(t_start+i*t_period+t_offset,'on')
    exp.op_aom_switch.profile(t_start+i*t_period+t_op_pulsewidth+t_offset,'off')

for i in range(int(round((t_end-t_start)/t_period))):
    exp.fort_aom_switch.profile(t_start+i*t_period,'off')
    exp.fort_aom_switch.profile(t_start+i*t_period+t_fort_pulsewidth,'on')


exp.mot_3d_x_shutter_switch.profile(t_x_shutter_open,'on')
exp.mot_3d_x_shutter_switch.profile(t_x_shutter_close,'off')
exp.mot_3d_y_shutter_switch.profile(t_y_shutter_open,'off')
exp.mot_3d_y_shutter_switch.profile(t_y_shutter_close,'on')
exp.mot_3d_z1_shutter_switch.profile(t_z1_shutter_open,'on')
exp.mot_3d_z1_shutter_switch.profile(t_z1_shutter_close,'off')

## Science Phase

exp.red_pointing_dds.profile(0,'r2')
exp.red_pointing_aom_switch.profile(0,'off')
exp.ryd780a_aom_switch.profile(0,'off')
exp.ryd780a_dds.profile(0,'off')

exp.ryd780a_dds.profile(170,'r2')
exp.red_pointing_aom_switch.profile(170,'on')

#exp.ryd780a_aom_switch.profile(170,'on')
#exp.ryd780a_aom_switch.profile(170+t_rydberg,'off')
#exp.fort_aom_switch.profile(170,'off')
#exp.fort_aom_switch.profile(170.006,'on')

t_start=170
t_end=170.2
t_pulsewidth=0.001*1
t_period=0.001*5
for i in range(int(round((t_end-t_start)/t_period))):
    exp.ryd780a_aom_switch.profile(t_start+i*t_period,'on')
    exp.ryd780a_aom_switch.profile(t_start+i*t_period+t_pulsewidth,'off')

for i in range(int(round((t_end-t_start)/t_period))):
    exp.fort_aom_switch.profile(t_start+i*t_period,'off')
    exp.fort_aom_switch.profile(t_start+i*t_period+t_pulsewidth,'on')

exp.fort_dds.profile(t_end,'on')

exp.ryd780a_dds.profile(t_end,'off')
exp.red_pointing_aom_switch.profile(t_end,'off')

exp.blue_pointing_dds.profile(0,'off')
exp.blue_pointing_aom_switch.profile(0,'off')
exp.blue_pointing_dds.profile(170,'r2')
exp.blue_pointing_aom_switch.profile(170,'on')
exp.blue_pointing_dds.profile(171,'off')
exp.blue_pointing_aom_switch.profile(171,'off')

## Blow-away Phase

AO(175,0,coil_driver_polarity*-0.1)
AO(175,1,coil_driver_polarity*0.1)
AO(175,2, coil_driver_polarity*-0.371) #X
AO(175,3,coil_driver_polarity*-0.553) #Y
AO(175,4,coil_driver_polarity*-0.0518) #Z
# exp.mot_3d_dds.profile(176,'Blowaway')
# exp.fort_dds.profile(176,'Blowaway')
# t_start=176
# t_end=176.15
# t_pulsewidth=0.001*1
# t_period=0.001*2
# for i in range(int(round((t_end-t_start)/t_period))):
#     exp.mot_aom_switch.profile(t_start+i*t_period,'on')
#     exp.mot_aom_switch.profile(t_start+i*t_period+t_pulsewidth,'off')
#
# for i in range(int(round((t_end-t_start)/t_period))):
#     exp.fort_aom_switch.profile(t_start+i*t_period,'off')
#     exp.fort_aom_switch.profile(t_start+i*t_period+t_pulsewidth,'on')
#
# exp.fort_dds.profile(t_end,'on')


## Readout Phase
AO(180,0,0) # turn off quadrupole fields
AO(180,1,0)
AO(180,2, coil_driver_polarity*-0.30) #X
AO(180,3, coil_driver_polarity*-0.50) #Y
AO(180,4, coil_driver_polarity*-0.015) #Z
t_readout_2nd=195

exp.mot_3d_dds.profile(t_readout_2nd,'RO')
exp.camera.take_shot(t_readout_2nd)
t_start=t_readout_2nd
t_end=t_readout_2nd+exp.camera.pulse_length
t_pulsewidth=0.001*0.4
t_period=0.001*0.8
for i in range(int(round((t_end-t_start)/t_period))):
    exp.mot_aom_switch.profile(t_start+i*t_period,'on')
    exp.mot_aom_switch.profile(t_start+i*t_period+t_pulsewidth,'off')

for i in range(int(round((t_end-t_start)/t_period))):
    exp.fort_aom_switch.profile(t_start+i*t_period,'off')
    exp.fort_aom_switch.profile(t_start+i*t_period+t_pulsewidth,'on')

AO(t_readout_2nd,7,10) # Turn on repumper. Sets rf attenuator voltage to 10V
exp.hf_aom_switch.profile(t_readout_2nd,'on')
exp.hf_aom_switch.profile(t_readout_2nd+exp.camera.pulse_length,'off')
AO(t_readout_2nd+exp.camera.pulse_length,7,0)

exp.fort_aom_switch.profile(t_readout_2nd+exp.camera.pulse_length,'off')
exp.fort_dds.profile(t_readout_2nd+exp.camera.pulse_length,'off')
## Ending
