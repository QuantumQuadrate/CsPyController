def get_iter_variable(experimentResults, v_name, iter=0):
    return experimentResults['iterations/{}/variables/{}'.format(iter, v_name)].value


def get_iter_retention_loading(experimentResults, i):
    def loading_fom(l, l_goal=0.3, o=4):
        '''FOM function is approx linear below goal, and approx constant above'''
        return l_goal*numpy.power(numpy.power(l, o)/(numpy.power(l_goal, o) + numpy.power(l, o)), 1./o)

    iterRes = experimentResults['iterations/{}'.format(i)]
    retention_all = iterRes['analysis/loading_retention/retention'].value
    retention_err_all = iterRes['analysis/loading_retention/retention_sigma'].value
    loading_all = iterRes['analysis/loading_retention/loading'].value
    # loading_err_all = iterRes['analysis/loading_retention/loading_sigma'].value
    retention_avg = numpy.prod(retention_all[:2])
    retention_err_mean = numpy.nanmean(retention_err_all[:2])
    loading = numpy.prod(loading_fom(loading_all)[:2])
    loading_err_mean = 0.0001  # numpy.sqrt(loading_avg[0])
    return (retention_avg, retention_err_mean, loading, loading_err_mean)


def readout(experimentResults, exclude_sites=[], shot=0):
    """Optimization that optimizes readout via the histogram overlap."""

    iterationResults = experimentResults['iterations/0']
    # get number of retained atoms
    retention = iterationResults['analysis/loading_retention/retention'].value
    # get overlap from histogram results
    hist = iterationResults['analysis/histogram_results'].value
    # take histogram overlap for the relevant shot
    overlap = hist['overlap'][shot]
    # get variable values
    num_measurements = len(iterationResults['measurements'])
    # calculate the cost for each site
    sitecosts = retained
    sitecosts -= overlap

    # calculate the statistical uncertainties for each site
    site_uncertainties = numpy.multiply(
        iterationResults['analysis/loading_retention/retention_sigma'].value,
        iterationResults['analysis/loading_retention/loaded'].value
    )

    for exclude_site in exclude_sites:
        sitecosts[exclude_site] = numpy.nan
        site_uncertainties[exclude_site] = numpy.nan
    # average all sites
    sites = len(sitecosts)-len(exclude_sites)
    return (numpy.nanmean(sitecosts)/sites, numpy.linalg.norm(site_uncertainties)/sites)


def loading_retention_readout(experimentResults, exclude_sites=[], shot=0):
    """Our usual loading optimization that also optimizes readout via the histogram overlap.
    Can be used to reduce atom temperature with a trap drop.
    Optical pumping optimization is more sensitive if used with an OP_Depump phase."""

    def loading_fom(l, l_goal=0.2, o=4):
        '''FOM function is approx linear below goal, and approx constant above'''
        return l_goal*numpy.power(numpy.power(l, o)/(numpy.power(l_goal, o) + numpy.power(l, o)), 1./o)

    iterationResults = experimentResults['iterations/0']

    # get number of retained atoms
    retention = iterationResults['analysis/loading_retention/retention'].value[:2]
    # get the number of reloaded atoms
    reloaded = iterationResults['analysis/loading_retention/reloaded'].value[:2]

    # get overlap from histogram results
    hist = iterationResults['analysis/histogram_results'].value
    # average overlap over all shots (should produce a 49 element array)
    overlap = hist['overlap'][shot][:2]

    # get variable values
    Readout_time = iterationResults['variables/exra_readout_780'].value
    num_measurements = len(iterationResults['measurements'])
    loaded = iterationResults['analysis/loading_retention/loaded'].value[:2]

    # product of the site cost for each metric that we want good, can't make one really good
    # at the expense of another
    print('retention: {}'.format(retention))
    print('loading: {}'.format(loaded/num_measurements))
    print('overlap: {}'.format(overlap/Readout_time))
    print('reloading: {}'.format(reloaded/num_measurements))
    sitecosts = numpy.array([
        numpy.prod(numpy.power(retention, 3)),              # ideally 1
        numpy.prod(loading_fom(loaded/num_measurements)),   # ideally 1 -> 0.2 loading
        numpy.nanmean(overlap/(Readout_time)),              # ideally 0 (goal <0.5%)
        numpy.nanmean(reloaded/num_measurements)            # ideally 0 (goal <0.5%)
    ])
    print(sitecosts)
    # weights for each metric
    weights = -1.0*numpy.array([5.0, 1.0, -100.0, -100.0])

    # calculate the statistical uncertainties for each site
    site_uncertainties = 5.0*numpy.linalg.norm(
        iterationResults['analysis/loading_retention/retention_sigma'].value[:2]
    )
    return numpy.dot(sitecosts, weights), numpy.linalg.norm(site_uncertainties)


# self.yi, self.y_stat_sigma = readout(experimentResults=experimentResults, exclude_sites = [2])
self.yi, self.y_stat_sigma = loading_retention_readout(experimentResults=experimentResults, exclude_sites=[2])


# short drop for normal retention
# r0, e0, l0, le0 = get_iter_retention_loading(experimentResults, 0)
# long drop for temperature
# r1, e1, l1, le1 = get_iter_retention_loading(experimentResults, 1)

# self.yi = -l0
# self.y_stat_sigma = le0


# return inf instead of nan
if numpy.isnan(self.yi):
    self.yi = numpy.inf
