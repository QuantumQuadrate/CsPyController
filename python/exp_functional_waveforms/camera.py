'''A camera class which remembers when the last camera shot occurred'''

from switch import Switch

''' Create a special camera class so we can keep track of when the last shot was

example usage:
Hamamatsu = Camera(
                0,  # time 
                39  # HSDIO channel
            )
'''
class Camera(Switch):
    """A special case of switch that also keeps track of when the last shot was."""

    def __init__(self, HSDIO, channel, delay=0, t=0, pulse_length=0.001):
        super(Camera, self).__init__(HSDIO, channel, {'open':1, 'closed':0}, delay=delay)
        self.last_shot = t
        self.pulse_length = pulse_length

    def take_shot(self, t):
        '''takes a camera shot by sending a trigger pulse of width defined by self.pulse_length'''
        self.last_shot = t
        self.profile(t, 'open')
        return self.profile(t + self.pulse_length, 'close')
 
