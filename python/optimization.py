"""
optimization.py
Part of the CsPyController experiment control software
author = Martin Lichtman
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

from cs_errors import PauseError

class Optimization(AnalysisWithFigure):
    version = '2014.05.07'
    enable = Bool()  # whether or not to activate this optimization
    axes = Member()
    xi = Member()  # the current settings (len=axes)
    yi = Member()  # the current cost
    xlist = Member()  # a history of the settings (shape=(iterations,axes))
    ylist = Member()  # a history of the costs (shape=(iterations))
    best_xi = Member()
    best_yi = Member()
    generator = Member()
    initial_step = Float(.01)
    optimization_method = Int(0)
    end_condition_step_size = Float(.0001)
    cost_function = Str()

    def __init__(self, name, experiment, description=''):
        super(Optimization, self).__init__(name, experiment, description)
        self.properties += ['version', 'enable', 'initial_step', 'end_condition_step_size', 'cost_function']

    def preExperiment(self, experimentResults):
        if self.enable:

            #start all the independent variables at the value given for the 0th iteration
            x0 = numpy.array([i.valueList[0] for i in self.experiment.independentVariables])
            self.axes = len(self.experiment.independentVariables)
            self.xi = x0

            #create a new generator to choose optimization points
            methods = [self.simplex, self.genetic, self.gradient_descent]
            self.generator = methods[self.optimization_method](x0)

            self.xlist = []
            self.ylist = []
            self.best_xi = None
            self.best_yi = float('inf')

    def postIteration(self, iterationResults, experimentResults):
        if self.enable:

            # evaluate cost of iteration just finished

            # sum up all the loaded atoms from shot 0 in region 24
            # (negative because cost will be minimized, must convert to float otherwise negative wraps around)
            # self.yi = -numpy.sum(numpy.array([m['analysis/squareROIsums'][0][24] for m in iterationResults['measurements'].itervalues()]), dtype=numpy.float64)

            # take the retention in shot 1
            #self.yi = -numpy.sum(numpy.array([m['analysis/squareROIthresholded'][1] for m in iterationResults['measurements'].itervalues()]))

            # # take the signal-to-noise in shot 1 for all regions
            # region_sum = numpy.sum(numpy.array([m['analysis/squareROIsums'][1] for m in iterationResults['measurements'].itervalues()]))
            # # background is the whole shot 1, except the regions
            # all_sum = numpy.sum(numpy.array([m['data/Hamamatsu/shots/1'] for m in iterationResults['measurements'].itervalues()]))
            # background_sum = all_sum - region_sum
            # # get the size of an image
            # region_pixels = 49*9  # 49 regions, 3x3 pixels each
            # image_shape = numpy.shape(iterationResults['measurements/0/data/Hamamatsu/shots/1'])
            # image_pixels = image_shape[0]*image_shape[1]
            # background_pixels = image_pixels - region_pixels
            # #normalize by pixels
            # signal = region_sum*1.0/region_pixels
            # noise = background_sum*1.0/background_pixels
            # self.yi = -signal/noise

            # evaluate the cost function, with access to all backend variables
            # The cost function must define 'self.yi ='
            # For example:
            # self.yi = -numpy.sum(numpy.array([m['analysis/squareROIthresholded'][1] for m in iterationResults['measurements'].itervalues()]))
            exec(self.cost_function, globals(), locals())

            iterationResults['analysis/optimization_xi'] = self.xi
            iterationResults['analysis/optimization_yi'] = self.yi
            if self.yi < self.best_yi:
                self.best_xi = self.xi
                self.best_yi = self.yi
            self.xlist.append(self.xi)
            self.ylist.append(self.yi)

            # let the simplex generator decide on the next point to look at
            try:
                self.xi = self.generator.next()
            except StopIteration:
                # the optimizer has reached an end condition
                logger.info('optimizer reached end condition')
                self.experiment.set_status('end')
                return
            self.setVars(self.xi)
            self.updateFigure()

    def postExperiment(self, experimentResults):
        # store the best point
        experimentResults['analysis/best_xi'] = self.best_xi
        experimentResults['analysis/best_yi'] = self.best_yi

    def updateFigure(self):
        fig = self.backFigure
        fig.clf()

        # plot cost
        ax = fig.add_subplot(self.axes+2, 1, 1)
        ax.plot(self.ylist)
        ax.set_ylabel('cost')

        # plot settings
        d = numpy.array(self.xlist).T
        for i in range(self.axes):
            ax = fig.add_subplot(self.axes+2, 1, i+2)
            ax.plot(d[i])
            ax.set_ylabel(self.experiment.independentVariables[i].name)

        super(Optimization, self).updateFigure()

    def setVars(self, xi):
        for i, x in zip(self.experiment.independentVariables, xi):
            i.currentValue = x
            i.set_gui({'currentValueStr': str(x)})

    def genetic(self, x0):
        yi = self.yi
        xi = x0
        while True:  # TODO: some exit condition?

            # take random step on each axis, gaussian distribution with mean=0 and variance=initial_step
            x_test = xi * self.initial_step * numpy.random.randn(len(xi))

            # test the new point
            yield x_test

            # if the new point is better, keep it
            if self.yi < yi:
                xi = x_test
                yi = self.yi

    def gradient_descent(self, x0):
        axes = len(x0)
        step_size = self.initial_step
        y0 = self.yi
        while True:
            # find gradient at the current point by making a small move on each axis
            dx = numpy.zeros(axes)
            dy = numpy.zeros(axes)
            for i in xrange(axes):
                logger.info('testing gradient on axis' + str(i))
                x_test = x0.copy()
                if x_test[i] == 0:
                    x_test[i] = self.initial_step
                else:
                    x_test[i] *= 1 + self.initial_step
                yield x_test
                dx[i] = x_test[i]-x0[i]
                dy[i] = self.yi-y0
            gradient = dy / dx

            # try a point in this new direction
            yield x0 + step_size * gradient

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
                    yield x0 + step_size * gradient
                # the line search loop has exited because no more improvement is being found
                # keep the second to last point and use that as a starting point
                x0 = x_best
                y0 = y_best
            else:
                # the new point was no improvement, so halve the step size until we find something better
                while self.yi >= y_best:

                    # or end the optimization if the step size gets sufficiently small
                    if step_size < self.end_condition_step_size:
                        raise StopIteration

                    step_size *= 0.5
                    yield x0 + step_size * gradient
                # the line search loop has exited because we found a better point
                # keep the last point and use that as a starting point
                x0 = self.xi
                y0 = self.yi


    #Nelder-Mead downhill simplex method
    def simplex(self, x0):
        """Perform the simplex algorithm.  x is 2D array of settings.  y is a 1D array of costs at each of those settings.
        When comparisons are made, lower is better."""

        #x0 is assigned when this generator is created, but nothing else is done until the first time next() is called

        axes = len(x0)
        n = axes + 1
        x = numpy.zeros((n, axes))
        y = numpy.zeros(n)
        x[0] = self.xi
        y[0] = self.yi

        # for the first several measurements, we just explore the cardinal axes to create the simplex
        for i in xrange(axes):
            logger.info('exploring axis' + str(i))
            # for the new settings, start with the initial settings and then modify them by unit vectors
            xi = x0.copy()
            if xi[i] == 0:
                xi[i] = .1
            else:
                xi[i] *= 1 + self.initial_step
            yield xi
            x[i+1] = self.xi
            y[i+1] = self.yi

        # loop until all sides of the simplex are smaller than the end_condition
        while numpy.amax([numpy.sqrt(numpy.sum((x[i]-x[0])**2)) for i in xrange(1, n)]) >= self.end_condition_step_size:

            # order the values
            order = numpy.argsort(y)
            x[:] = x[order]
            y[:] = y[order]

            #find the mean of all except the worst point
            x0 = numpy.mean(x[:-1], axis=0)

            #reflection
            logger.info('reflecting')
            # reflect the worst point in the mean of the other points, to try and find a better point on the other side
            a = 1
            xr = x0+a*(x0-x[-1])
            #yr = datapoint(xr)
            yield xr
            yr = self.yi

            if y[0] <= yr < y[-2]:
                #if the new point is no longer the worst, but not the best, use it to replace the worst point
                logger.info('keeping reflection')
                x[-1, :] = xr[:]
                y[-1] = yr

            #expansion
            elif yr < y[0]:
                logger.info('expanding')
                #if the new point is the best, keep going in that direction
                b = 2
                xe = x0+b*(x0-x[-1])
                #ye = datapoint(xe)
                yield xe
                ye = self.yi
                if ye < yr:
                    #if this expanded point is even better than the initial reflection, keep it
                    logger.info('keeping expansion')
                    x[-1, :] = xe[:]
                    y[-1] = ye
                else:
                    #if the expanded point is not any better than the reflection, use the reflection
                    logger.info('keeping reflection (after expansion)')
                    x[-1, :] = xr[:]
                    y[-1] = yr

            #contraction
            else:
                logger.info('contracting')
                # The reflected point is still worse than all other points, so try not crossing over the mean, but instead
                # go halfway between the original worst point and the mean.
                c = -0.5
                xc = x0+c*(x0-x[-1])
                #yc = datapoint(xc)
                yield xc
                yc = self.yi
                if yc < y[-1]:
                    #if the contracted point is better than the original worst point, keep it
                    logger.info('keeping contraction')
                    x[-1, :] = xc[:]
                    y[-1] = yc

                #reduction
                else:
                    # the contracted point is the worst of all points considered.  So reduce the size of the whole simplex,
                    # bringing each point in halfway towards the best point
                    logger.info('reducing')
                    d = 0.5
                    for i in range(1, len(x)):
                        x[i] = x[0]+d*(x[i]-x[0])
