from astropy.io import fits
import astropy.cosmology as co
import matplotlib.pyplot as plt
import numpy as np
import os

cur_path = os.getcwd()
file_path = os.path.join("example_data", "spectra", "NGC7099_2016-10-01.fits")#'example_data', 'spectra', '1045','spec-1045-52725-0628.fits')
fits.info(file_path)
"""
hdul = fits.open(file_path)
data_set0 = hdul[0].data
data_set1 = hdul[1].data
data_set2 = hdul[2].data

#=====================================================================================
#Section 1 - automatic from fits file?

#Variables from fits file?
redshift = data_set2['Z']
ra       = data_set2['PLUG_RA']  #Not consistant, RA or PLUG_RA?
dec      = data_set2['PLUG_DEC'] #Not consistant, DEC or PLUG_DEC?
vdisp    = data_set2['VDISP']

lamb       = 10**data_set1['loglam']
wavelength = lamb[np.where(lamb > 3600 * (1 + redshift))]
flux       = data_set1['flux'][np.where(lamb > 3600 * (1 + redshift))]
error      = data_set1['ivar'] #??
restframe_wavelength = wavelength/(1+redshift)
r_instrument = np.zeros(len(wavelength))
for wi, w in enumerate(wavelength):
    r_instrument[wi] = 600 #1800#Where is the resolution in the file? Optional input?

#=====================================================================================
#Section 2 - User inputs or automatic?

#EMISSION LINES - User inputs or read from the file?
lines_mask = data_set1['or_mask']
#N_angstrom_masked = ?

ageMin = 0. #Always zero?# input
ageMax = co.Planck15.age(redshift).value #Always this value? #input

ZMin   = 0.0001 # user input or from fits file?
ZMax   = 10    # user input or from fits file?

#=====================================================================================
#Section 3

#User inputs
models_key       = 'm11'
model_libs       = ['MILES']
imfs             = ['kr']
data_wave_medium = 'air'
flux_units       = 1
downgrade_models = True


plt.plot(wavelength, flux)
plt.show()

hdul.close()

#User fills in the inputs (section 3)
#Uploads file
#If .fits, find the remaining variables, if missing variables say invalid file. Follow the example data
#If .ascii, user manually fills in inputs such as redshift, ra, etc
"""
def fits_file(file):

	hdul = fits.open(file)
	data_set0 = hdul[0].data
	data_set1 = hdul[1].data
	data_set2 = hdul[2].data

	variable_list1 = ['loglam', 'flux', 'ivar']
	variable_list2 = ['Z', 'PLUG_RA', 'PLUG_DEC', 'VDISP']
	error_list     = []

	for i in range(len(variable_list1)):
		try:
			data_set1[variable_list1[i]]
		except(KeyError):
			error_list.append(variable_list1[i])

	for i in range(len(variable_list2)):
		try:
			data_set2[variable_list2[i]]
		except(KeyError):
			error_list.append(variable_list2[i])

	print(error_list)

	hdul.close()

	return error_list

    
#fits_file(file_path)
