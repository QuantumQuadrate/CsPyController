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
import pprint

from cs_errors import PauseError

from atom.api import Typed, Member, Int

from instrument_property import Prop, BoolProp, IntProp, FloatProp, StrProp, ListProp
from cs_instruments import Instrument
from digital_waveform import NumpyChannels


__author__ = 'Martin Lichtman'
logger = logging.getLogger(__name__)


def shallow_copy(d):
    new_d = {}
    for k in d:
        new_d[k] = d[k]
    return new_d


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
    repeats = Member()
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

        Function must create a new transition at t0 even if it doesnt do anything

        2015/09/07 Joshua Isaacs

        :param time: The start time of the repeat
        :param function: Some function that takes in a time t and returns t+dt
        :param repeats: Number of times func should be repeated
        :return elapsed time for all repetitions:
        """
        logger.debug('add_repeat called')
        # mark the transition_list position where the repeat starts
        start_index = len(self.transition_list)  # transition_list[start_index] points to next entry
        t0 = time
        dt = function(time) - t0
        stop_index = len(self.transition_list)  # transition_list[stop_index] points to last repeat entry

        # check that dt is an integer multiple of cycles
        req_cycles_per_repeat = dt*self.clockRate.value*self.units.value
        cycles_per_repeat = int(round(req_cycles_per_repeat))
        # warn if cycle error is too large (remember finite precision for FPs)
        if abs(req_cycles_per_repeat - cycles_per_repeat) < 0.1:
            msg = (
                "Requested repeat cycle time is not an integer number of cycles.  Requested cycles: `{}`,"
                " actual: `{}`"
            )
            logger.warning(msg.format(req_cycles_per_repeat, cycles_per_repeat))
        # recalculate dt to remove FP errors
        if self.units.value > 0:
            dt = cycles_per_repeat/(self.clockRate.value*self.units.value)
            # there is some initialization order issue where these are 0 at start up

        # warn if the repeat cycle time is possibly unstable
        if cycles_per_repeat < self.experiment.Config.config.getint('HSDIO', 'MinStableWaitCycles'):
            logger.warning((
                "Repeat cycle time is possibly unstable."
                " Consider doubling the repeat function length."
            ))

        # Check t0 times to make sure each repeat in repeat_list is unique
        if len(self.repeat_list) == 0 or sum([r['t0'] == t0 for r in self.repeat_list]) == 0:
            cycle_dict = {
                't0': t0,
                'dt': dt,
                'tf': t0 + dt*repeats,
                'repeats': repeats,
                'cycles_per_repeat': cycles_per_repeat,
                'start_index': start_index,
                'stop_index': stop_index
            }
            self.repeat_list.append(cycle_dict)
        else:
            # shouldn't be here
            logger.error("Possible duplicate repeat")
            raise PauseError

        # tag the repeated transitions in the transition_list
        for idx in xrange(start_index, stop_index):
            # add entries to the tuple with the cycle dict
            self.transition_list[idx] += (cycle_dict,)
        return time + dt*repeats

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
            # keep track of repeats, [ -1 -1 -1 (cycle_dict, 0) (cycle_dict, 1) ... -1 -1]
            # -1 is non-repeat, a tuple with cycle info dict and the cycle index is inserted for each
            # cycle transition
            repeats = [-1 if len(i) < 4 else i[3] for i in self.transition_list]

            # Create two arrays to store the compiled times and states.
            # These arrays will be appended to to increase their size as we go along.
            index_list = np.zeros(1, dtype=np.uint64)
            state_list = np.zeros((1, self.numChannels), dtype=np.bool)
            repeat_list = [-1]

            # sort the transitions time.  If there is a tie, preserve the order.
            # mergesort is slower than the default quicksort, but it is 'stable'
            # which means items of the same value are kept in their relative order, which is desired here
            order = np.argsort(indices, kind='mergesort')

            # go through all the transitions, updating the compiled sequence as we go
            cycle_idx = 0
            for i in order:
                if len(self.transition_list[i]) > 3:
                    logger.info("repeat cycle: {} detected at index: {}".format(self.transition_list[i], i))
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
                    # compress the repeats list along with the others
                    repeat_list.append(-1)
                    if repeats[i] != -1:
                        # need a compressed cycle index
                        repeat_list[-1] = repeats[i]
                        cycle_idx += 1
                    else:
                        # reset the cycle index if not in a repeat cycle
                        cycle_idx = 0

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
            self.repeats = repeat_list

        else:
            self.times = np.zeros(0, dtype=np.float64)
            self.time_durations = np.zeros(0, dtype=np.float64)
            self.indices = np.zeros(0, dtype=np.uint64)
            self.states = np.zeros((0, self.numChannels), dtype=np.bool)
            self.repeats = []
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
            s = transition_list[0]['state'].replace(' ', '')
            hex_state = hex(int(s, 2))
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
            for q in range(hardware_quanta):
                # add in the transition
                if q == 0 and time % hardware_quanta:
                    # if not synchronous with the hardware quanta move transition forward
                    logger.warning('Detected a hardware quanta roudin event. Auto fixing by one cycle')
                    transitions.append(str(time-(time % hardware_quanta)))
                    # dont move time counter up to account for shift
                else:
                    transitions.append(str(time))
                    # move time counter up one cycle
                    time += 1
                # and the state
                states.append(t['state'])
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

    def add_repeat_waveform(self, transition_list, waveformsInUse):
        """Generate a list of waveform dicts with 'name', 'xml', and 'cycles' keys."""
        repeat_only_list = []  # the core repeat transitions
        other_transitions = [0]  # the other transitions that break up the repeat cycles
        repeats_done = False
        repeat_sample_clock_cycles = 0
        sample_clock_cycles_to_next_ot = -1
        # keeps track of wait time when there are state changes during the repeat from other channels
        sample_clock_cycles_to_next_ot_option = -1
        cycles_per_repeat = transition_list[0]['cycles_per_repeat']

        first_cycle_err = "An HSDIO state change was detected during the first repeat cycle."
        for t in transition_list:
            if self.repeats[t['index']] == -1:
                if repeat_sample_clock_cycles < cycles_per_repeat:
                    logger.error(first_cycle_err)
                    raise PauseError
                if not repeats_done or sample_clock_cycles_to_next_ot < 0:
                    # mark the total time to first other transition, use from before but cant overwrite
                    # because I am dumb
                    sample_clock_cycles_to_next_ot = sample_clock_cycles_to_next_ot_option
                #if sample_clock_cycles_to_next_ot <
                repeats_done = True
                other_transitions.append(shallow_copy(t))
            else:
                if cycles_per_repeat != t['cycles_per_repeat']:
                    logger.error("An overlapping repeat cycle was detected.")
                if repeats_done:
                    logger.error(first_cycle_err + "Also check that you aren't accidentally doing a dds grey code switch.")
                    raise PauseError
                repeat_only_list.append(shallow_copy(t))
                repeat_sample_clock_cycles += t['waitTime']
                sample_clock_cycles_to_next_ot_option = repeat_sample_clock_cycles
                if repeat_sample_clock_cycles >= t['cycles_per_repeat']:
                    # clean up waits
                    repeat_only_list[-1]['waitTime'] -= repeat_sample_clock_cycles - t['cycles_per_repeat']+1
                    repeat_sample_clock_cycles = t['cycles_per_repeat']
                    # repeat the last transition so the cycle has the correct length
                    last_t = shallow_copy(t)
                    last_t['waitTime'] = 0
                    repeat_only_list.append(last_t)
                    # repeats should be done now
                    repeats_done = True
                    # need a dummy transition to get the loop to work
                    other_transitions[0] = shallow_copy(t)

        # if we didn't go through the loop handle this stuff now
        if sample_clock_cycles_to_next_ot < 0:
            sample_clock_cycles_to_next_ot = repeat_sample_clock_cycles
            sample_clock_cycles_to_next_ot *= repeat_only_list[0]['repeats']
        other_transitions[0]['waitTime'] = sample_clock_cycles_to_next_ot

        # now let make a list of transition_lists broken up by the other transitions
        transition_lists = []
        transition_cycles = []
        cycle_count = 0
        modulo = 0
        for i, ot in enumerate(other_transitions):
            # calculate how many full cycles before each other transition
            sample_clock_cycles_to_next_ot = ot['waitTime']
            if modulo:  # from last round
                sample_clock_cycles_to_next_ot -= repeat_only_list[0]['cycles_per_repeat'] - modulo
            full_cycles, modulo = divmod(sample_clock_cycles_to_next_ot, repeat_sample_clock_cycles)
            if cycle_count + full_cycles > repeat_only_list[0]['repeats']:
                full_cycles = repeat_only_list[0]['repeats'] - cycle_count
                modulo = 0
            new_repeat_only_list = self.update_transition_list(repeat_only_list, ot)
            repeat_only_list = new_repeat_only_list
            # generate a waveform for the full cycles
            transition_lists.append(repeat_only_list)
            transition_cycles.append(full_cycles)
            cycle_count += full_cycles
            # generate a patch waveform if a cycle is interrupted
            if modulo > 0:
                # step through repeat waveform and switch to new_repeat_only_list, when cycles are exceeded
                transition_lists.append([])
                transition_cycles.append(1)
                cycle_count += 1
                # copy the old transitions in, and switch after modulo time
                if i>=len(other_transitions):
                    logger.error('Transition at last repeat phase. Move the transition back one cycle.')
                    raise PauseError
                else:
                    new_repeat_only_list = self.update_transition_list(repeat_only_list, other_transitions[i+1])
                extra_idx = 1  # assume we will ned another transition until proven otherwise
                ctime = 0
                for idx in range(len(repeat_only_list)):
                    if ctime < modulo:
                        transition_lists[-1].append(shallow_copy(repeat_only_list[idx]))
                    if ctime == modulo:
                        transition_lists[-1].append(shallow_copy(new_repeat_only_list[idx]))
                        extra_idx = 0  # the transition occurred during an existing transition
                    if ctime > modulo:
                        transition_lists[-1].append(shallow_copy(new_repeat_only_list[idx-extra_idx]))
                    ctime += repeat_only_list[idx]['waitTime']
                # add in the last transition if we had to make a new one
                if extra_idx:
                    transition_lists[-1].append(shallow_copy(new_repeat_only_list[-1]))
                    # fix waitTimes
                    ctime = 0
                    for idx, tt in enumerate(transition_lists[-1]):
                        ctime += tt['waitTime']
                        if ctime > modulo:
                            tt['waitTime'] -= ctime-modulo
                            transition_lists[-1][idx+1]['waitTime'] = ctime-modulo
                            break
                    ctime = 0
                    for tt in transition_lists[-1]:
                        ctime += tt['waitTime']
                    if ctime != repeat_sample_clock_cycles-1:
                        logger.error('Error in repeat loop, wrong cycle count')
                        raise PauseError

        # now that we have split up the lists and applied the other transisions, generate the new waveforms
        waveforms = []
        for idx, tl in enumerate(transition_lists):
            wform = self.add_waveform(tl, waveformsInUse)
            wform['cycles'] = transition_cycles[idx]
            waveforms.append(wform)
            # print wform
        return waveforms

    def update_transition_list(self, t_list, update):
        """Change the states in t_list based on the updated state.

        The differential is calculated based on the last state in t_list.
        """
        # find delta
        update_state_list = map(int, update['state'].split(' '))
        old_state_list = map(int, t_list[-1]['state'].split(' '))
        delta = []
        for idx in range(len(update_state_list)):
            delta.append(update_state_list[idx] - old_state_list[idx])
        # apply delta
        new_list = []
        for t in t_list:
            new_t = shallow_copy(t)
            s = map(int, t['state'].split(' '))
            # if this goes out of range 0, 1 then you were changing one of the repeating channels
            new_state = []
            for idx in range(len(s)):
                new_state.append(s[idx] + delta[idx])
                if new_state[-1] != 0 and new_state[-1] != 1:
                    logger.error("Changing a repeating channels during a repeat cycle is not allowed.")
                    raise PauseError
            # cast back to a string
            new_t['state'] = ' '.join(map(str, new_state))
            new_list.append(new_t)
        return new_list

    def find_repeat_overlaps(self):
        """Go through the list of repeats and return a list of overlaps."""
        # replace with an array of t0's and tf's then sort
        overlap = []
        for i in np.argsort([r['t0'] for r in self.repeat_list])[:-1]:
            if self.repeat_list[i]['tf'] > self.repeat_list[i+1]['t0']:
                overlap.append(i)
                logger.warning('HSDIO Repeat Overlap at ts={}'.format(self.repeat_list[i+1]['t0']))
        return overlap

    def add_wait(self, script, waitTime):
        """Append a wait statement to the script."""
        # the HSDIO card cannot handle a wait value longer than this, so we repeat it as many
        # times as necessary
        max_wait_cycles = 536870912
        wait_phrase = 'wait {}'
        for m in range(int(waitTime/max_wait_cycles)):
            script.append(wait_phrase.format(max_wait_cycles))
        # add the remaining wait
        script.append(wait_phrase.format(int(waitTime % max_wait_cycles)))

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
        Repeats are still useful to keep down the processing time on LabView, for me 4 M samples can take
        about a minute to upload and unpack.
        Using repeats reduces the size of waveforms and can lead to less dead time between iterations.
        """
        if self.enable:
            # build dictionary of waveforms keyed on waveform name
            waveformsInUse = []
            self.complex_waveform_counter = 0

            script = ['script script1']
            master_waveform_list = []

            if len(self.find_repeat_overlaps()) > 0:
                self.repeat_list = []
                logger.error('HSDIO Repeat Overlap Error: make sure HSDIO Repeat calls do not overlap')
                raise PauseError

            # list of indicies and waitTimes to be added to a single waveform
            transition_list = []
            # repeat cycle state info
            in_repeat_cycle = False
            # go through each transition
            for i in xrange(len(self.indices)):
                waitTime = self.getNormalizedWaitTime(i)
                # append index and waittime to list of transitions to add as a single waveform
                transition_list.append({
                    'index': i,
                    'waitTime': waitTime,
                    'state': ' '.join([str(int(state)) for state in self.states[i]])
                })

                # check if transition is part of a repeat request, if so handle it separatly
                if in_repeat_cycle or self.repeats[i] != -1:
                    # first time in cycle?
                    if not in_repeat_cycle:
                        cumulative_time = 0
                        total_time = self.repeats[i]['cycles_per_repeat']*self.repeats[i]['repeats']
                    # mark as in cycle
                    in_repeat_cycle = True
                    # check end condition
                    cumulative_time += waitTime
                    if self.repeats[i] != -1:
                        # append some extra info to transition dict
                        for key in ['cycles_per_repeat', 'repeats']:
                            transition_list[-1][key] = self.repeats[i][key]
                    if cumulative_time > total_time:
                        # break out after this transition
                        in_repeat_cycle = False
                        # add all the stuff in now
                        waveforms = self.add_repeat_waveform(transition_list, waveformsInUse)
                        # cycle might be broken up into multiple waveforms
                        for w in waveforms:
                            # might have a cycle broken up in the middle by something else changing
                            if w['cycles'] > 1:
                                script.append('repeat {}'.format(w['cycles']))
                                script.append('generate {}'.format(w['name']))
                                script.append('end repeat')
                            else:
                                script.append('generate {}'.format(w['name']))
                            master_waveform_list.append(w['xml'])
                            # add in the necessary wait statement after the cycle
                        self.add_wait(script, cumulative_time-total_time)
                        transition_list = []

                # if not a repeat do the normal thing
                else:
                    # if the waitTime is less than the stable time add another state to the transition list
                    # if the next transition is marked as a repeat then, just stop now
                    minWait = self.experiment.Config.config.getint('HSDIO', 'MinStableWaitCycles')
                    if (waitTime >= minWait) or (i+1 == len(self.repeats)) or (self.repeats[i+1] != -1):
                        waveform = self.add_waveform(transition_list, waveformsInUse)
                        # reset transition list
                        transition_list = []
                        # generate waveform
                        script.append('generate {}'.format(waveform['name']))
                        # add waveform to list if it is new
                        if waveform['xml']:
                            master_waveform_list.append(waveform['xml'])
                        self.add_wait(script, waitTime)

            script.append('end script')
            self.repeat_list = []
            xml_str = '<HSDIO><script>{}</script>\n<waveforms>{}</waveforms>\n'.format(
                '\n'.join(script),
                '\n'.join(master_waveform_list)
            )
            #pprint.pprint(script)
            #pprint.pprint(master_waveform_list)
            # [7:] removes the <HSDIO> on what is returned from super.toHardware
            return xml_str + super(HSDIO, self).toHardware()[7:]
        else:
            # let Instrument.toHardware send <name><enable>False</enable><name>
            return super(HSDIO, self).toHardware()
