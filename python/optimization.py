"""
optimization.py
Part of the CsPyController experiment control software
author = Martin Lichtman
housekeeper =  Y.S.@AQuA
created = 2014.05.22
modified >= 2014.05.22

This file contains an Analysis which is called after every iteration when running an optimization.
The analysis evaluates how good the current set point is, based on the results of the iteration measurements.
The set point is then updated by the optimization routine.

Three methods are available:  Nelder-Mead simplex, gradient descent, and genetic.

The cost function is specified on the front panel, and must define 'self.yi ='
For example:
self.yi = -numpy.sum(numpy.array([m['analysis/squareROIthresholded'][1] for m in iterationResults['measurements'].itervalues()]))
"""

from __future__ import division
__author__ = 'Martin Lichtman'
import logging
logger = logging.getLogger(__name__)

import traceback, os
import numpy
from math import isnan

import matplotlib as mpl
mpl.use('PDF')
import matplotlib.pyplot as plt
from matplotlib.backends.backend_pdf import PdfPages

from atom.api import Bool, Member, Float, Int, Str
from analysis import AnalysisWithFigure


class Optimization(AnalysisWithFigure):
    """
    self.xi: initial values of the x-axis, i.e. variables themselves
    self.yi: initial values of the y-axis, i.e. the cost function values.
    The basic logic layout of this class: the generator decides which x values to run for the next round (possibly
    containing more than one iteration).
    """
    version = '2015.11.30'
    enable_override = Bool()  # this must be true for optimizer to function, regardless of ivar.optimize settings
    enable = Bool()  # whether or not to activate this optimization
    enable_gui = Bool()  # shows the enable state on the gui checkbox
    axes = Member()
    xi = Member()  # the current settings (len=axes)
    yi = Member()  # the current cost
    y_stat_sigma = Member()  # the statistical uncertainty of the current cost function
    xlist = Member()  # a history of the settings (shape=(iterations,axes))
    ylist = Member()  # a history of the costs (shape=(iterations))
    y_stat_sigma_list = Member()  # a history of the statistical uncertainty of the current cost function
    best_xi = Member()
    best_yi = Member()
    best_yi_str = Str()  # for gui display, the best cost
    best_experiment_number = Member()
    best_experiment_number_str = Str()
    yi_str = Str()  # for gui display, the current cost
    yi0_str = Str()  # for gui display, the initial cost
    generator = Member()
    initial_step = Member()  # an array of initial steps for each variable
    optimization_method = Int(0)
    line_search_initial_step = Float(.01)  # a global initial step for line search algorithms
    end_condition_step = Float(.0001)
    end_tolerances = Member()
    cost_function = Str()
    optimization_variables = Member()
    is_done = Bool()
    firstrun = Member()

    def __init__(self, name, experiment, description=''):
        super(Optimization, self).__init__(name, experiment, description)
        self.properties += ['version', 'enable', 'initial_step', 'line_search_initial_step', 'end_condition_step',
                            'cost_function', 'optimization_method', 'enable_override']

    def setup(self, hdf5):
        """
        A note about the two "enable" options: enable and enable_override. If enable_override is True and there is at
        least one independent variable that the optimizer can work on, the "enable" option is automatically set to be
        true.
        :param hdf5:
        :return:
        """
        self.optimization_variables = []
        enable = False  # don't enable unless there are some optimization variables
        if self.enable_override:  # to enable you must both enable on the Optimization page and on each ivar
            for i, x in enumerate(self.experiment.independentVariables):
                if x.optimize:
                    enable = True  # there is at least one optimization variable
                    self.optimization_variables += [x]
                    x.setIndex(0)
        self.enable = enable
        self.set_gui({'enable_gui': enable})

        if self.enable:

            self.is_done = False
            self.firstrun = True  # so we can record the initial cost

            # start all the independent variables at the value given for the 0th iteration
            self.xi = numpy.array([i.valueList[0] for i in self.optimization_variables], dtype=float)
            # create an array to store the separate initial steps for each variable
            self.initial_step = numpy.array([i.optimizer_initial_step for i in self.optimization_variables], dtype=float)
            self.axes = len(self.optimization_variables)
            # create an array to store the ivar.optimizer_end_tolerance
            self.end_tolerances = numpy.array([i.optimizer_end_tolerance for i in self.optimization_variables], dtype=float)

            # save the optimizer data
            hdf5['analysis/optimizer/names'] = [i.name for i in self.optimization_variables]
            hdf5['analysis/optimizer'].create_dataset('values', [0, self.axes], maxshape=[None, self.axes])
            hdf5['analysis/optimizer'].create_dataset('costs', [0], maxshape=[None])
            hdf5['analysis/optimizer'].create_dataset('statistical_uncertainty', [0], maxshape=[None])
            hdf5['analysis/optimizer/best_values'] = numpy.zeros(self.axes, dtype=float)
            hdf5['analysis/optimizer/best_cost'] = numpy.inf
            hdf5['analysis/optimizer/best_experiment_number'] = 0

            #create a new generator to choose optimization points
            methods = [self.simplex, self.genetic, self.gradient_descent, self.weighted_simplex, self.smart_simplex]
            self.generator = methods[self.optimization_method](self.xi)

            self.xlist = []
            self.ylist = []
            self.y_stat_sigma_list = []
            self.best_xi = None
            self.best_yi = numpy.inf
        else:
            self.is_done = True

    def update(self, hdf5, experimentResults):
        if self.enable:

            # evaluate the cost function, with access to all backend variables
            # The cost function must define 'self.yi ='
            # For example:
            # self.yi = -numpy.sum(numpy.array([m['analysis/squareROIthresholded'][1] for m in iterationResults['measurements'].itervalues()]))

            try:
                exec(self.cost_function, globals(), locals())
            except Exception as e:
                logger.error('Exception evaluating cost function:\n{}\n{}'.format(e, traceback.format_exc()))
                self.yi = numpy.inf
                self.y_stat_sigma = 0
            # if the evaluated value is nan, set it to inf so it will always be the worst point
            if isnan(self.yi):
                self.yi = numpy.inf
                self.y_stat_sigma = 0
            if isnan(self.y_stat_sigma):
                self.y_stat_sigma = 0

            # store this data point
            self.xlist.append(self.xi)
            self.ylist.append(self.yi)
            self.y_stat_sigma_list.append(self.y_stat_sigma)
            # expand the values array
            a = hdf5['analysis/optimizer/values']
            a.resize(a.len()+1, axis=0)
            a[-1] = self.xi
            # expand the costs array
            b = hdf5['analysis/optimizer/costs']
            b.resize(b.len()+1, axis=0)
            b[-1] = self.yi
            # expand the cost statistical uncertainty array
            bb = hdf5['analysis/optimizer/statistical_uncertainty']
            bb.resize(bb.len()+1, axis=0)
            bb[-1] = self.y_stat_sigma

            if self.firstrun:
                self.set_gui({'yi0_str': str(self.yi)})
                self.firstrun = False

            # check to see if this is the best point
            if self.yi < self.best_yi:
                # update instance variables; maybe it will be a good idea to establish a range to extract the best
                self.best_xi = self.xi
                self.best_yi = self.yi
                self.best_experiment_number = experimentResults.attrs['experiment_number']
                # update hdf5
                hdf5['analysis/optimizer/best_values'][...] = self.xi
                hdf5['analysis/optimizer/best_cost'][...] = self.yi
                hdf5['analysis/optimizer/best_experiment_number'][...] = self.best_experiment_number
                # update experiment independent variables
                for i, j in zip(self.optimization_variables, self.xi):
                    i.set_gui({'function': str(j)})

                # update the ramsey fit guess
                self.experiment.Ramsey.optimizer_update_guess()

            # update the gui
            self.set_gui({'yi_str': str(self.yi), 'best_yi_str': str(self.best_yi),
                          'best_experiment_number_str': str(self.best_experiment_number)})

            # let the generator decide on the next point to look at
            try:
                self.xi = self.generator.next()
            except StopIteration:
                # the optimizer has reached an end condition
                logger.info('optimizer reached end condition')
                self.is_done = True
                self.experiment.set_status('end')
                return
            self.setVars(self.xi)
            self.updateFigure()
        else:
            self.is_done = True

    def finalize(self, hdf5):
        if self.enable:
            # store the cost graph to a pdf
            if self.experiment.saveData:
                try:
                    pdf_path = os.path.join(self.experiment.path, 'pdf')
                    if not os.path.exists(pdf_path):
                        os.mkdir(pdf_path)
                    filename = os.path.join(pdf_path, '{}_optimizer.pdf'.format(self.experiment.experimentPath))

                    fig = plt.figure(figsize=(22.5, 1.25*(1+len(self.optimization_variables))))
                    dpi = 80
                    fig.set_dpi(dpi)
                    fig.suptitle(self.experiment.experimentPath)
                    self.draw_figure(fig)
                    plt.savefig(filename,
                                format='pdf', dpi=dpi, transparent=True, bbox_inches='tight',
                                pad_inches=.25, frameon=False)
                    plt.close(fig)
                except Exception as e:
                    logger.warning('Problem saving optimizer pdf:\n{}\n'.format(e))

    def draw_figure(self, fig):
        # plot cost
        ax = fig.add_subplot(self.axes+2, 1, 1)
        ax.plot(self.ylist)
        ax.set_ylabel('cost')

        # plot cost with statistical error bars
        ax = fig.add_subplot(self.axes+2, 1, 2)
        ax.errorbar(range(len(self.ylist)), self.ylist, yerr=self.y_stat_sigma_list, fmt='o')
        ax.set_ylabel('cost with error bar')

        # plot settings
        d = numpy.array(self.xlist).T
        for i in range(self.axes):
            ax = fig.add_subplot(self.axes+2, 1, i+3)
            ax.plot(d[i])
            ax.set_ylabel(self.optimization_variables[i].name)

    def updateFigure(self):
        fig = self.backFigure
        fig.clf()

        # fig.set_dpi(100)
        # fig.set_size_inches(18, len(self.optimization_variables), forward=False)

        self.draw_figure(fig)

        super(Optimization, self).updateFigure()

    def setVars(self, xi):
        for i, x in zip(self.optimization_variables, xi):
            if x < i.optimizer_min:
                i.currentValue = i.optimizer_min
            elif x > i.optimizer_max:
                i.currentValue = i.optimizer_max
            else:
                i.currentValue = x
            i.set_gui({'currentValueStr': str(i.currentValue)})

    def genetic(self, x0):
        yi = self.yi
        xi = x0
        while True:  # TODO:  Some exit condition?  We don't have any notion of reducing step size for this algorithm.

            # take random step on each axis, gaussian distribution with mean=0 and variance=initial_step
            x_test = xi + self.initial_step * numpy.random.randn(self.axes)

            # test the new point
            yield x_test

            # if the new point is better, keep it
            if self.yi < yi:
                xi = x_test
                yi = self.yi

    def gradient_descent(self, x0):
        """An optimization algorithm that finds the local gradient, then moves in the direction of fastest descent.
        A line search is done along that direction, then the process repeats."""

        axes = len(x0)
        # initial_step is used as the number multiplied by the gradient during the line search.
        # Separate step_sizes are used for each variable during the gradient evaluation.
        step_size = self.line_search_initial_step
        y0 = self.yi
        while True:
            # find gradient at the current point by making a small move on each axis
            dx = numpy.zeros(axes)
            dy = numpy.zeros(axes)
            for i in xrange(axes):
                logger.info('testing gradient on axis' + str(i))
                x_test = x0.copy()
                x_test[i] += self.initial_step[i]
                yield x_test
                dx[i] = x_test[i]-x0[i]
                dy[i] = self.yi-y0
            gradient = dy / dx

            # try a point in this new direction
            yield x0 - step_size * gradient

            # compare the new point to the old one
            x_best = x0
            y_best = y0
            if self.yi < y_best:
                # the new point is better, but there may be more room for improvement,
                # do a line search by doubling the step size as many times as we can,
                # until there is no more improvement
                # the loop will enter at least once
                while self.yi < y_best:
                    x_best = self.xi
                    y_best = self.yi
                    step_size *= 2  # double the step size
                    yield x0 - step_size * gradient
                # the line search loop has exited because no more improvement is being found
                # keep the second to last point and use that as a starting point
                x0 = x_best
                y0 = y_best
            else:
                # the new point was no improvement, so halve the step size until we find something better
                while self.yi >= y_best:

                    # or end the optimization if the step size gets sufficiently small
                    if step_size < self.end_condition_step:
                        raise StopIteration

                    step_size *= 0.5
                    yield x0 - step_size * gradient
                # the line search loop has exited because we found a better point
                # keep the last point and use that as a starting point
                x0 = self.xi
                y0 = self.yi

    #Nelder-Mead downhill simplex method
    def simplex(self, x0):
        """Perform the simplex algorithm.  x is 2D array of settings.  y is a 1D array of costs at each of those settings.
        When comparisons are made, lower is better."""

        # x0 is assigned when this generator is created, but nothing else is done until the first time next() is called

        axes = len(x0)
        n = axes + 1
        x = numpy.zeros((n, axes))
        y = numpy.zeros(n)
        x[0] = x0
        y[0] = self.yi

        # for the first several measurements, we just explore the cardinal axes to create the simplex
        for i in xrange(axes):
            logger.info('simplex: exploring axis' + str(i))
            # for the new settings, start with the initial settings and then modify them by unit vectors
            xi = x0.copy()
            # add the initial step size as the first offset
            xi[i] += self.initial_step[i]
            yield xi
            x[i+1] = xi
            y[i+1] = self.yi

        logger.debug('Finished simplex exploration.')

        # loop until the simplex is smaller than the end tolerances on each axis
        while numpy.any((numpy.amax(x, axis=0)-numpy.amin(x, axis=0)) > self.end_tolerances):

            logger.debug('Starting new round of simplex algorithm.')

            # order the values
            order = numpy.argsort(y)
            x[:] = x[order]
            y[:] = y[order]

            # find the mean of all except the worst point
            x0 = numpy.mean(x[:-1], axis=0)

            #reflection
            logger.info('simplex: reflecting')
            # reflect the worst point in the mean of the other points, to try and find a better point on the other side
            a = 1
            xr = x0+a*(x0-x[-1])
            # yield so we can take a datapoint
            yield xr
            yr = self.yi

            if y[0] <= yr < y[-2]:
                #if the new point is no longer the worst, but not the best, use it to replace the worst point
                logger.info('simplex: keeping reflection')
                x[-1] = xr
                y[-1] = yr

            #expansion
            elif yr < y[0]:
                logger.info('simplex: expanding')
                # if the new point is the best, keep going in that direction
                b = 2
                xe = x0+b*(x0-x[-1])
                # yield so we can take a datapoint
                yield xe
                ye = self.yi
                if ye < yr:
                    #if this expanded point is even better than the initial reflection, keep it
                    logger.info('simplex: keeping expansion')
                    x[-1] = xe
                    y[-1] = ye
                else:
                    #if the expanded point is not any better than the reflection, use the reflection
                    logger.info('simplex: keeping reflection (after expansion)')
                    x[-1] = xr
                    y[-1] = yr

            #contraction
            else:
                logger.info('simplex: contracting')
                # The reflected point is still worse than all other points, so try not crossing over the mean,
                # but instead go halfway between the original worst point and the mean.
                c = -0.5
                xc = x0+c*(x0-x[-1])
                # yield so we can take a datapoint
                yield xc
                yc = self.yi
                if yc < y[-1]:
                    #if the contracted point is better than the original worst point, keep it
                    logger.info('simplex: keeping contraction')
                    x[-1] = xc
                    y[-1] = yc

                #reduction
                else:
                    # the contracted point is the worst of all points considered.  So reduce the size of the whole
                    # simplex, bringing each point in halfway towards the best point
                    logger.info('simplex: reducing')
                    d = 0.9
                    # we don't technically need to re-evaluate x[0] here, as it does not change
                    # however, due to noise in the system it is preferable to re-evaluate x[0] occasionally,
                    # and now is a good time to do it
                    for i in xrange(axes):
                        x[i] = x[0]+d*(x[i]-x[0])
                        # yield so we can take a datapoint
                        yield x[i]
                        y[i] = self.yi


    #Nelder-Mead downhill simplex method using a weighted centroid
    def weighted_simplex(self, x0):
        """Perform the simplex algorithm.
        This is the same as simplex(), except that a weighted mean is used to find the centroid of n points
        during reflection, instead of an unweighted mean.
        x is 2D array of settings.  y is a 1D array of costs at each of those settings.
        When comparisons are made, lower is better."""

        # x0 is assigned when this generator is created, but nothing else is done until the first time next() is called

        axes = len(x0)
        n = axes + 1
        x = numpy.zeros((n, axes))
        y = numpy.zeros(n)
        x[0] = x0
        y[0] = self.yi

        # for the first several measurements, we just explore the cardinal axes to create the simplex
        for i in xrange(axes):
            logger.info('simplex: exploring axis' + str(i))
            # for the new settings, start with the initial settings and then modify them by unit vectors
            xi = x0.copy()
            # add the initial step size as the first offset
            xi[i] += self.initial_step[i]
            yield xi
            x[i+1] = xi
            y[i+1] = self.yi

        logger.debug('Finished simplex exploration.')

        # loop until the simplex is smaller than the end tolerances on each axis
        while numpy.any((numpy.amax(x, axis=0)-numpy.amin(x, axis=0)) > self.end_tolerances):

            logger.debug('Starting new round of simplex algorithm.')

            # order the values
            order = numpy.argsort(y)
            x[:] = x[order]
            y[:] = y[order]

            # find the mean of all except the worst point, taking into account the weight of how good each point is
            # negative weight is used because cost is a minimizer
            x0 = numpy.average(x[:-1], axis=0, weights=-y[:-1])


            #reflection
            logger.info('simplex: reflecting')
            # reflect the worst point in the mean of the other points, to try and find a better point on the other side
            a = 1
            xr = x0+a*(x0-x[-1])
            # yield so we can take a datapoint
            yield xr
            yr = self.yi

            if y[0] <= yr < y[-2]:
                #if the new point is no longer the worst, but not the best, use it to replace the worst point
                logger.info('simplex: keeping reflection')
                x[-1] = xr
                y[-1] = yr

            #expansion
            elif yr < y[0]:
                logger.info('simplex: expanding')
                # if the new point is the best, keep going in that direction
                b = 2
                xe = x0+b*(x0-x[-1])
                # yield so we can take a datapoint
                yield xe
                ye = self.yi
                if ye < yr:
                    #if this expanded point is even better than the initial reflection, keep it
                    logger.info('simplex: keeping expansion')
                    x[-1] = xe
                    y[-1] = ye
                else:
                    #if the expanded point is not any better than the reflection, use the reflection
                    logger.info('simplex: keeping reflection (after expansion)')
                    x[-1] = xr
                    y[-1] = yr

            #contraction
            else:
                logger.info('simplex: contracting')
                # The reflected point is still worse than all other points, so try not crossing over the mean,
                # but instead go halfway between the original worst point and the mean.
                c = -0.5
                xc = x0+c*(x0-x[-1])
                # yield so we can take a datapoint
                yield xc
                yc = self.yi
                if yc < y[-1]:
                    #if the contracted point is better than the original worst point, keep it
                    logger.info('simplex: keeping contraction')
                    x[-1] = xc
                    y[-1] = yc

                #reduction
                else:
                    # the contracted point is the worst of all points considered.  So reduce the size of the whole
                    # simplex, bringing each point in halfway towards the best point
                    logger.info('simplex: reducing')
                    d = 0.9
                    # we don't technically need to re-evaluate x[0] here, as it does not change
                    # however, due to noise in the system it is preferable to re-evaluate x[0] occasionally,
                    # and now is a good time to do it
                    for i in xrange(axes):
                        x[i] = x[0]+d*(x[i]-x[0])
                        # yield so we can take a datapoint
                        yield x[i]
                        y[i] = self.yi

    # Nelder-Mead downhill simplex method, with modifications to better suit AQuA reality
    def smart_simplex(self, x0):
        """Perform the smart simplex algorithm: compared to the original downhill simplex method, this method is more
          robust against the slow/sudden drift experienced a lot in this experimental project.
        x is 2D array of settings.  y is a 1D array of costs at each of those settings.
        When comparisons are made, lower is better.
        A note about yield: always yield one set of x, and then get the corresponding y.
        """

        # x0 is assigned when this generator is created, but nothing else is done until the first time next() is called

        axes = len(x0)
        n = axes + 1
        x = numpy.zeros((n, axes))
        y = numpy.zeros(n)
        x[0] = x0
        y[0] = self.yi

        # for the first several measurements, we just explore the cardinal axes to create the simplex
        for i in xrange(axes):
            logger.info('simplex: exploring axis' + str(i))
            # for the new settings, start with the initial settings and then modify them by unit vectors
            xi = x0.copy()
            # add the initial step size as the first offset
            xi[i] += self.initial_step[i]
            yield xi
            x[i+1] = xi
            y[i+1] = self.yi

        logger.debug('Finished simplex exploration.')

        # loop until the simplex is smaller than the end tolerances on each axis
        while numpy.any((numpy.amax(x, axis=0)-numpy.amin(x, axis=0)) > self.end_tolerances):

            logger.debug('Starting new round of simplex algorithm.')

            # order the values; what really matters is the mapping relation between x&y; actual indexing order does
            # not matter.
            order = numpy.argsort(y)
            x[:] = x[order]
            y[:] = y[order]

            # find the mean of all except the worst point; x[:-1] means everything up to the second last term.
            x0 = numpy.mean(x[:-1], axis=0)

            #reflection
            logger.info('simplex: reflecting')
            # reflect the worst point in the mean of the other points, to try and find a better point on the other side
            a = 1
            xr = x0+a*(x0-x[-1])
            # yield so we can take a datapoint
            yield xr
            yr = self.yi

            if y[0] <= yr < y[-2]:
                #if the new point is no longer the worst, but not the best, use it to replace the worst point
                logger.info('simplex: keeping reflection')
                x[-1] = xr
                y[-1] = yr

            #expansion
            elif yr < y[0]:
                logger.info('simplex: expanding')
                # if the new point is the best, keep going in that direction
                b = 2
                xe = x0+b*(x0-x[-1])
                # yield so we can take a datapoint
                yield xe
                ye = self.yi
                if ye < yr:
                    #if this expanded point is even better than the initial reflection, keep it
                    logger.info('simplex: keeping expansion')
                    x[-1] = xe
                    y[-1] = ye
                else:
                    #if the expanded point is not any better than the reflection, use the reflection
                    logger.info('simplex: keeping reflection (after expansion)')
                    x[-1] = xr
                    y[-1] = yr

            #contraction
            else:
                logger.info('simplex: contracting')
                # The reflected point is still worse than all other points, so try not crossing over the mean,
                # but instead go halfway between the original worst point and the mean.
                c = -0.5
                xc = x0+c*(x0-x[-1])
                # yield so we can take a datapoint
                yield xc
                yc = self.yi
                if yc < y[-1]:
                    #if the contracted point is better than the original worst point, keep it
                    logger.info('simplex: keeping contraction')
                    x[-1] = xc
                    y[-1] = yc

                #reduction
                else:
                    # the contracted point is the worst of all points considered.  So reduce the size of the whole
                    # simplex, bringing each point in halfway towards the best point
                    logger.info('simplex: reducing')
                    d = 0.5
                    # we don't technically need to re-evaluate x[0] here, as it does not change
                    # however, due to noise in the system it is preferable to re-evaluate x[0] occasionally,
                    # and now is a good time to do it
                    for i in xrange(axes):
                        x[i] = x[0]+d*(x[i]-x[0])
                        # yield so we can take a datapoint
                        yield x[i]
                        y[i] = self.yi
