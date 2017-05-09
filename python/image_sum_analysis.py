"""
image_sum_analysis.py
Part of the CsPyController package.

This analysis integrates the signal from many shots to produce an average signal plot

author = 'Martin Lichtman'
created = '2014.09.08'
modified >= '2014.09.08'
modified >= '2017.05.09'
"""

import os.path
import logging
from colors import my_cmap, green_cmap

import numpy as np
from atom.api import Bool, Str, Member, Int, observe

from analysis import AnalysisWithFigure, mpl_rectangle

import matplotlib.pyplot as plt
from mpl_toolkits.axes_grid1 import make_axes_locatable

logger = logging.getLogger(__name__)

# get the config file
from __init__ import import_config
config = import_config()

class ImageSumAnalysis(AnalysisWithFigure):
    data = Member()
    enable = Bool()
    sum_array = Member()  # holds the sum of each shot
    count_array = Member()  # holds the number of measurements summed
    mean_array = Member()  # holds the mean image for each shot
    background_array = Member()
    showROIs = Bool(False)  # should we superimpose ROIs?
    shot = Int()  # which shot to display
    update_lock = Bool(False)
    min_str = Str()
    max_str = Str()
    min = Member()
    max = Member()
    min_minus_bg = Member()
    max_minus_bg = Member()
    #pdf = Member()
    pdf_path = Member()
    subtract_background = Bool()
    iteration = Int()
    shots_path = Member()

    def __init__(self, experiment):
        super(ImageSumAnalysis, self).__init__('ImageSumAnalysis', experiment, 'Sums shot0 images as they come in')
        self.properties += ['enable', 'showROIs', 'shot', 'background_array', 'subtract_background', 'min_str',
                            'max_str', 'min', 'max', 'min_minus_bg', 'max_minus_bg']
        self.min = 0
        self.max = 1
        self.shots_path = 'data/' + config.get('CAMERA', 'DataGroup') + '/shots'

    def set_background(self):
        self.background_array = self.mean_array[self.shot]

    def preExperiment(self, experimentResults):
        if self.enable and self.experiment.saveData:
            #self.pdf = PdfPages(os.path.join(self.experiment.path, 'image_mean_{}.pdf'.format(self.experiment.experimentPath)))

            # create the nearly complete path name to save pdfs to.  The iteration and .pdf will be appended.
            pdf_path = os.path.join(self.experiment.path, 'pdf')
            if not os.path.exists(pdf_path):
                os.mkdir(pdf_path)
            self.pdf_path = os.path.join(pdf_path, '{}_image_mean'.format(self.experiment.experimentPath))

    def preIteration(self, iterationResults, experimentResults):
        #clear old data
        self.mean_array = None

    def analyzeMeasurement(self, measurementResults, iterationResults, experimentResults):

        self.iteration = iterationResults.attrs['iteration']

        if self.shots_path in measurementResults:
            if self.mean_array is None:
                #start a sum array of the right shape
                #self.sum_array = np.array([shot for shot in measurementResults['data/Andor_4522/shots'].itervalues()], dtype=np.uint64)
                #self.count_array = np.zeros(len(self.sum_array), dtype=np.uint64)
                self.sum_array = np.array([shot for shot in measurementResults[self.shots_path].itervalues()], dtype=np.float64)
                self.count_array = np.zeros(len(self.sum_array), dtype=np.float64)
                self.mean_array = self.sum_array.astype(np.float64)

            else:
                #add new data
                for i, shot in enumerate(measurementResults[self.shots_path].itervalues()):
                    self.sum_array[i] += shot
                    self.count_array[i] += 1.0
                    self.mean_array[i] = self.sum_array[i]/self.count_array[i]
            self.update_min_max()
            self.updateFigure()  # only update figure if image was loaded

    def update_min_max(self):
        if (self.mean_array is not None) and (self.shot < len(self.mean_array)):
            #update the min/max that this and other image plots will use
            if self.min_str == '':
                self.min = np.amin(self.mean_array[self.shot])
                try:
                    if self.subtract_background:
                        self.min_minus_bg = np.amin(self.mean_array[self.shot]-self.background_array)
                except:
                    logger.warning('Could not subtract background array to create min in ImageSumAnalysis.analyzeMeasurement')
                    logger.warning('array shapes: mean_array: {} background_array: {}'.format(self.mean_array[self.shot].shape, self.background_array.shape))
            else:
                try:
                    self.min = float(self.min_str)
                    self.min_minus_bg = self.min
                except:
                    logger.warning('Could not cast string to float in to create min in ImageSumAnalysis.analyzeMeasurement')
            if self.max_str == '':
                self.max = np.amax(self.mean_array[self.shot])
                try:
                    if self.subtract_background:
                        self.max_minus_bg = np.amax(self.mean_array[self.shot]-self.background_array)
                except:
                    logger.warning('Could not subtract background array to create max in ImageSumAnalysis.analyzeMeasurement')
            else:
                try:
                    self.max = float(self.max_str)
                    self.max_minus_bg = self.max
                except:
                    logger.warning('Could not cast string to float in to create max in ImageSumAnalysis.analyzeMeasurement')
            print(self.min, self.max)

    def analyzeIteration(self, iterationResults, experimentResults):
        if self.enable:
            iterationResults['sum_array'] = self.sum_array
            iterationResults['mean_array'] = self.mean_array

            # create image of all shots for pdf
            self.savefig(iterationResults.attrs['iteration'])

    @observe('shot', 'showROIs', 'subtract_background')
    def reload(self, change):
        self.updateFigure()

    @observe('min_str', 'max_str')
    def change_scaling(self, change):
        self.update_min_max()
        self.updateFigure()

    def savefig(self, iteration):
        try:
            # save to PDF
            if self.experiment.saveData:
                for shot in xrange(self.mean_array.shape[0]):

                    fig = plt.figure(figsize=(8, 6))
                    dpi = 80
                    fig.set_dpi(dpi)
                    self.draw_fig(fig, iteration, shot)
                    plt.savefig('{}_{}_{}.pdf'.format(self.pdf_path, iteration, shot),
                                format='pdf', dpi=dpi, transparent=True, bbox_inches='tight',
                                pad_inches=.25, frameon=False)
                    plt.close(fig)
        except Exception as e:
            logger.exception('Problem in HistogramGrid.savefig()')


    def draw_fig(self, fig, iteration, shot):
        if (self.mean_array is not None) and (shot < len(self.mean_array)):
            #gs = GridSpec(1, 2, width_ratios=[20, 1])
            #ax = fig.add_subplot(gs[0, 0])
            ax = fig.add_subplot(111)

            if self.subtract_background:
                data = self.mean_array[shot] - self.background_array
                min = self.min_minus_bg
                max = self.max_minus_bg
            else:
                data = self.mean_array[shot]
                min = self.min
                max = self.max

            im = ax.matshow(data, cmap=my_cmap, vmin=min, vmax=max)

            #label plot
            fig.suptitle('{} iteration {} shot {} mean'.format(self.experiment.experimentPath, iteration, shot))

            # make a colorbar
            # create an axes on the right side of ax. The width of cax will be 5%
            # of ax and the padding between cax and ax will be fixed at 0.05 inch.
            divider = make_axes_locatable(ax)
            cax = divider.append_axes("right", size="5%", pad=0.05)
            fig.colorbar(im, cax=cax)

            if self.showROIs:
                #overlay ROIs
                for ROI in self.experiment.squareROIAnalysis.ROIs:
                    mpl_rectangle(ax, ROI)
                for ROI in self.experiment.squareROIAnalysis.ROIs_bg:
                    mpl_rectangle(ax, ROI)

    def updateFigure(self):
        if not self.update_lock:
            try:
                self.update_lock = True

                fig = self.backFigure
                fig.clf()

                self.draw_fig(fig, self.iteration, self.shot)

                super(ImageSumAnalysis, self).updateFigure()
            except Exception as e:
                logger.warning('Problem in ImageSumAnalysis.updateFigure()\n:{}'.format(e))
            finally:
                self.update_lock = False

    #def finalize(self, experimentResults):
    #    if self.enable and self.experiment.saveData:
    #        self.pdf.close()
