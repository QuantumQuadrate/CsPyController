def CNOT(experimentResults, site1, site2):

    a11 = experimentResults['iterations/0/analysis/loading_retention/atoms']
    a10 = experimentResults['iterations/1/analysis/loading_retention/atoms']
    a01 = experimentResults['iterations/2/analysis/loading_retention/atoms']
    a00 = experimentResults['iterations/3/analysis/loading_retention/atoms']
        
    # then evaluate if the CNOT works properly when both atoms load
    # by simply adding the number of retained atoms, and not the retained fraction,
    # we can simultaneously optimize loading.  The output rotations should be set so 
    # that a high-high signal is always desirable.
    # atoms is size 250 x 2 x 49
    cost = (numpy.sum(a11[:,0,site1]*a11[:,0,site2]*a11[:,1,site1]*a11[:,1,site2]) +
                numpy.sum(a10[:,0,site1]*a10[:,0,site2]*a10[:,1,site1]*a10[:,1,site2]) +
                numpy.sum(a01[:,0,site1]*a01[:,0,site2]*a01[:,1,site1]*a01[:,1,site2]) +
                numpy.sum(a00[:,0,site1]*a00[:,0,site2]*a00[:,1,site1]*a00[:,1,site2]) )
    
    # normalize by number of measurements, and add a minus sign because the optimizer minimizes
    return -cost


def CNOT11(experimentResults, site1, site2):

    a11 = experimentResults['iterations/0/analysis/loading_retention/atoms']
        
    # then evaluate if the CNOT works properly when both atoms load
    # by simply adding the number of retained atoms, and not the retained fraction,
    # we can simultaneously optimize loading.  The output rotations should be set so 
    # that a high-high signal is always desirable.
    # atoms is size 250 x 2 x 49
    cost = (numpy.sum(a11[:,0,site1]*a11[:,0,site2]*a11[:,1,site1]*a11[:,1,site2]) )
    
    # normalize by number of measurements, and add a minus sign because the optimizer minimizes
    return -cost


def control_loss(experimentResults, site1):
    # maximize retention of the control atom
    return -experimentResults['iterations/0/analysis/loading_retention/retention'].value[site1]


def loading_retention_readout(experimentResults):
    """Our usual loading optimization that also optimizes readout via the histogram overlap.
    Can be used to reduce atom temperature with a trap drop.
    Optical pumping optimization is more sensitive if used with an OP_Depump phase."""
    
    iterationResults = experimentResults['iterations/0']
    
    # get number of retained atoms
    retained = iterationResults['analysis/loading_retention/retained'].value
    
    # get overlap from histogram results
    hist = iterationResults['analysis/histogram_results'].value
    #average overlap over all shots (should produce a 49 element array)
    overlap = numpy.nanmean(hist['overlap'], axis=0)
    
    # get variable values
    Readout_time = iterationResults['variables/Readout_time'].value
    #total_AO_time = iterationResults['variables/total_AO_time'].value  # no longer exists now with functional waveforms
    num_measurements = len(iterationResults['measurements'])
    
    # calculate the cost for each site
    sitecosts=-(retained-num_measurements*overlap)/(Readout_time)
    
    # average all sites
    return numpy.nanmean(sitecosts)

def minimize_retention(experimentResults):
    """Minimize the retention, such as would be used with an OP_Depump (no microwave) experiment."""
    
    iterationResults = experimentResults['iterations/0']
    retention = iterationResults['analysis/loading_retention/retention'].value
    return numpy.nanmean(retention)

def high_low(experimentResults):
    """Maximize retention in the 0th iteration, and minimize retention in the 1st iteration.
    Useful for maximizing loading and optical pumping at the same time."""
    
    loading0 = experimentResults['iterations/0/analysis/loading_retention/loading'].value
    loading1 = experimentResults['iterations/1/analysis/loading_retention/loading'].value
    retention0 = experimentResults['iterations/0/analysis/loading_retention/retention'].value
    retention1 = experimentResults['iterations/1/analysis/loading_retention/retention'].value
    
    # maximize retention difference, maximize mean loading
    cost = (retention0-retention1)*(loading0+loading1)/2.0
    # average all sites, minus sign to minimize
    return -numpy.nanmean(cost)


#self.yi = control_loss(experimentResults, 36)
#self.yi = CNOT(experimentResults, 36, 22)
#self.yi = CNOT11(experimentResults, 36, 22)
#self.yi = loading_retention_readout(experimentResults)
#self.yi = minimize_retention(experimentResults)
self.yi = high_low(experimentResults)

# evaluate cost of iteration just finished
#iterationResults = experimentResults['iterations/0']
#num_measurements = len(iterationResults['measurements'])
#iterations = map(int, experimentResults['iterations'].keys())
#iterations.sort()

# 2 layer OP optimizer that takes |1>-|0>
#retention0 = experimentResults['iterations/0/analysis/loading_retention/retention'].value
#retention1 = experimentResults['iterations/1/analysis/loading_retention/retention'].value
#self.yi = -numpy.nanmean(retention1-retention0)

# minimize |0>
#retention0 = experimentResults['iterations/0/analysis/loading_retention/retention'].value
#self.yi = numpy.nanmean(retention0)

## sum up all the loaded atoms from shot 0 in region 24 optimize brightness
## (negative because cost will be minimized, must convert to float otherwise negative wraps around)
# self.yi = -numpy.sum(numpy.array([m['analysis/squareROIsums'][0][24] for m in iterationResults['measurements'].itervalues()]), dtype=numpy.float64)

## take the retention in shot 1 for site 31 thresholded
#self.yi = -numpy.sum(numpy.array([m['analysis/squareROIthresholded'][1,31] for m in iterationResults['measurements'].itervalues()]))

## take the signal-to-noise in for selected shot and regions
#regions = range(49)
#shot = 0
#roi_size = 3*3  # each roi is 3 by 3 pixels
## create a length 49 array of the roi sums
#roi_sums = numpy.sum(numpy.array([m['analysis/squareROIsums'][shot] for m in iterationResults['measurements'].itervalues()]), axis=0)
## sum over either all regions, or just selected ones
#all_region_sum = numpy.sum(roi_sums)
#region_sum = numpy.sum(roi_sums[regions])
## background is the whole shot, except the regions
#all_sum = numpy.sum(numpy.array([m['data/Hamamatsu/shots/'+str(shot)] for m in iterationResults['measurements'].itervalues()]))
#background_sum = all_sum - all_region_sum
## get the size of an image
#all_region_pixels = len(roi_sums)*roi_size  # 49 regions
#region_pixels = len(regions)*roi_size  # selected regions
#image_shape = numpy.shape(iterationResults['measurements'].values()[0]['data/Hamamatsu/shots/'+str(shot)])
#image_pixels = image_shape[0]*image_shape[1]
#background_pixels = image_pixels - all_region_pixels
##normalize by pixels
#signal = region_sum*1.0/region_pixels
#noise = background_sum*1.0/background_pixels
#self.yi = noise/signal

#take the amplitude of a gaussian fit to the ROIs
#self.yi = -iterationResults['analysis/gaussian_roi/fit_params'].value[4]

#loading & retention
#loaded = iterationResults['analysis/loading_retention/loaded'].value
#retained = experimentResults['iterations/0/analysis/loading_retention/retained'].value
#atoms = experimentResults['iterations/0/analysis/loading_retention/atoms'].value
#loading = numpy.mean(iterationResults['analysis/loading_retention/loading'].value)
#retention = iterationResults['analysis/loading_retention/retention'].value
#self.yi = -numpy.nanmean(retained)

# retention from all iterations
#all_retained = numpy.nanmean(numpy.array([experimentResults['iterations/{}/analysis/loading_retention/retained'.format(i)].value for i in iterations]), axis=0)

# histogram
#hist = iterationResults['analysis/histogram_results'].value
#average overlap over all shots (should produce a 49 element array)
#overlap = numpy.nanmean(hist['overlap'], axis=0)
#average all ROIs from shot 0
#overlap = numpy.nanmean(hist[0]['overlap'])

# overlap from all iterations
#all_overlap = numpy.nanmean(numpy.array([experimentResults['iterations/{}/analysis/histogram_results'.format(i)].value['overlap'] for i in iterations]), axis=0)

# gaussian fit
# maximize:  amplitude
# minimize:  wx, wy, goodness of fit
#fit = numpy.sum(numpy.abs(iterationResults['analysis/gaussian_roi/covariance_matrix'].value))
#amplitude = iterationResults['analysis/gaussian_roi/fit_params'].value[4]
#wx = iterationResults['analysis/gaussian_roi/fit_params'].value[5]
#wy = iterationResults['analysis/gaussian_roi/fit_params'].value[6]
#blacklevel = iterationResults['analysis/gaussian_roi/fit_params'].value[8]
#self.yi = fit*wx*wy*blacklevel / amplitude

# use the DC Noise Eater data
# box 0, channel 1, std of error signal
# self.yi = numpy.std([m['data/DC_noise_eater'][0,1,11] for m in iterationResults])

# use the Ramsey curve fit
# ramsey experiment optimizer cost function:
#ramsey_frequency = experimentResults['analysis/Ramsey/frequency'].value
#ramsey_decay = experimentResults['analysis/Ramsey/decay'].value
#self.yi = -ramsey_frequency

#sitecosts=-loading
# take only site 39 with ramsey data
#self.yi = -(all_retained[39]-250*all_overlap[39])/Readout_time - ramsey_frequency - ramsey_decay

# return inf instead of nan
if numpy.isnan(self.yi):
    self.yi = numpy.inf
