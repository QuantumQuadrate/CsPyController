from exp_functional_waveforms.dds import DDS

HSDIO = experiment.LabView.HSDIO.add_transition
HSDIO_repeat = experiment.LabView.HSDIO.add_repeat
AO = experiment.LabView.AnalogOutput.add_transition
DO = experiment.LabView.DAQmxDO.add_transition
label = experiment.functional_waveforms_graph.label

################################################################################
# DDS STUFF ####################################################################
################################################################################

# Rb D2 AOM profiles
RB_D2_DDS = DDS(
    HSDIO,
    (
        HSDIO_channels['rb_d2_dds_p0']['channel'],
        HSDIO_channels['rb_d2_dds_p1']['channel'],
        HSDIO_channels['rb_d2_dds_p2']['channel']
    ),
    {
        'mot': (0, 0, 0),
        'pgc': (1, 0, 0),
        'off': (0, 1, 0),
        'read': (1, 1, 0),
        'mon': (0, 0, 1),
        'p5': (1, 0, 1),
        'read_mz': (0, 1, 1),
        'p7': (1, 1, 1)
    }
).profile

# FORT AOM profiles
FORT_DDS = DDS(
    HSDIO,
    (
        HSDIO_channels['fort_dds_p0']['channel'],
        HSDIO_channels['fort_dds_p1']['channel'],
    ),
    {
        'on': (0,0),
        'off': (1,0),
        'high': (0,1),
        'low': (1,1),
    }
).profile


################################################################################
# AO STUFF #####################################################################
################################################################################


def ramp(t, channel, v1, v2, duration):
    """Sweep one analog output channel from v1 to v2."""
    t_list = linspace(t, t+duration, 100)  # make 100 time steps
    v_list = linspace(v1, v2, 100)  # make 100 voltage steps
    for t, v in zip(t_list, v_list):
        # step through each value and assign it to the AO channel
        AO(t, channel, v)
    return t+duration  # return the end time


################################################################################
# INIT AND TEARDOWN ############################################################
################################################################################


def init(t, b_field='mot'):
    RB_D2_DDS(t, 'off')
    for chan in range(32):
        HSDIO(t, chan, False)

    for chan in HSDIO_channels:
        # overwrite intial states if defined
        HSDIO(t, HSDIO_channels[chan]['channel'], HSDIO_channels[chan]['default'])

    for chan in Bfields[b_field]:
        AO(t, Bfield_channels[chan]['channel'], Bfields[b_field][chan]['voltage'])

    ts = []
    ts.append(RB_D2_DDS(t, 'off'))
    return max(ts)


def end(t):
    return init(t)

################################################################################
# HSDIO STUFF ##################################################################
################################################################################


# def chop(t, channels, phases, period):
#     """Add a single cycle of a chopping pattern to the HSDIO transition list.
#
#     If the phase for a channel is 0 it turns on at time t
#     If the phase for a channel is 1>p>0 it turns on at time (t+period*phase)
#     If the phase for a channel is 0>p>-1 it starts on and turns off at time (t + period*(1 + phase))
#
#     channels is a list of channel numbers
#     phases is a list of phases between -1 and 1 equal in length to the number of
#         channels being switched
#     period is the period of the cycle
#     returns t + period
#     """
#     if len(channels) != len(phases):
#         print "Chop function requries equal length lists of channels and phases"
#         raise PauseError
#
#     for i, c in enumerate(channels):
#         p = phases[i]
#         if abs(p) > 1:
#             print "Chop function expects phases to be within abs(p)<=1"
#             raise ValueError
#         init_state = p < 0
#         # if phase is negative substract from end of phase
#         if init_state:
#             p = 1 + p
#         # put in initial value for the cycle
#         msg = "ch[{}]: t({}) = {}"
#         print(msg.format(c, 0, init_state))
#         HSDIO(t, c, init_state)
#         # put in transition
#         print(msg.format(c, p, not init_state))
#         HSDIO(t + (p * period), c, not init_state)
#     return t + period


def chop_dds(channels, phases, profiles, period):
    """Add a single cycle of a chopping pattern for DDS profiles.

    If the phase for a channel is 0 it turns on at time t
    If the phase for a channel is 1>p>0 it turns on at time (t+period*phase)

    channels is a list of channel numbers
    phases is a list of phases between 0 and 1 equal in length to the number of
        channels being switched
    profiles is a list of length 2 lists of dds profile names, index 0 is the initial profile
    period is the period of the cycle
    returns t + period
    """
    if len(channels) != len(phases) or len(channels) != len(profiles):
        print "Chop function requries equal length lists of channels and phases"
        raise PauseError

    def chop_function(t):
        # TODO: check that profiles are grey coded!!!!!!!!
        for i, c in enumerate(channels):
            # set up initial state
            init_state = profiles[i][0]
            msg = "ch[{}]: t({}) = {}"
            #print(msg.format(c, 0, init_state))
            c(t, init_state)
            # now change state at phase list
            for j, p in enumerate(phases[i]):
                if p > 1 or p < 0:
                    print "chop_dds function expects phases to be within 0<p<1"
                    raise ValueError
                # put in initial value for the cycle
                # put in transition
                #print(msg.format(c, p, profiles[i][j + 1]))
                c(t + (p * period), profiles[i][j + 1])
        return t + period

    return chop_function


def MXY_shutter(t, state):
    """Open or close the MOT XY shutter, True -> open, False -> closed."""
    # start shurt early
    label(t, 'MOTXY shutter')
    HSDIO(t, HSDIO_channels['scope_trig_1']['channel'], not state)
    # shift forward by the delay plus half the switching time
    t_switch = t - MXY_shutter_delay_ms - MXY_shutter_time_ms/2
    HSDIO(t_switch, HSDIO_channels['mxy_shutter']['channel'], state)
    return t


def counter_sample_clock(t, bins, period_ms):
    # throwaway bins to clear counter
    for i in range(bins):
        HSDIO(t, HSDIO_channels['spcm_gate_780']['channel'], True)
        HSDIO(t + 0.5*period_ms, HSDIO_channels['spcm_gate_780']['channel'], False)
        t += period_ms
    return t


def counter_sample_clock_overhead(t, bins=1):
    """Generate throwaway bins to clear counter."""
    return counter_sample_clock(t, bins, throwaway_bin_duration)


def counter_sample_clock_measurement(t, bins=1, duration=1):
    """Generate throwaway bins to clear counter."""
    return counter_sample_clock(t, bins, duration/bins)


def counter_readout(t, duration):
    """Actual readout starts at t."""
    # subtract off time for setup pulses
    t_setup = t - (throwaway_bins-1)*throwaway_bin_duration
    tp = counter_sample_clock_overhead(t_setup, bins=throwaway_bins-1)
    if abs(tp - t) >= 0.000005:  # 1 clock cycle
        print "There was an alignment issue with the setup pulse timings. "
        print "t_setup = {} ms, t_period = {} ms, t_start = {} ms, t_start_actual = {}".format(
            t_setup,
            throwaway_bin_duration,
            t,
            tp
        )
        raise PauseError
    # start the readout
    label(t, 'readout')
    # send real timing pulses to counter
    t = counter_sample_clock_measurement(t, bins=measurement_bins, duration=duration)
    # end the readout
    return counter_sample_clock_overhead(t, bins=1)

################################################################################
# MOT ##########################################################################
################################################################################


def mot_loading(t, duration):
    """Load atoms from background."""
    phase = 'mot'

    label(t, 'MOT loading')
    # dds sometimes adds greycode delays for stability
    ts = []
    ts.append(RB_D2_DDS(t, phase))
    # might as well keep it off when loading the mot
    if dump_fort_at_end:
        ts.append(FORT_DDS(t, 'off'))
    # add repumper

    for chan in Bfields[phase]:
        AO(t, Bfield_channels[chan]['channel'], Bfields[phase][chan]['voltage'])

    t = max(ts)
    t += duration
    return t

################################################################################
# PGC ##########################################################################
################################################################################


def pgc(t, duration):
    """Compress and cool."""
    phase = 'pgc'

    label(t, 'PGC')
    # dds sometimes adds greycode delays for stability
    ts = []
    ts.append(RB_D2_DDS(t, phase))
    ts.append(FORT_DDS(t, 'on'))
    t = max(ts)
    t_start = t

    for chan in Bfields[phase]:
        AO(t, Bfield_channels[chan]['channel'], Bfields[phase][chan]['voltage'])

    t = max(ts)
    ts = [t + duration]

    # chop FORT
    t = t_start
    label(t, 'fort load c0')
    cycles = int(duration*1000*readout_chop_freq_MHz) - 1
    period_ms = 0.001/readout_chop_freq_MHz
    label(t + period_ms, 'fort load c1')

    channels = [FORT_DDS]
    phases = [[0.3, 0.76]]
    profiles = [
        ['on', 'off', 'on']
    ]
    t = HSDIO_repeat(t, chop_dds(channels, phases, profiles, period_ms), cycles)
    ts.append(t)
    t = max(ts)
    return t

################################################################################
# DROP MOT #####################################################################
################################################################################


def drop_mot(t, duration):
    """Turn mot off"""
    phase = 'off'

    label(t, 'OFF')
    # dds sometimes adds greycode delays for stability
    ts = []
    ts.append(RB_D2_DDS(t, phase))
    # add repumper

    for chan in Bfields[phase]:
        AO(t, Bfield_channels[chan]['channel'], Bfields[phase][chan]['voltage'])

    t = max(ts)
    t += duration
    return t

################################################################################
# MOT READOUT ##################################################################
################################################################################


def mot_readout(t, duration):
    """Image MOT."""
    phase = 'read'

    label(t, 'OFF')
    # dds sometimes adds greycode delays for stability
    ts = []
    ts.append(RB_D2_DDS(t, phase))
    # add repumper

    for chan in Bfields[phase]:
        AO(t, Bfield_channels[chan]['channel'], Bfields[phase][chan]['voltage'])

    # camera triggers
    HSDIO(t, HSDIO_channels['point_grey_1']['channel'], True)
    HSDIO(t + 1, HSDIO_channels['point_grey_1']['channel'], False)

    HSDIO(t, HSDIO_channels['luca_trig_1']['channel'], True)
    HSDIO(t + 1, HSDIO_channels['luca_trig_1']['channel'], False)
    ts.append(t + 1)

    t = max(ts)
    t += duration
    return t


def mot_spcm_readout(t, duration):
    """MOT signal with SPCM."""
    return counter_readout(t, duration)

################################################################################
# FORT READOUT #################################################################
################################################################################


def fort_readout(t, duration, mz_only=False, count=True):
    """Image atom in FORT."""
    phase = 'read'
    if mz_only:
        phase = 'read_mz'
    label(t, 'readout prep')

    # set b fields
    if phase not in Bfields:
        print "No `{}` b-fields specified, using normal read fields".format(phase)
        phase_b = 'read'
    else:
        phase_b = phase
    for chan in Bfields[phase_b]:
        AO(t, Bfield_channels[chan]['channel'], Bfields[phase_b][chan]['voltage'])

    # dds sometimes adds greycode delays for stability
    RB_D2_DDS(t, 'off')

    # throwaway bins to clear counter
    if count:
        t = counter_sample_clock_overhead(t, bins=throwaway_bins-1)
    else:
        t += (throwaway_bins-1)*throwaway_bin_duration
    # start the readout
    label(t, 'readout')
    t_start = t

    # chop FORT and MOT out of phase
    cycles = int(duration*1000*readout_chop_freq_MHz)
    period_ms = 0.001/readout_chop_freq_MHz
    label(t + period_ms, 'readout c1')
    label(t + cycles*period_ms/2, 'readout half')
    channels = [RB_D2_DDS, FORT_DDS]
    phases = [[0.25, 0.7], [0.3, 0.76]]
    profiles = [
        ['off', phase, 'off'],
        ['on', 'off', 'on']
    ]
    t = HSDIO_repeat(t, chop_dds(channels, phases, profiles, period_ms), cycles)

    # record end times
    ts = [t]

    if count:
        # send real timing pulses to counter
        t = t_start
        t = counter_sample_clock_measurement(t, bins=measurement_bins, duration=duration)
        # end the readout
        t = counter_sample_clock_overhead(t, bins=1)
        ts.append(t)

    t = max(ts)
    return t

################################################################################
# FORT READOUT #################################################################
################################################################################


def parametric_heating(t, duration, freq):
    """Heat atoms at twice trap freq.

    duration in ms, freq in kHz
    """
    phase = 'off'

    label(t, 'p_heat')
    for chan in Bfields[phase]:
        AO(t, Bfield_channels[chan]['channel'], Bfields[phase][chan]['voltage'])
    # dds sometimes adds greycode delays for stability
    ts = []
    ts.append(RB_D2_DDS(t, phase))
    t = max(ts)

    # chop FORT
    cycles = int(duration*freq)
    print cycles
    period_ms = 1.0/freq
    label(t + period_ms, 'p_heat c1')

    channels = [FORT_DDS]
    phases = [[0.3, 0.76]]
    profiles = [
        ['high', 'low', 'high']
    ]
    t = HSDIO_repeat(t, chop_dds(channels, phases, profiles, period_ms), cycles)
    t += 0.35
    FORT_DDS(t, 'on')
    return t


################################################################################
# EXPERIMENT####################################################################
################################################################################

def expmnt(t, duration):
    label(t, 'exp start')
    #HSDIO(t, HSDIO_channels['scope_trig_1']['channel'], True)
    FORT_DDS(t, 'off')
    t += duration
    FORT_DDS(t, 'on')
    label(t, 'exp end')
    #HSDIO(t, HSDIO_channels['scope_trig_1']['channel'], False)
    return t


################################################################################
# TIMINGS ######################################################################
################################################################################


def fort_experiment():
    # HSDIO initialization
    t = 0
    t = init(t)
    t += 0.001
    # load mot
    t = mot_loading(t, mot_time)
    t = pgc(t, pgc_time)
    t = drop_mot(t, drop_time)

    t = fort_readout(t, readout_780 + exra_readout_780)
    t = drop_mot(t, 0.01)
    t = pgc(t, post_read_pgc_time)

    # close shutter for Mxy beam
    # wait for the shutter switch time so we dont turn off during pgc
    t = drop_mot(t, MXY_shutter_time_ms)
    MXY_shutter(t, False)

    if test_mz_readout:
        t = fort_readout(t, test_mz_readout_duration, mz_only=True, count=False)

    if p_heating:
        t = parametric_heating(t, p_heating_duration, p_heating_freq)

    # wait the remainder of the gap time
    t = drop_mot(t, gap_time/2 - MXY_shutter_time_ms)
    t = expmnt(t, fort_drop_us/1000)
    t = drop_mot(t, gap_time/2)
    t = fort_readout(t, readout_780, mz_only=True)
    # open shutter for Mxy beam
    MXY_shutter(t + 0.2, True)  # fudge

    if dump_fort_at_end:
        t += 0.25
        FORT_DDS(t, 'off')
        t += 0.5
        FORT_DDS(t, 'on')
        t += 0.25
    else:
        t += 1
    t = end(t)
    print "actual(requested) cycle time {}({}) ms".format(t, cycle_time)
    check_cycle_time(t)


# CW MOT
def mot_cw_experiment():
    # HSDIO initialization
    t = 0
    t = init(t)
    # load mot
    t = mot_loading(t, 1)
    HSDIO(t, HSDIO_channels['scope_trig_1']['channel'], True)
    t = mot_spcm_readout(t, readout_780)
    HSDIO(t, HSDIO_channels['scope_trig_1']['channel'], False)
    t = cycle_time - readout_780 - 10
    t = mot_spcm_readout(t, readout_780)
    t = cycle_time
    t = init(t)
    print "actual(requested) cycle time {}({}) ms".format(t, cycle_time)

################################################################################
# ERROR CHECKING################################################################
################################################################################


def check_cycle_time(t):
    if t > cycle_time:
        print "Calculated cycle time ({} ms) exceeds specified cycle time ({} ms)".format(t, cycle_time)
        raise PauseError

################################################################################
# EXPERIMENT TYPES #############################################################
################################################################################


exps = {
    fort_exp: fort_experiment,
    mot_cw_exp: mot_cw_experiment,
}

# Experiment type switch
exps[exp_type]()
