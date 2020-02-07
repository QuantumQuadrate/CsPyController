fort_exp = 0
mot_cw_exp = 1
mot_tof_exp = 2
mot_gtoggle_exp = 3

DO_channels = {
    'error1': { 'channel': 4 },
    'error2': { 'channel': 5 },
    'idle': { 'channel': 6 },
    'running': { 'channel': 7 }
}

HSDIO_channels = {
    #'point_grey_1': { 'channel': 0, 'default': False },  # reused for error coutner
    'rb_d2_dds_p0': { 'channel': 5, 'default': False },
    'rb_d2_dds_p1': { 'channel': 6, 'default': False },
    'rb_d2_dds_p2': { 'channel': 7, 'default': False },
    'cs_d2_dds_p0': { 'channel': 8, 'default': False },
    'cs_d2_dds_p1': { 'channel': 9, 'default': False },
    'cs_d2_dds_p2': { 'channel': 10, 'default': False },
    'fort_dds_p0': { 'channel': 11, 'default': False },
    'fort_dds_p1': { 'channel': 3, 'default': False },

    'mxy_shutter': { 'channel': 12, 'default': True },
    'm_shutter': { 'channel': 2, 'default': False },
    'rb_hf_shutter': { 'channel': 13, 'default': False },
    'op_shutter': { 'channel': 14, 'default': True },
    'cs_hf_shutter': { 'channel': 15, 'default': True },
    'mz2_shutter': { 'channel': 17, 'default': True },

    'cs_459_aom_switch': { 'channel': 18, 'default': False },

    'ne_adc_trig_1': { 'channel': 25, 'default': False },
    'ne_adc_trig_0': { 'channel': 24, 'default': False },
    'fpga_threshold_sel': { 'channel': 26, 'default': False },
    'fpga_counter_gate': { 'channel': 30, 'default': False },
    'spcm_gate_780': {'channel': 28, 'default': False },
    'error_cntr_gate': { 'channel': 0, 'default': False },

    'rb_uwave_switch': { 'channel': 29, 'default': False }, # uWave on/off switch
    'rb_horn_switch': { 'channel': 1, 'default': False },   # transfer switch between horn and F-EOM (default)
    'cs_uwave_switch': { 'channel': 4, 'default': False },  # uWave on/off switch
    'cs_horn_switch': { 'channel': 16, 'default': False },  # transfer switch between horn and F-EOM (default)

    'luca_trig_1': { 'channel': 27, 'default': False },
    'scope_trig_1': { 'channel': 31, 'default': False }
}

AO_channels = {
    'fort_attn': { 'channel': 13, 'conversion': 1 },
}

Bfield_channels = {
    'Bx': { 'channel': 8, 'conversion': -1.0  },
    'By': { 'channel': 12, 'conversion': -1.0  },
    'Bz': { 'channel': 9, 'conversion': -1.0 },
    'Bq1': { 'channel': 10, 'conversion': -1.0 },
    'Bq2': { 'channel': 11, 'conversion': -1.0 }
}


field_settle_time = 0.4  # ms for b field changes to settle

###########################################################
## AOM STUFF ##############################################
###########################################################

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


def cs_d2_aom_calc(det):
    """Calculate the AOM frequency to get the requested detuning in units of Gamma"""

    # d2 linewidth
    gamma_MHz = 5.234
    # double pass
    aom_passes = 2
    # locked to the 3-5 crossover
    lock_offset_MHz = -1.0 * (251.0916 + 201.2871) / 2
    return aom_calc(det*gamma_MHz, lock_offset_MHz, aom_passes)


def fort_attn_cal(x, v_bias=1.295):
    """Calculate the modulation voltage necessary to change the power to the ratio at v=0"""
    # bias = v_bias - 1.295
    return -0.908368 + 1.39935*x - 0.987305*x**2 + 0.496318*x**3

###########################################################
## SPCM STUFF #############################################
###########################################################

throwaway_bins = 3
throwaway_bin_duration = 0.01  # 10 us
measurement_bins = 40
readout_chop_freq_MHz = 1.25
op_chop_freq_MHz = 1.0/2

###########################################################
## SHUTTER STUFF ##########################################
###########################################################

MXY_shutter_delay_ms = 1.714
MXY_shutter_time_ms = 0.4

# closes all MOT and HF paths (rb+cs)
M_shutter_delay_ms = 1.38
M_shutter_time_ms = 1.0

# MZ retro shutter for SSRO
MZ2_shutter_delay_ms = 1.4
MZ2_shutter_time_ms = 0

SSRO = True  # default
# RB
RB_HF_shutter_delay_ms = 0.98
RB_HF_shutter_time_ms = 0.82
# CS
CS_HF_shutter_delay_ms = 1.4
CS_HF_shutter_time_ms = 1.2

OP_shutter_delay_ms = 1.63
OP_shutter_time_ms = 1.2


###########################################################
## RF STUFF ###############################################
###########################################################

rb_uwave_freq =5.017099491477866
cs_uwave_freq =6.360851014014818

rb_qubit_freq_ghz = 6.834682611
cs_qubit_freq_ghz = 9.192631770
