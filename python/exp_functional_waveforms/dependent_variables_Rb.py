'''Constants for Rubidium Experiment

This is merely a scratchpad. The code needs to be copied & pasted to Dependent variables window
to really apply the code.

Minho Kwon 2018-02-27

## TODO: backup to file in same way that we backup the functional waveforms
'''

f_3DMOT_Loading=f_MOT_baseline+f_3DMOT_loading_offset
f_BA=f_MOT_baseline+f_BA_offset
f_2DMOT=f_MOT_baseline+f_2DMOT_offset
f_RO=f_MOT_baseline+f_RO_offset

# Actuator movement range is limited to prevent them being stuck

Corrected_Red_X=median([actuatorlimits['RedX'][0],actuatorlimits['RedX'][1],Red_X])
Corrected_Red_Y=median([actuatorlimits['RedY'][0],actuatorlimits['RedY'][1],Red_Y])
Corrected_Blue_X=median([actuatorlimits['BlueX'][0],actuatorlimits['BlueX'][1],Blue_X])
Corrected_Blue_Y=median([actuatorlimits['BlueY'][0],actuatorlimits['BlueY'][1],Blue_Y])
