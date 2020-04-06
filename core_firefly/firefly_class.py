"""
.. moduleauthor:: Daniel Thomas <daniel.thomas__at__port.ac.uk>
.. contributions:: Johan Comparat <johan.comparat__at__gmail.com>
.. contributions:: Violeta Gonzalez-Perez <violegp__at__gmail.com>

Firefly is initiated with this script. 
All input data and parmeters are now specified in this one file.

"""

#import python
#import stellar_population_models

import numpy as np
import sys, os
from os.path import join
import time

import astropy.cosmology as co
import subprocess

import core_firefly.firefly.firefly_setup as setup
import core_firefly.firefly.firefly_models as spm

from astropy.io import fits

class Firefly():

	def __init__(self):

		FF_DIR = os.path.dirname(os.path.abspath(__file__))

		os.environ['FF_DIR'] = FF_DIR

		STELLARPOPMODELS_DIR = os.path.join(FF_DIR, 'stellar_population_models')
		os.environ['STELLARPOPMODELS_DIR'] = STELLARPOPMODELS_DIR

		os.environ['OBJC_DISABLE_INITIALIZE_FORK_SAFETY'] = 'yes'
		print(os.environ)

		self.cosmo = co.Planck15

		#specify whether write results
		self.write_results    = True
		self.override_results = True
		self.N_angstrom_masked = 20


	def set_enviromment_var(var: str, path: str):
		
		os.environ[var] = path


	def model_input(self,
					redshift,
					ra,
					dec,
					vdisp,
					r_instrument):

		self.redshift = redshift#1.33

		# RA and DEC
		self.ra  = ra#53.048
		self.dec = dec#-27.72

		#velocity dispersion in km/s
		self.vdisp = vdisp#220.
		self.r_instrument_value = r_instrument

	def settings(self,
				 models_key,
				 ageMin,
				 ageMax,
				 ZMin,
				 ZMax,
				 model_libs,
				 imfs,
				 data_wave_medium,
				 flux_units,
				 downgrade_models):

		# masking emission lines
		# N_angstrom_masked set to 20 in _init_ function
		"""
		self.N_angstrom_masked = 20 #20
		self.lines_mask = ((self.restframe_wavelength > 3728 - self.N_angstrom_masked) & (self.restframe_wavelength < 3728 + self.N_angstrom_masked)) | ((self.restframe_wavelength > 3726.03 - self.N_angstrom_masked) & (self.restframe_wavelength < 3726.03 + self.N_angstrom_masked))
		n = 1

		for i in range(len(self.restframe_wavelength)):

			if self.lines_mask[i] == True:
				print(n, ")", self.restframe_wavelength[i])
				n += 1
		"""

		#key which models and minimum age and metallicity of models to be used 
		self.models_key = models_key #'m11'
		self.ageMin     = ageMin #0.
		self.ageMax     = ageMax
		self.ZMin       = ZMin #0.001 
		self.ZMax       = ZMax #10.

		#model flavour
		self.model_libs= [model_libs] #['MILES']

		#model imf
		self.imfs = [imfs] #['kr']

		#specify whether data in air or vaccum
		self.data_wave_medium = data_wave_medium #'air'

		#Firefly assumes flux units of erg/s/A/cm^2.
		#Choose factor in case flux is scaled
		#(e.g. flux_units=10**(-17) for SDSS)
		self.flux_units= flux_units #1

		#specify whether models should be downgraded 
		#to the instrumental resolution and galaxy velocity dispersion
		self.downgrade_models = downgrade_models #True

	def mask_emissionlines(self, element_emission_lines,  N_angstrom_masked = 20):

		"""
		Firefly needs to mask emission lines of elements as this can affect the fitting.
		"""
		self.N_angstrom_masked = N_angstrom_masked

		#Dictionary of corrosponding elements to their emission lines
		emission_dict = {'HeII' : (3202.15, 4685.74),
						 'NeV'  : (3345.81, 3425.81),
						 'OII'  : (3726.03, 3728.73),
						 'NeIII': (3868.69, 3967.40),
						 'H5'   : 3889.05,
						 'He'   : 3970.07,
						 'Hd'   : 4101.73,
						 'Hg'   : 4340.46,
						 'OIII' : (4363.15, 4958.83, 5006.77),
						 'ArIV' : (4711.30, 4740.10),
						 'Hb'   : 4861.32,
						 'NI'   : (5197.90, 5200.39),
						 'HeI'  : 5875.60,
						 'OI'   : (6300.20, 6363.67),
						 'NII'  : (6547.96, 6583.34),
						 'Ha'   : 6562.80,
						 'SII'  : (6716.31, 6730.68),
						 'ArIII': 7135.67}

		#Create an array full of booleans equal to False, same size as the restframe_wavelength
		self.lines_mask = np.full((len(self.restframe_wavelength)), False, dtype=bool) 

		#Loop through the input of the emission lines list
		for i in range(len(element_emission_lines)):

			#Check if the value is in the dictionary
			if element_emission_lines[i] in emission_dict:

				ele_line = element_emission_lines[i]
				line = emission_dict[ele_line]

				#Check if it contains a tuple (some elements have more then one emission line)
				if type(line) == tuple:

					#Find the number of emission lines for this value
					n_lines = len(line)

					#Loop through and mask them
					for n in range(n_lines):

						n_line = line[n]

						#Creates the boolean array
						temp_lines_mask = ((self.restframe_wavelength > n_line - self.N_angstrom_masked) & (self.restframe_wavelength < n_line + self.N_angstrom_masked))
						#Adds the boolean array to the exisiting one to save it
						self.lines_mask = (temp_lines_mask | self.lines_mask)
						
				else:
					temp_lines_mask = ((self.restframe_wavelength > line - self.N_angstrom_masked) & (self.restframe_wavelength < line + self.N_angstrom_masked))
					self.lines_mask = (temp_lines_mask | self.lines_mask)

			else:
				raise KeyError

		print(self.lines_mask)

		n = 1

		for i in range(len(self.restframe_wavelength)):

			if self.lines_mask[i] == True:
				print(n, ")", self.restframe_wavelength[i])
				n += 1


	def run(self, 
			input_file, 
			output_file,
			emissionline_list,
			N_angstrom_masked,
			n_spectrum):

		#set output folder and output filename in firefly directory 
		#and write output file

		#input file with path to read in wavelength, flux and flux error arrays
		#the example is for an ascii file with extension 'ascii'
		self.input_file = input_file

		file_extension = os.path.splitext(input_file)[1]			
		if file_extension == ".ascii":

			data = np.loadtxt(self.input_file, unpack=True)
			lamb = data[0,:]

			self.wavelength = data[0,:][np.where(lamb>3600*(1+self.redshift))]
			self.flux = data[1,:][np.where(lamb>3600*(1+self.redshift))]
			self.error = self.flux*0.1
			#self.restframe_wavelength = self.wavelength/(1+self.redshift)

			#instrumental resolution
			self.r_instrument = np.zeros(len(self.wavelength))

			for wi, w in enumerate(self.wavelength):
				self.r_instrument[wi] = self.r_instrument_value

		else:
			hdul = fits.open(input_file)

			self.flux       = hdul[1].data['flux'][n_spectrum]
			self.wavelength = 10**hdul[1].data['loglam'][n_spectrum]
			self.ivar       = hdul[1].data['ivar'][n_spectrum]

			self.redshift = hdul[1].data['Z'][n_spectrum]
			self.vdisp    = hdul[1].data['vdisp'][n_spectrum]
			self.ra       = hdul[1].data['ra'][n_spectrum]
			self.dec      = hdul[1].data['dec'][n_spectrum]

			hdul.close()

		if self.ageMax is None:
			self.ageMax = self.cosmo.age(self.redshift).value

		print(self.ageMax)
		self.restframe_wavelength = self.wavelength / (1.0+self.redshift)
		self.mask_emissionlines(element_emission_lines = emissionline_list,
								N_angstrom_masked = N_angstrom_masked)

		t0 = time.time()

		"""
		if file_extension == ".ascii":
			n = -6
		elif file_extension == ".fits":
			n = -5	

		output_file = join( outputFolder , 'spFly-' + os.path.basename( self.input_file )[0:n] ) + ".fits"
		"""

		print()
		print( 'Output file: ', output_file                 )
		print()
		prihdr              = spm.pyfits.Header()
		prihdr['FILE']      = os.path.basename(output_file)
		prihdr['MODELS']	= self.models_key
		prihdr['FITTER']	= "FIREFLY"	
		prihdr['AGEMIN']	= str(self.ageMin)		
		prihdr['AGEMAX']	= str(self.ageMax)
		prihdr['ZMIN']	    = str(self.ZMin)
		prihdr['ZMAX']	    = str(self.ZMax)
		prihdr['redshift']	= self.redshift
		prihdr['HIERARCH age_universe']	= np.round(self.ageMax, 3)
		prihdu = spm.pyfits.PrimaryHDU(header=prihdr)
		tables = [prihdu]

		#define input object to pass data on to firefly modules and initiate run
		spec=setup.firefly_setup(path_to_spectrum  = self.input_file, 
								 N_angstrom_masked = self. N_angstrom_masked)
		
		if file_extension == ".ascii":
			spec.openSingleSpectrum(self.wavelength, 
									self.flux, 
									self.error, 
									self.redshift, 
									self.ra, 
									self.dec, 
									self.vdisp, 
									self.lines_mask, 
									self.r_instrument)
		else:
			spec.openWebsiteData(lines_mask = self.lines_mask,
								 n_spectrum = n_spectrum)
		#spec.openMANGASpectrum(data_release, path_to_logcube, path_to_drpall, bin_number, plate_number, ifu_number)

		self.did_not_converge = 0.
		try :
			#prepare model templates
			model = spm.StellarPopulationModel(spec, 
											   output_file, 
											   self.cosmo, 
											   models                = self.models_key, 
											   model_libs            = self.model_libs, 
											   imfs                  = self.imfs, 
											   age_limits            = [self.ageMin,self.ageMax], 
											   downgrade_models      = self.downgrade_models, 
											   data_wave_medium      = self.data_wave_medium, 
											   Z_limits              = [self.ZMin, self.ZMax], 
											   use_downgraded_models = False, 
											   write_results         = self.write_results, 
											   flux_units            = self.flux_units)
			#initiate fit
			model.fit_models_to_data()
			tables.append( model.tbhdu )

		except (ValueError):
			tables.append(model.create_dummy_hdu())
			print('did not converge')

		complete_hdus = spm.pyfits.HDUList(tables)
		complete_hdus.writeto(output_file, overwrite=True)

		print()
		print ("Done... total time:", int(time.time()-t0) ,"seconds.")
		print()
		return output_file

