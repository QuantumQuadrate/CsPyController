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
        'p6': (0, 1, 1),
        'p7': (1, 1, 1)
    }
).profile

# FORT AOM profiles
FORT_DDS = DDS(
    HSDIO,
    (
        HSDIO_channels['fort_dds_p0']['channel'],
    ),
    {
        'on': (0,),
        'off': (1,),
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
# HSDIO STUFF ##################################################################
################################################################################


def chop(t, channels, phases, period):
    """Add a single cycle of a chopping pattern to the HSDIO transition list.

    If the phase for a channel is 0 it turns on at time t
    If the phase for a channel is 1>p>0 it turns on at time (t+period*phase)
    If the phase for a channel is 0>p>-1 it starts on and turns off at time (t + period*(1 + phase))

    channels is a list of channel numbers
    phases is a list of phases between -1 and 1 equal in length to the number of
        channels being switched
    period is the period of the cycle
    returns t + period
    """
    if len(channels) != len(phases):
        print "Chop function requries equal length lists of channels and phases"
        raise PauseError

    for i, c in enumerate(channels):
        p = phases[i]
        if abs(p) > 1:
            print "Chop function expects phases to be within abs(p)<=1"
            raise ValueError
        init_state = p < 0
        # if phase is negative substract from end of phase
        if init_state:
            p = 1 + p
        # put in initial value for the cycle
        msg = "ch[{}]: t({}) = {}"
        print(msg.format(c, 0, init_state))
        HSDIO(t, c, init_state)
        # put in transition
        print(msg.format(c, p, not init_state))
        HSDIO(t + (p * period), c, not init_state)
    return t + period


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
    # add repumper

    for chan in Bfields[phase]:
        AO(t, Bfield_channels[chan]['channel'], Bfields[phase][chan]['voltage'])

    t = max(ts)
    t += duration
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
    HSDIO(t, HSDIO_channels['scope_trig_1']['channel'], True)
    HSDIO(t + 1, HSDIO_channels['scope_trig_1']['channel'], False)

    HSDIO(t, HSDIO_channels['point_grey_1']['channel'], True)
    HSDIO(t + 1, HSDIO_channels['point_grey_1']['channel'], False)

    HSDIO(t, HSDIO_channels['luca_trig_1']['channel'], True)
    HSDIO(t + 1, HSDIO_channels['luca_trig_1']['channel'], False)
    ts.append(t + 1)

    t = max(ts)
    t += duration
    return t

################################################################################
# FORT READOUT #################################################################
################################################################################


def fort_readout(t, duration):
    """Image atom in FORT."""
    phase = 'read'
    label(t, 'readout prep')
    for chan in Bfields[phase]:
        AO(t, Bfield_channels[chan]['channel'], Bfields[phase][chan]['voltage'])

    # throwaway bins to clear counter
    for i in range(throwaway_bins-1):
        HSDIO(t, HSDIO_channels['spcm_gate_780']['channel'], True)
        HSDIO(t + 0.5*throwaway_bin_duration, HSDIO_channels['spcm_gate_780']['channel'], False)
        t += throwaway_bin_duration

    # start the readout
    label(t, 'readout')
    t_start = t

    # chop FORT and MOT out of phase
    cycles = int(duration*1000*readout_chop_freq_MHz)
    print cycles
    period_ms = 0.001/readout_chop_freq_MHz
    # brute force
    for c in xrange(cycles):
        # MOT on FORT off
        RB_D2_DDS(t, 'read')
        FORT_DDS(t, 'off')
        # MOT off FORT on
        RB_D2_DDS(t + period_ms/2, 'off')
        FORT_DDS(t + period_ms/2, 'on')
        t += period_ms
    # channels = [RB_D2_DDS, FORT_DDS]
    # phases = [[0.05, 0.65], [0.35, 0.55]]
    # profiles = [
    #     ['read', 'off', 'read'],
    #     ['on', 'on', 'off']
    # ]
    # t = HSDIO_repeat(
    #     t,
    #     chop_dds(channels, phases, profiles, period_ms),
    #     cycles
    # )



    # record end times
    ts = [t]
    
    # send real timing pulses to counter
    t = t_start
    for i in range(measurement_bins):
        HSDIO(t + i*duration, HSDIO_channels['spcm_gate_780']['channel'], True)
        HSDIO(t + i*duration, HSDIO_channels['scope_trig_1']['channel'], True)
        HSDIO(t + (i+0.5)*duration, HSDIO_channels['spcm_gate_780']['channel'], False)
        HSDIO(t + (i+0.5)*duration, HSDIO_channels['scope_trig_1']['channel'], False)
        t += duration

    HSDIO(t, HSDIO_channels['spcm_gate_780']['channel'], True)
    HSDIO(t + 0.5*throwaway_bin_duration, HSDIO_channels['spcm_gate_780']['channel'], False)
    t += throwaway_bin_duration

    ts.append(t)
    t = max(ts)
    return t

################################################################################
# TIMINGS ######################################################################
################################################################################


# HSDIO initialization
for chan in range(32):
    HSDIO(0, chan, False)
    HSDIO(cycle_time, chan, False)

t = 0

# load mot
t = mot_loading(t, mot_time)
t = pgc(t, pgc_time)
t = drop_mot(t, drop_time)

for i in range(2):
    t = fort_readout(t, readout_780)
    t = drop_mot(t, 10)

################################################################################
# ERROR CHECKING################################################################
################################################################################

if t > cycle_time:
    print "Calculated cycle time ({} ms) exceeds specified cycle time ({} ms)".format(t, cycle_time)
    raise PauseError
