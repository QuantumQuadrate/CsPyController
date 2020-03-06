Bfields_mot = {
    'Bx': { 'current': Ix},
    'By': { 'current': Iy},
    'Bz': {'current': Iz},
    'Bq1': {'current': Iq},
    'Bq2': {'current': Iq}
}

Bfields_mot_q_off = {
    'Bx': { 'current': Ix},
    'By': { 'current': Iy},
    'Bz': {'current': Iz},
    'Bq1': {'current': 0},
    'Bq2': {'current': 0}
}

Bfields_pgc = {
    'Bx': {'current': Ix_pgc},
    'By': { 'current': Iy_pgc},
    'Bz': {'current': Iz_pgc},
    'Bq1': {'current':  0},
    'Bq2': {'current': 0}
}

Bfields_pgc_post = {
    'Bx': {'current': Ix_pgc + dIx_pgc},
    'By': { 'current': Iy_pgc + dIy_pgc},
    'Bz': {'current': Iz_pgc + dIz_pgc},
    'Bq1': {'current':  0},
    'Bq2': {'current': 0}
}

Bfields_off = {
    'Bx': {'current': Ix_pgc},
    'By': { 'current': Iy_pgc},
    'Bz': {'current': Iz_pgc},
    'Bq1': {'current': 0},
    'Bq2': {'current': 0}
}

Bfields_read = {
    'Bx': {'current': Ix_read},
    'By': { 'current': Iy_read},
    'Bz': {'current': Iz_read},
    'Bq1': {'current':  0},
    'Bq2': {'current': 0}
}

Bfields_read_mz = {
    'Bx': {'current': 0*Ix_read+ 0.24361092 + Ix_read_mz},
    'By': { 'current': 0*Iy_read +0.375+ Iy_read_mz},
    'Bz': {'current': 0*Iz_read -0.025 + Iz_read_mz},
    'Bq1': {'current': 0},
    'Bq2': {'current': 0}
}

Bfields_expt = {
    'Bx': {'current': Ix_expt},
    'By': { 'current': Iy_expt},
    'Bz': {'current': Iz_expt},
    'Bq1': {'current': 0 },
    'Bq2': {'current': 0}
}

Bfields_op = {
    'Bx': {'current': Ix_op},
    'By': { 'current': Iy_op},
    'Bz': {'current': Iz_op},
    'Bq1': {'current':  0},
    'Bq2': {'current': 0}
}

Bfields = {
    'mot': Bfields_mot,
    'mot_q_off': Bfields_mot_q_off,
    'pgc': Bfields_pgc,
    'pgc_post': Bfields_pgc_post,
    'off': Bfields_off,
    'read': Bfields_read,
    'read_mz': Bfields_read_mz,
    'op': Bfields_op,
    'expt': Bfields_expt,
}

for phase in Bfields:
    for chan in Bfields[phase]:
        Bfields[phase][chan]['voltage'] = Bfields[phase][chan]['current'] * Bfield_channels[chan]['conversion']

#print(Bfields)
rb_d2_pgc2_det += pgc2_det_scan_offset
cs_d2_pgc2_det += pgc2_det_scan_offset
rb_d2_pgc2_amp += pgc2_amp_scan_offset
cs_d2_pgc2_amp += pgc2_amp_scan_offset

# step rb and cs uwave pulses simultaneously
if uwave_phase is not None:
    cs_uwave_time_ms = (0.5/cs_uwave_freq)*uwave_phase
    rb_uwave_time_ms = (0.5/rb_uwave_freq)*uwave_phase

rb_qubit_freq_offset_khz += uwave_offset_khz
cs_qubit_freq_offset_khz += uwave_offset_khz

rb_rf_preamp_db = -4.5 # - 3 db from var attn
rb_d2_aom_profiles = {
    'mot': { 'freq': rb_d2_aom_calc(rb_d2_mot_det), 'amp': rb_d2_mot_amp - rb_rf_preamp_db },
    'pgc': { 'freq': rb_d2_aom_calc(rb_d2_pgc_det), 'amp': rb_d2_pgc_amp - rb_rf_preamp_db  },
    'pgc2': { 'freq': rb_d2_aom_calc(rb_d2_pgc2_det), 'amp': rb_d2_pgc2_amp - rb_rf_preamp_db  },
    'off': { 'freq': 0, 'amp': -100 },
    'mon': { 'freq': rb_d2_aom_calc(-2.75), 'amp': -7.2 - rb_rf_preamp_db},
    'read': { 'freq': rb_d2_aom_calc(rb_d2_read_det), 'amp': rb_d2_read_amp - rb_rf_preamp_db },
    'read_mz': { 'freq': rb_d2_aom_calc(rb_d2_read_mz_det), 'amp': rb_d2_read_mz_amp - rb_rf_preamp_db },
}

cs_rf_preamp_db = 19-3 # 19 db amp + 3 db from var attn
cs_d2_aom_profiles = {
    'mot': { 'freq': cs_d2_aom_calc(cs_d2_mot_det), 'amp': cs_d2_mot_amp - cs_rf_preamp_db},
    'pgc': { 'freq': cs_d2_aom_calc(cs_d2_pgc_det), 'amp': cs_d2_pgc_amp  - cs_rf_preamp_db},
    'pgc2': { 'freq': cs_d2_aom_calc(cs_d2_pgc2_det), 'amp': cs_d2_pgc2_amp  - cs_rf_preamp_db},
    'off': { 'freq': 0, 'amp': -100 },
    'mon': { 'freq': 105.8, 'amp': 3 - cs_rf_preamp_db},
    'read': { 'freq': cs_d2_aom_calc(cs_d2_read_det), 'amp': cs_d2_read_amp - cs_rf_preamp_db },
    'read_mz': { 'freq': cs_d2_aom_calc(cs_d2_read_mz_det), 'amp': cs_d2_read_mz_amp - cs_rf_preamp_db },
}

fort_aom_profiles = {
    'on': { 'freq': 100, 'amp': -2.7 }, # -2.9
    'off': { 'freq': 80, 'amp': -100  },
    'high': { 'freq': 100, 'amp': -2.7 },
    'low': { 'freq': 100, 'amp': fort_low_pow  },
}

if exp_type in [fort_exp]:
    #mot_time = cycle_time - (2*readout_780 + drop_time + 10 + 0*gap_time + pgc_time + 5.2 + post_read_pgc_time)
    mot_time = cycle_time - (2*readout_780 + exra_readout_780 + max(op_time_ms, 2.5) + 2*uwave_gap_time_ms + drop_time + gap_time + 1 + pgc_time + 5.2 + post_read_pgc_time + op_time_ms +8)

    if test_mz_readout:
        cycle_time += test_mz_readout_duration
    if p_heating:
        cycle_time += p_heating_duration
    print "mot_time: {}".format(mot_time)

if dump_fort_at_end:
    # set pin default for fort off if we are keeping it off
    HSDIO_channels['fort_dds_p0']['default'] = True

if exp_type in [mot_cw_exp]:
    print "MOT CW experiment cycle time: {} ms".format(cycle_time)
