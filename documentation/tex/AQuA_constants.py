# settings updated 2015-07-02
# These constant settings do not need to be commented out
# because they will be overwritten by the independent and dependent variables.

### experiment flags ###

background = False  # Use when taking a background image.  Turns off 2D and 3D MOT during idle, loading and PGC1
alignment = False  # changes dds rydA profile 3 to lower power when true
doGates = True  # Set to false to change delay_before_excitaiton and switching_delay to 5 ms, when you DON"T want blockade.
doRamsey1038 = False  # changes rydA waveform leaving the traps on, turns ryd 459 off in DDS
doRamsey459 = False    # turns 1038 off in dds
do1038Trap = False  # sets Pre_Readout_Time to 0, turns on 1038 (780 still on)
doPatternLoad = False  # turns on first blow away to do patterned loading if true
all780off = False  # sets the 780 bits to always off


### packages ###
import numpy as np


### SI Prefixes ###

tera=1e12; giga=1e9; mega=1e6; kilo=1e3; milli=1e-3; micro=1e-6; nano=1e-9; pico=1e-12;


### physics constants ###

c0=299792458  # m/s
eps0=8.854187817e-12  # F/m
alpha=7.2973525698e-3
kB_SI=1.3806488e-23  # J/K
hyperfine_splitting_6s1_2 = 9.19263e9
hyperfine_splitting_7p1_2 = 377.4e6
gamma_6p3_2 = 2*pi*5.1e6
gamma_7p1_2 = 2*pi*1e6
alpha_780_cgs = -247e-24
alpha_780_SI = alpha_780_cgs*4*pi*eps0*1e-6
saturation_intensity = 27  # W/m^2


### MOT ###

MOT_loading_time = 480.250866709
MOT_frequency = 107.682685945  # profile 0
MOT_power = -3.12639959015  # profile 0

hyperfine_frequency = 268.425729262  # profile 0
hyperfine_power = -0.253770318123  # profile 0

MOT_2D_time = 429.924189099 #controlled by a shutter. needs time to open and close.  bounces upon opening
trap_on_time_during_loading = 435.982310345
MOT_drop_time = 65.2040961701


### PGC 1 ###

PGC_1_time = 6.11868915721
PGC_1_frequency = 91.4499601693  # profile 1
PGC_1_power = -6.82121127689  # profile 1
PGC_1_hyperfine_frequency = 278.5 #not in any waveform
PGC_1_hyperfine_power = 0 #not in any waveform
MOT_to_PGC_B_field_delay = .6
trap_780_delay_for_PGC_1 = 4.28533651393


### PGC 2 ###

PGC_2_time = 8.53133176334
PGC_2_frequency = 81.9991546641  # profile 4
PGC_2_power = 0.213636966912  # profile 4
PGC_2_hyperfine_frequency = 278.5 #not currently in any waveform
PGC_2_hyperfine_power = 0 #not currently in any waveform
Readout_to_PGC_2_B_field_delay = .001


### Trapping ###
SHG_780_freq = 75.8393240905  # controls DDS AOM RF frequency
SHG_780_power = -3.01422252233  # controls DDS AOM RF power.  Best output is at -2.5 dBm, so do not go higher.


### Blowaway ###

# talks to HP 8665A on GPIB18
blowaway_freq = 219.986031065  # 219 MHz in traps, 227 MHz on resonance
blowaway_power = -11.8722125912  #dBm
blow_away_time = 0.21308523234
blow_away_time2=.05 if doPatternLoad else 0

### Readout ###

Readout_time = 49.3480613968
Readout_time2=28.61*1.5
Readout_frequency = 93.7598022702 #profile 3
Readout_power = -6.03238305528 #profile 3
Readout_hyperfine_frequency = 278.0  # not in any waveform
Readout_hyperfine_power = 0  # not in any waveform
EMCCD_gain = 181.749846

Pre_Readout_Time = 0 if do1038Trap else 43.3446849926
pre_readout_frequency = 94.0404898782 #profile 5
pre_readout_power = -5.30880810422 #profile 5

grey_cooling_time=0 #this time plus 6ms is the actual time (due to shutter timings)
grey_cooling_freq=137.972


### Optical Pumping ###

optical_pumping_time = 2.28983292731
optical_pumping_frequency = 98.0541205654
optical_pumping_amp = -0.358305975447
OP_2nd_time = 0
OP_hyperfine_frequency = 278.5  # controlled by freq generator not currently connected to computer
OP_hyperfine_power = 0  # controlled by freq gen or waveplates, must be stepped by hand
depumping_894_time = 4  # 2 ms, used for optimzation
single_site_459_OP_time = 0
Op_Hf_extratime = 0.0113537818625  # how long should the repump stay on after OP is off


### Raman ###

raman_459_pulse = 0
raman_detuning=-19.677
raman_pulse_at_freq_2 = 0
ramsey_gap_time = 0

# for raman 459 laser AOM
raman_freq = 143.375
raman_power = 0

# for variable phase gates using 459 Raman light
phase_site1_pulse_time = 0.015625  # set to make a better Cz based on CNOT phase measurements
phase_site2_pulse_time = 0.0125  # set to make a better Cz based on CNOT phase measurements, was 0.01550388 set for Grover search


### microwaves ###

microwave_pi_pulse = 0.046980904846724854
microwave_pi_by_2 = 0.024043454856288376
microwave_2pi_pulse = 2*microwave_pi_pulse
microwave_pi_by_3 = microwave_pi_pulse / 3.0
parity_phase=0
microwave_freq = 199.9997627743545 # nominally 200 MHz for 9.192631770 hyperfine resonance
microwave_power = -0.156241917688

# for stark shifted microwaves:
uwave_freq_offset1 = 0 # was -0.04585 for shift into resonance
uwave_freq_offset2 = 0 # was -0.04324 for shift into resonance

uwave_Ramsey_gap_LS_off=0
Ramsey_phase=0
rydA_starkshift_amp=-6.83
CNOT_phase = 5.379881452179586 # for blockade > no blockade, subtract pi for no blockade > blockade

microwave_pi2_phase = CNOT_phase

### Rydberg ###

# 459
rydberg_A_459_time_control_pi = 0.000414327482797
rydberg_A_459_time_target_pi = 0.000448575969385
rydberg_A_459_time_site3_pi = 0.000525662201527
rydberg_CP_phase = pi/4

# 2 photon Rabi
rydberg_RFE_pi_time_1 =0.00100422686648# 0.00092152053906 # set for nominal delays.  For 1038_of_in_Rydberg, use 0.000990595325118+.000050
difference_between_control_pi_1_and_control_pi_2 = 0
rydberg_RFE_2pi_time_2 =0.00180218354061# 0.00186846426297
rydberg_RFE_pi_time_2 = rydberg_RFE_2pi_time_2 / 2
rydberg_RFE_pi_time_3 = 0.000719100549482
second_pulse_time=0 #second pulse pi time 0.00095228

# timing
extra_delay=0  # extra delay in cz gate
ryd_mag_wait = 0.520647359994
no_blockade_wait=5

# These offsets are the sum total of the AOM frequency shifts for the 2-photon rydberg light.           #swapped
# Set this using a TPS experiment.  The 459 switch frequency will change to compensate in the dependent variables.
site_1_RydA_frequency_offset = 302.70488610619867+0.0518940068288 +0.193  +0.186 +0.049 -0.037 +0.079 -0.1278 -0.001441 -0.0125  # site 36
site_2_RydA_frequency_offset = 302.78459692347343-0.00364065531018 +0.208 +0.2015 +0.048 +0.009 +0.046 -0.1599 -0.02482 +0.0189  # site 22
site_3_RydA_frequency_offset = 303.9208481236127

# Rydberg B (not currently used)
rydberg_B_1038_time_control = 0
rydberg_B_459_time_control = 0
rydberg_B_459_time_target = 0
RydB_switch_AOM_frequency_1 = 143
RydB_switch_AOM_frequency_2 = 143


### Beam scanners ###

# 1038 scanner 1: best efficiency 147 (centered on ~site 29)
# 1038 scanner 2: best efficiency 160 (centered on ~site 29)

# scanner frequencies for site 1 (36)
scanner_1_frequency_1_459 = 141+1.5 +0.39+0.222884324146-1+0.493+0.805+0.366+0.0868155168215+0.315212577304-0.7920
scanner_2_frequency_1_459 = 148+1.4 -0.126+0.35808028156+3.22+0.178 +0.758+0.28+0.229270539601+0.173357167019+0.001113
scanner_1_frequency_1_1038 = 150-3.25-0.877-0.13-0.52+0.426362469435 -0.0551
scanner_2_frequency_1_1038 = 150+1.8-1.266+0.0870343173826 +0.1296

balance_factor1038 = 0  # was -.5  # factor to balance both sites

# scanner frequencies for site 2 (22)
scanner_1_frequency_2_459 = 141+1.5+5 +0.24+0.180584146561-1+0.361+1.002+0.291+0.0662026289501+0.334102839822-0.8602
scanner_2_frequency_2_459 = 148+1.4 -0.4268+0.461947485083+2.94+0.214 +0.804+0.264+0.26821292278+0.161219586188-0.03948
scanner_1_frequency_2_1038 = 150+3.25-0.727-0.03-0.15+0.114509224724 -0.1797
scanner_2_frequency_2_1038 =  150-0.93-0.57+0.0708502277652 +0.08771

# scanner frequencies for site 3 (32)
scanner_1_frequency_3_459 = (151.3442542607478 +0.512 -1.25-0.95790709854 +0.9973  +  156.33873138212303 +0.4 -1.077 -0.1084 )/2 -0.755
scanner_2_frequency_3_459 = 154.96796762492144-0.535582232016 +1.097 +1.82 -0.6392 - 4 -0.25
scanner_1_frequency_3_1038 = 142.9986134303044+0.0939437725381 -0.176 -0.1414 -0.099
scanner_2_frequency_3_1038 = 159.48602642618764+0.116047769885 -0.2694


### timing ###

delay_no_1038_in_Rydberg=.000120  # subtracted from end of 1038 in 1st pulse and added to beginning of 1038 in last pulse, so that 1038 is never on in Rydberg by itself

PGC_to_bias_B_field_delay = 2.99383121373
delay_before_blowaway = 0 # was 5

trap_modulation_time = 0 #not currently controlled by computer
trap_release_time = .020  # used for optimization
delay_between_camera_shots = 35  # 31.3 spec'd mnimum wasn't enough

DDS_profile_delay = .00006
RydA_onoff_delay_time = .000375
RydA_on_delay = .000325
RydA_off_delay = .000400

# delays to line up all the pulses
scanner_delay__extra_time_459 = .0003
scanner_delay__extra_time_1038 = scanner_delay__extra_time_459
Ryd1038_onoff_delay_time = .000650

HSDIO2_delay = .010970
Ryd1038_on_delay = .000156+.00023
Ryd1038_off_delay = -.000218+0.000044

Ryd1038_on_delay2 = 0#.000156+.000262
Ryd1038_off_delay2 =0# -.000238

# added raw Ryd1038_on_delay to make sure scanner is switched before pulse starts
Ryd1038_scanner1_delay = .000110+.000156
Ryd1038_scanner2_delay = .000070+.000156

Ryd459A_on_delay = .000090
Ryd459A_off_delay = .000012

Ryd459A_on_delay2 =0# .000090
Ryd459A_off_delay2 =0# .000012

# add Ryd459A_on_delay to make sure scanner is switched before pulse starts
Ryd459_scanner1_delay = .000350+.000090
Ryd459_scanner2_delay = .000400+.000090
delay_before_switching =.000350+0.000150
# SHG
trap780top_off_delay = .000670+0.0005
trap780top_on_delay = .000260
# TiSapph
trap780bottom_off_delay = .000894+0.0005
trap780bottom_on_delay = .000070
# wait as little time as possible before excitation
delay_before_excitation_pulse = max(HSDIO2_delay,
                                                              Ryd1038_on_delay, Ryd1038_scanner1_delay, Ryd1038_scanner2_delay, 
                                                              Ryd459A_on_delay, Ryd459_scanner1_delay, Ryd459_scanner2_delay, 
                                                              trap780top_off_delay, trap780bottom_off_delay
                                                              ) if doGates else 5
# time it takes to fully switch sitesRyd
switching_delay = max(Ryd1038_on_delay, Ryd1038_scanner1_delay, Ryd1038_scanner2_delay, 
                                                              Ryd459A_on_delay, Ryd459_scanner1_delay, Ryd459_scanner2_delay, 
                                                              ) if doGates else 5
# buffer to make sure everything is off again
delay_after_excitation_pulse = .000790

_685_time = 0
frequency_685 = 194
power_685 = 0

close_3D_shutter_time = 10.75
close_HF_shutter_time = 0
close_shutter_time = 10.75
lifetime_delay = 0
T2_delay = 3

slow_noise_eater_laser_time = 1.5  # time for each slow_noise_eater laser measurements
slow_noise_eater_magnetic_time = 3  # time for each magnetic field axis calibration


### magnetic fields ###

B_antihelmholtz = 1.4585356911757419

MOT25 = -0.725105444533
MOT36 = 0.419825949767
MOTb = 0
MOTv = -0.2536193

PGC25 = -0.849223557474
PGC36 = 1.0521398316
PGCb = 0
PGCv = -0.212002706826

PR25 = 0.0137550618104
PR36 = -0.041390028587
PRb = 0
PRv = -0.0107629184279

RO25 = -0.456076059135
RO36 = 0.457737110679
ROb = 0
ROv = -0.262290387664

EXP25 = -0.0285618703994
EXP36 = -0.0187129311724
EXPb = 2.182
EXPv = -0.270314008062

RYD25 = -0.0285618703994
RYD36 = -0.0187129311724
RYDb = 2.182
RYDv = -0.270314008062


### report ###

# sorts a list in place
def inplacesort(list):
    list.sort()
    return list

# quick save report strings to file
def tofile(path,str):
    with open(path,'w') as f:
        f.write(str)
    return str

#for pretty printing of j,m_j levels
def asHalf(f):
    n=int(f*2)
    if (n%2) == 0:
        return str(int(f))
    else:
        return str(n)+'/2'
 

### random benchmarking ###
#import random_benchmarking


### gate set tomography ###
#import gate_set_tomography
#GST_scripts, GST_lengths = gate_set_tomography.template_to_HSDIO_scripts(r'E:\AQuA_settings\GST\Phase1DataTemplate1a.txt')