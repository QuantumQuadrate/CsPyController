import datetime
import numpy as np
import logging
import os
import time
from multiprocessing import Pool
from histogram_analysis_helpers import calculate_histogram, histogram_grid_plot, save_fig
# MPL plotting
import matplotlib as mpl


from atom.api import Bool, Member, Str, observe, Int, List

from analysis import AnalysisWithFigure, ROIAnalysis

logger = logging.getLogger(__name__)
mpl.use('PDF')


class HistogramAnalysis(AnalysisWithFigure):
    """This class live updates a histogram as data comes in."""
    enable = Bool()
    all_shots_array = Member()
    update_lock = Bool(False)
    list_of_what_to_plot = Str()
    ROI_source = Member()

    def __init__(self, name, experiment, description=''):
        super(HistogramAnalysis, self).__init__(name, experiment, description)

        # point analysis at the roi sum source
        self.ROI_source = getattr(
            self.experiment,
            self.experiment.Config.config.get('CAMERA', 'HistogramROISource')
        )

        self.properties += ['enable', 'list_of_what_to_plot', 'ROI_source']
        self.queueAfterMeasurement = True
        self.measurementDependencies += [self.ROI_source]

    def preIteration(self, iteration_results, experiment_results):
        # reset the histogram data
        self.all_shots_array = None

    def analyzeMeasurement(self, measurement_results, iteration_results, experiment_results):
        if self.enable:
            # every measurement, update a big array of all the ROI sums, then
            # histogram only the requested shot/site
            d = measurement_results[self.ROI_source.meas_analysis_path]
            if self.all_shots_array is None:
                self.all_shots_array = np.array([d])
            else:
                self.all_shots_array = np.append(
                    self.all_shots_array,
                    np.array([d]),
                    axis=0
                )
            self.updateFigure()

    @observe('list_of_what_to_plot')
    def reload(self, change):
        if self.enable:
            self.updateFigure()

    def updateFigure(self):
        if self.draw_fig:
            if not self.update_lock:
                try:
                    self.update_lock = True
                    fig = self.backFigure
                    fig.clf()

                    if ((self.all_shots_array is not None) and
                            (len(self.all_shots_array) > 1)):

                        # parse the list of what to plot from a string to a
                        # list of numbers
                        try:
                            plotlist = eval(self.list_of_what_to_plot)
                        except Exception:
                            msg = 'Couldnt eval plotlist in HistogramAnalysis'
                            logger.exception(msg)
                            return

                        ax = fig.add_subplot(111)
                        shots = [i[0] for i in plotlist]
                        rois = [i[1] for i in plotlist]
                        data = self.all_shots_array[:, shots, 0, rois]
                        bins = int(1.2 * np.rint(np.sqrt(len(data))))
                        labels = [
                            '({},{})'.format(i[0], i[1]) for i in plotlist
                        ]
                        ax.hist(
                            data,
                            bins,
                            histtype='step',
                            label=labels
                        )
                        ax.legend()
                    super(HistogramAnalysis, self).updateFigure()
                except Exception:
                    msg = 'Problem in HistogramAnalysis.updateFigure()'
                    logger.exception(msg)
                finally:
                    self.update_lock = False


class HistogramGrid(ROIAnalysis):
    """This class gives a big histogram grid with 0 and 1 atom cutoffs after
    every iteration.
    """
    enable = Bool()
    all_shots_array = Member()
    histogram_results = Member()
    shot = Int()
    pdf_path = Member()
    bins = Member()
    calculate_new_cutoffs = Bool()
    automatically_use_cutoffs = Bool()
    cutoff_shot_mapping = Str()
    cutoffs_from_which_experiment = Str()
    ROI_source = Member()
    figures = Member()  # stores figures for each shot from the last iteration
    pool = Member()

    def __init__(self, name, experiment, description=''):
        super(HistogramGrid, self).__init__(name, experiment, description)
        # point analysis at the roi sum source
        self.ROI_source = getattr(
            self.experiment,
            self.experiment.Config.config.get('CAMERA', 'HistogramROISource')
        )
        self.properties += [
            'enable', 'shot', 'calculate_new_cutoffs', 'camera',
            'automatically_use_cutoffs', 'cutoff_shot_mapping', 'ROI_source'
        ]
        self.queueAfterMeasurement = True
        self.measurementDependencies += [self.ROI_source]
        self.figures = []
        self.pool = Pool(2)

    def set_rois(self):
        pass

    def fromHDF5(self, hdf):
        super(HistogramGrid, self).fromHDF5(hdf)
        self.find_camera()

    def preExperiment(self, experiment_results):
        # call threading setup code
        super(HistogramGrid, self).preExperiment(experiment_results)

        if self.enable and self.experiment.saveData:
            # create the nearly complete path name to save pdfs to.
            # The iteration and .pdf will be appended.
            pdf_path = os.path.join(self.experiment.path, 'pdf')
            if not os.path.exists(pdf_path):
                os.mkdir(pdf_path)
            self.pdf_path = os.path.join(
                pdf_path,
                '{}_histogram_grid'.format(self.experiment.experimentPath)
            )

    def analyzeIteration(self, iteration_results, experiment_results):
        if self.enable:
            # all_shots_array will be shape (measurements,shots,rois)
            # or (measurements, sub-measurements shots, rois)
            data_path = self.ROI_source.iter_analysis_path
            all_shots_array = iteration_results[data_path].value
            # flatten sub-measurements
            if len(all_shots_array.shape) == 4:
                all_shots_array = all_shots_array.reshape(-1, *all_shots_array.shape[2:])

            # perform histogram calculations and fits on all shots and regions
            self.calculate_all_histograms(all_shots_array)

            if self.automatically_use_cutoffs:
                self.use_cutoffs()

            # save data to hdf5
            # convert histogram results back to custom numpy dataset
            data_path = 'analysis/histogram_results'
            iteration_results[data_path] = self.convert_histogram_results()

            # make the histograms and save them, updates figure asynchronously when all figs are done
            self.make_figures(iteration_results.attrs['iteration'])

    def convert_histogram_results(self):
        """Rework new histogram data format so it doesn't break dependent analyses."""
        hist_dtype = np.dtype([
            ('histogram', str(self.bins) + 'i4'),
            ('bin_edges', str(self.bins+1) + 'f8'),
            ('error', 'f8'),
            ('mean1', 'f8'),
            ('mean2', 'f8'),
            ('width1', 'f8'),
            ('width2', 'f8'),
            ('amplitude1', 'f8'),
            ('amplitude2', 'f8'),
            ('cutoff', 'f8'),
            ('loading', 'f8'),
            ('overlap', 'f8'),
            ('poisson', 'bool_')  # length 25 string for specifying the type of fit (new 5/2018)
        ])
        shots = len(self.histogram_results)
        rois = len(self.histogram_results[0])
        results = np.empty((shots, rois), dtype=hist_dtype)
        results.fill(0)
        for s, shot in enumerate(self.histogram_results):
            for r, roi in enumerate(shot):
                a2, m1, m2 = roi['fit_params'][:3]
                a1 = 1.0 - a2
                if roi['method'] == "poisson":
                    w1 = np.sqrt(m1)
                    w2 = np.sqrt(m2)
                    poisson = True
                else:
                    w1, w2 = roi['fit_params'][3:5]
                    poisson = False
                results[s, r] = (
                    roi['hist_y'],
                    roi['hist_x'],
                    np.nan,  # I haven't calculated the fit residuals yet
                    m1,
                    m2,
                    w1,
                    w2,
                    a1,
                    a2,
                    roi['cuts'][0],
                    roi['loading'],
                    roi['overlap'],
                    poisson
                )
        return results

    @observe('shot')
    def refresh(self, change):
        if self.enable:
            self.updateFigure()

    def make_figures(self, iteration):
        try:
            pe = self.ROI_source.photoelectronScaling.value
            ex = self.ROI_source.exposureTime.value
        except AttributeError:
            pe = None
            ex = None
        # clean old figures out of memory
        for f in self.figures:
            f.clf()
        self.figures = []
        # hist_data_shots = []
        for shot in range(len(self.histogram_results)):
            self.figures.append(None)
            hist_data = {
                'dpi': 80,
                'font': 8,
                'log': False,
                'iteration': iteration,
                'shot': shot,
                'roi_rows': self.experiment.ROI_rows,
                'roi_columns': self.experiment.ROI_columns,
                'hist_data': self.histogram_results[shot],
                'cutoff_source': self.cutoffs_from_which_experiment,
                'save_path': self.pdf_path,
                'experiment_path': self.experiment.experimentPath,
                'scaling': pe,
                'exposure_time': ex,
                'meas_per_iteration': self.experiment.measurementsPerIteration,
                'save': self.experiment.saveData
            }
            # create new figures in parallel asynchronous processes
            self.pool.apply_async(histogram_grid_plot, args=(hist_data, ), callback=self.add_shot_figure)

    def add_shot_figure(self, result):
        """Add figure to figure list when calculations are complete.

        When all figures are done update the figure.
        """
        logger.info('completed shot {}'.format(result['shot']))
        self.figures[result['shot']] = result['fig']
        # start new process to save file here because if we save in the other process
        # it adds an instance method to the figure object and it can no longer be pickled
        logger.info('starting save process for shot: {}'.format(result['shot']))
        self.pool.apply_async(save_fig, args=(result, ))
        # check to see if all figures are completed
        for f in self.figures:
            if f is None:
                return  # still working
        logger.info('done with all shots')
        # update the figure to show the histograms for the selected shot
        self.updateFigure()

    def updateFigure(self):
        if self.draw_fig:
            try:
                # self.backFigure.clf()  # clear figure
                # set figure
                self.backFigure = self.figures[self.shot]
                super(HistogramGrid, self).updateFigure()
            except IndexError:
                logger.error('No histogram figure for shot: `{}`'.format(self.shot))
            except Exception:
                logger.exception('Problem in HistogramGrid.updateFigure()')

    def use_cutoffs(self):
        """Set the cutoffs.

        Because they are stored in a np field, but we need to set them using
        a deferred_call, the whole ROI array is first copied, then updated,
        then written back to the squareROIAnalysis or gaussian_roi.
        """

        experiment_timestamp = datetime.datetime.fromtimestamp(
            self.experiment.timeStarted
        ).strftime('%Y_%m_%d_%H_%M_%S')

        # register the new cutoffs with threshold analysis
        shots = len(self.histogram_results)
        rois = len(self.histogram_results[0])
        cuts = np.zeros((shots, rois), dtype='int')
        for s in range(shots):
            for r in range(rois):
                try:
                    cuts[s, r] = self.histogram_results[s][r]['cuts'][0]
                except OverflowError:
                    logger.error('overflow error occured with cut[{}][{}]: {}'.format(s, r, self.histogram_results[s][r]['cuts'][0]))
        self.experiment.thresholdROIAnalysis.set_thresholds(cuts, experiment_timestamp)

    def calculate_all_histograms(self, all_shots_array):
        """Calculate histograms and thresholds for each shot and roi"""
        measurements, shots, rois = all_shots_array.shape

        # Since the number of measurements is the same for each shot and roi,
        # we can compute the number of bins here:
        # choose 1.5*sqrt(N) as the number of bins
        self.bins = int(np.rint(1.5 * np.sqrt(measurements)))
        # use the same structure for histogram_results and roi_data so mapping is easy
        self.histogram_results = [[None for r in range(rois)] for s in range(shots)]
        roi_data = [[None for r in range(rois)] for s in range(shots)]

        # go through each shot and roi and format for a multiprocessing pool
        start = time.time()
        for shot in range(shots):
            for roi in range(rois):
                # get old cutoffs
                cutoff = self.experiment.thresholdROIAnalysis.threshold_array[shot][roi]['1']
                backup_cut = None
                if self.calculate_new_cutoffs:
                    backup_cut = cutoff
                    cutoff = None
                # get the data
                roi_data[shot][roi] = {
                    'data': all_shots_array[:, shot, roi],
                    'cutoff': cutoff,
                    'backup_cutoff': backup_cut,
                    'bins': self.bins,
                    'shot': shot,
                    'roi': roi
                }
        # create the pool and start the job, separate by shot (could also flatten...)
        for shot in range(shots):
            self.histogram_results[shot] = self.pool.map(calculate_histogram, roi_data[shot])
        logger.debug("hist fit time: {:.3f} s".format(time.time() - start))

        # make a note of which cutoffs were used
        if self.calculate_new_cutoffs:
            exp_time = datetime.datetime.fromtimestamp(
                self.experiment.timeStarted
            )
            fmt = '%Y_%m_%d_%H_%M_%S'
            self.cutoffs_from_which_experiment = exp_time.strftime(fmt)
        else:
            try:
                self.cutoffs_from_which_experiment = self.ROI_source.cutoffs_from_which_experiment
            except AttributeError:
                logger.warning('Unknown cutoff source')

    def gaussian1D(self, x, x0, a, w):
        """returns the height of a gaussian (with mean x0, amplitude, a and
        width w) at the value(s) x
        """
        # normalize
        g = a/(w*np.sqrt(2*np.pi))*np.exp(-0.5*(x-x0)**2/w**2)
        g[np.isnan(g)] = 0  # eliminate bad elements
        return g

    def two_gaussians(self, x, x0, a0, w0, x1, a1, w1):
        return self.gaussian1D(x, x0, a0, w0) + self.gaussian1D(x, x1, a1, w1)

    def analytic_cutoff(self, x1, x2, w1, w2, a1, a2):
        """Find the cutoffs analytically.  See MTL thesis for derivation."""
        return np.where(
            w1 == w2,
            self.intersection_of_two_gaussians_of_equal_width(x1, x2, w1, w2, a1, a2),
            self.intersection_of_two_gaussians(x1, x2, w1, w2, a1, a2)
        )

    def intersection_of_two_gaussians_of_equal_width(self, x1, x2, w1, w2, a1, a2):
        return (- x1**2 + x2**2 + w1**2/2*np.log(a1/a2))/(2*(x2-x1))

    def intersection_of_two_gaussians(self, x1, x2, w1, w2, a1, a2):
        a = w2**2*x1 - w1**2*x2
        # TODO: protect against imaginary root
        b = w1*w2*np.sqrt((x1-x2)**2 + (w2**2 - w1**2)*np.log(a1/a2)/2.0)
        c = w2**2 - w1**2
        return (a+b)/c  # use the positive root, as that will be the one between x1 and x2
