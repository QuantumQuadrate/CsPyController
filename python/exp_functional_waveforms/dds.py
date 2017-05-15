'''The DDS class for accessing functionality of the ../DDS.py controller

Example usage:

### set up the DDS channels to use the DDS class for grey coding ###
# Alias the the profile() method of each of these instances, for convenience.
MOT = DDS(
    HSDIO,                                      # pass in HSDIO function so it can be used in the class
    (32, 33, 34),                               # HSDIO channels for profile pins
    {                                           # dict with channel descriptions and pin settings
        'MOT':(0,0,0), 
        'PGC in MOT':(1,0,0), 
        'off':(0,1,0), 
        'monitor':(0,0,1), 
        'readout':(1,1,0), 
        'light assisted collisions':(1,0,1), 
        'Blowaway':(0,1,1), 
        'PGC in traps':(1,1,1)}
    ).profile

# set the MOT DDS to profile 'MOT' at time t
t1_0 = MOT(t, 'MOT')
# set the MOT DDS to profile 'PGC' at time t
t1_0 = MOT(t, 'PGC')
'''

class DDS(object):
    """This class represents a single DDS channel controlled by one or more HSDIO channels.
    This class does NOT communicate directly with the DDS box, that is taken care of in the DDS.py file.
    This class only manipulates the HSDIO channels which switch the current HSDIO profile.
    It takes care of grey coding the profile changes.
    This class only works properly if all calls to a particular instance are done sequentially, 
    but that is the expected situation for a single DDS channel.
    In other words, the sequencing for a DDS() object must be done monotonically."""
    
    def __init__(self, HSDIO, channels, profiles=None, t=0):
        """Create a new DDS channel.
        channels:   a list of the HSDIO channels corresponding to the DDS bits.  e.g. (0, 1, 18)
        profile:    a dict using profile names as keys to look up the bit settings.  
                    e.g. {"MOT": (0,0,0), "OFF": (1,0,0)}
        """
        self.HSDIO = HSDIO
        self.channels = channels
        self.profiles = profiles
        
        # keep track of the state
        self.bits = [False, False, False]
        # keep track of the last time a bit was changed, to see if we need to add a DDS delay
        # assume that a bit was changed immediately before this, to be conservative
        self.last_change = t
    
    def initialize(self, t, new_bits):
        """Sets the state.  Unlike set(), this function sets every bit, regardless of its current state."""
        # set the state in the HSDIO, adding a delay between each bit setting if necessary
        for channel, new_bit in zip(self.channels, new_bits):
            t = self.delay(t)
            self.HSDIO(t, channel, new_bit)
        # keep track that the bits have all been set
        self.bits = new_bits
        return t
    
    def delay(self, t):
        """Add a DDS delay if it is needed, and update the last_change parameter."""

        if t <= (self.last_change + DDS_profile_delay):
            t += DDS_profile_delay
        # update the last_change parameter
        self.last_change = t
        return t
    
    def set(self, t, new_bits):
        """Sets the state.  Only bits that need to be flipped are flipped.  Grey coding is automatic.
        new_bits: the state we want to set"""

        # go through the bits one at a time
        for channel, old_bit, new_bit in zip(self.channels, self.bits, new_bits):
            # check to see if the bit needs to be changed
            if old_bit != new_bit:
                # delay if we recently changed another bit
                t = self.delay(t)
                self.HSDIO(t, channel, new_bit)
        # keep track that the bits have all been set
        self.bits = new_bits
        return t
     
    def profile(self, t, profile):
        """Switch to a specific profile by looking up the name in the stored dict."""
        return self.set(t, self.profiles[profile])

