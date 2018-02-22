'''Constants for Rubidium Experiment

This is merely a scratchpad. The code needs to be copied & pasted to CsPy Constants window
to really apply the code.

Minho Kwon 2018-02-22
'''

# Experiment
t_exp=0.200

# AIO
AIsamplerate=20000
AIsamples=int(round(AIsamplerate*t_exp)) #Analog in samples
coil_driver_polarity=-1 # -1 flips the polarity. Needed for Matt's coil drivers.
AI_MOT_samplelist_lowerbound=0
AI_MOT_samplelist_higherbound=800
AI_ch_3DMOTX1=9
AI_ch_3DMOTX2=10
AI_ch_3DMOTY1=11
AI_ch_3DMOTY2=12
AI_ch_3DMOTZ1=13
AI_ch_3DMOTZ2=14
I_Q1=1.5
I_Q2=1.24
I_test_X=-0.30
I_test_Y=-0.20
I_test_Z=-0.013

# Some timings we rarely change
t1_PGcamera = 1 # usually for Red
t2_PGcamera = 40# usually for FORT
t_science = 170
t_start_blue_imaging=205
t_blue_exposure=0.02
t_PG_triggerduration=2
t_NE_FORT_trigger_start=110
t_NE_FORT_trigger_end=115

# For PG not oversaturate.
P_DDSRF_FORT_PG=-10 # RF amplitude for DDS FORT profile : low
P_DDSRF_780A_PG=-10 # RF amplitude for DDS 780A profile : PG

# some constants for testing.
my_MOT_SW_channel=7
my_FORT_SW_channel=8
op_aom_switch_chan=10
readout_chop_freq_MHz=1.25
op_chop_freq_MHz=1.00
