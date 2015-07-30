(
'parity phase = {}\n'.format(parity_phase) +

'\n'.join([i+' = '+str(locals()[i]) for i in [
'scanner_1_frequency_1_459',
'scanner_2_frequency_1_459',
'scanner_1_frequency_1_1038',
'scanner_2_frequency_1_1038',
'scanner_1_frequency_2_459',
'scanner_2_frequency_2_459',
'scanner_1_frequency_2_1038',
'scanner_2_frequency_2_1038'
]]) +

'\n\n' +

'\n'.join([i+' = '+str(locals()[i]) for i in [
'RydA_switch_AOM_frequency_1',
'RydA_switch_AOM_frequency_2',
'site_1_RydA_frequency_offset',
'site_2_RydA_frequency_offset',
'sitetosite_difference',
'rydberg_A_459_time_control',
'rydberg_A_459_time_target',
'microwave_pi_pulse',
'blow_away_time',
'T2_delay'
]])+    

'''

** Rydberg **
level: {}{}_{},{}
polarization:
\t459: 
\t1038: 
bias magnetic field during gate: 1.5G
beam waists:
\t459: {} (um)
\t1038 {} (um)
power at atoms:
\t459A: {}
\t1038: {}
frequencies:
\tdetuning from center of mass: {} (GHz)
\tRabi:
\t\t459a:  (MHz)
\t\t459b:  (MHz)
\t\t1038:  (MHz)
\t\tRydberg: {} (MHz)
spontaneous emission errors:
\tRydberg 2pi time:  (us)
\t7p lifetime:  (us)
\tRydberg lifetime: {} (us)
\tProbability of spontaneous decay from 7p in pi pulse:
\tProbability of Rydberg spontaneous decay in 2pi time:
'''.format(
Rydberg_n,
['S','P','D','F'][Rydberg_l],
asHalf(Rydberg_j),
asHalf(Rydberg_m),
Rydberg_459_beam_waist,
Rydberg_1038_beam_waist,
Rydberg_459_A_power_at_atoms,
Rydberg_1038_power_at_atoms,
Rydberg_detuning,
Rydberg_Rabi_Frequency_over_2pi * 2*pi,
1/Rydberg_sponteneous_emission_rate
)

+'\nblow_away_time = {}\n'.format(blow_away_time)

)
