<<<<<<< HEAD
"""HSDIO.py
Part of the AQuA Cesium Controller software package

author=Martin Lichtman
created=2013-10-08
modified>=2015-05-24
modified>=2017-10-23

This file holds everything needed to model the high speed digital output from
the National Instruments HSDIO card.  It communicates to LabView via the higher
up LabView(Instrument) class.
"""
from __future__ import division
import logging
import numpy as np
import dicttoxml

from cs_errors import PauseError

from atom.api import Typed, Member, Int

from instrument_property import Prop, BoolProp, IntProp, FloatProp, StrProp, ListProp
from cs_instruments import Instrument
from digital_waveform import NumpyChannels


__author__ = 'Martin Lichtman'
logger = logging.getLogger(__name__)


class ScriptTrigger(Prop):
    id = Typed(StrProp)
    source = Typed(StrProp)
    type = Typed(StrProp)
    edge = Typed(StrProp)
    level = Typed(StrProp)

    def __init__(self, name, experiment, description=''):
        super(ScriptTrigger, self).__init__('trigger', experiment, description)
        self.id = StrProp('id', experiment, '', '"ScriptTrigger0"')
        self.source = StrProp('source', experiment, '', '"PFI0"')
        self.type = StrProp('type', experiment, '', '"edge"')
        self.edge = StrProp('edge', experiment, '', '"rising"')
        self.level = StrProp('level', experiment, '', '"high"')
        self.properties += ['id', 'source', 'type', 'edge', 'level']


class StartTrigger(Prop):
    waitForStartTrigger = Typed(BoolProp)
    source = Typed(StrProp)
    edge = Typed(StrProp)

    def __init__(self, experiment):
        super(StartTrigger, self).__init__('startTrigger', experiment)
        self.waitForStartTrigger = BoolProp(
            'waitForStartTrigger',
            experiment,
            'HSDIO wait for start trigger',
            'False'
        )
        self.source = StrProp('source', experiment, 'start trigger source', '"PFI0"')
        self.edge = StrProp('edge', experiment, 'start trigger edge', '"rising"')
        self.properties += ['waitForStartTrigger', 'source', 'edge']


class HSDIO(Instrument):
    """A version of the HSDIO instrument that uses functionally defined waveforms."""

    version = '2015.05.24'

    numChannels = Int(32)
    resourceName = Member()
    clockRate = Member()
    units = Member()
    hardwareAlignmentQuantum = Member()
    waveforms = Member()
    channels = Member()
    triggers = Member()
    startTrigger = Member()

    # properties for functional waveforms
    transition_list = Member()  # list that will store the transitions as they are added
    states = Member()  # an array of the compiled transition states
    indices = Member()  # an array of the compiled transition indices
    times = Member()  # an array of the compiled transition times
    index_durations = Member()  # an array of the compiled transition durations (in terms of indexes)
    time_durations = Member()  # an array of compiled transition durations (in terms of time)
    # This will store HSDIO repeat [t_start,dt,t_finish, repeats] times so that we can edit transitions before
    # they go to LabVIEW
    repeat_list = Member()
    complex_waveform_counter = Int(0)

    def __init__(self, name, experiment):
        super(HSDIO, self).__init__(name, experiment)
        self.resourceName = StrProp(
            'resourceName',
            experiment,
            'the hardware location of the HSDIO card',
            "'Dev1'"
        )
        self.clockRate = FloatProp('clockRate', experiment, 'samples/channel/sec', '1000')
        self.units = FloatProp('units', experiment, 'multiplier for HSDIO timing values (milli=.001)', '1')
        self.hardwareAlignmentQuantum = IntProp(
            'hardwareAlignmentQuantum',
            experiment,
            '(PXI=1,SquareCell=2)',
            '1'
        )
        self.channels = NumpyChannels(experiment, self)
        self.triggers = ListProp(
            'triggers',
            self.experiment,
            listElementType=ScriptTrigger,
            listElementName='trigger'
        )
        self.startTrigger = StartTrigger(experiment)
        self.properties += [
            'version', 'resourceName', 'clockRate', 'units', 'hardwareAlignmentQuantum', 'triggers',
            'channels', 'startTrigger', 'numChannels'
        ]
        # script and waveforms are handled specially in HSDIO.toHardware()
        self.doNotSendToHardware += ['units', 'numChannels']
        self.transition_list = []  # an empty list to store state transitions
        self.repeat_list = []  # list to store repeat times

    def evaluate(self):
        """Prepare the instrument."""
        if self.enable and self.experiment.allow_evaluation:
            logger.debug('HSDIO.evaluate()')
            super(HSDIO, self).evaluate()
            self.parse_transition_list()
            # reset the transition list so it starts empty for the next usage
            self.transition_list = []

    def add_transition(self, time, channel, state):
        """Append a transition to the list of transitions.

        The values are not processed until evaluate is called.
        Generally the master functional waveform instrument should evaluate before HSDIO evaluates.
        :param time: float.  Absolute time since the HSDIO was triggered, in the units specified by self.units
        :param channel: int.  The channel number to change.
        :param state: bool.  Should the channel go high  (True) or low (False) at this time?
        :return: Nothing.
        """
        self.transition_list.append((time, channel, state))

    def add_repeat(self, time, function, repeats):
        """Add a repeat loop to the script to take advantage of the HSDIO's builtin "Repeat" functionality.

        MUST USE CAREFULLY SO THAT NO CONFLICTS ARISE WITH NORMAL HSDIO USAGE!!!

        2015/09/07 Joshua Isaacs

        :param time: The start time of the repeat
        :param function: Some function that takes in a time t and returns t+dt
        :param repeats: Number of times func should be repeated
        :return elapsed time for all repetitions:
        """
        logger.debug('add_repeat called')
        # mark the transition_list position where the repeat starts
        start_index = len(self.transition_list)
        t0 = time
        dt = function(time) - t0
        stop_index = len(self.transition_list) - 1

        # check that dt is an integer multiple of cycles
        req_cycles_per_repeat = dt*self.clockRate.value*self.units.value
        cycles_per_repeat = int(req_cycles_per_repeat)
        # warn if cycle error is too large (remember finite precision for FPs)
        if abs(req_cycles_per_repeat - cycles_per_repeat) < 0.001:
            msg = (
                "Requested repeat cycle time is not an integer number of cycles.  Requested cycles: `{}`,"
                " actual: `{}`"
            )
            logger.warning(msg.format(req_cycles_per_repeat, cycles_per_repeat))

        # warn if the repeat cycle time is possibly unstable
        if cycles_per_repeat < self.experiment.Config.config.getint('HSDIO', 'MinStableWaitCycles'):
            logger.warning((
                "Repeat cycle time is possibly unstable."
                " Consider doubling the repeat function length."
            ))

        # Check t0 times to make sure each repeat in repeat_list is unique
        if len(self.repeat_list) == 0 or sum([r['t0'] == t0 for r in self.repeat_list]) == 0:
            self.repeat_list.append({
                't0': t0,
                'dt': dt,
                'tf': t0 + dt*repeats,
                'repeats': repeats,
                'cycles_per_repeat': cycles_per_repeat,
                'start_index': start_index,
                'stop_index': stop_index
            })
        return time

    def parse_transition_list(self):
        """Turn requested transitions into a list of states and delays."""
        if self.transition_list:
            # put all the transitions that have been stored together into one big list
            # convert the float time to an integer number of samples
            indices = np.rint(
                np.array(
                    [i[0] for i in self.transition_list],
                    dtype=np.float64
                )*self.clockRate.value*self.units.value
            ).astype(np.uint64)
            # compile the channels
            channels = np.array([i[1] for i in self.transition_list], dtype=np.uint8)
            # compile the states
            states = np.array([i[2] for i in self.transition_list], dtype=np.bool)

            # Create two arrays to store the compiled times and states.
            # These arrays will be appended to to increase their size as we go along.
            # MFE2017: Appending can get computationally expensive with numpy for large arrays since it makes
            # a new array each call. If this is causing a delay consider doing block appends or precalculating
            # the array length.
            index_list = np.zeros(1, dtype=np.uint64)
            state_list = np.zeros((1, self.numChannels), dtype=np.bool)

            # sort the transitions time.  If there is a tie, preserve the order.
            # mergesort is slower than the default quicksort, but it is 'stable'
            # which means items of the same value are kept in their relative order, which is desired here
            order = np.argsort(indices, kind='mergesort')

            # make a list of repeat start indicies so we can easily check if the repeat is being called
            repeat_start_indices = [r['start_index'] for r in self.repeat_list]
            # go through all the transitions, updating the compiled sequence as we go
            for (idx, i) in enumerate(order):
                if i in repeat_start_indices:
                    # if this is a repeat call make sure there are no transitions that are accidentally being
                    # inserted into the repeat

                # check to see if the next time is the same as the last one in the time list
                if indices[i] == index_list[-1]:
                    # if this is a duplicate time, the latter entry overrides
                    state_list[-1][channels[i]] = states[i]
                else:
                    # If this is a new time, increase the length of time_list and state_list.
                    # Create the new state_list entry by copying the last entry.
                    index_list = np.append(index_list, indices[i])
                    state_list = np.append(state_list, state_list[-1, np.newaxis], axis=0)
                    # then update the last entry
                    state_list[-1, channels[i]] = states[i]

            # find the duration of each segment
            durations = np.empty_like(index_list)
            durations[:-1] = index_list[1:]-index_list[:-1]
            durations[-1] = 1  # add in a 1 sample duration at end for last transition

            # find the real time at each index (used for plotting)
            # send values in seconds, do not use units, so that the plot can apply its own units
            self.times = 1.0*index_list/self.clockRate.value
            self.time_durations = 1.0*durations/self.clockRate.value

            # update the exposed variables
            self.indices = index_list
            self.states = state_list
            self.index_durations = durations

        else:
            self.times = np.zeros(0, dtype=np.float64)
            self.time_durations = np.zeros(0, dtype=np.float64)
            self.indices = np.zeros(0, dtype=np.uint64)
            self.states = np.zeros((0, self.numChannels), dtype=np.bool)
            self.index_durations = np.zeros_like(self.indices)
        try:
            # print self.times[1],self.times[2]-self.times[1]
            # MFE2017: I dont know why the above line is here, but I killed the print statement, but
            # kept the line that might throw an exception
            delta = self.times[2]-self.times[1]
        except Exception as e:
            print "Exception in HSDIO: {}".format(e)

    def getNormalizedWaitTime(self, index):
        """Get the waitTime in cycles normalized by the hardware quanta.

        Returns a time to wait between index and index+1 waveforms in units of cycles*quanta.
        """
        waitTime = self.index_durations[index]
        # if the wait time is not a multiple of the hardwareAlignmentQuantum, round up to the next
        # valid sample quanta
        roundUp = (waitTime % self.hardwareAlignmentQuantum.value) != 0
        waitTime = int(waitTime/self.hardwareAlignmentQuantum.value)
        if (roundUp):
            waitTime += 1
        waitTime *= self.hardwareAlignmentQuantum.value
        return waitTime

    def waveform_name_generator(self, transition_list):
        """Make up a name for the waveform."""
        # complex waveforms cannot be easily reused
        if len(transition_list) > 1:
            self.complex_waveform_counter += 1
            return 'c{}'.format(self.complex_waveform_counter)
        # simple waveforms can be reused to save memory
        else:
            # the name is w followed by the hexadecimal expression of the state
            i = transition_list[0]['index']
            hex_state = hex(int(''.join([str(int(j)) for j in self.states[i]]), 2))
            return 'w' + hex_state

    def generate_waveform(self, wname, transition_list):
        """Build a waveform from a transition list.

        Returns an XML waveform string.
        """
        transitions = []
        states = []
        hardware_quanta = self.hardwareAlignmentQuantum.value
        # first transition starts at time 0
        time = 0
        for tnum, t in enumerate(transition_list):
            i = t['index']
            for k in range(t['waitTime']):
                for q in range(hardware_quanta):
                    # add in the transition
                    transitions.append(str(time))
                    # move time coutner up one cycle
                    time += 1
                    # and the state
                    states.append(' '.join([str(int(state)) for state in self.states[i]]))
                # the last transition in the list does not need to be unrolled
                if tnum + 1 == len(transition_list):
                    break
                # otherwise unroll the waittime for short waits, i.e. continue with the loop
        waveform = {'waveform': {
            'name': wname,
            'transitions': ' '.join(transitions),
            'states': '\n'.join(states)
        }}
        return dicttoxml.dicttoxml(waveform, root=False, attr_type=False)

    def add_waveform(self, transition_list, waveformsInUse):
        """Generate a new waveform if necessary from a transition_list."""
        wname = self.waveform_name_generator(transition_list)
        waveform = ''  # a repeated waveform does not need to be readded
        if wname not in waveformsInUse:
            # add waveform to those to be transferred to LabView
            waveformsInUse.append(wname)
            # don't create a real waveform object, just its toHardware signature
            waveform = self.generate_waveform(wname, transition_list)
            print wname
        return {
            'name': wname,
            'xml': waveform
        }

    def do_repeats_overlap(self):
        """Check to see if any of the Repeat regions overlap."""
        sorted_rpt = np.sort(self.repeat_list, axis=0)
        overlap = []
        for i in xrange(len(self.repeat_list)-1):
            # if tf current repeat > t0 next repeat
            if sorted_rpt[i][2] > sorted_rpt[i+1][0]:
                overlap.append(i)
                logger.warning('HSDIO Repeat Overlap at ts={}'.format(sorted_rpt[i+1][0]))
        return len(overlap) > 0

    def toHardware(self):
        """Generate the XML string necessary to program the HSDIO card.

        This overrides Instrument.toHardware() in order to accommodate the compiled way that scripts are
        specified (a la the former 'compressedGenerate').  The script is created based on self.times and
        self.states. A waveform is created for every transition.  These waveforms are only 1 sample long (or
        as long as necessary to satisfy hardwareAlignmentQuantum).  The timing is specified by placing 'wait'
        commands between these 1 sample waveforms.
        Only the necessary waveforms are created and passed to the HSDIO hardware.
        ______________________________________________________________________________________________________________

        2015/09/07 Joshua Isaacs

        Now checks for HSDIO.add_repeat and modifies script to remove explicit repetitions and replaces them
        with memory friendly HSDIO "Repeat"s
        ______________________________________________________________________________________________________________

        2017/10/23 Matt Ebert

        Transitions within some minimum time ~200 cycles (defined in the config file) are now combined into a
        single waveform that is explicitly defined.
        This removes the need for Josh's 2015 modification that involves repeating waveforms, unless you are
        running out of memory on your HSDIO card.
        Because it is no longer necessary I doubt that it will work with the new waveform stuff.
        I am putting in a console warning in case you try to use the repeat function.
        If you want to add it back in you should do the explicit roll out of the cycle for short times.
        """
        if self.enable:
            # build dictionary of waveforms keyed on waveform name
            waveformsInUse = []
            # keep a counter of comlex waveforms so they can each have a unique name
            self.complex_waveform_counter = 0
            script = ['script script1']
            master_waveform_list = []
            # list of indicies and waitTimes to be added to a single waveform
            transition_list = []

            # make sure that there are no overlapping repeat calls
            if self.do_repeats_overlap():
                logger.error('HSDIO Repeat Overlap Error: make sure HSDIO Repeat calls do not overlap')
                self.repeat_list = []
                raise PauseError

            for i in xrange(len(self.indices)):
                waitTime = self.getNormalizedWaitTime(i)
                # append index and waittime to list of transitions to add as a single waveform
                transition_list.append({
                    'index': i,
                    'waitTime': waitTime,
                })
                # if the waitTime is less than the stable time add another state to the transition list
                if waitTime >= self.experiment.Config.config.getint('HSDIO', 'MinStableWaitCycles'):
                    waveform = self.add_waveform(transition_list, waveformsInUse)
                    # reset transition list
                    transition_list = []
                    # generate waveform
                    script.append('generate {}'.format(waveform['name']))
                    # add waveform to list if it is new
                    if waveform['xml']:
                        master_waveform_list.append(waveform['xml'])
                    # the HSDIO card cannot handle a wait value longer than this, so we repeat it as many
                    # times as necessary
                    max_wait_cycles = 536870912
                    wait_phrase = 'wait {}'
                    for m in range(int(waitTime/max_wait_cycles)):
                        script.append(wait_phrase.format(max_wait_cycles))
                    # add the remaining wait
                    script.append(wait_phrase.format(int(waitTime % max_wait_cycles)))
            #
            # if len(self.repeat_list) > 0:
            #     ctr = 0
            #     for i in xrange(len(self.repeat_list)):
            #         if self.repeat_list[i][-1] > 2:
            #             tunits = self.clockRate.value*self.units.value
            #             t0, dt, tf = [
            #                 np.uint64(np.ceil(j*self.clockRate.value)*tunits/self.clockRate.value)
            #                 for j in self.repeat_list[i][:-1]
            #             ]
            #             repeats = self.repeat_list[i][-1]
            #             if ctr == 0:
            #                 script_list = script.split('\n')
            #
            #             # Ignore first line of script_list. For each single sample waveform there
            #             # is a waveform and a wait line so double the # of indices. Preserve indices
            #             # correlation with script so that iterating over repeats doesn't break. np.NaN out any
            #             # lines that aren't used so we can dump them at the end!
            #             idx_start = 2*np.where(self.indices == t0)[0][0] + 1 + 2*ctr
            #             idx_func = 2*np.where(self.indices == dt+t0)[0][0] + 1 + 2*ctr
            #             idx_end = 2*np.where(self.indices == tf)[0][0] + 1 + 2*ctr
            #
            #             # start by np.NaNing out repititions
            #             for idx in range(idx_func, idx_end):
            #                 script_list[idx] = np.NaN
            #
            #             script_list.insert(idx_start, 'Repeat {}'.format(int(repeats)))
            #             script_list.insert(idx_func+1, 'end Repeat')
            #             ctr += 1
            #
            #     cleaned_list = [j for j in script_list if str(j) != 'nan']
            #     # np.savetxt('script_clean.txt',cleaned_list)
            #     script = '\n'.join(cleaned_list)
            # ################################################################################################
            script.append('end script')
            print script
            self.repeat_list = []
            xml_str = '<HSDIO><script>{}</script>\n<waveforms>{}</waveforms>\n'.format(
                '\n'.join(script),
                '\n'.join(master_waveform_list)
            )
            # [7:] removes the <HSDIO> on what is returned from super.toHardware
            return xml_str + super(HSDIO, self).toHardware()[7:]
        else:
            # let Instrument.toHardware send <name><enable>False</enable><name>
            return super(HSDIO, self).toHardware()
=======
"""HSDIO.py
Part of the AQuA Cesium Controller software package

author=Martin Lichtman
created=2013-10-08
modified>=2015-05-24
modified>=2017-10-23

This file holds everything needed to model the high speed digital output from
the National Instruments HSDIO card.  It communicates to LabView via the higher
up LabView(Instrument) class.
"""
from __future__ import division
import logging
import numpy as np
import dicttoxml

from cs_errors import PauseError

from atom.api import Typed, Member, Int

from instrument_property import Prop, BoolProp, IntProp, FloatProp, StrProp, ListProp
from cs_instruments import Instrument
from digital_waveform import NumpyChannels


__author__ = 'Martin Lichtman'
logger = logging.getLogger(__name__)


class ScriptTrigger(Prop):
    id = Typed(StrProp)
    source = Typed(StrProp)
    type = Typed(StrProp)
    edge = Typed(StrProp)
    level = Typed(StrProp)

    def __init__(self, name, experiment, description=''):
        super(ScriptTrigger, self).__init__('trigger', experiment, description)
        self.id = StrProp('id', experiment, '', '"ScriptTrigger0"')
        self.source = StrProp('source', experiment, '', '"PFI0"')
        self.type = StrProp('type', experiment, '', '"edge"')
        self.edge = StrProp('edge', experiment, '', '"rising"')
        self.level = StrProp('level', experiment, '', '"high"')
        self.properties += ['id', 'source', 'type', 'edge', 'level']


class StartTrigger(Prop):
    waitForStartTrigger = Typed(BoolProp)
    source = Typed(StrProp)
    edge = Typed(StrProp)

    def __init__(self, experiment):
        super(StartTrigger, self).__init__('startTrigger', experiment)
        self.waitForStartTrigger = BoolProp(
            'waitForStartTrigger',
            experiment,
            'HSDIO wait for start trigger',
            'False'
        )
        self.source = StrProp('source', experiment, 'start trigger source', '"PFI0"')
        self.edge = StrProp('edge', experiment, 'start trigger edge', '"rising"')
        self.properties += ['waitForStartTrigger', 'source', 'edge']


class HSDIO(Instrument):
    """A version of the HSDIO instrument that uses functionally defined waveforms."""

    version = '2015.05.24'

    numChannels = Int(32)
    resourceName = Member()
    clockRate = Member()
    units = Member()
    hardwareAlignmentQuantum = Member()
    waveforms = Member()
    channels = Member()
    triggers = Member()
    startTrigger = Member()

    # properties for functional waveforms
    transition_list = Member()  # list that will store the transitions as they are added
    states = Member()  # an array of the compiled transition states
    indices = Member()  # an array of the compiled transition indices
    times = Member()  # an array of the compiled transition times
    index_durations = Member()  # an array of the compiled transition durations (in terms of indexes)
    time_durations = Member()  # an array of compiled transition durations (in terms of time)
    # This will store HSDIO repeat [t_start,dt,t_finish, repeats] times so that we can edit transitions before
    # they go to LabVIEW
    repeat_list = Member()
    complex_waveform_counter = Int(0)

    def __init__(self, name, experiment):
        super(HSDIO, self).__init__(name, experiment)
        self.resourceName = StrProp(
            'resourceName',
            experiment,
            'the hardware location of the HSDIO card',
            "'Dev1'"
        )
        self.clockRate = FloatProp('clockRate', experiment, 'samples/channel/sec', '1000')
        self.units = FloatProp('units', experiment, 'multiplier for HSDIO timing values (milli=.001)', '1')
        self.hardwareAlignmentQuantum = IntProp(
            'hardwareAlignmentQuantum',
            experiment,
            '(PXI=1,SquareCell=2)',
            '1'
        )
        self.channels = NumpyChannels(experiment, self)
        self.triggers = ListProp(
            'triggers',
            self.experiment,
            listElementType=ScriptTrigger,
            listElementName='trigger'
        )
        self.startTrigger = StartTrigger(experiment)
        self.properties += [
            'version', 'resourceName', 'clockRate', 'units', 'hardwareAlignmentQuantum', 'triggers',
            'channels', 'startTrigger', 'numChannels'
        ]
        # script and waveforms are handled specially in HSDIO.toHardware()
        self.doNotSendToHardware += ['units', 'numChannels']
        self.transition_list = []  # an empty list to store
        self.repeat_list = []

    def evaluate(self):
        """Prepare the instrument."""
        if self.enable and self.experiment.allow_evaluation:
            logger.debug('HSDIO.evaluate()')
            super(HSDIO, self).evaluate()
            self.parse_transition_list()
            # reset the transition list so it starts empty for the next usage
            self.transition_list = []

    def add_transition(self, time, channel, state):
        """Append a transition to the list of transitions.

        The values are not processed until evaluate is called.
        Generally the master functional waveform instrument should evaluate before HSDIO evaluates.
        :param time: float.  Absolute time since the HSDIO was triggered, in the units specified by self.units
        :param channel: int.  The channel number to change.
        :param state: bool.  Should the channel go high  (True) or low (False) at this time?
        :return: Nothing.
        """
        self.transition_list.append((time, channel, state))

    def add_repeat(self, time, function, repeats):
        """Add a repeat loop to the script to take advantage of the HSDIO's builtin "Repeat" functionality.

        MUST USE CAREFULLY SO THAT NO CONFLICTS ARISE WITH NORMAL HSDIO USAGE!!!

        2015/09/07 Joshua Isaacs

        :param time: The start time of the repeat
        :param function: Some function that takes in a time t and returns t+dt
        :param repeats: Number of times func should be repeated
        :return elapsed time for all repetitions:
        """
        logger.debug('add_repeat Called')
        # print '*************DEBUG func={}*************'.format(function)
        time = function(time)
        t0 = time
        # print repeats
        for i in xrange(repeats-2):
            time = function(time)
            if i == 0:
                dt = time-t0
        tf = time
        time = function(time)
        # Check t0 times to make sure each repeat in repeat_list is unique
        if len(self.repeat_list) == 0 or sum([self.repeat_list[i][0] == t0 for i in range(len(self.repeat_list))]) == 0:
            self.repeat_list.append([t0, dt, tf, repeats - 2])
        return time

    def parse_transition_list(self):
        """Turn requested transitions into a list of states and delays."""
        if self.transition_list:
            # put all the transitions that have been stored together into one big list
            # convert the float time to an integer number of samples
            indices = np.rint(
                np.array(
                    [i[0] for i in self.transition_list],
                    dtype=np.float64)*self.clockRate.value*self.units.value
            ).astype(np.uint64)
            # compile the channels
            channels = np.array([i[1] for i in self.transition_list], dtype=np.uint8)
            # compile the states
            states = np.array([i[2] for i in self.transition_list], dtype=np.bool)

            # Create two arrays to store the compiled times and states.
            # These arrays will be appended to to increase their size as we go along.
            index_list = np.zeros(1, dtype=np.uint64)
            state_list = np.zeros((1, self.numChannels), dtype=np.bool)

            # sort the transitions time.  If there is a tie, preserve the order.
            # mergesort is slower than the default quicksort, but it is 'stable'
            # which means items of the same value are kept in their relative order, which is desired here
            order = np.argsort(indices, kind='mergesort')

            # go through all the transitions, updating the compiled sequence as we go
            for i in order:
                # check to see if the next time is the same as the last one in the time list
                if indices[i] == index_list[-1]:
                    # if this is a duplicate time, the latter entry overrides
                    state_list[-1][channels[i]] = states[i]
                else:
                    # If this is a new time, increase the length of time_list and state_list.
                    # Create the new state_list entry by copying the last entry.
                    index_list = np.append(index_list, indices[i])
                    state_list = np.append(state_list, state_list[-1, np.newaxis], axis=0)
                    # then update the last entry
                    state_list[-1, channels[i]] = states[i]

            # find the duration of each segment
            durations = np.empty_like(index_list)
            durations[:-1] = index_list[1:]-index_list[:-1]
            durations[-1] = 1  # add in a 1 sample duration at end for last transition

            # find the real time at each index (used for plotting)
            # send values in seconds, do not use units, so that the plot can apply its own units
            self.times = 1.0*index_list/self.clockRate.value
            self.time_durations = 1.0*durations/self.clockRate.value

            # update the exposed variables
            self.indices = index_list
            self.states = state_list
            self.index_durations = durations

        else:
            self.times = np.zeros(0, dtype=np.float64)
            self.time_durations = np.zeros(0, dtype=np.float64)
            self.indices = np.zeros(0, dtype=np.uint64)
            self.states = np.zeros((0, self.numChannels), dtype=np.bool)
            self.index_durations = np.zeros_like(self.indices)
        try:
            # print self.times[1],self.times[2]-self.times[1]
            # MFE2017: I dont know why the above line is here, but I killed the print statement, but
            # kept the line that might throw an exception
            delta = self.times[2]-self.times[1]
        except Exception as e:
            print "Exception in HSDIO: {}".format(e)

    def getNormalizedWaitTime(self, index):
        """Get the waitTime in cycles normalized by the hardware quanta.

        Returns a time to wait between index and index+1 waveforms in units of cycles*quanta.
        """
        waitTime = self.index_durations[index]
        # if the wait time is not a multiple of the hardwareAlignmentQuantum, round up to the next
        # valid sample quanta
        roundUp = (waitTime % self.hardwareAlignmentQuantum.value) != 0
        waitTime = int(waitTime/self.hardwareAlignmentQuantum.value)
        if (roundUp):
            waitTime += 1
        waitTime *= self.hardwareAlignmentQuantum.value
        return waitTime

    def waveform_name_generator(self, transition_list):
        """Make up a name for the waveform."""
        # complex waveforms cannot be easily reused
        if len(transition_list) > 1:
            self.complex_waveform_counter += 1
            return 'c{}'.format(self.complex_waveform_counter)
        # simple waveforms can be reused to save memory
        else:
            # the name is w followed by the hexadecimal expression of the state
            i = transition_list[0]['index']
            hex_state = hex(int(''.join([str(int(j)) for j in self.states[i]]), 2))
            return 'w' + hex_state

    def generate_waveform(self, wname, transition_list):
        """Build a waveform from a transition list.

        Returns an XML waveform string.
        """
        transitions = []
        states = []
        hardware_quanta = self.hardwareAlignmentQuantum.value
        # first transition starts at time 0
        time = 0
        for tnum, t in enumerate(transition_list):
            i = t['index']
            state = ' '.join([str(int(state)) for state in self.states[i]])
            for q in range(hardware_quanta):
                # add in the transition
                transitions.append(str(time))
                # move time counter up one cycle
                time += 1
                # and the state
                states.append(state)
            time += t['waitTime'] - 1*hardware_quanta
            # the last transition in the list does not need to be unrolled
            if tnum + 1 == len(transition_list):
                break
            # otherwise unroll the waittime for short waits, i.e. continue with the loop
        waveform = {'waveform': {
            'name': wname,
            'transitions': ' '.join(transitions),
            'states': '\n'.join(states)
        }}
        return dicttoxml.dicttoxml(waveform, root=False, attr_type=False)

    def add_waveform(self, transition_list, waveformsInUse):
        """Generate a new waveform if necessary from a transition_list."""
        wname = self.waveform_name_generator(transition_list)
        waveform = ''  # a repeated waveform does not need to be readded
        if wname not in waveformsInUse:
            # add waveform to those to be transferred to LabView
            waveformsInUse.append(wname)
            # don't create a real waveform object, just its toHardware signature
            waveform = self.generate_waveform(wname, transition_list)
        return {
            'name': wname,
            'xml': waveform
        }

    def toHardware(self):
        """Generate the XML string necessary to program the HSDIO card.

        This overrides Instrument.toHardware() in order to accommodate the compiled way that scripts are
        specified (a la the former 'compressedGenerate').  The script is created based on self.times and
        self.states. A waveform is created for every transition.  These waveforms are only 1 sample long (or
        as long as necessary to satisfy hardwareAlignmentQuantum).  The timing is specified by placing 'wait'
        commands between these 1 sample waveforms.
        Only the necessary waveforms are created and passed to the HSDIO hardware.
        ______________________________________________________________________________________________________________

        2015/09/07 Joshua Isaacs

        Now checks for HSDIO.add_repeat and modifies script to remove explicit repetitions and replaces them
        with memory friendly HSDIO "Repeat"s
        ______________________________________________________________________________________________________________

        2017/10/23 Matt Ebert

        Transitions within some minimum time ~200 cycles (defined in the config file) are now combined into a
        single waveform that is explicitly defined.
        This removes the need for Josh's 2015 modification that involves repeating waveforms, unless you are
        running out of memory on your HSDIO card.
        Because it is no longer necessary I doubt that it will work with the new waveform stuff.
        I am putting in a console warning in case you try to use the repeat function.
        If you want to add it back in you should do the explicit roll out of the cycle for short times.
        """
        if self.enable:
            # build dictionary of waveforms keyed on waveform name
            waveformsInUse = []
            self.complex_waveform_counter = 0

            script = ['script script1']
            master_waveform_list = []

            # list of indicies and waitTimes to be added to a single waveform
            transition_list = []
            # go through each transition
            for i in xrange(len(self.indices)):
                waitTime = self.getNormalizedWaitTime(i)
                # append index and waittime to list of transitions to add as a single waveform
                transition_list.append({
                    'index': i,
                    'waitTime': waitTime,
                })
                # if the waitTime is less than the stable time add another state to the transition list
                if waitTime >= self.experiment.Config.config.getint('HSDIO', 'MinStableWaitCycles'):
                    waveform = self.add_waveform(transition_list, waveformsInUse)
                    # reset transition list
                    transition_list = []
                    # generate waveform
                    script.append('generate {}'.format(waveform['name']))
                    # add waveform to list if it is new
                    if waveform['xml']:
                        master_waveform_list.append(waveform['xml'])
                    # the HSDIO card cannot handle a wait value longer than this, so we repeat it as many
                    # times as necessary
                    max_wait_cycles = 536870912
                    wait_phrase = 'wait {}'
                    for m in range(int(waitTime/max_wait_cycles)):
                        script.append(wait_phrase.format(max_wait_cycles))
                    # add the remaining wait
                    script.append(wait_phrase.format(int(waitTime % max_wait_cycles)))

            # Check to see if any of the Repeat regions overlap
            sorted_rpt = np.sort(self.repeat_list, axis=0)

            # ########### PROBABLY BROKEN - MFE2017 ##########################################################
            if len(self.repeat_list) > 0:
                logger.warning('The repeat functionality is probably broken. - MFE2017')
            overlap = []
            for i in xrange(len(self.repeat_list)-1):
                if sorted_rpt[i][2] > sorted_rpt[i+1][0]:
                    overlap.append(i)
                    logger.warning('HSDIO Repeat Overlap at ts={}'.format(sorted_rpt[i+1][0]))
            if len(overlap) > 0:
                try:
                    self.repeat_list = []
                    raise Exception
                except:
                    logger.error('HSDIO Repeat Overlap Error: make sure HSDIO Repeat calls do not overlap')
                    raise PauseError
            if len(self.repeat_list) > 0:
                ctr = 0
                for i in xrange(len(self.repeat_list)):
                    if self.repeat_list[i][-1] > 2:
                        tunits = self.clockRate.value*self.units.value
                        t0, dt, tf = [
                            np.uint64(np.ceil(j*self.clockRate.value)*tunits/self.clockRate.value)
                            for j in self.repeat_list[i][:-1]
                        ]
                        repeats = self.repeat_list[i][-1]
                        if ctr == 0:
                            script_list = script.split('\n')

                        # Ignore first line of script_list. For each single sample waveform there
                        # is a waveform and a wait line so double the # of indices. Preserve indices
                        # correlation with script so that iterating over repeats doesn't break. np.NaN out any
                        # lines that aren't used so we can dump them at the end!
                        idx_start = 2*np.where(self.indices == t0)[0][0] + 1 + 2*ctr
                        idx_func = 2*np.where(self.indices == dt+t0)[0][0] + 1 + 2*ctr
                        idx_end = 2*np.where(self.indices == tf)[0][0] + 1 + 2*ctr

                        # start by np.NaNing out repititions
                        for idx in range(idx_func, idx_end):
                            script_list[idx] = np.NaN

                        script_list.insert(idx_start, 'Repeat {}'.format(int(repeats)))
                        script_list.insert(idx_func+1, 'end Repeat')
                        ctr += 1

                cleaned_list = [j for j in script_list if str(j) != 'nan']
                # np.savetxt('script_clean.txt',cleaned_list)
                script = '\n'.join(cleaned_list)
            # ################################################################################################
            script.append('end script')
            # print script
            self.repeat_list = []
            xml_str = '<HSDIO><script>{}</script>\n<waveforms>{}</waveforms>\n'.format(
                '\n'.join(script),
                '\n'.join(master_waveform_list)
            )
            # [7:] removes the <HSDIO> on what is returned from super.toHardware
            return xml_str + super(HSDIO, self).toHardware()[7:]
        else:
            # let Instrument.toHardware send <name><enable>False</enable><name>
            return super(HSDIO, self).toHardware()
>>>>>>> master
