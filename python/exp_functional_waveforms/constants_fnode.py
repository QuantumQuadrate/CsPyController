DO_channels = {
    'error1': { 'channel': 4 },
    'error2': { 'channel': 5 },
    'idle': { 'channel': 6 },
    'running': { 'channel': 7 }
}

HSDIO_channels = {
    'point_grey_1': { 'channel': 0 },
    'rb_d2_dds_p0': { 'channel': 5 },
    'rb_d2_dds_p1': { 'channel': 6 },
    'rb_d2_dds_p2': { 'channel': 7 },
    'rb_d1_dds_p0': { 'channel': 8 },
    'rb_d1_dds_p1': { 'channel': 9 },
    'rb_d1_dds_p2': { 'channel': 10 },
    'fort_dds_p0': { 'channel': 11 },
    'scope_trig_2': { 'channel': 27 },
    'spcm_gate_780': {'channel': 28},
    'noise_eater_trig_1': { 'channel': 29 },
    'luca_trig_1': { 'channel': 30 },
    'scope_trig_1': { 'channel': 31 }
}

Bfield_channels = {
    'Bx': { 'channel': 8, 'conversion': -1.0  },
    'Bz': { 'channel': 9, 'conversion': -1.0 },
    'Bq1': { 'channel': 10, 'conversion': -1.0 },
    'Bq2': { 'channel': 11, 'conversion': -1.0  }
}


#######################################################
## RB AOM STUFF ###########################################
#######################################################

def aom_calc(det_MHz, lock_offset_MHz, passes):
    """Calculate the AOM frequency to get the requested detuning in units of MHz"""
    return (det_MHz - lock_offset_MHz)/passes

def rb_d2_aom_calc(det):
    """Calculate the AOM frequency to get the requested detuning in units of Gamma"""

    # d2 linewidth
    gamma_MHz = 6.0666
    # double pass
    aom_passes = 2
    # locked to the 1-3 crossover
    lock_offset_MHz = -1.0 * (266.65 + 156.947) / 2
    return aom_calc(det*gamma_MHz, lock_offset_MHz, aom_passes)

#######################################################
## SPCM STUFF #############################################
#######################################################

throwaway_bins = 3
throwaway_bin_duration = 0.01  # 10 us
measurement_bins = 1
readout_chop_freq_MHz = 0.01
