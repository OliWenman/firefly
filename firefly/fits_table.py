from astropy.io import fits
import numpy as np
import os

class Fits_Table:

	def __init__(self, file):
		
		hdul = fits.open(file)

		self.file_okay = True

		try:
			self.spectra_array = hdul[1].data['spectra']
			self.flux_array    = hdul[1].data['flux']
			self.loglam_array  = hdul[1].data['loglam']
			self.ivar_array    = hdul[1].data['ivar']

			self.redshift_array = hdul[1].data['Z']
			self.vdisp_array    = hdul[1].data['vdisp']
			self.ra_array       = hdul[1].data['ra']
			self.dec_array      = hdul[1].data['dec']

			self.n_spectra      = len(self.spectra_array)
			self.length_spectra = len(self.flux_array) 
		
		except:
			self.file_okay = False

		hdul.close()
