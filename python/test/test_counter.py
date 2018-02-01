import pytest
import sys
import numpy as np
import h5py
sys.path.append("..")
import experiments
import Counter


dpath = 'data/counter/data'
apath = 'analysis/counter_data'


@pytest.fixture()
def experiment():
    """Instantiate an empty experiment object for a test"""
    return experiments.Experiment()


@pytest.fixture()
def counter(experiment):
    """Instantiate a counter object for a test"""
    return Counter.CounterAnalysis("counter", experiment, 'test')


@pytest.fixture()
def hdf5():
    """Create an hdf5 file in memory for testing"""
    try:
        h5 = h5py.File('test.hdf5', 'w', driver='core', backing_store=False)
    except IOError:
        h5 = h5py.File('test1.hdf5', 'w', driver='core', backing_store=False)
    h5.create_group('meas')
    h5.create_group('iter')

    def finalize():
        print 'deleting'
        h5.close()

    return h5


def setup_counter(counter, **kwargs):
    counter.meas_analysis_path = apath
    counter.meas_data_path = dpath
    counter.enable = True
    for key, value in kwargs.iteritems():
        setattr(counter, key, value)
    data_template = [0]*kwargs['drops'] + [1]*kwargs['bins']
    counter.preIteration(None, None)
    return data_template


def constant_data(settings, const=1):
    return {
        'data': np.array([
            settings['template']*settings['shots']*settings['meas_per_meas'] for r in range(settings['rois'])
        ], dtype=np.uint32)*const,
        'sum': np.sum(settings['template'])*const
    }


def insert_measurement(cntr, meas_res, settings, data_func=constant_data, **kwargs):
    # insert into hdf5 file
    d = data_func(settings, **kwargs)
    meas_res[dpath] = d['data']
    cntr.analyzeMeasurement(meas_res, None, None)
    # check that we get the summed data output in the hdf5 file
    result = meas_res[apath][()]
    # check the shape
    assert(result.shape == (settings['meas_per_meas'], settings['shots'], settings['rois'], 1))
    # check the sum
    assert(np.all(result == d['sum']))


@pytest.mark.parametrize('settings, meas, rois', [
    ({'shots': 2, 'drops': 3, 'bins': 25}, 1, 2),
    ({'shots': 2, 'drops': 3, 'bins': 1}, 1, 5),
    ({'shots': 2, 'drops': 3, 'bins': 40}, 3, 1),
    ({'shots': 1, 'drops': 3, 'bins': 40}, 3, 3),
])
def test_format_data(counter, settings, meas, rois):
    # push settings to counter object
    data_template = setup_counter(counter, **settings)
    # first test that no drop bins show up in the data
    test_data = np.array([
        data_template*settings['shots']*meas for r in range(rois)
    ], dtype=np.uint32)
    result = counter.format_data(test_data)
    assert(result.shape == (meas, settings['shots'], rois, settings['bins']))
    assert(np.all(result == 1))

    # next test that roi data shows up in the right place, mark data from each roi
    # with a different number
    test_data = np.array([
        np.array(data_template*settings['shots']*meas)*(r+1) for r in range(rois)
    ], dtype=np.uint32)
    result = counter.format_data(test_data)
    assert(result.shape == (meas, settings['shots'], rois, settings['bins']))
    for r in range(rois):
        assert(np.all(result[:, :, r] == r+1))

    # next test that measurement data shows up in the right place, mark data from each
    # measurement with a different number
    test_data = np.array([
        np.array([np.array(data_template*settings['shots'])*(m+1) for m in range(meas)]).flatten()
        for r in range(rois)
    ], dtype=np.uint32)
    result = counter.format_data(test_data)
    assert(result.shape == (meas, settings['shots'], rois, settings['bins']))
    for m in range(meas):
        assert(np.all(result[m] == m+1))

    # next test that shot data shows up in the right place, mark data from each
    # shot with a different number
    test_data = np.array([
        np.array([np.array(data_template)*(s+1) for s in range(settings['shots'])]).flatten().tolist()*meas
        for r in range(rois)
    ], dtype=np.uint32)
    result = counter.format_data(test_data)
    assert(result.shape == (meas, settings['shots'], rois, settings['bins']))
    for s in range(settings['shots']):
        assert(np.all(result[:, s] == s+1))


@pytest.mark.parametrize('settings, meas, rois', [
    ({'shots': 2, 'drops': 3, 'bins': 25}, 1, 2),
    ({'shots': 2, 'drops': 3, 'bins': 1}, 1, 5),
    ({'shots': 2, 'drops': 3, 'bins': 40}, 3, 1),
    ({'shots': 1, 'drops': 3, 'bins': 40}, 3, 3),
])
def test_analyze_meas(counter, hdf5, settings, meas, rois):
    # push settings to counter object
    data_template = setup_counter(counter, **settings)
    settings['meas_per_meas'] = meas
    settings['rois'] = rois
    settings['template'] = data_template
    insert_measurement(counter, hdf5['meas'], settings)


@pytest.mark.parametrize('settings, meas, rois', [
    ({'shots': 2, 'drops': 3, 'bins': 25}, 1, 2),
    ({'shots': 2, 'drops': 3, 'bins': 1}, 1, 5),
    ({'shots': 2, 'drops': 3, 'bins': 40}, 3, 1),
    ({'shots': 1, 'drops': 3, 'bins': 40}, 3, 3),
])
def test_analyze_iter(counter, hdf5, settings, meas, rois):
    # push settings to counter object
    data_template = setup_counter(counter, **settings)
    meas_per_iter = 10
    settings['meas_per_meas'] = meas
    settings['rois'] = rois
    settings['template'] = data_template
    for i in range(meas_per_iter):
        mr = hdf5['meas'].create_group(str(i))
        insert_measurement(counter, mr, settings, const=(i+1))
    counter.analyzeIteration(hdf5['iter'], None)
    result = hdf5['iter/shotData'][()]
    assert(result.shape == (meas_per_iter, meas, settings['shots'], rois))
    for i in range(meas_per_iter):
        assert(np.all(result[i] == (i+1)*settings['bins']))
