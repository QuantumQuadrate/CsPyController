import pytest
import sys
import numpy as np
import h5py
import ConfigParser
from atom.api import Member, Int
import time
sys.path.append("..")
import experiments
import threshold_analysis


class TExperiment(experiments.Experiment):
    Config = Member()
    roi_analysis = Member()
    test_hdf5 = Member()
    ROI_columns = Int(1)
    ROI_rows = Int(1)


class TConfig(object):
    """Test config instrument class"""
    def __init__(self, shots_to_ignore=-1):
        self.config = ConfigParser.RawConfigParser()
        self.config.add_section('CAMERA')  # expecting "camera" data path
        self.config.set('CAMERA', 'ThresholdROISource', 'roi_analysis')
        # ignore shot?
        if shots_to_ignore >= 0:
            self.config.set('CAMERA', 'ShotsToIgnore', shots_to_ignore)


class TROISource(object):
    """Test ROI source object"""
    def __init__(self, h5):
        self.meas_analysis_path = 'data'
        self.test_hdf5 = h5

    def insert_measurement(self, settings):
        # insert fake data into test hdf5 file
        if 'sub_meas' in settings:
            data = np.full((settings['sub_meas'], settings['shots'], settings['ROI_rows'], settings['ROI_columns']), 1)
        else:
            data = np.full((settings['shots'], settings['ROI_rows'], settings['ROI_columns']), 1)
        self.test_hdf5['meas/'+self.meas_analysis_path] = data

    def insert_measurement_roi(self, settings):
        # insert fake data into test hdf5 file
        if 'sub_meas' in settings:
            data = np.full((settings['sub_meas'], settings['shots'], settings['ROI_rows'], settings['ROI_columns']), 1)
        else:
            data = np.full((settings['shots'], settings['ROI_rows'], settings['ROI_columns']), 1)
        # scale entry by roi
        for rr in range(settings['ROI_rows']):
            for rc in range(settings['ROI_columns']):
                if len(data.shape) == 3:
                    data[:, rr, rc] *= rr*settings['ROI_rows'] + rc
                else:
                    data[:, :, rr, rc] *= rr*settings['ROI_rows'] + rc
        self.test_hdf5['meas/'+self.meas_analysis_path] = data

    def insert_measurement_shot(self, settings):
        # insert fake data into test hdf5 file
        if 'sub_meas' in settings:
            data = np.full((settings['sub_meas'], settings['shots'], settings['ROI_rows'], settings['ROI_columns']), 1)
        else:
            data = np.full((settings['shots'], settings['ROI_rows'], settings['ROI_columns']), 1)
        # scale entry by roi
        for s in range(settings['shots']):
            if len(data.shape) == 3:
                data[s, :, :] *= s
            else:
                data[:, s, :, :] *= s
        self.test_hdf5['meas/'+self.meas_analysis_path] = data


@pytest.fixture()
def hdf5():
    """Create an hdf5 file in memory for testing"""
    i = 0
    while True:
        # I dont understand why the hdf5 file a) isnt staying memory only and b) not closing
        try:
            h5 = h5py.File('test_{}.hdf5'.format(i), 'w', driver='core', backing_store=False)
        except IOError:
            i += 1
        else:
            break
    h5.create_group('meas')
    h5.create_group('iter')

    def finalize():
        h5.close()

    return h5


@pytest.fixture()
def experiment(hdf5):
    """Instantiate an empty experiment object for a test"""
    texp = TExperiment()
    # set up a simple config file as expected
    texp.Config = TConfig()
    texp.roi_analysis = TROISource(hdf5)
    texp.test_hdf5 = hdf5
    return texp


@pytest.fixture()
def threshold(experiment):
    """Instantiate a threshold_analysis object for testing"""
    return threshold_analysis.ThresholdROIAnalysis(experiment)


def setup_threshold(thld, thld_val, **kwargs):
    thld.enable = True
    for key, value in kwargs.iteritems():
        if 'ROI_' in key:
            setattr(thld.experiment, key, value)
        else:
            try:
                setattr(thld, key, value)
            except:
                pass
    # need to reinitialize rois/thresholds
    thld.set_rois()
    ta = np.full((kwargs['ROI_rows']*kwargs['ROI_columns'], kwargs['shots']), thld_val)
    thld.set_thresholds(ta, 0)


@pytest.mark.parametrize('settings, thld_val', [
    ({'ROI_rows': 1, 'ROI_columns': 1, 'shots': 2}, 1),
    ({'ROI_rows': 1, 'ROI_columns': 1, 'shots': 2}, 2),
    ({'ROI_rows': 1, 'ROI_columns': 1, 'shots': 2, 'sub_meas': 1}, 1),
    ({'ROI_rows': 1, 'ROI_columns': 1, 'shots': 2, 'sub_meas': 4}, 2),
    ({'ROI_rows': 2, 'ROI_columns': 1, 'shots': 2}, 1),
    ({'ROI_rows': 2, 'ROI_columns': 2, 'shots': 2}, 2),
    ({'ROI_rows': 2, 'ROI_columns': 1, 'shots': 2, 'sub_meas': 1}, 1),
    ({'ROI_rows': 2, 'ROI_columns': 2, 'shots': 2, 'sub_meas': 4}, 2),
])
def test_analyze_meas(threshold, settings, thld_val):
    # push settings to threshold object
    print settings
    setup_threshold(threshold, thld_val, **settings)
    threshold.experiment.roi_analysis.insert_measurement(settings)
    threshold.analyzeMeasurement(threshold.experiment.test_hdf5['meas'], None, None)
    res = threshold.experiment.test_hdf5['meas/'+threshold.meas_analysis_path][()]
    rois = settings['ROI_columns']*settings['ROI_rows']
    sub_meas = 1
    if 'sub_meas' in settings:
        sub_meas = settings['sub_meas']
    assert(res.shape == (sub_meas, settings['shots'], rois))
    if thld_val > 1:
        assert(not np.any(res))
    else:
        assert(np.all(res))


@pytest.mark.parametrize('settings, thld_val', [
    ({'ROI_rows': 1, 'ROI_columns': 1, 'shots': 2}, 1),
    ({'ROI_rows': 1, 'ROI_columns': 1, 'shots': 2}, 2),
    ({'ROI_rows': 1, 'ROI_columns': 1, 'shots': 2, 'sub_meas': 1}, 1),
    ({'ROI_rows': 1, 'ROI_columns': 1, 'shots': 2, 'sub_meas': 4}, 2),
    ({'ROI_rows': 2, 'ROI_columns': 1, 'shots': 2}, 1),
    ({'ROI_rows': 2, 'ROI_columns': 2, 'shots': 2}, 2),
    ({'ROI_rows': 2, 'ROI_columns': 1, 'shots': 2, 'sub_meas': 1}, 1),
    ({'ROI_rows': 2, 'ROI_columns': 2, 'shots': 2, 'sub_meas': 4}, 2),
])
def test_analyze_meas_roi(threshold, settings, thld_val):
    # push settings to threshold object
    print settings
    setup_threshold(threshold, thld_val, **settings)
    threshold.experiment.roi_analysis.insert_measurement_roi(settings)
    threshold.analyzeMeasurement(threshold.experiment.test_hdf5['meas'], None, None)
    res = threshold.experiment.test_hdf5['meas/'+threshold.meas_analysis_path][()]
    rois = settings['ROI_columns']*settings['ROI_rows']
    sub_meas = 1
    if 'sub_meas' in settings:
        sub_meas = settings['sub_meas']
    assert(res.shape == (sub_meas, settings['shots'], rois))
    for r in range(rois):
        if thld_val > r:
            assert(not np.any(res[:, :, r]))
        else:
            assert(np.all(res[:, :, r]))


@pytest.mark.parametrize('settings, thld_val', [
    ({'ROI_rows': 1, 'ROI_columns': 1, 'shots': 2}, 1),
    ({'ROI_rows': 1, 'ROI_columns': 1, 'shots': 2}, 2),
    ({'ROI_rows': 1, 'ROI_columns': 1, 'shots': 2, 'sub_meas': 1}, 1),
    ({'ROI_rows': 1, 'ROI_columns': 1, 'shots': 2, 'sub_meas': 4}, 2),
    ({'ROI_rows': 2, 'ROI_columns': 1, 'shots': 5}, 1),
    ({'ROI_rows': 2, 'ROI_columns': 2, 'shots': 5}, 2),
    ({'ROI_rows': 2, 'ROI_columns': 1, 'shots': 5, 'sub_meas': 1}, 1),
    ({'ROI_rows': 2, 'ROI_columns': 2, 'shots': 5, 'sub_meas': 4}, 2),
])
def test_analyze_meas_shot(threshold, settings, thld_val):
    # push settings to threshold object
    print settings
    setup_threshold(threshold, thld_val, **settings)
    threshold.experiment.roi_analysis.insert_measurement_shot(settings)
    threshold.analyzeMeasurement(threshold.experiment.test_hdf5['meas'], None, None)
    res = threshold.experiment.test_hdf5['meas/'+threshold.meas_analysis_path][()]
    rois = settings['ROI_columns']*settings['ROI_rows']
    sub_meas = 1
    if 'sub_meas' in settings:
        sub_meas = settings['sub_meas']
    assert(res.shape == (sub_meas, settings['shots'], rois))
    for s in range(settings['shots']):
        if thld_val > s:
            assert(not np.any(res[:, s, :]))
        else:
            assert(np.all(res[:, s, :]))
