'''generic switch class, no grey coding

example usage:

### set up the switches that do not need grey coding ###
# Alias the the profile() method of each of these instances, for convenience.
MOT2D_shutter = switch(
                    36,                         # HSDIO pin number
                    profiles={'on':0, 'off':1}  # active low override of the default
                    delay=0.001                 # channel delay to tune in timings
                ).profile
'''

class Switch(object):
    """A single HSDIO channel that controls a switch.  
    Unlike DDS(), this does not use any grey coding or delays.
    Default profile is active high output.
    If this is not correct override teh default setting.
    A positive delay makes the channel fire later
    """
    
    def __init__(self, HSDIO, channel, profiles={'on':1, 'off':0}, delay=0):
        """
        channel: the HSDIO channel that controls this device
        profiles: a dict of profile settings, e.g {'on':1, 'off':2}
        """
        self.HSDIO = HSDIO
        self.channel = channel
        self.profiles = profiles
        self.delay = delay
    
    def profile(self, t, profile):
        """Set the HSDIO channel to the requested state"""
        t_actual = t + self.delay
        if t_actual < 0:
            t_actual = 0
            logger.warning('Channel `%d` change event set to negative time, moving to 0.', self.channel)
        self.HSDIO(t + self.delay, self.channel, self.profiles[profile])
        return t

