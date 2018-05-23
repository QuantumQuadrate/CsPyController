Bfields_mot = {
    'Bx': { 'current': Ix},
    'Bz': {'current': Iz},
    'Bq1': {'current': Iq + Iy},
    'Bq2': {'current': Iq - Iy}
}

Bfields_mot_q_off = {
    'Bx': { 'current': Ix},
    'Bz': {'current': Iz},
    'Bq1': {'current': Iy},
    'Bq2': {'current': -1.0*Iy}
}

Bfields_pgc = {
    'Bx': {'current': Ix_pgc},
    'Bz': {'current': Iz_pgc},
    'Bq1': {'current':  Iy_pgc},
    'Bq2': {'current': -1.0*Iy_pgc}
}

Bfields_pgc_post = {
    'Bx': {'current': Ix_pgc + dIx_pgc},
    'Bz': {'current': Iz_pgc + dIz_pgc},
    'Bq1': {'current':  Iy_pgc + dIy_pgc},
    'Bq2': {'current': -1.0*(Iy_pgc + dIy_pgc)}
}

Bfields_off = {
    'Bx': {'current': Ix_pgc},
    'Bz': {'current': Iz_pgc},
    'Bq1': {'current':  Iy_pgc},
    'Bq2': {'current': -1.0*Iy_pgc}
}

Bfields_read = {
    'Bx': {'current': Ix_read},
    'Bz': {'current': Iz_read},
    'Bq1': {'current':  Iy_read},
    'Bq2': {'current': -1.0*Iy_read}
}

Bfields_read_mz = {
    'Bx': {'current': Ix_read + Ix_read_mz},
    'Bz': {'current': Iz_read + Iz_read_mz},
    'Bq1': {'current': Iy_read + Iy_read_mz},
    'Bq2': {'current': -1.0*(Iy_read + Iy_read_mz)}
}

Bfields_expt = {
    'Bx': {'current': Ix_expt},
    'Bz': {'current': Iz_expt},
    'Bq1': {'current':  Iy_expt},
    'Bq2': {'current': -1.0*Iy_expt}
}

Bfields_op = {
    'Bx': {'current': Ix_expt},
    'Bz': {'current': Iz_op},
    'Bq1': {'current':  Iy_expt},
    'Bq2': {'current': -1.0*Iy_expt}
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

rb_d2_aom_profiles = {
    'mot': { 'freq': rb_d2_aom_calc(rb_d2_mot_det), 'amp': rb_d2_mot_amp },
    'pgc': { 'freq': rb_d2_aom_calc(rb_d2_pgc_det), 'amp': rb_d2_pgc_amp  },
    'pgc2': { 'freq': rb_d2_aom_calc(rb_d2_pgc2_det), 'amp': rb_d2_pgc2_amp  },
    'off': { 'freq': 0, 'amp': -100 },
    'mon': { 'freq': 100.0, 'amp': 0.0},
    'read': { 'freq': rb_d2_aom_calc(rb_d2_read_det), 'amp': rb_d2_read_amp },
    'read_mz': { 'freq': rb_d2_aom_calc(rb_d2_read_mz_det), 'amp': rb_d2_read_mz_amp },
}

cs_d2_aom_profiles = {
    'mot': { 'freq': cs_d2_aom_calc(cs_d2_mot_det), 'amp': cs_d2_mot_amp },
    'pgc': { 'freq': cs_d2_aom_calc(cs_d2_pgc_det), 'amp': cs_d2_pgc_amp  },
    'pgc2': { 'freq': cs_d2_aom_calc(cs_d2_pgc2_det), 'amp': cs_d2_pgc2_amp  },
    'off': { 'freq': 0, 'amp': -100 },
    'mon': { 'freq': 100.0, 'amp': 0.0},
    'read': { 'freq': cs_d2_aom_calc(cs_d2_read_det), 'amp': cs_d2_read_amp },
    'read_mz': { 'freq': cs_d2_aom_calc(cs_d2_read_mz_det), 'amp': cs_d2_read_mz_amp },
}

fort_aom_profiles = {
    'on': { 'freq': 115, 'amp': -2.9 }, # -2.9
    'off': { 'freq': 80, 'amp': -100  },
    'high': { 'freq': 115, 'amp': 0 },
    'low': { 'freq': 115, 'amp': fort_low_pow  },
}

if exp_type in [fort_exp]:
    #mot_time = cycle_time - (2*readout_780 + drop_time + 10 + 0*gap_time + pgc_time + 5.2 + post_read_pgc_time)
    mot_time = cycle_time - (2*readout_780 + drop_time + gap_time + pgc_time + 5.2 + post_read_pgc_time + op_time_ms +2)

    if test_mz_readout:
        cycle_time += test_mz_readout_duration
    if p_heating:
        cycle_time += p_heating_duration
    cycle_time += exra_readout_780
    cycle_time += max(op_time_ms, 2.5)
    # cycle_time += gap_time
    print "mot_time: {}".format(mot_time)

if dump_fort_at_end:
    # set pin default for fort off if we are keeping it off
    HSDIO_channels['fort_dds_p0']['default'] = True

if exp_type in [mot_cw_exp]:
    print "MOT CW experiment cycle time: {} ms".format(cycle_time)
