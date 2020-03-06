"""recent_shot_analysis.py
   Part of the AQuA Cesium Controller software package

   author=Martin Lichtman
   created=2014-07-28
   modified>=2014-07-30
   modified>=2017-05-08

   The RecentShotAnalysis class updates a live view of the main experiment
   camera defined in the experiment config file.

   Updated by Matthew Ebert (5/2017)
   """


__author__ = 'Martin Lichtman'
import logging
logger = logging.getLogger(__name__)

from atom.api import Bool, Member, Int, observe

from analysis import AnalysisWithFigure, mpl_rectangle

from colors import my_cmap


class RecentShotAnalysis(AnalysisWithFigure):
    """Plots the currently incoming shot"""
    data = Member()
    data_path = Member()
    showROIs = Bool(False)
    shot = Int(0)
    # update_lock = Bool(False)
    draw_fig = Bool(False)
    subtract_background = Bool()

    def __init__(self, name, experiment, description=''):
        super(RecentShotAnalysis, self).__init__(name, experiment, description)
        self.properties += [
            'showROIs', 'shot', 'subtract_background', 'data_path'
        ]
        self.data_path = 'data/' + self.experiment.Config.config.get('CAMERA', 'DataGroup') + '/shots'
        self.queueAfterMeasurement = True
        self.measurementDependencies += [self.experiment.squareROIAnalysis]

    def analyzeMeasurement(self, measurementResults, iterationResults, experimentResults):
        self.data = []
        if self.data_path in measurementResults:
            #for each image
            for shot in measurementResults[self.data_path].values():
                self.data.append(shot)
        self.updateFigure()  # only update figure if image was loaded

    @observe('shot', 'showROIs', 'subtract_background')
    def reload(self, change):
        self.updateFigure()

    def updateFigure(self):
        if self.draw_fig:
            try:
                #self.update_lock = True
                fig = self.backFigure
                fig.clf()

                if (self.data is not None) and (self.shot < len(self.data)):
                    ax = fig.add_subplot(111)

                    if self.subtract_background:
                        data = self.data[self.shot] - self.experiment.imageSumAnalysis.background_array
                        vmin = self.experiment.imageSumAnalysis.min_minus_bg
                        vmax = self.experiment.imageSumAnalysis.max_minus_bg
                    else:
                        data = self.data[self.shot]
                        vmin = 100 #self.experiment.imageSumAnalysis.min # should allow users to change the limit.
                        vmax = 150 #self.experiment.imageSumAnalysis.max
                        # print 'in recentShotAnalysis'
                        # print(vmin, vmax)
                        # print(np.amin(self.data), np.amax(self.data))

                    ax.matshow(data, cmap=my_cmap, vmin=self.experiment.imageSumAnalysis.min, vmax=self.experiment.imageSumAnalysis.max)
                    ax.set_title('most recent shot '+str(self.shot))
                    if self.showROIs:
                        #overlay ROIs
                        for ROI in self.experiment.squareROIAnalysis.ROIs:
                            mpl_rectangle(ax, ROI)
                        for ROI in self.experiment.squareROIAnalysis.ROIs_bg:
                            mpl_rectangle(ax, ROI)

                super(RecentShotAnalysis, self).updateFigure()
            except Exception as e:
                logger.warning('Problem in RecentShotAnalysis.updateFigure()\n:{}'.format(e))
            #finally:
                #self.update_lock = False
