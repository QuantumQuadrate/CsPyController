from numpy import *
import h5py
import scipy.optimize as opt
from scipy.special import erf


def load_data(h5file,source,iteration,measurements,shots):
    if source == 'Hamamatsu':
        roi = array([range(4,7),range(3,6)])
        imdat = zeros((measurements,shots,len(roi[0,:]),len(roi[1,:])),dtype=int)
        for ms in range(measurements):
            for sht in range(shots):
                datpath = '/experiments/0/iterations/{}/measurements/{}/data/Hamamatsu/shots/{}'.format(iteration,ms,sht)
                #print filepath
                try:
                    im = array(h5file[(datpath)])
                    #fig,ax = plt.subplots(1,1)
                    #ax.imshow(mesDat)
                    #print mesDat[roi[0],:][:,roi[1]]
                    imdat[ms,sht,:,:] = im[roi[0],:][:,roi[1]]
                    #print ("mesDatarr",mesDatarr[it,ms,sht,:,:])
                except KeyError as e:
                    print "Error while loading data : {}".format(e)
                    print datpath
        histdat = imdat.sum(2).sum(2)
    else:
        histdat = None
    return histdat


def loading(histdat,cut):
    rload = (histdat[:,0]>=cut).sum()/(len(histdat[:,0])*1.0)
    return rload


def ret(histdat,cut,cuterr,popt):
    rload = (histdat[:,0]>=cut).sum()/(len(histdat[:,0])*1.0)
    print rload
    if rload > 0:
        retention = (1.0*(histdat[:,0]>=cut)*(histdat[:,1]>cut)).sum()/(histdat[:,0]>=cut).sum()
        shot_error = sqrt(retention*(1-retention)/(histdat[:,0]>=cut).sum())
        ct_error_plus = abs(1.0*((histdat[:,0]>=cut+cuterr)*(histdat[:,1]>cut+cuterr)).sum()/(histdat[:,0]>=cut+cuterr).sum()-retention)
        ct_error_minus = abs(1.0*((histdat[:,0]>=cut-cuterr)*(histdat[:,1]>cut-cuterr)).sum()/(histdat[:,0]>=cut-cuterr).sum()-retention)
        ovlp_error = get_overlap_error(cut,*abs(popt[:4]))
        print ct_error_plus,ct_error_minus
        retention_error = sqrt(shot_error**2+(ct_error_plus+ct_error_minus)**2*0.25+ovlp_error**2)
    else:
        retention = 0
        retention_error = 0
    return retention,retention_error


def fit_hist(histdat,guess=None):
    func = dblGauss

    #hdat = HmCountDat[it,:,1]
    bns = range(min(histdat),max(histdat),(max(histdat)-min(histdat))/30)
    h = histogram(histdat,bins=bns)#,normed=True)
    xdat = array(h[1][1:],dtype=float)
    ydat = array(h[0],dtype=float)

    if guess is None:
        x0g = 21000
        x1g = 24000
        std0g = 1000.0
        std1g = 2000.0
        a0g = 6.0e1
        a1g = 6.0e1
        guess = [x0g,x1g,std0g,std1g,a0g,a1g]

    popt,pcov = opt.curve_fit(f=func,xdata=xdat,ydata=ydat,p0=guess)
    perr = sqrt(diag(pcov))

    return popt,perr


def dblGauss(x,x0,x1,std0,std1,a0,a1):
    xp0 = x-x0
    xp1 = x-x1
    g0 = a0*exp(-0.5*(xp0/std0)**2)
    g1 = a1*exp(-0.5*(xp1/std1)**2)
    return g0+g1


def get_overlap_error(xc,x0,x1,s0,s1):
    return 0.5*( 1-erf((xc-x0)/(sqrt(2)*s0)) + 1-erf((x1-xc)/(sqrt(2)*s1)) )


def get_cut(x0,x1,s0,s1):
    rad = (x0-x1)**2+2*(s1**2-s0**2)*log(s1/s0)
    num = x1*s0**2-x0*s1**2-s0*s1*sqrt(rad)
    denuminv = 1/(s0**2-s1**2)
    xc = num*denuminv

    return xc


def get_cut_err(x0,x1,s0,s1,dx0,dx1,ds0,ds1):
    rad = (x0-x1)**2+2*(s1**2-s0**2)*log(s1/s0)
    num = x1*s0**2-x0*s1**2-s0*s1*sqrt(rad)
    rdinv = 1/sqrt(rad)
    denuminv = 1/(s0**2-s1**2)
    xc = num*denuminv

    px0 = -denuminv*(s1**2+s0*s1*rdinv*(x0-x1))
    px1 = denuminv*(s0**2+s0*s1*rdinv*(x0-x1))
    ps0 = denuminv*s0*(2*(x1-xc)-s1*sqrt(rad)/s0+s1*(s1**2/s0+s0*(2*log(s1/s0)+1)))/sqrt(rad)
    ps1 = denuminv*s1*(2*(xc-x0)-s0*sqrt(rad)/s1+s0*(s0**2/s1-s1*(2*log(s1/s0)+1)))/sqrt(rad)

    return dx0*px0+dx1*px1+ds0*ps0+ds1*ps1