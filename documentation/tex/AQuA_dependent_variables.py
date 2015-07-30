####### experiment specific #######


####### dependent calculations #######

### MOT ###

hyperfine_time = MOT_loading_time


### PGC ###

PGC_hyperfine_time = PGC_1_time


### Optical Pumping ###

OP_field_time = PGC_to_bias_B_field_delay+optical_pumping_time+Op_Hf_extratime  #+depumping_894_time

### microwaves ###

microwave_pulse_3pi_by_4 = microwave_pi_pulse*(3/4)
microwave_Raman_time = microwave_pi_pulse

#microwave_phase_pi2_pulse_site1 corresponds to DDS box 2 channel 3 profile 5, microwave_phase_pi2_pulse_site1 corresponds to DDS box 2 channel 3 profile 2
microwave_phase_pi2_pulse_site1 = microwave_pi2_phase #over-write this in grover experiments
microwave_phase_pi2_pulse_site2 = microwave_pi2_phase #over-write this in grover experiments

### composite pulses ###

k_c=arcsin(sin(3.1416*microwave_pi_pulse/microwave_2pi_pulse)/2)/6.283*microwave_2pi_pulse
#CORPS1=microwave_2pi_pulse + microwave_pi_pulse/2 - k_c
#CORPS2=microwave_2pi_pulse -2*k_c
#CORPS3=microwave_pi_pulse/2 - k_c
CORPS1=delay_before_excitation_pulse+7*microwave_pi_by_3
CORPS2=delay_before_excitation_pulse+5*microwave_pi_by_3
CORPS3=delay_before_excitation_pulse+microwave_pi_by_3
CORPS=CORPS1+CORPS2+CORPS3


### Rydberg ###

rydberg_A_459_time_control = rydberg_RFE_pi_time_1
rydberg_A_459_time_control_2 = difference_between_control_pi_1_and_control_pi_2 + rydberg_A_459_time_control
rydberg_A_459_time_target = rydberg_RFE_2pi_time_2 #CAUTION: sometimes this is 2pi time!
rydberg_A_459_time_site3 = 2*rydberg_RFE_pi_time_3

#for 459 alignment only
#rydberg_A_459_time_control = .8 * rydberg_A_459_time_control_pi
#rydberg_A_459_time_target = .8 * rydberg_A_459_time_target_pi
#rydberg_A_459_time_site3 = .9 * rydberg_A_459_time_site3_pi

rydberg_A_1038_time_control = rydberg_A_459_time_control
rydberg_A_1038_time_control_2 = rydberg_A_459_time_control_2
rydberg_A_1038_time_target = rydberg_A_459_time_target
rydberg_A_1038_time_site3= rydberg_A_459_time_site3 

#take out when doing ground-Rydberg Ramsey experiment
Ryd_ramsey_delay = 2*rydberg_RFE_pi_time_2 + 2*switching_delay

# These frequency offsets are used to calculate switchyard frequency for each site given new scanner values after alignments.
# The sum of all the frequency shifts should be constant given that the rydberg level and beam powers are not changed

RydA_switch_AOM_frequency_1 = .5 * (  site_1_RydA_frequency_offset 
                                                                                  -(scanner_1_frequency_1_459   - scanner_2_frequency_1_459)
                                                                                  -(scanner_1_frequency_1_1038 - scanner_2_frequency_1_1038) )
RydA_switch_AOM_frequency_2 =   .5* (  site_2_RydA_frequency_offset
                                                                                 -(scanner_1_frequency_2_459   - scanner_2_frequency_2_459)
                                                                                 -(scanner_1_frequency_2_1038 - scanner_2_frequency_2_1038) )
RydA_switch_AOM_frequency_3 = .5 * (  site_3_RydA_frequency_offset 
                                                                                  -(scanner_1_frequency_3_459   - scanner_2_frequency_3_459)
                                                                                  -(scanner_1_frequency_3_1038 - scanner_2_frequency_3_1038) )
sitetosite_difference = site_1_RydA_frequency_offset - site_2_RydA_frequency_offset


### Analog Output equations ###

# Table of magnetic field settings.  Rows are gradient, x25, x36, vert, x14.  Columns are:
MOT=0; PGC_1=1; readout=2; _685=3; Exp=4; ryd=5; prereadout=6; gradient_only=7; x1_4only=8; x2_5only=9; x3_6only=10; vertical_only=11; OFF=12;

magnetic_fields = np.array(
    [[B_antihelmholtz, 0,         0,         0,       0,         0,          0,        1, 0, 0, 0, 0, 0],
      [MOT25,              PGC25, RO25,  0,       EXP25, RYD25, PR25, 0, 0, 1, 0, 0, 0],
      [MOT36,              PGC36, RO36, -0.55, EXP36, RYD36, PR36, 0, 0, 0, 1, 0, 0],
      [MOTv,                 PGCv,   ROv,   -1.55, EXPv,    RYDv,   PRv,   0,  0, 0, 0, 1, 0],
      [MOTb,                PGCb,   ROb,    0,       EXPb,   RYDb,   PRb,   0, 1, 0, 0, 0, 0]])

# coil driver calibrations.  Drivers: CoilDriver.v2h.10, v2h.3, v2h.4, v2g.2, v2g.1
offset = np.array([-0.00144668, -0.0000453172, +0.000748044, -.00129657, -.00261032])
scale = np.array([-0.995666, -0.996497, -0.999946, -0.994236, -1.00318])
magnetic_fields = ((magnetic_fields.T + offset)/scale).T


### Report calculations below ###

# mot/readout parameter input
mot_beam_waist_1 = 2.5  # mm
mot_beam_waist_2 = 2.5  # mm
mot_beam_waist_3 = 1.54  # mm
readout_beam_power_1 = 560  # uW
readout_beam_power_2 = 415  # uW
readout_beam_power_3 = 205  # uW
readout_detuning = 18  # MHz
numerical_aperture_of_jenoptiq = .4
transmission_efficiency = .8
quantum_efficiency = .7
conversion_factor_for_camera = 5.8  # electrons/count
analog_gain = 4
EM_sensitivity = int(EMCCD_gain)  # from independent variable
EM_gain = 10**(((log(1000)-log(4))/250)*EM_sensitivity+log(4))
average_background_pixel_value = 10914*(Readout_time/.100)
roi_area = 9
imaging_system_mag = 25.5
camera_pixel_size = 16  # um

# array parameter input
number_of_array_spots = 64  # n
array_trap_spacing = 3.8  # d_microns
array_beam_waist = 1.73  # w0_microns
power_out_of_the_fiber_780 = 5  # W
transmission_to_atoms_780 = .45

# excitation beam parameter input
scanner_transmission_459 = .132
scanner_transmission_1038 = .25

horizontal_waist_459 = 3e-6
vertical_waist_459 = 3e-6
horizontal_waist_1038 = 3.2e-6
vertical_waist_1038 = 4.3e-6

total_raman_power_at_fiber = 263.8e-6
raman_detuning = 20e9 #Hz

Rydberg_A_459_power_at_fiber =303e-6
Rydberg_B_459_power_at_fiber = 120e-6
Rydberg_1038_power_at_fiber = 10e-3
Rydberg_n = 82
Rydberg_l = 0 #D level
Rydberg_j = 1/2
Rydberg_m = 1/2
Rydberg_detuning = .658e9 #Hz relative to f = (4 -> 4')

# mot/readout calculations
readout_detuning = readout_detuning*2*pi*1e6
readout_beam_intensity_1 = 2*readout_beam_power_1*1e-6/(pi*mot_beam_waist_1**2*1e-6)
readout_beam_intensity_2 = 2*readout_beam_power_2*1e-6/(pi*mot_beam_waist_2**2*1e-6)
readout_beam_intensity_3 = 2*readout_beam_power_3*1e-6/(pi*mot_beam_waist_3**2*1e-6)
total_intensity = 2*readout_beam_intensity_1+2*readout_beam_intensity_2+2*readout_beam_intensity_3
total_saturation_parameter = total_intensity/saturation_intensity
fractional_solid_angle = .5*(1-sqrt(1-numerical_aperture_of_jenoptiq**2))
scattering_rate = (gamma_6p3_2/2)*total_saturation_parameter/(1+(4*readout_detuning**2)/(gamma_6p3_2**2)+total_saturation_parameter)
detected_scattering_rate_for_single_atom = scattering_rate*fractional_solid_angle*transmission_efficiency*quantum_efficiency
detected_photon_number_during_exposure_time = detected_scattering_rate_for_single_atom*Readout_time*(1e-3)
expected_output_signal_dark_signal = detected_photon_number_during_exposure_time*analog_gain*EM_gain*quantum_efficiency/conversion_factor_for_camera
expected_output_signal = expected_output_signal_dark_signal+average_background_pixel_value*roi_area
pixel_size_after_mag = camera_pixel_size/imaging_system_mag #um

# array calculations
lattice_period = array_trap_spacing/pixel_size_after_mag #in pixels
array_ratio = array_trap_spacing/array_beam_waist #s=d/w
total_power_at_atoms = power_out_of_the_fiber_780*transmission_to_atoms_780 #W
P0 = (2*total_power_at_atoms/number_of_array_spots)/(pi*array_beam_waist**2e-12) #peak_intensity_in_one_spot
trap_depth = -(0.001*2*pi*alpha_780_cgs/(kB_SI*c0))*P0*2*exp(-array_ratio**2/2)*(1-2*exp(-array_ratio**2/2)) #mK

# raman calculations
Raman_Rabi_freq = total_raman_power_at_fiber/2*scanner_transmission_459/(2*pi*horizontal_waist_459*vertical_waist_459)*((-1.305e9)/(raman_detuning-hyperfine_splitting_7p1_2)-7.83e8/raman_detuning) #Hz
Raman_Stark_shift = total_raman_power_at_fiber/2*scanner_transmission_459/(2*pi*horizontal_waist_459*vertical_waist_459)*(4.1e9/(2*pi*(raman_detuning-hyperfine_splitting_7p1_2-hyperfine_splitting_6s1_2))-4.1e9/(2*pi*(raman_detuning-hyperfine_splitting_7p1_2+hyperfine_splitting_6s1_2)+2.46e9/(2*pi*(raman_detuning-hyperfine_splitting_6s1_2))-2.46e9/(2*pi*(raman_detuning+hyperfine_splitting_6s1_2)))) #Hz
Rydberg_A_flopping_to_nD3_2 = 1/(2*pi*Rydberg_n**(3/2))*sqrt(Rydberg_A_459_power_at_fiber*scanner_transmission_1038*Rydberg_1038_power_at_fiber*scanner_transmission_1038/(horizontal_waist_459*vertical_waist_459*horizontal_waist_1038*vertical_waist_1038))*(9.692e10/(Rydberg_detuning)+5.815e10/(Rydberg_detuning+hyperfine_splitting_7p1_2)) #Hz
Rydberg_B_flopping_to_nD3_2 = 1/(2*pi*Rydberg_n**(3/2))*sqrt(Rydberg_B_459_power_at_fiber*scanner_transmission_1038*Rydberg_1038_power_at_fiber*scanner_transmission_1038/(horizontal_waist_459*vertical_waist_459*horizontal_waist_1038*vertical_waist_1038))*(9.692e10/(Rydberg_detuning)+5.815e10/(Rydberg_detuning+hyperfine_splitting_7p1_2)) #Hz
Raman_459_power_out_of_fiber = total_raman_power_at_fiber*1e3 #mW
Raman_459_transmission_of_scanner = scanner_transmission_459
Raman_459_power_at_atoms = Raman_459_power_out_of_fiber*Raman_459_transmission_of_scanner #mW
Raman_459_detuning = raman_detuning*1e-9 #GHz
Raman_459_waist_at_atoms = sqrt(horizontal_waist_459*vertical_waist_459)*1E6 #um
Raman_459_7p1_2_Delta_f3 = -.2123 #GHz
Raman_459_7p1_2_Delta_f4 = .1651 #GHz
Raman_459_intermediate = 1/(Raman_459_detuning-Raman_459_7p1_2_Delta_f3)+(5/3)/(Raman_459_detuning-Raman_459_7p1_2_Delta_f4)
Raman_459_Rabi_Omega_over_2pi = 93.3*Raman_459_intermediate*Raman_459_power_at_atoms/Raman_459_waist_at_atoms**2 #MHz
Raman_459_gamma_p = 1/150 #GHz
Raman_459_omega_q = 9.192 #GHz
Raman_459_Pse_in_pi_pulse = Raman_459_gamma_p/4*(1/abs(Raman_459_intermediate))*(2/(Raman_459_detuning-Raman_459_7p1_2_Delta_f3)**2+1/(Raman_459_detuning-Raman_459_7p1_2_Delta_f3+Raman_459_omega_q)**2+1/(Raman_459_detuning-Raman_459_7p1_2_Delta_f3-Raman_459_omega_q)**2+(10/3)/(Raman_459_detuning-Raman_459_7p1_2_Delta_f4)**2+(5/3)/(Raman_459_detuning-Raman_459_7p1_2_Delta_f4+Raman_459_omega_q)**2+(5/3)/(Raman_459_detuning-Raman_459_7p1_2_Delta_f4-Raman_459_omega_q)**2)
Raman_459_differential_stark_shift = Raman_459_Rabi_Omega_over_2pi*(Raman_459_detuning/32)*((5/3)/(Raman_459_detuning-Raman_459_7p1_2_Delta_f4+Raman_459_omega_q)+1/(Raman_459_detuning-Raman_459_7p1_2_Delta_f3+Raman_459_omega_q)-(5/3)/(Raman_459_detuning-Raman_459_7p1_2_Delta_f4-Raman_459_omega_q)-1/(Raman_459_detuning-Raman_459_7p1_2_Delta_f3-Raman_459_omega_q)) #MHz

# Rydberg calculations
Rydberg_459_A_power_at_atoms = Rydberg_A_459_power_at_fiber*scanner_transmission_459*(1e3) #mW
Rydberg_1038_power_at_atoms = Rydberg_1038_power_at_fiber*scanner_transmission_1038*(1e3) #mW
Rydberg_459_beam_waist = sqrt(horizontal_waist_459*vertical_waist_459)*(1e6)
Rydberg_1038_beam_waist = sqrt(horizontal_waist_1038*vertical_waist_1038)*(1e6)
Rydberg_detuning_3p = -212.3*(2*pi) #MHz
Rydberg_detuning_4p = 165.1*(2*pi) #MHz
Rydberg_detuning = Rydberg_detuning*1e-9 +.165#GHz F=4 to 7P center of gravity
Rydberg_detuning_over_2pi = Rydberg_detuning*(2*pi)*1e3 #MHz

if Rydberg_l==0: #nS
    Rydberg_Rabi_Frequency_over_2pi = 20600*(sqrt(Rydberg_459_A_power_at_atoms*Rydberg_1038_power_at_atoms)/(Rydberg_n**(3/2)*Rydberg_459_beam_waist*Rydberg_1038_beam_waist*Rydberg_detuning))*(1-(5/8)*(Rydberg_detuning_3p/Rydberg_detuning_over_2pi)-(3/8)*(Rydberg_detuning_4p/Rydberg_detuning_over_2pi))/((1-(Rydberg_detuning_3p/Rydberg_detuning_over_2pi))*(1-(Rydberg_detuning_4p/Rydberg_detuning_over_2pi))) #MHz
elif Rydberg_l==2: #nD
    Rydberg_Rabi_Frequency_over_general = 240600*(sqrt(Rydberg_459_A_power_at_atoms*Rydberg_1038_power_at_atoms)/(Rydberg_n**(3/2)*Rydberg_459_beam_waist*Rydberg_1038_beam_waist*Rydberg_detuning)) # MHz
    angluar_factor_m3over2=1/(2*sqrt(6))
    Rydberg_Rabi_Frequency_over_2pi=Rydberg_Rabi_Frequency_over_general*angluar_factor_m3over2

Rydberg_AC_stark_shift = (160200*(Rydberg_1038_power_at_atoms/(Rydberg_n**3*Rydberg_1038_beam_waist**2))-93.47*(Rydberg_459_A_power_at_atoms/Rydberg_459_beam_waist**2))*(1/Rydberg_detuning)*((1/(1-Rydberg_detuning_3p/Rydberg_detuning_over_2pi))+((5/3)/(1-Rydberg_detuning_4p/Rydberg_detuning_over_2pi)))
Rydberg_sponteneous_emission_rate = (.43*(sqrt(Rydberg_1038_power_at_atoms)*Rydberg_459_beam_waist/(Rydberg_n**(3/2)*sqrt(Rydberg_459_A_power_at_atoms)*Rydberg_1038_beam_waist))+(2.5e-4)*(sqrt(Rydberg_459_A_power_at_atoms)*Rydberg_1038_beam_waist/(Rydberg_n**(3/2)*sqrt(Rydberg_1038_power_at_atoms)*Rydberg_459_beam_waist)))*(1/Rydberg_detuning)*(1-2*((5/8)*(Rydberg_detuning_3p/Rydberg_detuning_over_2pi)+(3/8)*(Rydberg_detuning_4p/Rydberg_detuning_over_2pi))+(5/8)*(Rydberg_detuning_3p/Rydberg_detuning_over_2pi)**2+(3/8)*(Rydberg_detuning_4p/Rydberg_detuning_over_2pi)**2)/((1-Rydberg_detuning_3p/Rydberg_detuning_over_2pi)*(1-Rydberg_detuning_4p/Rydberg_detuning_over_2pi)*(1-(5/8)*(Rydberg_detuning_3p/Rydberg_detuning_over_2pi)-(3/8)*(Rydberg_detuning_4p/Rydberg_detuning_over_2pi)))
Rydberg_blue_power_needed_to_match_red_Rabi = (1/scanner_transmission_459)*(Rydberg_1038_power_at_atoms*Rydberg_459_beam_waist**2)/(.00058*Rydberg_1038_beam_waist**2*Rydberg_n**3)

power_894 = .450 #uW
OP_repumper = 8.5 #uW
