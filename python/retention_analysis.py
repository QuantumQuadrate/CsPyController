import logging
import numpy as np
from atom.api import Bool, Str, Member, observe

from analysis import AnalysisWithFigure, Analysis

logger = logging.getLogger(__name__)


class RetentionAnalysis(Analysis):

    # Text output that can be updated back to the GUI
    enable = Bool()
    text = Str()

    def __init__(self, name, experiment, description=''):
        super(RetentionAnalysis, self).__init__(name, experiment, description)
        self.properties += ['enable', 'text']

    def analyzeIteration(self, iterationResults, experimentResults):
        if self.enable:
            self.retention(iterationResults)

    def retention(self, iter_res):
        # thresholdROI iteration data path
        th_path = self.experiment.thresholdROIAnalysis.iter_analysis_path
        atoms = iter_res[th_path][()]
        total = atoms.shape[0]
        # find the loading for each roi
        loaded = np.sum(atoms[:, 0, :], axis=0)
        # find the retention for each roi
        retained = np.sum(np.logical_and(
            atoms[:, 0, :],
            atoms[:, 1, :]
        ), axis=0)
        # find the number of reloaded atoms
        reloaded = np.sum(np.logical_and(
            np.logical_not(atoms[:, 0, :]),
            atoms[:, 1, :]
        ), axis=0)

        loading = loaded.astype('float') / total

        retention = retained.astype('float') / loaded
        # find the 1 sigma confidence interval for binomial data using the
        # normal approximation:
        # http://en.wikipedia.org/wiki/Binomial_proportion_confidence_interval
        retention_sigma = np.sqrt(retention * (1 - retention) / loaded)
        reloading = reloaded.astype('float') / total

        rows = self.experiment.ROI_rows
        columns = self.experiment.ROI_columns
        # write results to string
        text = 'total: ' + str(total) + '\n\n'
        text += 'loading:\tmax {:.3f},\tavg {:.3f}\n'.format(
            np.nanmax(loading),
            np.nanmean(loading)
        )
        text += '\n'.join(['\t'.join(
            map(
                lambda x: '{:.3f}'.format(x),
                loading[row * columns:(row + 1) * columns]
            )
        ) for row in xrange(rows)]) + '\n\n'
        text += 'retention:\tmax {:.3f},\tavg {:.3f}\n'.format(
            np.nanmax(retention),
            np.nanmean(retention)
        )
        text += '\n'.join(['\t'.join(
            map(
                lambda x: '{:.3f}'.format(x),
                retention[row * columns:(row + 1) * columns]
            )
        ) for row in xrange(rows)]) + '\n\n'
        text += 'reloading:\tmax {:.3f},\tavg {:.3f}\n'.format(
            np.nanmax(reloading),
            np.nanmean(reloading)
        )
        text += '\n'.join(['\t'.join(
            map(
                lambda x: '{:.3f}'.format(x),
                reloading[row * columns:(row + 1) * columns]
            )
        ) for row in xrange(rows)]) + '\n'

        iter_res['analysis/loading_retention/loaded'] = loaded
        iter_res['analysis/loading_retention/retained'] = retained
        iter_res['analysis/loading_retention/reloaded'] = reloaded
        iter_res['analysis/loading_retention/loading'] = loading
        iter_res['analysis/loading_retention/retention'] = retention
        iter_res['analysis/loading_retention/retention_sigma'] = retention_sigma
        iter_res['analysis/loading_retention/reloading'] = reloading
        iter_res['analysis/loading_retention/text'] = text
        iter_res['analysis/loading_retention/atoms'] = atoms

        self.set_gui({'text': text})


class RetentionGraph(AnalysisWithFigure):
    """Plots the average of a region of interest sum for an iteration."""

    enable = Bool()
    mean = Member()
    sigma = Member()
    current_iteration_data = Member()
    update_lock = Bool(False)
    list_of_what_to_plot = Str()
    draw_connecting_lines = Bool()
    draw_error_bars = Bool()
    add_only_filtered_data = Bool()
    ymin = Str()
    ymax = Str()

    def __init__(self, name, experiment, description=''):
        super(RetentionGraph, self).__init__(name, experiment, description)
        self.properties += [
            'enable', 'list_of_what_to_plot', 'draw_connecting_lines',
            'draw_error_bars', 'ymin', 'ymax'
        ]
        # threading stuff
        # self.queueAfterMeasurement = True
        # self.measurementDependencies += [self.experiment.retention_analysis]

    def preExperiment(self, experimentResults):
        # erase the old data at the start of the experiment
        self.mean = None
        self.sigma = None

    def preIteration(self, iterationResults, experimentResults):
        self.current_iteration_data = None

    def analyzeIteration(self, iterationResults, experimentResults):
        if self.enable:
            # check to see if retention analysis was done
            if 'analysis/loading_retention' in iterationResults:
                # load retention, and pad arrays with an extra dimension so
                # they can be concatenated
                retention = iterationResults['analysis/loading_retention/retention'].value[np.newaxis]
                sigma = iterationResults['analysis/loading_retention/retention_sigma'].value[np.newaxis]
                if self.mean is None:
                    # on first iteration start anew
                    self.mean = retention
                    self.sigma = sigma
                else:
                    # append
                    self.mean = np.append(self.mean, retention, axis=0)
                    self.sigma = np.append(self.sigma, sigma, axis=0)
                self.updateFigure()

    def analyzeMeasurement(self, measurementResults, iterationResults, experimentResults):
        pass
        # """Every measurement, update the results.  Plot the ratio of shots with an atom to shots without."""
        # # Check to see if we want to do anything with this data, based on the LoadingFilters.
        # # Careful here to use .value, otherwise it will always be True if the dataset exists.
        # if self.enable:
        #     if (not self.add_only_filtered_data) or (('analysis/loading_filter' in measurementResults) and measurementResults['analysis/loading_filter'].value):
        #
        #         # grab already thresholded data from SquareROIAnalysis
        #         a = measurementResults['analysis/squareROIthresholded']
        #         # add one dimension to the data to help with appending
        #         d = np.reshape(a, (1, a.shape[0], a.shape[1]))
        #
        #         if self.current_iteration_data is None:
        #             #on first measurement of an iteration, start anew
        #             new_iteration = True
        #             self.current_iteration_data = d
        #         else:
        #             #else append
        #             new_iteration = False
        #             self.current_iteration_data = np.append(self.current_iteration_data, d, axis=0)
        #
        #         # average across measurements
        #         # keepdims gives result with size (1 x shots X rois)
        #         mean = np.mean(self.current_iteration_data, axis=0, keepdims=True)
        #         #find the 1 sigma confidence interval using the normal approximation: http://en.wikipedia.org/wiki/Binomial_proportion_confidence_interval
        #         sigma = np.sqrt(mean*(1-mean)/len(self.current_iteration_data))
        #
        #         if self.mean is None:
        #             #on first iteration start anew
        #             self.mean = mean
        #             self.sigma = sigma
        #         else:
        #             if new_iteration:
        #                 #append
        #                 self.mean = np.append(self.mean, mean, axis=0)
        #                 self.sigma = np.append(self.sigma, sigma, axis=0)
        #             else:
        #                 #replace last entry
        #                 self.mean[-1] = mean
        #                 self.sigma[-1] = sigma
        #         self.updateFigure()

    @observe('list_of_what_to_plot', 'draw_connecting_lines', 'draw_error_bars', 'ymin', 'ymax')
    def reload(self, change):
        self.updateFigure()

    def updateFigure(self):
        if self.draw_fig:
            if not self.update_lock:
                try:
                    self.update_lock = True
                    fig = self.backFigure
                    fig.clf()

                    x_label = 'iteration'
                    x_vals = []
                    try:
                        for i, ivar in enumerate(self.experiment.ivarNames):
                            if len(self.experiment.ivarValueLists[i]) > 1:
                                print "found iterated variable: {}".format(ivar)
                                x_label = ivar
                                print self.experiment.ivarValueLists[i]
                                x_vals = self.experiment.ivarValueLists[i]
                                break
                    except TypeError:
                        logger.debug("unable to iterate over {}".format(self.experiment.ivarNames))
                    if self.mean is not None:
                        # parse the list of what to plot from a string to a
                        # list of numbers
                        try:
                            plotlist = eval(self.list_of_what_to_plot)
                        except Exception as e:
                            logger.warning('Could not eval plotlist in RetentionGraph:\n{}\n'.format(e))
                            return
                        # make one plot
                        ax = fig.add_subplot(111)
                        for i in plotlist:
                            try:
                                mean = self.mean[:, i]
                                sigma = self.sigma[:, i]
                            except:
                                logger.warning('Trying to plot data that does not exist in RetentionGraph: roi {}'.format(i))
                                continue
                            if x_vals == []:
                                x_vals = np.arange(len(mean))
                            label = '({})'.format(i)
                            linestyle = '-o' if self.draw_connecting_lines else 'o'
                            if self.draw_error_bars:
                                ax.errorbar(x_vals[:len(mean)], mean, yerr=sigma, fmt=linestyle, label=label)
                            else:
                                ax.plot(x_vals[:len(mean)], mean, linestyle, label=label)
                        # adjust the limits so that the data isn't right on the
                        # edge of the graph
                        if len(x_vals) > 1:
                            delta = abs(x_vals[1] - x_vals[0])
                        else:
                            delta = 1
                        ax.set_xlim(min(x_vals[:len(mean)]) - 0.3*delta, max(x_vals[:len(mean)]) + 0.3*delta)
                        if self.ymin != '':
                            ax.set_ylim(bottom=float(self.ymin))
                        if self.ymax != '':
                            ax.set_ylim(top=float(self.ymax))
                        # add legend using the labels assigned during ax.plot()
                        # or ax.errorbar()
                        ax.legend(bbox_to_anchor=(0., 1.02, 1., .102), loc=3, ncol=7, mode="expand", borderaxespad=0.)
                        ax.set_xlabel(x_label)
                        ax.set_ylabel('Retention')

                    super(RetentionGraph, self).updateFigure()
                except Exception as e:
                    logger.exception('Problem in RetentionGraph.updateFigure()')
                finally:
                    self.update_lock = False
