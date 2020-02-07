import pytest
import numpy as np
import histogram_analysis_helpers as hah

# make repeatable
np.random.seed(seed=0)


def default_settings(r=0.4, meas=300):
    n1 = int(r * meas)
    n0 = meas - n1
    a, b = 10., 20.  # background, atom signal, loading rate
    return {
        'm0': a, 'm1': a + b,
        's0': np.sqrt(a), 's1': np.sqrt(a + b),
        'r': r,
        'n0': n0, 'n1': n1,
        'cut_guess': hah.intersection('gaussian', (r, a, a + b, np.sqrt(a), np.sqrt(b)))
    }


def data_gen(settings):
    # we are binning so order doesnt matter
    return np.concatenate(
        (
            np.random.normal(loc=settings['m0'], scale=settings['s0'], size=settings['n0']),
            np.random.normal(loc=settings['m1'], scale=settings['s1'], size=settings['n1'])
        ),
        axis=None
    )


def assert_signal_schema(params, method='gaussian'):
    assert (len(params) == 5 if method == 'gaussian' else 3)
    assert (0 <= params[0] < 1)
    assert(params[1] < params[2])  # m0 < m1


def test_fit_distribution():
    settings = default_settings()

    for _ in range(100):
        raw_data = data_gen(settings)
        data = {
            'data': raw_data,
            'bins': int(1.5*np.sqrt(len(raw_data)))
        }
        result = hah.fit_distribution(data)
        # print(result)
        assert(result['method'] == 'gaussian')
        # print(result['cuts'][0] - cut_guess)
        assert(abs(result['cuts'][0] - settings['cut_guess']) < np.sqrt(settings['m1']))
        assert(len(result['hist_y']) == data['bins'])
        assert(len(result['hist_x']) == data['bins']+1)
        assert(len(result['cuts']) == result['max_atoms'])
        map(assert_signal_schema, [result['guess'], result['fit_params']])


def test_calculate_histogram_no_update():
    settings = default_settings()

    for _ in range(100):
        raw_data = data_gen(settings)
        data = {
            'data': raw_data,
            'bins': int(1.5*np.sqrt(len(raw_data))),
            'cutoff': settings['cut_guess'],
            'backup_cutoff': None
        }
        result = hah.calculate_histogram(data)
        assert(result['method'] == 'gaussian')
        assert(result['cuts'] == [data['cutoff']])
        assert(len(result['hist_y']) == data['bins'])
        assert(len(result['hist_x']) == data['bins'] + 1)
        assert(abs(result['loading'] - settings['r']) < 0.02)
        assert(abs(result['overlap'] - hah.overlap('gaussian', result['fit_params'], result['cuts'][0])) < 0.01)
        map(assert_signal_schema, [result['guess'], result['fit_params']])


def test_calculate_histogram_update():
    settings = default_settings()

    for _ in range(100):
        raw_data = data_gen(settings)
        data = {
            'data': raw_data,
            'bins': int(1.5*np.sqrt(len(raw_data))),
            'cutoff': None,
            'backup_cutoff': settings['cut_guess']
        }
        result = hah.calculate_histogram(data)
        assert(result['method'] == 'gaussian')
        assert(abs(result['cuts'][0] - data['backup_cutoff']) < 5)
        assert(len(result['hist_y']) == data['bins'])
        assert(len(result['hist_x']) == data['bins'] + 1)
        assert(abs(result['loading'] - settings['r']) < 0.065)
        assert(abs(result['overlap'] - hah.overlap('gaussian', result['fit_params'], result['cuts'][0])) < 0.01)
        map(assert_signal_schema, [result['guess'], result['fit_params']])
