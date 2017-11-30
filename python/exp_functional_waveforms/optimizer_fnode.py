def get_iter_variable(experimentResults, v_name, iter=0):
    return experimentResults['iterations/{}/variables/{}'.format(iter, v_name)].value


def get_iter_retention_loading(experimentResults, i):
    iterRes = experimentResults['iterations/{}'.format(i)]
    retention_all = iterRes['analysis/loading_retention/retention'].value
    retention_err_all = iterRes['analysis/loading_retention/retention_sigma'].value
    loading_all = iterRes['analysis/loading_retention/loading'].value
    total_atoms = iterRes['analysis/loading_retention/loaded'].value
    #loading_err_all = iterRes['analysis/loading_retention/loading_sigma'].value
    retention_avg = numpy.nanmean(retention_all)
    retention_err_mean = numpy.nanmean(retention_err_all)
    loading_avg = numpy.nanmean(loading_all)
    loading_err_mean = 1.0/numpy.sqrt(total_atoms/loading_avg)
    return (retention_avg, retention_err_mean, loading_avg, loading_err_mean)

# short drop for normal retention
r0, e0, l0, le1 = get_iter_retention_loading(experimentResults, 0)
# long drop for temperature
#r1, e1 = get_iter_retention(experimentResults, 1)

# step function for bad short retention
if r0 < 0.97:
    self.yi = - r0/4
    self.y_stat_sigma = e0/2
else:
    self.yi = -10*l0
    self.y_stat_sigma = -10*le1
