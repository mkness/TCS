"""
This file is part of The Cannon analysis project.
Copyright 2014 Melissa Ness.

# urls
- http://iopscience.iop.org/1538-3881/146/5/133/suppdata/aj485195t4_mrt.txt for calibration stars 
- http://data.sdss3.org/irSpectrumDetail?locid=4330&commiss=0&apogeeid=2M17411636-2903150&show_aspcap=True object explorer 
- http://data.sdss3.org/basicIRSpectra/searchStarA
- http://data.sdss3.org/sas/dr10/apogee/spectro/redux/r3/s3/a3/ for the data files 

# to-do
- need to add a test that the wavelength range is the same - and if it isn't interpolate to the same range 
- format PEP8-ish (four-space tabs, for example)
- take logg_cut as an input
- extend to perform quadratic fitting
"""

#from astropy.io import fits as pyfits 
import pyfits
import scipy 
import glob 
import pickle
import pylab 
from scipy import interpolate 
from scipy import ndimage 
from scipy import optimize as opt
import numpy as np
from datetime import datetime
normed_training_data = 'normed_data_alpha_apocask_gc_ind.pickle'

def weighted_median(values, weights, quantile):
    """weighted_median

    keywords
    --------

    values: ndarray
        input values

    weights: ndarray
        weights to apply to each value in values

    quantile: float
        quantile selection

    returns
    -------
    val: float
        median value
    """
    sindx = np.argsort(values)
    cvalues = 1. * np.cumsum(weights[sindx])
    cvalues = cvalues / cvalues[-1]
    foo = sindx[cvalues > quantile]
    if len(foo) == 0:
        return values[0]
    indx = foo[0]
    return values[indx]

def continuum_normalize_tsch(dataall,maskall, pixlist, delta_lambda=150):
    pixlist = list(pixlist) 
    Nlambda, Nstar, foo = dataall.shape
    continuum = np.zeros((Nlambda, Nstar))
    dataall_flat = np.ones((Nlambda, Nstar, 3))
    for jj in range(Nstar):
        bad_a = np.logical_or(np.isnan(dataall[:, jj, 1]) ,np.isinf(dataall[:,jj, 1]))
        bad_b = np.logical_or(dataall[:, jj, 2] <= 0. , np.isnan(dataall[:, jj, 2]))
        bad = np.logical_or( np.logical_or(bad_a, bad_b) , np.isinf(dataall[:, jj, 2]))
        dataall[bad, jj, 1] = 0.
        dataall[bad, jj, 2] = np.Inf #LARGE#np.Inf #100. #np.Inf
        continuum = np.zeros((Nlambda, Nstar))
        var_array = 100**2*np.ones((len(dataall))) 
        var_array[pixlist] = 0.000
        ivar = 1. / ((dataall[:, jj, 2] ** 2) + var_array) 
        bad = np.isnan(ivar)
        ivar[bad] =  0
        bad = np.isinf(ivar)
        ivar[bad] =  0
        take1 = logical_and(dataall[:,jj,0] > 15150, dataall[:,jj,0] < 15800)
        take2 = logical_and(dataall[:,jj,0] > 15890, dataall[:,jj,0] < 16430)
        take3 = logical_and(dataall[:,jj,0] > 16490, dataall[:,jj,0] < 16950)
        #fit1 = numpy.polynomial.chebyshev.Chebyshev.fit(x=dataall[take1,jj,0], y=dataall[take1,jj,1], w=ivar[take1],deg=3)# 2 or 3 is good for all, 2 only a few points better in temp 
        #fit2 = numpy.polynomial.chebyshev.Chebyshev.fit(x=dataall[take2,jj,0], y=dataall[take2,jj,1], w=ivar[take2],deg=3)
        #fit3 = numpy.polynomial.chebyshev.Chebyshev.fit(x=dataall[take3,jj,0], y=dataall[take3,jj,1], w=ivar[take3],deg=3)
        fit1 = numpy.polynomial.chebyshev.Chebyshev.fit(x=dataall[take1,jj,0], y=dataall[take1,jj,1], w=ivar[take1],deg=2)# 2 or 3 is good for all, 2 only a few points better in temp 
        fit2 = numpy.polynomial.chebyshev.Chebyshev.fit(x=dataall[take2,jj,0], y=dataall[take2,jj,1], w=ivar[take2],deg=2)
        fit3 = numpy.polynomial.chebyshev.Chebyshev.fit(x=dataall[take3,jj,0], y=dataall[take3,jj,1], w=ivar[take3],deg=2)
        continuum[take1,jj] = fit1(dataall[take1,jj,0])
        continuum[take2,jj] = fit2(dataall[take2,jj,0])
        continuum[take3,jj] = fit3(dataall[take3,jj,0])
        dataall_flat[:, jj, 0] = dataall[:,jj,0]
        dataall_flat[take1, jj, 1] = dataall[take1,jj,1]/fit1(dataall[take1,0,0])
        dataall_flat[take2, jj, 1] = dataall[take2,jj,1]/fit2(dataall[take2,0,0]) 
        dataall_flat[take3, jj, 1] = dataall[take3,jj,1]/fit3(dataall[take3,0,0]) 
        dataall_flat[take1, jj, 2] = dataall[take1,jj,2]/fit1(dataall[take1,0,0]) 
        dataall_flat[take2, jj, 2] = dataall[take2,jj,2]/fit2(dataall[take2,0,0]) 
        dataall_flat[take3, jj, 2] = dataall[take3,jj,2]/fit3(dataall[take3,0,0]) 
    for star in range(Nstar):
        print "get_continuum(): working on star" ,star
    for jj in range(Nstar):
        bad_a = np.logical_or(np.isnan(dataall_flat[:, jj, 1]) ,np.isinf(dataall_flat[:,jj, 1]))
        bad_b = np.logical_or(dataall_flat[:, jj, 2] <= 0. , np.isnan(dataall_flat[:, jj, 2]))
        bad =  np.logical_or(bad_a, bad_b) 
        LARGE  =200.
        dataall_flat[bad,jj, 1] = 1. 
        dataall_flat[bad,jj, 2] = LARGE 
        bad = np.where(dataall[:, jj, 2] > LARGE) 
        dataall_flat[bad,jj, 1] = 1. 
        dataall_flat[bad,jj, 2] = LARGE 
        bad = np.isnan(dataall[:, jj, 1])
        dataall_flat[bad,jj, 1] = 1. 
        dataall_flat[bad,jj, 2] = LARGE 
        bad = np.isinf(dataall_flat[:, jj, 2])
        dataall_flat[bad,jj, 1] = 1. 
        dataall_flat[bad,jj, 2] = LARGE 
        #maskbin1 = [np.int(a) & 2**0 for a in mask[:,jj,0]] 
        #maskbin2 = [np.int(a) & 2**12 for a in mask[:,jj,0]] 
        #maskbin3 = [np.int(a) & 2**13 for a in mask[:,jj,0]] 
        #bad = maskall[:,jj] != 0
        #dataall_flat[bad,jj, 2] = LARGE 
    return dataall_flat, continuum 


def continuum_normalize(dataall, SNRall, delta_lambda=50):
    """continuum_normalize

    keywords
    --------

    dataall: ndarray, shape=(Nlambda, Nstar, 3)
        wavelengths, flux densities, errors

    delta_lambda:
        half-width of median region in angstroms


    returns
    -------
    continuum:     (Nlambda, Nstar)
        continuum level

    .. note::

        * does a lot of stuff *other* than continuum normalization

    .. todo::

        * bugs: for loops!
    """
    Nlambda, Nstar, foo = dataall.shape
    continuum = np.zeros((Nlambda, Nstar))
   
    file_in = open('coeffs_2nd_order_test18.pickle', 'r')
    dataall2, metaall, labels, offsets, coeffs, covs, scatters,chis,chisqs = pickle.load(file_in)
    file_in.close()
    
   # sanitize inputs
    for jj in range(Nstar):
    #    #BROKEN
        bad_a = np.logical_or(np.isnan(dataall[:, jj, 1]) ,np.isinf(dataall[:,jj, 1]))
        bad_b = np.logical_or(dataall[:, jj, 2] <= 0. , np.isnan(dataall[:, jj, 2]))
        bad = np.logical_or( np.logical_or(bad_a, bad_b) , np.isinf(dataall[:, jj, 2]))
        dataall[bad, jj, 1] = 0.
        dataall[bad, jj, 2] = np.Inf #LARGE#np.Inf #100. #np.Inf
        continuum = np.zeros((Nlambda, Nstar))
    assert foo == 3
    for star in range(Nstar):
        #x = [0.02, 0.08] 
        #y = [90.0, 50.0] 
        #z = np.polyfit(log(x), log(y), 1)
        #p = np.poly1d(z)
        #good = dataall[:,star,2] < 0.1
        good1 = logical_and(coeffs[:,0] > 0.998, coeffs[:,0] < 1.002 ) 
        good2 = logical_and(dataall[:,star,2] < 0.5, dataall[:,star,1] > 0.6) 
        good3 = logical_and(logical_and(abs(coeffs[:,1]) <0.005/1000., abs(coeffs[:,2])  <0.005), abs(coeffs[:,3]) < 0.005)
        good = logical_and(good2,good3) 
        medtest = median(dataall[:,star,1][good]) 
        #stdval = std(dataall[:,star,1][good])
        snrval = SNRall[star] 
        if snrval >= 100.0:
          q = 0.90
        if snrval <= 15.00:
          q = 0.50
        if logical_and(snrval > 15.0, snrval < 100.0): 
          #q = e**(-0.06891241*log(snrval)**2 +  0.76047574*log(snrval) - 2.14601435) 
          #q = e**(-0.094*log(snrval)**2 +  0.95*log(snrval) - 2.50) 
          q = e**(0.26*log(snrval)**2 -  1.83*log(snrval) + 2.87) 
        print "get_continuum(): working on star" ,star
        for ll, lam in enumerate(dataall[:, 0, 0]):
            if dataall[ll, star, 0] != lam:
                print dataall[ll,star,0], lam , dataall[ll,0,0] 
                print ll, star 
                print ll+1, star+1, dataall[ll+1, star+1, 0], dataall[ll+1,0,0] 
                print ll+2, star+2, dataall[ll+2, star+2, 0], dataall[ll+2,0,0] 
                assert False
            indx = (np.where(abs(dataall[:, star, 0] - lam) < delta_lambda))[0]
            
            coeffs_indx = coeffs[indx][:,0]
            test1 = logical_and(coeffs_indx > 0.995, coeffs_indx < 1.005) 
            test2 = logical_or(coeffs_indx <= 0.995, coeffs_indx >= 1.005) 
            #test1 = logical_and( b[indx star, 1] > 0.6, logical_and(logical_and(abs(coeffs[indx,1]) <0.005/1000., abs(coeffs[indx][:,2])  <0.005), abs(coeffs[indx,3]) < 0.005)) 
            #test2 = logical_or(logical_or(abs(coeffs[indx,1]) >= 0.005/1000., abs(coeffs[indx,2])  >= 0.005), logical_or( b[indx,star,1] <= 0.6, abs(coeffs[indx,3]) >=  0.005)) 
            #test2 = logical_or(coeffs_indx <= 0.998, coeffs_indx >= 1.002) 
            coeffs_indx[test2] = 100**2.
            coeffs_indx[test1] = 0
            ivar = 1. / ((dataall[indx, star, 2] ** 2) + coeffs_indx) 
            ivar = 1. / (dataall[indx, star, 2] ** 2)
            ivar = np.array(ivar)
            #q = 0.85
            q = 0.90
            continuum[ll, star] = weighted_median(dataall[indx, star, 1], ivar, q)
    for jj in range(Nstar):
        bad = np.where(continuum[:,jj] <= 0) 
        continuum[bad,jj] = 1.
        dataall[:, jj, 1] /= continuum[:,jj]
        dataall[:, jj, 2] /= continuum[:,jj]
        #dataall[:, jj, 1] /= medtest
        #dataall[:, jj, 2] /= medtest
        dataall[bad,jj, 1] = 1. 
        dataall[bad,jj, 2] = LARGE 
        bad = np.where(dataall[:, jj, 2] > LARGE) 
        dataall[bad,jj, 1] = 1. 
        dataall[bad,jj, 2] = LARGE 
    return dataall 


def get_bad_pixel_mask(testfile,nlam): 
  name = testfile.split('.txt')[0]
  adir = open(testfile, 'r')
  al2 = adir.readlines()
  bl2 = []
  bl3 = []
  dirname = '/home/ness/new_laptop/Apogee_DR12/data.sdss3.org/sas/dr12/apogee/spectro/redux/r5/stars/l25_6d/v603/'
  for each in al2:
    bl2.append(each.strip()) 
    bl3.append((each.split('/'))[-2] +'/'+ ("apStar-s3-")+each.split('aspcapStar-v304-')[-1].strip())  
  if glob.glob(dirname):
    dirin = [dirname+each for each in bl3] 
    mask  = np.zeros((nlam, len(bl2),1))
    for jj,each in enumerate(dirin):
      a=pyfits.open(each) 
      mask[:,jj,0] = (np.atleast_2d(a[3].data))[0]
  else: 
    mask  = np.zeros((nlam, len(bl2),1))
  return mask 

def get_normalized_test_data_tsch(testfile, pixlist):
  name = testfile.split('.txt')[0]
  a = open(testfile, 'r')
  al2 = a.readlines()
  bl2 = []
  for each in al2:
    bl2.append(each.strip())
  ids = []
  for each in bl2:
    ids.append(each.split('-2M')[-1].split('.fits')[0])

  if glob.glob(name+'_alpha.pickle'):
    file_in2 = open(name+'_alpha.pickle', 'r')
    testdata = pickle.load(file_in2)
    file_in2.close()
    a = open(testfile, 'r')
    al2 = a.readlines()
    bl2 = []
    for each in al2:
      bl2.append(each.strip())
    SNR = np.zeros((len(bl2)))
    for jj,each in enumerate(bl2):
      a = pyfits.open(each)
      #SNR[jj]  = a[0].header['SNRVIS4']
      SNR[jj]  = a[0].header['SNR']
      file_in2 = open(name+'_SNR.pickle', 'w')
      pickle.dump(SNR,  file_in2)
      file_in2.close()
    return testdata, ids

  SNRall = np.zeros(len(bl2))
  for jj,each in enumerate(bl2):
    a = pyfits.open(each) 
    if shape(a[1].data) != (8575,):
      ydata = a[3].data[0] 
      ysigma = a[2].data[0]
      len_data = a[2].data[0]
      #mask = a[3].data[0] # was 3 before for SNRVIS1
      #ydata = a[1].data[3] # SNR test - NOTE THIS IS FOR TEST TO READ IN A SINGLE VISIT - TESTING ONLY - OTHERWISE SHOULD BE 0 TO READ IN THE MEDIAN SPECTRA 
      #ysigma = a[2].data[3]
      #len_data = a[2].data[3]
      if jj == 0:
        nlam = len(a[3].data[0])
        testdata = np.zeros((nlam, len(bl2), 3))
    if shape(a[1].data) == (8575,):
      ydata = a[3].data
      ysigma = [0]*nlam # a[2].data
      len_data = a[2].data
      if jj == 0:
        nlam = len(a[1].data)
        testdata = np.zeros((nlam, len(bl2), 3))
    start_wl =  a[1].header['CRVAL1']
    diff_wl = a[1].header['CDELT1']
    SNR = a[0].header['SNR']
    #SNR = a[0].header['SNRVIS4']
    SNRall[jj] = SNR

    val = diff_wl*(nlam) + start_wl 
    wl_full_log = np.arange(start_wl,val, diff_wl) 
    wl_full = [10**aval for aval in wl_full_log]
    xdata = wl_full
    testdata[:, jj, 0] = xdata
    testdata[:, jj, 1] = ydata
    testdata[:, jj, 2] = ysigma
    #maskdata[:, jj] = mask
  #mask = get_bad_pixel_mask(testfile,nlam) 
  mask = np.zeros((nlam, len(bl),1))
  #for jj,each in enumerate(bl2):
  #  bad = mask[:,jj] != 0 
  #  testdata[bad, jj, 2] = 200.
  testdata, contall = continuum_normalize_tsch(testdata,mask,pixlist, delta_lambda=50)
  file_in = open(name+'_alpha.pickle', 'w')  
  file_in2 = open(name+'_SNR.pickle', 'w')
  pickle.dump(testdata,  file_in)
  pickle.dump(SNRall,  file_in2)
  file_in.close()
  file_in2.close()
  return testdata , ids # not yet implemented but at some point should probably save ids into the normed pickle file 


def get_normalized_test_data(testfile,noise=0): 
  """
    inputs
    ------
    testfile: str
        the file in with the list of fits files want to test - if normed, move on,
        if not normed, norm it
    if not noisify carry on as normal, otherwise do the noise tests

    returns
    -------
    testdata:
  """
  name = testfile.split('.txt')[0]
  
  a = open(testfile, 'r')
  al2 = a.readlines()
  bl2 = []
  for each in al2:
    bl2.append(each.strip())
  ids = []
  for each in bl2:
    ids.append(each.split('-2M')[-1].split('.fits')[0])
  
  if noise == 0: 
    if glob.glob(name+'_alpha.pickle'):
      file_in2 = open(name+'_alpha.pickle', 'r') 
      testdata = pickle.load(file_in2)
      file_in2.close()
      a = open(testfile, 'r')
      al2 = a.readlines()
      bl2 = []
      for each in al2:
        bl2.append(each.strip())
      SNR = np.zeros((len(bl2))) 
      for jj,each in enumerate(bl2):
        a = pyfits.open(each) 
        #SNR[jj]  = a[0].header['SNRVIS4']
        #SNR[jj]  = a[0].header['SNRVIS4']
        SNR[jj]  = a[0].header['SNR']
        file_in2 = open(name+'_alpha_SNR.pickle', 'w')  
        pickle.dump(SNR,  file_in2)
        file_in2.close()
      return testdata, ids 
  if noise == 1: 
    if not glob.glob(name+'._SNR.pickle'):
      a = open(testfile, 'r')
      al2 = a.readlines()
      bl2 = []
      for each in al2:
       # bl2.append(testdir+each.strip())
        bl2.append(each.strip())
      SNR = np.zeros((len(bl2))) 
      for jj,each in enumerate(bl2):
        a = pyfits.open(each) 
        SNR[jj]  = a[0].header['SNR']
        #SNR[jj]  = a[0].header['SNRVIS4']
        file_in2 = open(name+'_SNR.pickle', 'w')  
        pickle.dump(SNR,  file_in2)
        file_in2.close()
    if glob.glob(name+'.pickle'):
      if glob.glob(name+'_SNR.pickle'): 
        file_in2 = open(name+'.pickle', 'r') 
        testdata = pickle.load(file_in2)
        file_in2.close()
        file_in3 = open(name+'_SNR.pickle', 'r') 
        SNR = pickle.load(file_in3)
        file_in3.close()
        ydata = testdata[:,:,1]
        ysigma = testdata[:,:,2]
        testdata[:,:,1], testdata[:,:,2] =  add_noise(ydata, ysigma, SNR)
        return testdata, ids

  a = open(testfile, 'r')
  al2 = a.readlines()
  bl2 = []
  for each in al2:
    bl2.append(each.strip())
  ids = []
  for each in bl2:
    ids.append(each.split('-2M')[-1].split('.fits')[0])

  SNRall = np.zeros(len(bl2))
  for jj,each in enumerate(bl2):
    a = pyfits.open(each) 
    if shape(a[1].data) != (8575,):
      ydata = a[1].data[0] 
      ysigma = a[2].data[0]
      len_data = a[2].data[0]
      if jj == 0:
        nlam = len(a[1].data[0])
        testdata = np.zeros((nlam, len(bl2), 3))
    if shape(a[1].data) == (8575,):
      ydata = a[1].data
      ysigma = a[2].data
      len_data = a[2].data
      if jj == 0:
        nlam = len(a[1].data)
        testdata = np.zeros((nlam, len(bl2), 3))
    start_wl =  a[1].header['CRVAL1']
    diff_wl = a[1].header['CDELT1']
    SNR = a[0].header['SNR']
    #SNR = a[0].header['SNRVIS4']
    SNRall[jj] = SNR

    #ydata = a[1].data
    #ysigma = a[2].data
    #start_wl =  a[1].header['CRVAL1']
    #diff_wl = a[1].header['CDELT1']
    #if jj == 0:
    #    nlam = len(a[1].data)
    #    testdata = np.zeros((nlam, len(bl2), 3))
    val = diff_wl*(nlam) + start_wl 
    wl_full_log = np.arange(start_wl,val, diff_wl) 
    wl_full = [10**aval for aval in wl_full_log]
    xdata = wl_full
    testdata[:, jj, 0] = xdata
    testdata[:, jj, 1] = ydata
    testdata[:, jj, 2] = ysigma
  testdata = continuum_normalize(testdata,SNRall) # testdata
  file_in = open(name+'.pickle', 'w')  
  file_in2 = open(name+'_SNR.pickle', 'w')
  pickle.dump(testdata,  file_in)
  pickle.dump(SNRall,  file_in2)
  file_in.close()
  file_in2.close()
  return testdata , ids # not yet implemented but at some point should probably save ids into the normed pickle file 

def get_normalized_training_data_tsch(pixlist):
  if glob.glob(normed_training_data): 
        file_in2 = open(normed_training_data, 'r') 
        dataall, metaall, labels, Ametaall, cluster_name, ids = pickle.load(file_in2)
        file_in2.close()
        return dataall, metaall, labels, Ametaall, cluster_name, ids
  #fn = 'training_apokasc_gc_ind.list'  
  fn = 'training_apokasc_gc_ind_feh.list'  # this is normal one should use this - only adding one below for test of RCG versus RC
  #fn = 'apokasc_clump_rbg_unknown_params.txt'  # this is normal one should use this - only adding one below for test of RCG versus RC
  fn = 'training_apokasc_clumpidout.list'  # this is normal one should use this - only adding one below for test of RCG versus RC
  T_est,g_est,feh_est,alpha_est, T_A, g_A, feh_A = np.loadtxt(fn, usecols = (1,2,3,4,1,2,3), unpack =1) 
  labels = ["teff", "logg", "feh", "alpha"]
  a = open(fn, 'r') 
  al = a.readlines() 
  bl = []
  cluster_name = [] 
  ids = []
  for each in al:
    bl.append(each.split()[0]) 
    cluster_name.append(each.split()[1]) 
    ids.append(each.split()[0].split('-2M')[-1].split('.fits')[0])

  for jj,each in enumerate(bl):
    each = each.strip('\n')
    a = pyfits.open(each) 
    b = pyfits.getheader(each) 
    start_wl =  a[1].header['CRVAL1']
    diff_wl = a[1].header['CDELT1']
    print np.atleast_2d(a[1].data).shape
    if jj == 0:
      nmeta = len(labels)
      nlam = len(a[1].data)
      #nlam = len(a[1].data[0])
    val = diff_wl*(nlam) + start_wl 
    wl_full_log = np.arange(start_wl,val, diff_wl) 
    ydata = (np.atleast_2d(a[3].data))[0] 
    ydata_err =[0]*nlam# (np.atleast_2d(a[2].data))[0] 
    ydata_flag = (np.atleast_2d(a[3].data))[0] 
    assert len(ydata) == nlam
    wl_full = [10**aval for aval in wl_full_log]
    xdata= np.array(wl_full)
    ydata = np.array(ydata)
    ydata_err = np.array(ydata_err)
    starname2 = each.split('.fits')[0]+'.txt'
    sigma = (np.atleast_2d(a[2].data))[0]# /y1
    if jj == 0:
      npix = len(xdata) 
      dataall = np.zeros((npix, len(bl), 3))
      metaall = np.ones((len(bl), nmeta))
      Ametaall = np.ones((len(bl), nmeta))
    if jj > 0:
      assert xdata[0] == dataall[0, 0, 0]

    dataall[:, jj, 0] = xdata
    dataall[:, jj, 1] = ydata
    dataall[:, jj, 2] = sigma

    for k in range(0,len(bl)): 
        # must be synchronised with labels 
      metaall[k,0] = T_est[k] 
      metaall[k,1] = g_est[k] 
      metaall[k,2] = feh_est[k] 
      metaall[k,3] = alpha_est[k] 
      Ametaall[k,0] = T_A[k] 
      Ametaall[k,1] = g_A[k] 
      Ametaall[k,2] = feh_A[k] 

  pixlist = list(pixlist) 
  #mask = get_bad_pixel_mask('test18_names.txt',nlam)
  mask = np.zeros((nlam, len(bl),1))
  dataall, contall = continuum_normalize_tsch(dataall,mask, pixlist, delta_lambda=50)
  file_in = open(normed_training_data, 'w')  
  pickle.dump((dataall, metaall, labels, Ametaall, cluster_name, ids),  file_in)
  file_in.close()
  return dataall, metaall, labels , Ametaall, cluster_name, ids

def get_normalized_training_data():
  if glob.glob(normed_training_data): 
        file_in2 = open(normed_training_data, 'r') 
        dataall, metaall, labels, Ametaall, cluster_name, ids = pickle.load(file_in2)
        file_in2.close()
        return dataall, metaall, labels, Ametaall, cluster_name, ids
  fn = "starsin_new_all_ordered.txt"
  fn = "test4_selfg.txt"
  fn = 'mkn_labels_edit.txt'  # this is for using all stars ejmk < 0.3 but with offest to aspcap values done in a consistent way to rest of labels 
  fn = 'mkn_labels_Atempfeh_edit.txt'  # this is for using all stars ejmk < 0.3 but with offest to aspcap values done in a consistent way to rest of labels 
  fn = 'test14.txt' # this is for teff < 600 cut which worked quite nicely 
  fn = 'test18.txt'  # this is for using all stars ejmk < 0.3 but with offest to aspcap values done in a consistent way to rest of labels 
  #fn = 'test14.txt' # this is for teff < 600 cut which worked quite nicely 
  #fn = 'test18_apstar.txt'  # this is for using all stars ejmk < 0.3 but with offest to aspcap values done in a consistent way to rest of labels 
  T_est,g_est,feh_est,T_A, g_A, feh_A = np.loadtxt(fn, usecols = (4,6,8,3,5,7), unpack =1) 
  #T_est,g_est,feh_est,T_A, g_A, feh_A = np.loadtxt(fn, usecols = (3,5,7,2,4,6), unpack =1) 
  labels = ["teff", "logg", "feh", "alpha" ]
  a = open(fn, 'r') 
  al = a.readlines() 
  bl = []
  cluster_name = [] 
  ids = []
  for each in al:
    bl.append(each.split()[0]) 
    cluster_name.append(each.split()[1]) 
    ids.append(each.split()[0].split('-2M')[-1].split('.fits')[0])

  SNRall = np.zeros((len(bl))) 
  for jj,each in enumerate(bl):
    each = each.strip('\n')
    a = pyfits.open(each) 
    b = pyfits.getheader(each) 
    SNRall[jj] = a[0].header['SNR']
    start_wl =  a[1].header['CRVAL1']
    diff_wl = a[1].header['CDELT1']
    print np.atleast_2d(a[1].data).shape
    if jj == 0:
      nmeta = len(labels)
      nlam = len(a[1].data)
      #nlam = len(a[1].data[0])
    val = diff_wl*(nlam) + start_wl 
    wl_full_log = np.arange(start_wl,val, diff_wl) 
    ydata = (np.atleast_2d(a[1].data))[0] 
    ydata_err = (np.atleast_2d(a[2].data))[0] 
    ydata_flag = (np.atleast_2d(a[3].data))[0] 
    assert len(ydata) == nlam
    wl_full = [10**aval for aval in wl_full_log]
    xdata= np.array(wl_full)
    ydata = np.array(ydata)
    ydata_err = np.array(ydata_err)
    starname2 = each.split('.fits')[0]+'.txt'
    sigma = (np.atleast_2d(a[2].data))[0]# /y1
    if jj == 0:
      npix = len(xdata) 
      dataall = np.zeros((npix, len(bl), 3))
      metaall = np.ones((len(bl), nmeta))
      Ametaall = np.ones((len(bl), nmeta))
    if jj > 0:
      assert xdata[0] == dataall[0, 0, 0]

    dataall[:, jj, 0] = xdata
    dataall[:, jj, 1] = ydata
    dataall[:, jj, 2] = sigma

    for k in range(0,len(bl)): 
        # must be synchronised with labels 
      metaall[k,0] = T_est[k] 
      metaall[k,1] = g_est[k] 
      metaall[k,2] = feh_est[k] 
      Ametaall[k,0] = T_A[k] 
      Ametaall[k,1] = g_A[k] 
      Ametaall[k,2] = feh_A[k] 
  dataall = continuum_normalize(dataall,SNRall) #dataall

  file_in = open(normed_training_data, 'w')  
  pickle.dump((dataall, metaall, labels, Ametaall, cluster_name, ids),  file_in)
  file_in.close()
  return dataall, metaall, labels , Ametaall, cluster_name, ids

def add_noise(ydata, ysigma, SNR):
    factor = 10.000
    #factor = ((SNR*1./30)**2 - 1)**0.5
    #y_noise_level = ((factor)/np.array(SNR)) 
    y_noise_level = sqrt(1+(factor -1)**2)*ysigma
    #y_noise_level = ((1+(factor-1)**2)**0.5)*ysigma
    y_noise_level_all =  normal(0,y_noise_level)  
    #y_noise_level_all = [ normal(0, a, len(ydata)) for a in y_noise_level]  
    #sigma_noise_level = abs(normal(0, (factor)*ysigma**2) ) 
    sigma_noise_level = abs(normal(0, sqrt(1+(factor-1)**2)*ysigma**2) ) 
    ydata_n = ydata + array(y_noise_level_all)
    #ydata_n = ydata + array(y_noise_level_all).T
    ysigma_n = (ysigma**2 + sigma_noise_level)**0.5
    return ydata_n, ysigma_n
#def add_noise(ydata, ysigma, SNR):
#    factor = 10.000
#    factor = ((SNR*1./30)**2 - 1)**0.5
#    #y_noise_level = ((factor-1)/np.array(SNR))*3.1**0.5 #3.1 is the number of pixels in a resolution element 
#    y_noise_level = ((factor)/np.array(SNR)) #3.1 is the number of pixels in a resolution element 
#    y_noise_level_all = [ normal(0, a, len(ydata)) for a in y_noise_level]  
#    sigma_noise_level = abs(normal(0, (factor)*ysigma**2) ) 
#    ydata_n = ydata + array(y_noise_level_all).T
#    ysigma_n = (ysigma**2 + sigma_noise_level)**0.5
#    return ydata_n, ysigma_n

def do_one_regression_at_fixed_scatter(data, features, scatter):
    """
    Parameters
    ----------
    data: ndarray, [nobjs, 3]
        wavelengths, fluxes, invvars

    meta: ndarray, [nobjs, nmeta]
        Teff, Feh, etc, etc

    scatter:


    Returns
    -------
    coeff: ndarray
        coefficients of the fit

    MTCinvM: ndarray
        inverse covariance matrix for fit coefficients

    chi: float
        chi-squared at best fit

    logdet_Cinv: float
        inverse of the log determinant of the cov matrice
        :math:`\sum(\log(Cinv))`
    """
    # least square fit
    #pick = logical_and(data[:,1] < np.median(data[:,1]) + np.std(data[:,1])*3. , data[:,1] >  median(data[:,1]) - np.std(data[:,1])*3.)#5*std(data[:,1]) ) 
    Cinv = 1. / (data[:, 2] ** 2 + scatter ** 2)  # invvar slice of data
    M = features
    MTCinvM = np.dot(M.T, Cinv[:, None] * M) # craziness b/c Cinv isnt a matrix
    x = data[:, 1] # intensity slice of data
    MTCinvx = np.dot(M.T, Cinv * x)
    try:
        coeff = np.linalg.solve(MTCinvM, MTCinvx)
    except np.linalg.linalg.LinAlgError:
        print MTCinvM, MTCinvx, data[:,0], data[:,1], data[:,2]
        print features
    assert np.all(np.isfinite(coeff)) 
    chi = np.sqrt(Cinv) * (x - np.dot(M, coeff)) 
    logdet_Cinv = np.sum(np.log(Cinv)) 
    return (coeff, MTCinvM, chi, logdet_Cinv )

def do_one_regression(data, metadata):
    """
    does a regression at a single wavelength to fit calling the fixed scatter routine
    # inputs:
    """
    ln_s_values = np.arange(np.log(0.0001), 0., 0.5)
    chis_eval = np.zeros_like(ln_s_values)
    for ii, ln_s in enumerate(ln_s_values):
        foo, bar, chi, logdet_Cinv = do_one_regression_at_fixed_scatter(data, metadata, scatter = np.exp(ln_s))
        chis_eval[ii] = np.sum(chi * chi) - logdet_Cinv
    if np.any(np.isnan(chis_eval)):
        s_best = np.exp(ln_s_values[-1])
        return do_one_regression_at_fixed_scatter(data, metadata, scatter = s_best) + (s_best, )
    lowest = np.argmin(chis_eval)
    #if lowest == 0 or lowest == len(ln_s_values) + 1:
    if lowest == 0 or lowest == len(ln_s_values)-1:
        s_best = np.exp(ln_s_values[lowest])
        return do_one_regression_at_fixed_scatter(data, metadata, scatter = s_best) + (s_best, )
    #print data
    #print metadata
    #print "LOWEST" , lowest
    ln_s_values_short = ln_s_values[np.array([lowest-1, lowest, lowest+1])]
    chis_eval_short = chis_eval[np.array([lowest-1, lowest, lowest+1])]
    z = np.polyfit(ln_s_values_short, chis_eval_short, 2)
    f = np.poly1d(z)
    fit_pder = np.polyder(z)
    fit_pder2 = pylab.polyder(fit_pder)
    s_best = np.exp(np.roots(fit_pder)[0])
    return do_one_regression_at_fixed_scatter(data, metadata, scatter = s_best) + (s_best, )

def do_regressions(dataall, features):
    """
    """
    nlam, nobj, ndata = dataall.shape
    nobj, npred = features.shape
    featuresall = np.zeros((nlam,nobj,npred))
    featuresall[:, :, :] = features[None, :, :]
    return map(do_one_regression, dataall, featuresall)

def train(dataall, metaall, order, fn, Ametaall, cluster_name, logg_cut=100., teff_cut=0., leave_out=None):
    """
    - `leave out` must be in the correct form to be an input to `np.delete`
    """
    #good = np.logical_and((metaall[:, 1] < logg_cut), (metaall[:,0] > teff_cut) ) 
    #dataall = dataall[:, good]
    #metaall = metaall[good]
    #nstars, nmeta = metaall.shape
    
    if leave_out is not None: #
        dataall = np.delete(dataall, [leave_out], axis = 1) 
        metaall = np.delete(metaall, [leave_out], axis = 0) 
        Ametaall = np.delete(Ametaall, [leave_out], axis = 0) 
   
    diff_t = np.abs(array(metaall[:,0] - Ametaall[:,0]) ) 
    #good = np.logical_and((metaall[:, 1] < logg_cut), (diff_t < 600. ) ) 
    good = np.logical_and((metaall[:, 1] > 0.2), (diff_t < 6000. ) ) 
    #good = np.logical_and((metaall[:, 1] < logg_cut), (diff_t < 6000. ) ) 
    dataall = dataall[:, good]
    metaall = metaall[good]
    nstars, nmeta = metaall.shape
    

    offsets = np.mean(metaall, axis=0)
    features = np.ones((nstars, 1))
    if order >= 1:
        features = np.hstack((features, metaall - offsets)) 
    if order >= 2:
        newfeatures = np.array([np.outer(m, m)[np.triu_indices(nmeta)] for m in (metaall - offsets)])
        features = np.hstack((features, newfeatures))

    blob = do_regressions(dataall, features)
    coeffs = np.array([b[0] for b in blob])
    #invcovs = np.array([b[1] for b in blob])
    covs = np.array([np.linalg.inv(b[1]) for b in blob])
    chis = np.array([b[2] for b in blob])
    chisqs = np.array([np.dot(b[2],b[2]) - b[3] for b in blob]) # holy crap be careful
    scatters = np.array([b[4] for b in blob])

    fd = open(fn, "w")
    pickle.dump((dataall, metaall, labels, offsets, coeffs, covs, scatters,chis,chisqs), fd)
    fd.close()



def get_goodness_fit(fn_pickle, filein, Params_all, MCM_rotate_all):
    fd = open(fn_pickle,'r')
    dataall, metaall, labels, offsets, coeffs, covs, scatters, chis, chisq = pickle.load(fd) 
    fd.close() 
    #file_with_star_data = str(filein)+".pickle"
    file_with_star_data = str(filein)+"_alpha.pickle"
    #file_with_star_data = "self_2nd_order_age.pickle" # this is temporary hack until this is there above 
    #f_flux = open(file_with_star_data, 'r') 
    file_normed = normed_training_data.split('.pickle')[0]
    #if filein != file_normed: 
    #  flux = pickle.load(f_flux) 
    #if filein == file_normed: 
    #  flux, metaall, labels, Ametaall, cluster_name, ids = pickle.load(f_flux)
    if filein != file_normed: 
      f_flux = open(file_with_star_data, 'r') 
      flux = pickle.load(f_flux) 
    if filein == file_normed: 
      #f_flux = open('self_2nd_order_alpha.pickle', 'r') 
      f_flux = open('normed_data_alpha_apocask_gc_ind.pickle', 'r') 
      flux, metaall, labels, Ametaall, cluster_name, ids = pickle.load(f_flux)
    f_flux.close() 
    labels = Params_all 
    nlabels = shape(labels)[1]
    nstars = shape(labels)[0]
    features_data = np.ones((nstars, 1))
    offsets = np.mean(labels, axis = 0) 
    features_data = np.hstack((features_data, labels - offsets)) 
    newfeatures_data = np.array([np.outer(m, m)[np.triu_indices(nlabels)] for m in (labels - offsets)])
    features_data = np.hstack((features_data, newfeatures_data)) 
    chi2_all = np.zeros(nstars) 
    chi_all = np.zeros((len(coeffs),nstars) )
    for jj in range(nstars):
        model_gen = np.dot(coeffs,features_data.T[:,jj]) 
        data_star = flux[:,jj,1] 
        Cinv = 1. / (flux[:,jj, 2] ** 2 + scatters ** 2)  # invvar slice of data
        chi =  np.sqrt(Cinv) * (data_star - np.dot(coeffs, features_data.T[:,jj]))  
        chi2 = sum( (Cinv) * (data_star - np.dot(coeffs, features_data.T[:,jj]))**2) 
        #chi2 = (Cinv)*(model_gen - data_star)**2 
        chi2_all[jj] = chi2
        chi_all[:,jj] = chi
    #return chi2_all 
    return chi_all

def func(x1, x2, x3, x4, x5, x6, x7, x8, x9, x10, x11, x12 , x13, x14, a, b, c, d):
    f = (0 
         + x1*a 
         + x2*b 
         + x3*c 
         + x4*d 
         + x5* a**2# 
         + x6 * a * b
         + x7 * a * c
         + x8 * a * d 
         + x9* b**2
         + x10  * b * c 
         + x11  * b * d 
         + x12* c**2  
         + x13 * c * d
         + x14* d**2 )
    return f


## non linear stuff below ##
# returns the non linear function 

# thankyou stack overflow for the example below on how to use the optimse function  
def nonlinear_invert(f, x1, x2, x3, x4, x5, x6, x7, x8, x9, x10, x11, x12, x13, x14, sigmavals):
    def wrapped_func(observation_points, a, b, c, d):
        x1, x2, x3, x4, x5, x6, x7, x8, x9, x10, x11, x12, x13, x14   = observation_points
        return func(x1, x2, x3, x4, x5, x6, x7, x8, x9, x10, x11, x12, x13, x14,  a, b, c, d)

    xdata = np.vstack([x1, x2, x3, x4, x5, x6, x7, x8, x9, x10, x11, x12, x13, x14 ])
    model, cov = opt.curve_fit(wrapped_func, xdata, f, sigma = sigmavals,maxfev = 4000)#absolute_sigma = True)  is not an option in my version of scipy will upgrade scipy
    return model, cov 




def infer_labels_nonlinear(fn_pickle,testdata, ids, fout_pickle, weak_lower,weak_upper):
#def infer_labels(fn_pickle,testdata, fout_pickle, weak_lower=0.935,weak_upper=0.98):
    """
    best log g = weak_lower = 0.95, weak_upper = 0.98
    best teff = weak_lower = 0.95, weak_upper = 0.99
    best_feh = weak_lower = 0.935, weak_upper = 0.98 
    this returns the parameters for a field of data  - and normalises if it is not already normalised 
    this is slow because it reads a pickle file 
    """
    file_in = open(fn_pickle, 'r') 
    dataall, metaall, labels, offsets, coeffs, covs, scatters,chis,chisq = pickle.load(file_in)
    file_in.close()
    nstars = (testdata.shape)[1]
    nlabels = len(labels)
    Params_all = np.zeros((nstars, nlabels))
    MCM_rotate_all = np.zeros((nstars, np.shape(coeffs)[1]-1, np.shape(coeffs)[1]-1.))
    covs_all = np.zeros((nstars,nlabels, nlabels))
    for jj in range(0,nstars):
      #if np.any(testdata[:,jj,0] != dataall[:, 0, 0]):
      if np.any(abs(testdata[:,jj,0] - dataall[:, 0, 0]) > 0.0001): 
          print testdata[range(5),jj,0], dataall[range(5),0,0]
          assert False
      xdata = testdata[:,jj,0]
      ydata = testdata[:,jj,1]
      ysigma = testdata[:,jj,2]
      ydata_norm = ydata  - coeffs[:,0] # subtract the mean 
      f = ydata_norm 
      t,g,feh,alpha = metaall[:,0], metaall[:,1], metaall[:,2], metaall[:,3]
      x0,x1,x2,x3,x4,x5,x6,x7,x8,x9,x10,x11,x12,x13,x14 = coeffs[:,0], coeffs[:,1], coeffs[:,2], coeffs[:,3], coeffs[:,4], coeffs[:,5], coeffs[:,6] ,coeffs[:,7], coeffs[:,8], coeffs[:,9], \
      coeffs[:,10], coeffs[:,11], coeffs[:, 12], coeffs[:,13],coeffs[:,14]  
      Cinv = 1. / (ysigma ** 2 + scatters ** 2)
      Params,covs = nonlinear_invert(f, x1, x2, x3, x4, x5, x6, x7, x8, x9, x10, x11, x12, x13, x14, 1/Cinv**0.5 ) 
      Params = Params+offsets 
      coeffs_slice = coeffs[:,-14:]
      MCM_rotate = np.dot(coeffs_slice.T, Cinv[:,None] * coeffs_slice)
      Params_all[jj,:] = Params 
      MCM_rotate_all[jj,:,:] = MCM_rotate 
      covs_all[jj,:,:] = covs
    filein = fout_pickle.split('_tags') [0] 
    #if filein == 'self': 
    if filein == 'self_2nd_order': 
      file_in = open(fout_pickle, 'w')  
      #pickle.dump((Params_all, covs_all),  file_in)
      file_normed = normed_training_data.split('.pickle')[0]
      chi2 = get_goodness_fit(fn_pickle, file_normed, Params_all, MCM_rotate_all)
      chi2_def = chi2/len(xdata)*1.
      pickle.dump((Params_all, covs_all,chi2_def,ids),  file_in)
      file_in.close()
    else: 
      chi2 = get_goodness_fit(fn_pickle, filein, Params_all, MCM_rotate_all)
      #chi2 = 1.
      chi2_def = chi2/len(xdata)*1.
      file_in = open(fout_pickle, 'w')  
      pickle.dump((Params_all, covs_all, chi2_def, ids),  file_in)
      file_in.close()
    return Params_all , MCM_rotate_all

def infer_labels(fn_pickle,testdata, fout_pickle, weak_lower,weak_upper):
    """
    best log g = weak_lower = 0.95, weak_upper = 0.98
    best teff = weak_lower = 0.95, weak_upper = 0.99
    best_feh = weak_lower = 0.935, weak_upper = 0.98 
    this returns the parameters for a field of data  - and normalises if it is not already normalised 
    this is slow because it reads a pickle file 
    """
    file_in = open(fn_pickle, 'r') 
    dataall, metaall, labels, offsets, coeffs, covs, scatters,chis,chisqs = pickle.load(file_in)
    file_in.close()
    nstars = (testdata.shape)[1]
    nlabels = len(labels)
    Params_all = np.zeros((nstars, nlabels))
    MCM_rotate_all = np.zeros((nstars, nlabels, nlabels))
    for jj in range(0,nstars):
      if np.any(testdata[:,jj,0] != dataall[:, 0, 0]):
          print testdata[range(5),jj,0], dataall[range(5),0,0]
          assert False
      xdata = testdata[:,jj,0]
      ydata = testdata[:,jj,1]
      ysigma = testdata[:,jj,2]
      ydata_norm = ydata  - coeffs[:,0] # subtract the mean 
      coeffs_slice = coeffs[:,-3:]
      #ind1 = np.logical_and(logical_and(dataall[:,jj,0] > 16200., dataall[:,jj,0] < 16500.), np.logical_and(ydata > weak_lower , ydata < weak_upper)) 
      ind1 =  np.logical_and(ydata > weak_lower , ydata < weak_upper)
      Cinv = 1. / (ysigma ** 2 + scatters ** 2)
      MCM_rotate = np.dot(coeffs_slice[ind1].T, Cinv[:,None][ind1] * coeffs_slice[ind1])
      MCy_vals = np.dot(coeffs_slice[ind1].T, Cinv[ind1] * ydata_norm[ind1]) 
      Params = np.linalg.solve(MCM_rotate, MCy_vals)
      Params = Params + offsets 
      print Params
      Params_all[jj,:] = Params 
      MCM_rotate_all[jj,:,:] = MCM_rotate 
    file_in = open(fout_pickle, 'w')  
    pickle.dump((Params_all, MCM_rotate_all),  file_in)
    file_in.close()
    return Params_all , MCM_rotate_all


def lookatfits(fn_pickle, pixelvalues,testdataall): 
  #  """"
  #  this is to plot the individual pixel fits  on the 6x6 panel 
  #  """"
    file_in = open(fn_pickle, 'r') 
    testdataall, metaall, labels, offsets, coeffs, covs, scatters,chis,chisqs = pickle.load(file_in)
    file_in.close()
    axis_t, axis_g, axis_feh = metaall[:,0], metaall[:,1], metaall[:,2]
    nstars = (testdataall.shape)[1]
    offsets = np.mean(metaall, axis=0)
    features = np.ones((nstars, 1))
    features = np.hstack((features, metaall - offsets)) 
    features2 = np.hstack((features, metaall )) 
    for each in pixelvalues:
        flux_val_abs = testdataall[each,:,1]
        flux_val_norm = testdataall[each,:,1] - np.dot(coeffs, features.T)[each,:] 
        coeff = coeffs[each,:] 
        y_feh_abs = coeff[3]*features[:,3] + coeff[0]*features[:,0]
        y_feh_norm = coeff[3]*features[:,3] + coeff[0]*features[:,0]  -(coeff[3]*features2[:,3] + coeff[0]*features2[:,0]) 
        y_g_abs = coeff[2]*features[:,2] + coeff[0]*features[:,0]
        y_g_norm = coeff[2]*features[:,2] + coeff[0]*features[:,0]  - (coeff[2]*features2[:,2] + coeff[0]*features2[:,0]) 
        y_t_abs = coeff[1]*features[:,1] + coeff[0]*features[:,0] 
        y_t_norm = coeff[1]*features[:,1] + coeff[0]*features[:,0] - (coeff[1]*features2[:,1] + coeff[0]*features2[:,0]) 
        for flux_val, y_feh, y_g, y_t, namesave,lab,ylims in zip([flux_val_abs, flux_val_norm], [y_feh_abs,y_feh_norm],[y_g_abs, y_g_norm], [y_t_abs,y_t_norm],['abs','norm'], ['flux','flux - mean'],
                [[-0.2,1.2], [-1,1]] ): 
            y_meandiff = coeff[0] - flux_val 
            fig = plt.figure(figsize = [12.0, 12.0])
            #
            ax = plt.subplot(3,2,1)
            pick = testdataall[each,:,2] > 0.1
            ax.plot(metaall[:,2], flux_val, 'o',alpha =0.5,mfc = 'None', mec = 'r') 
            ax.plot(metaall[:,2][pick], flux_val[pick], 'kx',markersize = 10) 
            ax.plot(metaall[:,2], y_feh, 'k') 
            ind1 = argsort(metaall[:,2]) 
            ax.fill_between(sort(metaall[:,2]), array(y_feh + std(flux_val))[ind1], array(y_feh - std(flux_val))[ind1] , color = 'y', alpha = 0.2)
            ax.set_xlabel("[Fe/H]", fontsize = 14 ) 
            ax.set_ylabel(lab, fontsize = 14 ) 
            ax.set_title(str(np.int((testdataall[each,0,0])))+"  $\AA$")
            ax.set_ylim(ylims[0], ylims[1]) 
            #
            ax = plt.subplot(3,2,2)
            ax.plot(metaall[:,1], flux_val, 'o', alpha =0.5, mfc = 'None', mec = 'b') 
            ax.plot(metaall[:,1][pick], flux_val[pick], 'kx',markersize = 10)  
            ax.plot(metaall[:,1], y_g, 'k') 
            ind1 = argsort(metaall[:,1]) 
            ax.fill_between(sort(metaall[:,1]), array(y_g + std(flux_val))[ind1], array(y_g - std(flux_val))[ind1] , color = 'y', alpha = 0.2)
            ax.set_xlabel("log g", fontsize = 14 ) 
            ax.set_ylabel(lab, fontsize = 14 ) 
            ax.set_title(str(np.int((testdataall[each,0,0])))+"  $\AA$")
            ax.set_ylim(ylims[0], ylims[1]) 
            #
            ax = plt.subplot(3,2,3)
            ax.plot(metaall[:,0], flux_val, 'o',alpha =0.5, mfc = 'None', mec = 'green') 
            ax.plot(metaall[:,0][pick], flux_val[pick], 'kx', markersize = 10) 
            ax.plot(metaall[:,0], y_t, 'k') 
            ind1 = argsort(metaall[:,0]) 
            ax.fill_between(sort(metaall[:,0]), array(y_t + std(flux_val))[ind1], array(y_t - std(flux_val))[ind1] , color = 'y', alpha = 0.2)
            ax.set_xlabel("Teff", fontsize = 14 ) 
            ax.set_ylabel(lab, fontsize = 14 ) 
            ax.set_ylim(ylims[0], ylims[1]) 
            #
            ax = plt.subplot(3,2,4)
            diff_flux = coeffs[each,0] - testdataall[each,:,1] 
            xrange1 = arange(0,shape(testdataall)[1],1) 
            ind1 = argsort(metaall[:,2]) 
            ind1_pick = argsort(metaall[:,2][pick]) 
            ax.plot(xrange1, (coeffs[each,0] - testdataall[each,:,1])[ind1], 'o',alpha = 0.5, mfc = 'None', mec = 'grey') 
            ax.plot(xrange1[pick], (coeffs[each,0] - testdataall[each,:,1][pick])[ind1_pick], 'kx',markersize = 10) 
            ax.fill_between(xrange1, array(mean(diff_flux) + std(diff_flux)), array(mean(diff_flux) - std(diff_flux))  , color = 'y', alpha = 0.2)
            ax.set_xlabel("Star Number (increasing [Fe/H])", fontsize = 14 ) 
            ax.set_ylabel("flux star - mean flux", fontsize = 14 ) 
            ax.set_ylim(-1.0, 1.0) 
            #
            ax = plt.subplot(3,2,5)
            for indx, color, label in [
                                       ( 1, "g", "Teff"),
                                       ( 2, "b", "logg"),
                                       ( 3, "r", "FeH")]:
              _plot_something(ax, testdataall[:, 0, 0][each-10:each+10], coeffs[:, indx][each-10:each+10], covs[:, indx, indx][each-10:each+10], color, label=label)
            ax.axvline(testdataall[:,0,0][each],color = 'grey') 
            ax.axhline(0,color = 'grey',linestyle = 'dashed') 
            ax.set_xlim(testdataall[:,0,0][each-9], testdataall[:,0,0][each+9]) 
            ax.legend(loc = 4,fontsize  = 10) 
            ax.set_xlabel("Wavelength $\AA$", fontsize = 14 ) 
            ax.set_ylabel("coeffs T,g,FeH", fontsize = 14 ) 
            #
            ax = plt.subplot(3,2,6)
            _plot_something(ax, testdataall[:, 0, 0][each-10:each+10], coeffs[:, 0][each-10:each+10], covs[:, 0, 0][each-10:each+10], 'k', label='mean')
            ax.set_ylim(0.6,1.1) 
            ax.set_xlim(testdataall[:,0,0][each-9], testdataall[:,0,0][each+9]) 
            ax.legend(loc = 4,fontsize  = 10) 
            ax.axvline(testdataall[:,0,0][each],color = 'grey') 
            ax.axhline(0,color = 'grey',linestyle = 'dashed') 
            ax.set_xlabel("Wavelength $\AA$", fontsize = 14 ) 
            ax.set_ylabel("Mean flux", fontsize = 14 ) 

            savefig(fig, str(each)+"_"+str(namesave) , transparent=False, bbox_inches='tight', pad_inches=0.5)
            fig.clf()
       # return 

def _plot_something(ax, wl, val, var, color, lw=2, label=""):
    factor = 1.
    if label == "Teff": factor = 1000. # yes, I feel dirty; MAGIC
    sig = np.sqrt(var)
    ax.plot(wl, factor*(val+sig), color=color, lw=lw, label=label)
    ax.plot(wl, factor*(val-sig), color=color, lw=lw) 
    ax.fill_between(wl, factor*(val+sig), factor*(val-sig), color = color, alpha = 0.2) 
    return None
  
    

def savefig(fig, prefix, **kwargs):
 #   for suffix in (".png"):
    suffix = ".png"
    print "writing %s" % (prefix + suffix)
    fig.savefig(prefix + suffix)#, **kwargs)
    close() 


def leave_one_cluster_out():
# this is the test routine to leave one cluster out 
    dataall, metaall, labels, Ametaall, cluster_name, ids= get_normalized_training_data_tsch()
    nameu = unique(cluster_name) 
    nameu = array(nameu) 
    cluster_name = array(cluster_name)
    for each in nameu:
      clust_pick = each
      take = array(cluster_name) == clust_pick
      inds = arange(0,len(cluster_name),1) 
      inds1 = inds[take] 
      cluster_take = each #cluster_name[take][0]
      #return inds1, cluster_name
      train(dataall, metaall,  2,  fpickle2, Ametaall, cluster_name, logg_cut= 40.,teff_cut = 0., leave_out=inds1)
      field = "self_2nd_order_alpha_"
      file_in = open(normed_training_data, 'r') 
      testdataall, metaall, labels, Ametaall, cluster_name, ids = pickle.load(file_in)
      file_in.close() 
      testmetaall, inv_covars = infer_labels_nonlinear("coeffs_2nd_order_alpha.pickle", testdataall,ids, field+str(cluster_take)+"_tags_alpha.pickle",-10.950,10.99) 
      #plot_leave_one_out(field, clust_pick) 
    return 

def leave_one_star_out():
# this is the test routine to leave one star out 
    dataall, metaall, labels, Ametaall, cluster_name, ids= get_normalized_training_data()
    #nameu = unique(cluster_name) 
    #nameu = array(nameu) 
    cluster_name = array(cluster_name)
    ids = array(ids)
    idsnew = [] 
    for each in ids: 
      if len(ids) > 20:
        idsnew.append(each.split('2m')[-1]) 
      else: 
        idsnew.append(each.split)
    idsnew = array(idsnew) 
    nameu = [a+"_"+b for a,b in zip(cluster_name, idsnew)] 
    nameu = array(nameu) 
    for each in nameu:
      name_pick = each
      take = array(nameu) == name_pick
      inds = arange(0,len(cluster_name),1) 
      inds1 = inds[take] 
      star_take = each #cluster_name[take][0]
      #return inds1, cluster_name
      train(dataall, metaall,  2,  fpickle2, Ametaall, cluster_name, logg_cut= 40.,teff_cut = 0., leave_out=inds1)
      # up to here 
      field = "self_2nd_order_alpha_apokasc_gc_"
      file_in = open(normed_training_data, 'r') 
      testdataall, metaall, labels, Ametaall, cluster_name, ids = pickle.load(file_in)
      file_in.close() 
      testmetaall, inv_covars = infer_labels_nonlinear("coeffs_2nd_order_alpha_apokasc_gc.pickle", testdataall[:,take], idsnew[take], field+str(star_take)+"_itags_alpha_apokasc_gc_ind.pickle",-10.950,10.99) 
      #plot_leave_one_out(field, clust_pick) 
    return 

def plot_leave_one_out(filein,cluster_out): 
    file_in2 = open(filein+"tags_alpha_apokasc_gc_ind.pickle", 'r') 
    params, covs_params = pickle.load(file_in2)
    sp = shape(params) 
    params = array(params)
    covs_params = array(covs_params)
    file_in2.close()
    # this is the test to 
    filein2 = 'test14.txt' # originally had for test4g_self and for ages_test4g_self that goes with this
    filein2 = 'test18.txt' # originally had for test4g_self and for ages_test4g_self that goes with this
    filein3 = 'ages.txt' # note ages goes with test14 
    plot_markers = ['ko', 'yo', 'ro', 'bo', 'co','k*', 'y*', 'r*', 'b*', 'c*', 'ks', 'rs', 'bs', 'cs', 'rd', 'kd', 'bd', 'rd', 'mo', 'ms' ]
    # M92, M15, M53, N5466, N4147, M13, M2, M3, M5, M107, M71, N2158, N2420, Pleaides, N7789, M67, N6819 , N188, N6791 
    t,g,feh,t_err,feh_err = loadtxt(filein2, usecols = (4,6,8,16,17), unpack =1) 
    tA,gA,fehA = loadtxt(filein2, usecols = (3,5,7), unpack =1) 
    age = loadtxt(filein3, usecols = (0,), unpack =1) 
    g_err, age_err = [0]*len(g) , [0]*len(g) 
    g_err, age_err = array(g_err), array(age_err) 
    diffT = abs(array(t) - array(tA) ) 
    a = open(filein2) 
    al = a.readlines() 
    
    names = []
    for each in al:
      names.append(each.split()[1]) 
    diffT = array(diffT) 
    #pick =logical_and(names != cluster_name,  diffT < 600. ) 
    names = array(names) 
    #pick =  diffT < 600. # I need to implement this < 6000 K 
    #pick2 =logical_and(names == cluster_out,  diffT < 600. ) 
    pick =  diffT < 6000. # I need to implement this < 6000 K 
    pick2 =logical_and(names == cluster_out,  diffT < 6000. ) 

    t_sel,g_sel,feh_sel,t_err_sel,g_err_sel,feh_err_sel = t[pick2], g[pick2], feh[pick2], t_err[pick2], g_err[pick2], feh_err[pick2] 
    t,g,feh,t_err,g_err,feh_err = t[pick], g[pick], feh[pick], t_err[pick], g_err[pick], feh_err[pick] 
    #
    names = array(names) 
    names = names[pick] 
    unames = unique(names) 
    starind = arange(0,len(names), 1) 
    name_ind = [] 
    names = array(names) 
    for each in unames:
      takeit = each == names 
      name_ind.append(np.int(starind[takeit][-1]+1. ) )
    cluster_ind = [0] + list(sort(name_ind))# + [len(al)]
    #
    params_sel = array(params)[pick2]
    covs_params_sel = array(covs_params)[pick2]
    params = array(params)[pick]
    covs_params = array(covs_params)[pick]
    sp2 = shape(params) 
    sp3 = len(t) 
    rcParams['figure.figsize'] = 12.0, 10.0
    fig, temp = pyplot.subplots(3,1, sharex=False, sharey=False)
    fig = plt.figure() 
    ax = fig.add_subplot(111, frameon = 0 ) 
    ax.set_ylabel("The Cannon", labelpad = 40, fontsize = 20 ) 
    ax.tick_params(labelcolor= 'w', top = 'off', bottom = 'off', left = 'off', right = 'off' ) 
    ax1 = fig.add_subplot(311)
    ax2 = fig.add_subplot(312)
    ax3 = fig.add_subplot(313)

    params_labels = [params[:,0], params[:,1], params[:,2] ,  covs_params[:,0,0]**0.5, covs_params[:,1,1]**0.5, covs_params[:,2,2]**0.5 ]
    cval = ['k', 'b', 'r', ] 
    input_ASPCAP = [t, g, feh, t_err, g_err, feh_err ] 
    listit_1 = [0,1,2]
    listit_2 = [1,0,0]
    axs = [ax1,ax2,ax3]
    labels = ['teff', 'logg', 'Fe/H']
    for i in range(0,len(cluster_ind)-1): 
      indc1 = cluster_ind[i]
      indc2 = cluster_ind[i+1]
      for ax, num,num2,label1,x1,y1 in zip(axs, listit_1,listit_2,labels, [4800,3.0,0.3], [3400,1,-1.5]): 
        pick = logical_and(g[indc1:indc2] > 0, logical_and(t_err[indc1:indc2] < 300, feh[indc1:indc2] > -4.0) ) 
        cind = array(input_ASPCAP[1][indc1:indc2][pick]) 
        cind = array(input_ASPCAP[num2][indc1:indc2][pick]).flatten() 
        ax.plot(input_ASPCAP[num][indc1:indc2][pick], params_labels[num][indc1:indc2][pick], plot_markers[i]) 
    
    ax1.plot(params_sel[:,0], t_sel, 'y*', label = cluster_out, markersize = 14)
    ax2.plot(params_sel[:,1], g_sel, 'y*', label = cluster_out, markersize = 14)
    ax3.plot(params_sel[:,2], feh_sel, 'y*', label = cluster_out, markersize = 14)
    ax1.legend(loc=2,numpoints=1)
    ax2.legend(loc=2,numpoints=1)
    ax3.legend(loc=2,numpoints=1)
   
    ax1.text(5400,3700,"y-axis, $<\sigma>$ = "+str(round(mean(params_labels[0+3]),2)),fontsize = 14) 
    ax2.text(3.9,1,"y-axis, $<\sigma>$ = "+str(round(mean(params_labels[1+3]),2)),fontsize = 14) 
    ax3.text(-0.3,-2.5,"y-axis, $<\sigma>$ = "+str(round(mean(params_labels[2+3]),2)),fontsize = 14) 
    ax1.plot([0,6000], [0,6000], linewidth = 1.5, color = 'k' ) 
    ax2.plot([0,5], [0,5], linewidth = 1.5, color = 'k' ) 
    ax3.plot([-3,2], [-3,2], linewidth = 1.5, color = 'k' ) 
    ax1.set_xlim(3500, 6000) 
    ax1.set_ylim(1000,6000)
    ax1.set_ylim(3500,6000)
    ax2.set_xlim(0, 5) 
    ax3.set_xlim(-3, 1) 
    ax1.set_xlabel("ASPCAP Teff, [K]", fontsize = 14,labelpad = 5) 
    ax1.set_ylabel("Teff, [K]", fontsize = 14,labelpad = 5) 
    ax2.set_xlabel("ASPCAP logg, [dex]", fontsize = 14,labelpad = 5) 
    ax2.set_ylabel("logg, [dex]", fontsize = 14,labelpad = 5) 
    ax3.set_xlabel("ASPCAP [Fe/H], [dex]", fontsize = 14,labelpad = 5) 
    ax3.set_ylabel("[Fe/H], [dex]", fontsize = 14,labelpad = 5) 
    ax2.set_ylim(0,5)
    ax3.set_ylim(-3,1) 
    fig.subplots_adjust(hspace=0.22)
    prefix = "/Users/ness/Downloads/Apogee_Raw/calibration_apogeecontinuum/documents/plots/"+str(cluster_out)+"_out"
    savefig2(fig, prefix, transparent=False, bbox_inches='tight', pad_inches=0.5)
    close("all")
    print sp, sp2, sp3
    return 

if __name__ == "__main__":
    pixlist = loadtxt("pixtest4.txt", usecols = (0,), unpack =1) 
    #dataall, metaall, labels, Ametaall, cluster_name, ids = get_normalized_training_data()
    dataall, metaall, labels, Ametaall, cluster_name, ids = get_normalized_training_data_tsch(pixlist)
    fpickle = "coeffs.pickle" 
    if not glob.glob(fpickle):
        train(dataall, metaall, 1,  fpickle, Ametaall,cluster_name, logg_cut= 40.,teff_cut = 0.)
    fpickle2 = "coeffs_2nd_order_alpha_apokasc_gc_ind.pickle"
    if not glob.glob(fpickle2):
        train(dataall, metaall, 2,  fpickle2, Ametaall, cluster_name, logg_cut= 40.,teff_cut = 0.)
    self_flag = 2
    self_flag = 1
    self_flag = 0
    self_flag = 2
    self_flag = 0
    
    if self_flag < 1:
      startTime = datetime.now()
      a = open('all.txt', 'r') 
      a = open('redclump2.txt', 'r')
      a = open('redclump3.txt', 'r')
      a = open('redclump4.txt', 'r')
      a = open('redclump5.txt', 'r')
      #a = open('all_test.txt', 'r') 
      #a = open('all_test.txt', 'r') 
      #a = open('all_test2.txt', 'r') 
      #a = open('all_test3.txt', 'r') 
      al = a.readlines()
      bl = []
      for each in al:
        bl.append(each.strip()) 
      for each in bl: 
        testfile = each
        field = testfile.split('.txt')[0]+'_' #"4332_"
        #testdataall, ids = get_normalized_test_data(testfile) # if flag is one, do on self 
        testdataall, ids = get_normalized_test_data_tsch(testfile,pixlist)
        testmetaall, inv_covars = infer_labels_nonlinear("coeffs_2nd_order_alpha_apokasc_gc_ind.pickle", testdataall, ids, field+"tags_chi2_df_v1_alpha_apokasc_gc_ind.pickle",0.00,1.40) 
        print(datetime.now()-startTime)
    if self_flag == 1:
      field = "self_alpha_"
      file_in = open(normed_training_data, 'r') 
      testdataall, metaall, labels, Ametaall, cluster_name,ids = pickle.load(file_in)
      lookatfits('coeffs_alpha.pickle',[1002,1193,1383,1496,2803,4000,4500, 5125],testdataall)
      file_in.close() 
      testmetaall, inv_covars = infer_labels("coeffs_alpha.pickle", testdataall, field+"tags_alpha.pickle",-10.960,11.03) 
    if self_flag == 2:
      field = "self_2nd_order_"
      file_in = open(normed_training_data, 'r') 
      testdataall, metaall, labels, Ametaall, cluster_name,ids = pickle.load(file_in)
      file_in.close() 
      testmetaall, inv_covars = infer_labels_nonlinear("coeffs_2nd_order_alpha_apokasc_gc_ind.pickle", testdataall, ids, field+"tags_alpha_apokasc_gc_ind.pickle",-10.950,10.99) 
    if self_flag == 3:
      leave_one_star_out()
      #leave_one_cluster_out()
