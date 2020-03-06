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
        'pgc2': (1, 0, 1),
        'read_mz': (0, 1, 1),
        'off2': (1, 1, 1)
    }
).profile

# Cs D2 AOM profiles
CS_D2_DDS = DDS(
    HSDIO,
    (
        HSDIO_channels['cs_d2_dds_p0']['channel'],
        HSDIO_channels['cs_d2_dds_p1']['channel'],
        HSDIO_channels['cs_d2_dds_p2']['channel']
    ),
    {
        'mot': (0, 0, 0),
        'pgc': (1, 0, 0),
        'off': (0, 1, 0),
        'read': (1, 1, 0),
        'mon': (0, 0, 1),
        'pgc2': (1, 0, 1),
        'read_mz': (0, 1, 1),
        'off2': (1, 1, 1)
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


def cal_ramp(t, channel, x1, x2, duration, cal=None):
    """Sweep one analog output channel from v1 to v2."""
    t_list = linspace(t, t+duration, 100)  # make 100 time steps
    v_list = fort_attn_cal(linspace(x1, x2, 100))  # make 100 voltage steps
    for t, v in zip(t_list, v_list):
        # step through each value and assign it to the AO channel
        AO(t, channel, v)
    return t+duration  # return the end time


def cal_mod(t, channel, f, amp, cycles, cal=None):
    """Sweep one analog output channel from v1 to v2."""
    duration = cycles/f
    ppc = 20
    t_list = linspace(t, t+duration, cycles*ppc)  # make 100 time steps
    v_list = fort_attn_cal(1+amp*sin(2*pi*f*t_list))  # make 100 voltage steps
    for t, v in zip(t_list, v_list):
        # step through each value and assign it to the AO channel
        AO(t, channel, v)
    return t+duration  # return the end time

################################################################################
# INIT AND TEARDOWN ############################################################
################################################################################


def init(t, b_field='mot'):
    RB_D2_DDS(t, 'mot')
    CS_D2_DDS(t, 'mot')
    for chan in range(32):
        HSDIO(t, chan, False)

    for chan in HSDIO_channels:
        # overwrite intial states if defined
        HSDIO(t, HSDIO_channels[chan]['channel'], HSDIO_channels[chan]['default'])

    for chan in Bfields[b_field]:
        AO(t, Bfield_channels[chan]['channel'], Bfields[b_field][chan]['voltage'])

    AO(t, AO_channels['fort_attn']['channel'], 0)

    ts = []
    ts.append(RB_D2_DDS(t, 'mot'))
    ts.append(CS_D2_DDS(t, 'mot'))
    t = max(ts)
    return error_counter_start(t)


def end(t, b_field='mot'):
    t = error_counter_end(t)
    RB_D2_DDS(t, 'mot')
    CS_D2_DDS(t, 'mot')
    for chan in range(32):
        HSDIO(t, chan, False)

    for chan in HSDIO_channels:
        # overwrite intial states if defined
        HSDIO(t, HSDIO_channels[chan]['channel'], HSDIO_channels[chan]['default'])

    for chan in Bfields[b_field]:
        AO(t, Bfield_channels[chan]['channel'], Bfields[b_field][chan]['voltage'])

    AO(t, AO_channels['fort_attn']['channel'], 0)
    ts = []
    ts.append(RB_D2_DDS(t, 'mot'))
    ts.append(CS_D2_DDS(t, 'mot'))
    return max(ts)

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
            print(msg.format(c, 0, init_state))
            c(t, init_state)
            # now change state at phase list
            for j, p in enumerate(phases[i]):
                if p > 1 or p < 0:
                    print "chop_dds function expects phases to be within 0<p<1.  p={}".format(p)
                    raise ValueError
                # put in initial value for the cycle
                # put in transition
                #print(msg.format(c, p, profiles[i][j + 1]))
                c(t + (p * period), profiles[i][j + 1])
        return t + period

    return chop_function


def chop_dds_hsdio(dds_channels, dds_phases, dds_profiles, hsdio_channels, hsdio_phases, hsdio_profiles, period):
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
    if len(dds_channels) != len(dds_phases) or len(dds_channels) != len(dds_profiles):
        print "Chop function requries equal length lists of channels and phases"
        raise PauseError
    if len(hsdio_channels) != len(hsdio_phases) or len(hsdio_channels) != len(hsdio_profiles):
        print "Chop function requries equal length lists of channels and phases"
        raise PauseError

    def chop_function(t):
        # DDS repeats
        # TODO: check that profiles are grey coded!!!!!!!!
        for i, c in enumerate(dds_channels):
            # set up initial state
            init_state = dds_profiles[i][0]
            msg = "ch[{}]: t({}) = {}"
            # print(msg.format(c, 0, init_state))
            c(t, init_state)
            # now change state at phase list
            for j, p in enumerate(dds_phases[i]):
                if p > 1 or p < 0:
                    print "chop_dds_hsdio function expects phases to be within 0<p<1"
                    raise ValueError
                # put in initial value for the cycle
                # put in transition
                # print(msg.format(c, p, profiles[i][j + 1]))
                c(t + (p * period), dds_profiles[i][j + 1])

        # HSDIO repeats
        for i, c in enumerate(hsdio_channels):
            # set up initial state
            init_state = hsdio_profiles[i][0]
            msg = "ch[{}]: t({}) = {}"
            # print(msg.format(c, 0, init_state))
            HSDIO(t, c, init_state)
            # now change state at phase list
            for j, p in enumerate(hsdio_phases[i]):
                if p > 1 or p < 0:
                    print "chop_dds_hsdio function expects phases to be within 0<p<1"
                    raise ValueError
                # put in initial value for the cycle
                # put in transition
                # print(msg.format(c, p, profiles[i][j + 1]))
                HSDIO(t + (p * period), c, hsdio_profiles[i][j + 1])
        return t + period

    return chop_function


def MXY_shutter(t, state):
    """Open or close the MOT XY shutter, True -> open, False -> closed."""
    # start shurt early
    label(t, 'MOTXY shutter')
    #HSDIO(t, HSDIO_channels['scope_trig_1']['channel'], not state)
    # shift forward by the delay plus half the switching time
    t_switch = t - MXY_shutter_delay_ms - MXY_shutter_time_ms/2
    HSDIO(t_switch, HSDIO_channels['mxy_shutter']['channel'], state)
    return t


def M_shutter(t, state):
    """Open or close MOT shutter, True -> open, False -> closed."""
    # start shurt early
    label(t, 'MOT shutter')
    #HSDIO(t, HSDIO_channels['scope_trig_1']['channel'], not state)
    # shift forward by the delay plus half the switching time
    t_switch = t - M_shutter_delay_ms - M_shutter_time_ms/2
    HSDIO(t_switch, HSDIO_channels['m_shutter']['channel'], not state)
    return t


def HF_shutter(t, state):
    """Open or close HF shutter, True -> open, False -> closed."""
    label(t, 'HF shutter')
    #HSDIO(t, HSDIO_channels['scope_trig_1']['channel'], not state)
    # shift forward by the delay plus half the switching time
    # switch RB
    t_switch = t - RB_HF_shutter_delay_ms - RB_HF_shutter_time_ms/2
    HSDIO(t_switch, HSDIO_channels['rb_hf_shutter']['channel'], not state)
    # switch CS
    t_switch = t - CS_HF_shutter_delay_ms - CS_HF_shutter_time_ms/2
    HSDIO(t_switch, HSDIO_channels['cs_hf_shutter']['channel'], state)
    return t


def OP_shutter(t, state):
    """Open or close OP shutter, True -> open, False -> closed."""
    label(t, 'OP shutter')
    #HSDIO(t, HSDIO_channels['scope_trig_1']['channel'], state)
    # shift forward by the delay plus half the switching time
    t_switch = t - OP_shutter_delay_ms - OP_shutter_time_ms/2
    HSDIO(t_switch, HSDIO_channels['op_shutter']['channel'], not state)
    return t


def MZ2_shutter(t, state):
    """Open or close <Z retro-reflection shutter, True -> open, False -> closed."""
    label(t, 'MZ2 shutter')
    HSDIO(t, HSDIO_channels['scope_trig_1']['channel'], not state)
    # shift forward by the delay plus half the switching time
    t_switch = t - MZ2_shutter_delay_ms - MZ2_shutter_time_ms/2
    HSDIO(t_switch, HSDIO_channels['mz2_shutter']['channel'], state)
    return t


def counter_sample_clock(t, bins, period_ms, channel):
    """Generate an evenly spaced number of counter sample clock cycles equal to bins"""
    # throwaway bins to clear counter
    for i in range(bins):
        HSDIO(t, channel, True)
        HSDIO(t + 0.5*period_ms, channel, False)
        t += period_ms
    return t


def counter_sample_clock_overhead(t, bins=1, channel=None):
    """Generate throwaway bins to clear counter."""
    if channel is None:
        channel = HSDIO_channels['spcm_gate_780']['channel']
    return counter_sample_clock(t, bins, throwaway_bin_duration, channel)


def counter_sample_clock_measurement(t, bins=1, duration=1, channel=None):
    """Generate throwaway bins to clear counter."""
    if channel is None:
        channel = HSDIO_channels['spcm_gate_780']['channel']
    return counter_sample_clock(t, bins, duration/bins, channel)


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
    # HSDIO(t, HSDIO_channels['scope_trig_1']['channel'], True)
    t = counter_sample_clock_measurement(t, bins=measurement_bins, duration=duration)
    # HSDIO(t, HSDIO_channels['scope_trig_1']['channel'], False)
    # end the readout
    return counter_sample_clock_overhead(t, bins=1)


def error_counter_start(t):
    """start reading out the counter to catch errors (call at start)"""
    chan = HSDIO_channels['error_cntr_gate']['channel']
    t = counter_sample_clock_overhead(t, bins=throwaway_bins-1, channel=chan)
    label(t, 'error capture start')
    # we dont really need to wait for this (just make it short and the last bin will hold most of the counts)
    t_end = counter_sample_clock_measurement(t, bins=measurement_bins, duration=1, channel=chan)
    # do a second shot
    t_end = error_counter_end(t_end)
    t_end = counter_sample_clock_overhead(t_end, bins=throwaway_bins-1, channel=chan)
    t_end = counter_sample_clock_measurement(t_end, bins=measurement_bins, duration=1, channel=chan)
    return t


def error_counter_end(t):
    """stop reading out the counter to catch errors (call at end)"""
    chan = HSDIO_channels['error_cntr_gate']['channel']
    return counter_sample_clock_overhead(t, bins=1, channel=chan)


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
    ts.append(CS_D2_DDS(t, phase))
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


def pgc(t, duration, no_chop=False, bphase='pgc', fphase='on', phase='pgc', chop_cooling=False):
    """Compress and cool."""
    label(t, 'PGC')
    # dds sometimes adds greycode delays for stability
    ts = []
    if chop_cooling:
        ts.append(RB_D2_DDS(t, 'off2'))
        ts.append(CS_D2_DDS(t, 'off2'))
    else:
        ts.append(RB_D2_DDS(t, phase))
        ts.append(CS_D2_DDS(t, phase))
    ts.append(FORT_DDS(t, fphase))

    for chan in Bfields[bphase]:
        AO(t, Bfield_channels[chan]['channel'], Bfields[bphase][chan]['voltage'])
    ts.append(t + field_settle_time)

    t = max(ts)
    t_start = t
    ts = [t + duration]
    if duration > 0:
        if not no_chop:
            # chop FORT
            t = t_start
            label(t, 'fort load c0')
            cycles = int(duration*1000*readout_chop_freq_MHz) - 1
            period_ms = 0.001/readout_chop_freq_MHz
            label(t + period_ms, 'fort load c1')

            channels = [FORT_DDS]
            phases = [[0.5, 0.96]]
            profiles = [
                [fphase, 'off', fphase]
            ]
            if chop_cooling:
                channels += [RB_D2_DDS, CS_D2_DDS]
                phases += [
                    [0.35+mot_timing_offset, 0.75+mot_timing_offset],
                    [0.35+cs_mot_timing_offset, 0.75+cs_mot_timing_offset],
                ]
                profiles += [
                    ['off2', phase, 'off2'],
                    ['off2', phase, 'off2']
                ]
            t = HSDIO_repeat(t, chop_dds(channels, phases, profiles, period_ms), cycles)
            ts.append(t)
        t = max(ts)
    return t

################################################################################
# DROP MOT #####################################################################
################################################################################


def drop_mot(t, duration, b_phase='off'):
    """Turn mot off"""
    phase = 'off'

    label(t, 'OFF')
    # dds sometimes adds greycode delays for stability
    ts = []
    ts.append(RB_D2_DDS(t, phase))
    ts.append(CS_D2_DDS(t, phase))
    # add repumper

    for chan in Bfields[phase]:
        AO(t, Bfield_channels[chan]['channel'], Bfields[b_phase][chan]['voltage'])

    t = max(ts)
    t += duration
    return t


################################################################################
# DEPUMP TO LOWER HF STATE #####################################################
################################################################################

def depump(t, duration):
    """Turn mot off"""
    aom_phase = 'pgc'
    b_phase = "expt"
    # dds sometimes adds greycode delays for stability
    ts = []
    ts.append(RB_D2_DDS(t, 'off'))
    ts.append(CS_D2_DDS(t, 'mot'))
    # add repumper

    for chan in Bfields[b_phase]:
        AO(t, Bfield_channels[chan]['channel'], Bfields[b_phase][chan]['voltage'])

    t = max(ts)

    n = 20
    duration -= n*0.001
    t += duration/2
    for i in range(n):
        FORT_DDS(t, 'low')
        t += 0.001/2
        FORT_DDS(t, 'high')
        t += 0.001/2
    t += duration/2
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
    ts.append(CS_D2_DDS(t, phase))
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


def fort_readout(t, duration, mz_only=False, count=True, parallel_cnt=False, s1=False, fphase='on'):
    """Image atom in FORT."""
    phase = 'read'
    if mz_only:
        phase = 'read_mz'
    label(t, 'readout prep')
    HSDIO(t, HSDIO_channels['fpga_threshold_sel']['channel'], s1)

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
    CS_D2_DDS(t, 'off')
    t += field_settle_time

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
    channels = [RB_D2_DDS, CS_D2_DDS, FORT_DDS]
    phases = [
        [0.35+mot_timing_offset, 0.75+mot_timing_offset],
        [0.35+cs_mot_timing_offset, 0.75+cs_mot_timing_offset],
        [0.5, 0.96]
    ]

    foff = 'off'
    if fphase == 'high':
        foff = 'low'  # cant do 2 -> 1 b/c grey code
    profiles = [
        ['off', phase, 'off'],
        ['off', phase, 'off'],
        [fphase, foff, fphase]
    ]
    # trigger the fpga counter
    if parallel_cnt:
        HSDIO(t, HSDIO_channels['fpga_counter_gate']['channel'], True)
    HSDIO(t, HSDIO_channels['luca_trig_1']['channel'], True)
    # HSDIO(t, HSDIO_channels['scope_trig_1']['channel'], True)
    t = HSDIO_repeat(t, chop_dds(channels, phases, profiles, period_ms), cycles)
    # HSDIO(t, HSDIO_channels['scope_trig_1']['channel'], False)
    HSDIO(t, HSDIO_channels['luca_trig_1']['channel'], False)
    RB_D2_DDS(t+0.0025, 'off')
    CS_D2_DDS(t+0.0025, 'off')
    if parallel_cnt:
        HSDIO(t, HSDIO_channels['fpga_counter_gate']['channel'], False)
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

    HSDIO(t, HSDIO_channels['fpga_threshold_sel']['channel'], False)
    return t

################################################################################
# OPTICAL PUMPING ##############################################################
################################################################################


def optical_pumping(t, duration, fphase='on'):
    """Prepare the initial HF zeeman state."""
    phase = 'op'
    label(t, 'op prep')

    ts = []
    ts.append(FORT_DDS(t, fphase))

    # set b fields
    if phase not in Bfields:
        print "No `{}` b-fields specified, using normal expt fields".format(phase)
        phase_b = 'expt'
    else:
        phase_b = phase
    for chan in Bfields[phase_b]:
        AO(t, Bfield_channels[chan]['channel'], Bfields[phase_b][chan]['voltage'])

    # change uWave routing switch to go to the F-EOM
    HSDIO(t, HSDIO_channels['rb_horn_switch']['channel'], False)
    HSDIO(t, HSDIO_channels['cs_horn_switch']['channel'], False)
    ts.append(t+field_settle_time)
    t = max(ts)

    # chop FORT and OP out of phase
    cycles = int(duration*1000*op_chop_freq_MHz)
    if cycles > 0:
        HSDIO(t, HSDIO_channels['rb_uwave_switch']['channel'], True)
        # HSDIO(t, HSDIO_channels['cs_uwave_switch']['channel'], True)
        period_ms = 0.001/op_chop_freq_MHz
        label(t + period_ms, 'op c1')
        label(t + cycles*period_ms/2, 'op half')
        dds_channels = [FORT_DDS]
        dds_phases = [[0.05, 0.30]]
        dds_profiles = [
            [fphase, 'off', fphase]
        ]
        hsdio_chs = []
        hsdio_phases = []
        hsdio_profiles = []
        # old RF switches cant chop at high frequency (only cs has fast switch)
        hsdio_chs = [HSDIO_channels['cs_uwave_switch']['channel']]
        hsdio_phases = [[0.4-op_timing_offset, 0.6-op_timing_offset]]
        hsdio_profiles = [
            [False, True, False]
        ]
        # hsdio_chs = []
        # hsdio_phases = []
        # hsdio_profiles = []
        # HSDIO(t, HSDIO_channels['scope_trig_1']['channel'], True)
        t = HSDIO_repeat(
            t,
            chop_dds_hsdio(
                dds_channels, dds_phases, dds_profiles,
                hsdio_chs, hsdio_phases, hsdio_profiles,
                period_ms
            ),
            cycles
        )
        t += 0.000001
        HSDIO(t, HSDIO_channels['rb_uwave_switch']['channel'], False)
        # t = FORT_DDS(t, fphase)
    # HSDIO(t, HSDIO_channels['scope_trig_1']['channel'], False)
    return t


################################################################################
# PARAMETRIC HEATING ###########################################################
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
    ts.append(CS_D2_DDS(t, phase))
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
    t += 1.35
    FORT_DDS(t, 'on')
    return t


################################################################################
# EXPERIMENT####################################################################
################################################################################


def expmnt(t, duration, fphase='on', drop=True, exp_type='fdrop', min_drop=0, min_time=0):
    """Experiment type."""
    label(t, 'exp start')
    # HSDIO(t, HSDIO_channels['scope_trig_1']['channel'], True)
    fdrop_transient = 0
    if exp_type != 'fdrop':
        fdrop_transient = 0.0003
    drop_time = max(min_drop, duration)
    ts = []
    if drop and (drop_time > 0):
        if fphase == 'high':
            FORT_DDS(t-fdrop_transient, 'low')
        else:
            FORT_DDS(t-fdrop_transient, 'off')
        ts.append(t+drop_time+fdrop_transient)
        FORT_DDS(ts[0], fphase)

    print('start: {}'.format(t))
    if exp_type == 'blue_align':
        t = blue_align_expmnt(t, duration, fphase=fphase, min_time=min_time)
    else:
        t += max(duration, min_time)
    print('end: {}'.format(t))

    ts.append(t)
    t = max(ts)
    label(t, 'exp end')
    # HSDIO(t+0.01, HSDIO_channels['scope_trig_1']['channel'], False)
    return t


def blue_align_expmnt(t, duration, fphase='on', min_time=0):
    """Scatter photons from Cs blue laser to locate beam on atoms."""
    HSDIO(t, HSDIO_channels['cs_459_aom_switch']['channel'], True)
    HSDIO(t+duration, HSDIO_channels['cs_459_aom_switch']['channel'], False)
    return max(t+duration, t+min_time)

################################################################################
# EXPERIMENT####################################################################
################################################################################


def uwave_rotation(t, duration, gap=0, fort_phase='on', atom='rb'):
    label(t, 'uwave start')
    horn_switch = HSDIO_channels['{}_horn_switch'.format(atom)]['channel']
    uwave_switch = HSDIO_channels['{}_uwave_switch'.format(atom)]['channel']
    HSDIO(t, horn_switch, True)
    t += 0.001
    HSDIO(t, uwave_switch, True)

    # ramsey style
    if gap > 0:
        t += duration/2.0
        HSDIO(t, uwave_switch, False)
        if gap > 0.1:
            # if the gap is longish turn up fort to induce oscillation
            FORT_DDS(t, 'high')
            t += gap/2.0
            # FORT_DDS(t, 'on')
            # t += 0.1
            # HSDIO(t, uwave_switch, True)
            # t += duration
            # HSDIO(t, uwave_switch, False)
            # FORT_DDS(t, 'high')
            t += gap/2.0
            FORT_DDS(t, 'on')
        else:
            t += gap
        HSDIO(t, uwave_switch, True)
        t += duration/2.0
    else:
        t += duration

    label(t, 'uwave end')
    HSDIO(t, uwave_switch, False)
    t += 0.001
    HSDIO(t, horn_switch, False)
    return t


################################################################################
# MONITOR#######################################################################
################################################################################


def monitor(t, duration):
    """Monitor laser powers for feedback"""
    label(t, 'monitor start')
    phase = 'mon'
    ts = []
    settle_time = 0.15

    # Rb power first
    ts.append(RB_D2_DDS(t, phase))
    ts.append(CS_D2_DDS(t, 'off'))
    ts.append(FORT_DDS(t, 'on'))
    t = max(ts)
    t += settle_time  # settling time
    HSDIO(t, HSDIO_channels['ne_adc_trig_0']['channel'], True)
    t += (duration - 3*settle_time)/3

    # Cs power second
    ts.append(RB_D2_DDS(t, 'off'))
    ts.append(CS_D2_DDS(t, phase))
    t = max(ts)
    t += settle_time
    HSDIO(t, HSDIO_channels['ne_adc_trig_1']['channel'], True)
    t += (duration - 3*settle_time)/3

    # Both HF only for background subtraction
    ts.append(RB_D2_DDS(t, 'off'))
    ts.append(CS_D2_DDS(t, 'off'))
    t = max(ts)
    t += settle_time
    HSDIO(t, HSDIO_channels['ne_adc_trig_1']['channel'], False)
    t += (duration - 3*settle_time)/3

    ts.append(RB_D2_DDS(t, 'mot'))
    ts.append(CS_D2_DDS(t, 'mot'))  # only do feedback for Rb right now
    ts.append(FORT_DDS(t, 'on'))
    t = max(ts)

    HSDIO(t, HSDIO_channels['ne_adc_trig_0']['channel'], False)
    label(t, 'monitor end')
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

    t = fort_readout(t, readout_780 + exra_readout_780, parallel_cnt=True, s1=False)
    t = drop_mot(t, 0.01)
    # t = pgc(t, post_read_pgc_time, no_chop=False, bphase='pgc_post', fphase='on', phase='pgc2', chop_cooling=False)
    t = pgc(t, post_read_pgc_time, no_chop=False, bphase='pgc_post', fphase='on', phase='pgc2', chop_cooling=True)

    # close shutter for Mxy beam
    # wait for the shutter switch time so we dont turn off during pgc
    shutter_wait = max([MXY_shutter_time_ms, RB_HF_shutter_time_ms, CS_HF_shutter_time_ms, M_shutter_time_ms])
    t = drop_mot(t, shutter_wait)
    MXY_shutter(t+2.5, False)
    if SSRO:
        HF_shutter(t, False)
    MZ2_shutter(t-1, False)
    # dont close shutters since it limits gap_time and doesnt appear to be limiting depumping
    # if not depump_hf:
    #     M_shutter(t, False)
    # turn on OP
    OP_shutter(t-4.5, True)
    op_shutter_t = t + 3.1
    # FORT_DDS(t-0.005, 'high')
    t = optical_pumping(t, op_time_ms, fphase='on')
    # FORT_DDS(t+0.01, 'on')
    t = max(t+2.5, op_shutter_t)
    OP_shutter(t-1, False)

    if p_heating:
        t = parametric_heating(t, p_heating_duration, p_heating_freq)

    # wait the remainder of the gap time
    FORT_DDS(t, 'high')
    t -= 2
    if depump_hf:
        FORT_DDS(t, 'on')
        t = depump(t, 2)
        FORT_DDS(t, 'high')
        t = drop_mot(t, gap_time*0.75 - shutter_wait-2, b_phase='expt')
    else:
        t = drop_mot(t, gap_time*0.75 - shutter_wait, b_phase='expt')

    # mot with no HF pumps into F=1
    t_adj = max(rb_uwave_time_ms, cs_uwave_time_ms)
    t_adj -= 0.5 - max(rb_uwave_gap_time_ms, cs_uwave_gap_time_ms)

    if False and depump_hf:
        switch_time = 0.1  # time to wait to avoid grey code error
        t = depump(t, gap_time*0.25 - t_adj - switch_time)
        # FORT_DDS(t, 'on')
        t = drop_mot(t, switch_time, b_phase='expt')
    else:
        t = drop_mot(t, 0.5, b_phase='expt')
        t = drop_mot(t, gap_time*0.25 - t_adj, b_phase='expt')
    t += 2

    # t = expmnt(t, pulse_459, fphase='low', exp_type='blue_align', drop=False, min_drop=6, min_time=5)
    t = expmnt(t, fort_drop_us/1000, fphase='on', exp_type='fdrop')
    t += 0.001
    t = uwave_rotation(t, rb_uwave_time_ms, gap=uwave_gap_time_ms, atom='rb', fort_phase='high')
    t += 0.01
    t = uwave_rotation(t, cs_uwave_time_ms, gap=uwave_gap_time_ms, atom='cs', fort_phase='high')
    t += 0.1
    FORT_DDS(t, 'high')

    if test_mz_readout:
        t = fort_readout(t, test_mz_readout_duration, mz_only=True, count=False)

    # dont close shutters since it limits gap_time and doesnt appear to be limiting depumping
    # if not depump_hf:
    #     M_shutter(t-2.3, True)
    # t += 1.
    t = fort_readout(t, readout_780 + exra_readout_780, parallel_cnt=True, s1=False)
    # t = fort_readout(t, readout_780, mz_only=True, parallel_cnt=True, s1=True, fphase='high')
    # open shutter for mz readout
    # open shutter for Mxy beam
    MXY_shutter(t-2+3.5*0+1+1, True)  # fudge
    if SSRO:
        HF_shutter(t + 0.6-3*0, True)
    # MZ2_shutter(t-7.35, True)
    MZ2_shutter(t, True)

    t += 2.5
    t = monitor(t, 2)  # 2 ms of monitor

    if dump_fort_at_end:
        t += 0.15
        FORT_DDS(t, 'off')
        t += 0.5
        FORT_DDS(t, 'on')
        t += 0.15
    else:
        t += 0.8
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


def mot_tof_experiment():
    # HSDIO initialization
    t = 0
    t = init(t)
    # load mot
    t = mot_loading(t, cycle_time-2*readout_780-pgc_time-drop_time-5)
    t = mot_spcm_readout(t, readout_780)
    t += 0.1
    t = pgc(t, pgc_time, no_chop=True)
    t = drop_mot(t, drop_time)
    # set the aoms to the near resonance
    t = pgc(t, 0.001, phase='mot', no_chop=True)
    HSDIO(t, HSDIO_channels['scope_trig_1']['channel'], True)
    HSDIO(t, HSDIO_channels['luca_trig_1']['channel'], True)
    t = mot_spcm_readout(t, readout_780)
    HSDIO(t, HSDIO_channels['luca_trig_1']['channel'], False)
    HSDIO(t, HSDIO_channels['scope_trig_1']['channel'], False)
    t = drop_mot(t, 0.01)
    print t
    t = cycle_time
    t = init(t)
    print "actual(requested) cycle time {}({}) ms".format(t, cycle_time)


# CW MOT
def mot_grad_toggle_experiment():
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
    t = cycle_time/2.

    for chan in Bfields['pgc']:
        AO(t, Bfield_channels[chan]['channel'], Bfields['pgc'][chan]['voltage'])
    AO(t, Bfield_channels['Bq1']['channel'], 0.5)
    AO(t, Bfield_channels['Bq2']['channel'], 0.5)

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
    mot_tof_exp: mot_tof_experiment,
    mot_gtoggle_exp: mot_grad_toggle_experiment,
}

# Experiment type switch
exps[exp_type]()
