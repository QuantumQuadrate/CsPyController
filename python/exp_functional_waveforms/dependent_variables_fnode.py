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
    'Bq1': {'current':  Iy_read + Iy_read_mz},
    'Bq2': {'current': -1.0*(Iy_read + Iy_read_mz)}
}

Bfields = {
    'mot': Bfields_mot,
    'mot_q_off': Bfields_mot_q_off,
    'pgc': Bfields_pgc,
    'off': Bfields_off,
    'read': Bfields_read,
    'read_mz': Bfields_read_mz,
}

for phase in Bfields:
    for chan in Bfields[phase]:
        Bfields[phase][chan]['voltage'] = Bfields[phase][chan]['current'] * Bfield_channels[chan]['conversion']

#print(Bfields)

rb_d2_aom_profiles = {
    'mot': { 'freq': rb_d2_aom_calc(rb_d2_mot_det), 'amp': rb_d2_mot_amp },
    'pgc': { 'freq': rb_d2_aom_calc(rb_d2_pgc_det), 'amp': rb_d2_pgc_amp  },
    'off': { 'freq': 0, 'amp': -100 },
    'mon': { 'freq': 100.0, 'amp': 0.0},
    'read': { 'freq': rb_d2_aom_calc(rb_d2_read_det), 'amp': rb_d2_read_amp },
    'read_mz': { 'freq': rb_d2_aom_calc(rb_d2_read_mz_det), 'amp': rb_d2_read_mz_amp },
}

fort_aom_profiles = {
    'on': { 'freq': 115, 'amp': -2.55 },
    'off': { 'freq': 80, 'amp': -100  },
    'high': { 'freq': 115, 'amp': -1 },
    'low': { 'freq': 115, 'amp': -3.7  },
}

if exp_type in [fort_exp]:
    mot_time = cycle_time - (2*readout_780 + drop_time + gap_time + pgc_time + 2.1 + post_read_pgc_time)
    if test_mz_readout:
        cycle_time += test_mz_readout_duration
    if p_heating:
        cycle_time += p_heating_duration
    cycle_time += exra_readout_780
    print "mot_time: {}".format(mot_time)

if exp_type in [mot_cw_exp]:
    print "MOT CW experiment cycle time: {} ms".format(cycle_time)
