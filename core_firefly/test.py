# -*- coding: utf-8 -*-
"""
Created on Thu Mar 26 20:24:04 2020

@author: Oli
"""
from astropy.io import fits
import numpy as np

#input_files = ["/Users/User/Documents/University/Third_Year/Project/Webstie/firefly_website/core_firefly/example_data/spectra/0266/spec-0266-51602-0573.fits", r"/Users/User/Documents/University/Third_Year/Project/Webstie/firefly_website/core_firefly/example_data/spectra/0266/spec-0266-51602-0573.fits", r"/Users/User/Documents/University/Third_Year/Project/Webstie/firefly_website/core_firefly/example_data/spectra/0266/spec-0266-51602-0573.fits"]
input_files = ["/Users/User/Documents/University/Third_Year/Project/Webstie/firefly_website/core_firefly/example_data/spectra/0266/spec-0266-51602-0573.fits", 
               "/Users/User/Documents/University/Third_Year/Project/Webstie/firefly_website/core_firefly/example_data/spectra/0266/spec-0266-51630-0623.fits",
               "/Users/User/Documents/University/Third_Year/Project/Webstie/firefly_website/core_firefly/example_data/spectra/1045/spec-1045-52725-0628.fits"]

flux       = np.array([])
loglam     = np.array([])
ivar       = np.array([])
redshift = np.array([])
vdisp    = np.array([])
ra       = np.array([])
dec      = np.array([])


max_length = 0

for file in input_files:
    
    hdulist = fits.open(file)

    if max_length < len(hdulist[1].data['flux']):
        max_length = len(hdulist[1].data['flux'])
    
    hdulist.close()

for file in input_files:
    
    hdulist = fits.open(file)

    temp_flux = hdulist[1].data['flux']
    temp_flux = np.pad(hdulist[1].data['flux'], (0,max_length - len(temp_flux)), mode='constant', constant_values=0)
    flux      = np.append(flux, temp_flux)
    
    temp_loglam = hdulist[1].data['loglam']
    temp_loglam = np.pad(hdulist[1].data['loglam'], (0, max_length - len(temp_loglam)), mode='constant', constant_values=0)
    loglam      = np.append(loglam, temp_loglam)
    
    temp_ivar = hdulist[1].data['ivar']
    temp_ivar = np.pad(hdulist[1].data['ivar'], (0, max_length - len(temp_ivar)), mode='constant', constant_values=0)
    ivar      = np.append(ivar, temp_ivar)
    
    ra = np.append(ra, hdulist[0].header['RA'])
    dec = np.append(dec, hdulist[0].header['DEC'])
    redshift = np.append(redshift, hdulist[2].data['Z']) 
    vdisp = np.append(vdisp, hdulist[2].data['VDISP'])
    
    hdulist.close()
 
flux   = np.reshape(flux,   (len(input_files), max_length)) 
loglam = np.reshape(loglam, (len(input_files), max_length))
ivar   = np.reshape(ivar,   (len(input_files), max_length))

array_format = str(max_length) + 'D'

col1 = fits.Column(name ='flux',   format = array_format, array = flux)
col2 = fits.Column(name ='loglam', format = array_format, array = loglam)
col3 = fits.Column(name ='ivar',   format = array_format, array = ivar)
col4 = fits.Column(name ='Z',      format = 'D', array = redshift)
col5 = fits.Column(name ='vdisp',  format = 'D', array = vdisp)
col6 = fits.Column(name ='ra',     format = 'D', array = ra)
col7 = fits.Column(name ='dec',    format = 'D', array = dec)

coldefs = fits.ColDefs([col1, col2, col3, col4, col5, col6, col7])
hdul    = fits.BinTableHDU.from_columns(coldefs)

hdul.writeto('testtable.fits', overwrite=True)