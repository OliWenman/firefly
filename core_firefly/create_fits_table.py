# -*- coding: utf-8 -*-
"""
Created on Thu Mar 26 20:24:04 2020

@author: Oli
"""
from astropy.io import fits
import numpy as np
import os
import matplotlib.pyplot as plt

#input_files = ["/Users/User/Documents/University/Third_Year/Project/Webstie/firefly_website/core_firefly/example_data/spectra/0266/spec-0266-51602-0573.fits", r"/Users/User/Documents/University/Third_Year/Project/Webstie/firefly_website/core_firefly/example_data/spectra/0266/spec-0266-51602-0573.fits", r"/Users/User/Documents/University/Third_Year/Project/Webstie/firefly_website/core_firefly/example_data/spectra/0266/spec-0266-51602-0573.fits"]
input_files = ["/Users/User/Documents/University/Third_Year/Project/Webstie/firefly_website/core_firefly/example_data/spectra/0266/spec-0266-51602-0573.fits", 
               "/Users/User/Documents/University/Third_Year/Project/Webstie/firefly_website/core_firefly/example_data/spectra/0266/spec-0266-51630-0623.fits",
               "/Users/User/Documents/University/Third_Year/Project/Webstie/firefly_website/core_firefly/example_data/spectra/1045/spec-1045-52725-0628.fits",
               "/Users/User/Documents/University/Third_Year/Project/Webstie/firefly_website/core_firefly/example_data/spectra/3586/spec-3586-55181-0003.fits"]

output_file = 'testtable2.fits'

spectra_name = np.array([])
flux         = np.array([])
loglam       = np.array([])
ivar         = np.array([])
redshift     = np.array([])
vdisp        = np.array([])
ra           = np.array([])
dec          = np.array([])

max_length = 0

#Loop through files, check which one has the largest array
for file in input_files:
    
    hdulist = fits.open(file)

    if max_length < len(hdulist[1].data['flux']):
        max_length = len(hdulist[1].data['flux'])
    
    hdulist.close()

zero_array = np.zeros(max_length)
#Loop through the files
for file in input_files:
    
    hdulist = fits.open(file)

    #Find flux, pad it out with the last value if its smaller then the largest array so all are same length
    #Append it to the flux array
    #temp_flux = hdulist[1].data['flux']
    #temp_flux = np.pad(hdulist[1].data['flux'], (0,max_length - len(temp_flux)), mode='constant', constant_values=0)
    #flux = np.append(flux, temp_flux)


    new_length = max_length - len(hdulist[1].data['flux'])
    temp_flux = np.append(hdulist[1].data['flux'], np.full(shape = new_length, fill_value = hdulist[1].data['loglam'][-1]))
    flux = np.append(flux, temp_flux)

    #Find loglam, pad it out with the last value if its smaller then the largest array so all are same length
    #Append it to the loglam array
    temp_loglam = np.append(hdulist[1].data['loglam'], np.full(shape = new_length, fill_value = hdulist[1].data['loglam'][-1]))
    loglam = np.append(loglam, temp_loglam)

    #Find ivar, pad it out with the last value if its smaller then the largest array so all are same length
    #Append it to the ivar array
    temp_ivar = np.append(hdulist[1].data['ivar'], np.full(shape = new_length, fill_value = hdulist[1].data['ivar'][-1]))
    ivar = np.append(ivar, temp_ivar)
    
    spectra_name = np.append(spectra_name, os.path.basename(file))
    ra           = np.append(ra, hdulist[0].header['RA'])
    dec          = np.append(dec, hdulist[0].header['DEC'])
    redshift     = np.append(redshift, hdulist[2].data['Z']) 
    vdisp        = np.append(vdisp, hdulist[2].data['VDISP'])
    
    hdulist.close()

#Reshape the arrays so they are 2D
flux   = np.reshape(flux,   (len(input_files), max_length)) 
loglam = np.reshape(loglam, (len(input_files), max_length))
ivar   = np.reshape(ivar,   (len(input_files), max_length))

#Store the arrays in the correct format
array_format = str(max_length) + 'D'

#Create the columns for the fits table
col0 = fits.Column(name ='spectra',format = '20A', array = spectra_name)
col1 = fits.Column(name ='flux',   format = array_format, array = flux)
col2 = fits.Column(name ='loglam', format = array_format, array = loglam)
col3 = fits.Column(name ='ivar',   format = array_format, array = ivar)
col4 = fits.Column(name ='Z',      format = 'D', array = redshift)
col5 = fits.Column(name ='vdisp',  format = 'D', array = vdisp)
col6 = fits.Column(name ='ra',     format = 'D', array = ra)
col7 = fits.Column(name ='dec',    format = 'D', array = dec)

#Add the columns and save the table
coldefs = fits.ColDefs([col0, col1, col2, col3, col4, col5, col6, col7])
hdul    = fits.BinTableHDU.from_columns(coldefs)
#hdul.header['OBSERVER'] = 'Edwin Hubble'

hdul.writeto(output_file, overwrite=True)


hdul = fits.open(output_file)

flux_array = hdul[1].data['flux']

print(hdul[1].header)

max_spectra = 100
for i in range(len(flux_array)):

    if i >= max_spectra:
        i = max_spectra
        break

    flux   = flux_array[i]
    loglam = hdul[1].data['loglam'][i]
    ivar   = hdul[1].data['ivar'][i]

    redshift = hdul[1].data['Z'][i]
    vdisp    = hdul[1].data['vdisp'][i]
    ra       = hdul[1].data['ra'][i]
    dec      = hdul[1].data['dec'][i]

    #plt.plot(10**loglam, flux)

hdul.close()
a = np.full((3), 0)
print(a)
print(type(a.dtype))