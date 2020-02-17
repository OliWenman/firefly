from astropy.io import fits

import os

cur_path = os.getcwd()

file_path = os.path.join(cur_path, 'example_data', 'spectra', '0266', 'spec-0266-51630-0623.fits')

hdul = fits.open(file_path)

data_set0 = hdul[0].data
data_set1 = hdul[1].data
data_set2 = hdul[2].data


#Input file variables
#flux - 3600 a conversion?
#wavelength - 3600 a conversion?

#Model variables?
#redshift = data_set2['Z']
#ra = data_set2['PLUG_RA']?
#dec = data_set2['PLUG_DEC]?
#vdisp = data_set1['vdisp']
#r_instrument = data_set2['INSTRUMENT']???
#N_angstrom_masked
#lines_mask - Lots of variables?
#models_key - manual 
#ageMin
#ageMax = cosmo.age(redshift).value
#ZMin choice 
#ZMax choice


#model_libs
#imfs
#data_wave_medium
#flux_units
#downgrade_models

hdul.close()