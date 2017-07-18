
'''profiles are enumerated and of the form:

profiles = {
    'MOT':0, 
    'PGC in MOT':1, 
    'readout':2, 
    '685':3, 
    'optical pumping':4, 
    'Rydberg':5, 
    'light assisted collisions':6,
    'gradient only':7, 
    'x1_4 only':8, 
    'x2_5 only':9, 
    'x3_6 only':10, 
    'vertical only':11, 
    'off':12
}

settings are of the form:

columns are profiles, and rows are specific coils
np.array([
    [],
    [],
    []
])
'''

class BFields(object):
    """Switch to the magnetic fields of choice, defined by the magnetic fields matrix."""

    def __init__(self, AO, profiles, fields):
        self.AO = AO
        self.profiles = profiles
        self.fields = fields

    def set_fields(self, t, profile):
        # for each AO channel (rows of the magnetic field matrix)
        for channel, fields in enumerate(self.fields):
            # switch to the field defined by the column of the magnetic fields matrix selected by 'profile'
            self.AO(t, channel, fields[profiles[profile]])
        return t

