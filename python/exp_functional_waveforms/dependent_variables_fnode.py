Bfields_mot = {
    'Bx': { 'current': Ix},
    'Bz': {'current': Iz},
    'Bq1': {'current': Iq + Iy},
    'Bq2': {'current': Iq - Iy}
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

Bfields_read = Bfields_pgc

Bfields = {
    'mot': Bfields_mot,
    'pgc': Bfields_pgc,
    'off': Bfields_off,
    'read': Bfields_read,
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
}

fort_aom_profiles = {
    'on': { 'freq': 112.5, 'amp': -3 },
    'off': { 'freq': 0, 'amp': -100  },
}


mot_time = cycle_time - 150
