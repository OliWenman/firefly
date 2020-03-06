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

class Firefly():

	def __init__(self):

		#FF_DIR = sys.path.append(os.getcwd())
		#FF_DIR = os.getcwd()
		FF_DIR = "/Users/User/Documents/University/Third_Year/Project/Webstie/firefly_website/core_firefly/"


		os.environ['FF_DIR'] = FF_DIR

		STELLARPOPMODELS_DIR = os.path.join(FF_DIR, 'stellar_population_models')
		os.environ['STELLARPOPMODELS_DIR'] = STELLARPOPMODELS_DIR

		self.cosmo = co.Planck15

		#specify whether write results
		self.write_results    = True
		self.override_results = True


	def set_enviromment_var(var: str, path: str):
		
		os.environ[var] = path


	def model_input(self):

		self.redshift = 1.33

		# RA and DEC
		self.ra=53.048
		self.dec=-27.72

		#velocity dispersion in km/s
		self.vdisp = 220.


	def file_input(self, input_file:str):

		#input file with path to read in wavelength, flux and flux error arrays
		#the example is for an ascii file with extension 'ascii'
		self.input_file = input_file
		self.data = np.loadtxt(self.input_file, unpack=True)
		self.lamb = self.data[0,:]

		try:
			self.wavelength = self.data[0,:][np.where(self.lamb>3600*(1+self.redshift))]
			self.flux = self.data[1,:][np.where(self.lamb>3600*(1+self.redshift))]
			self.error = self.flux*0.1
			self.restframe_wavelength = self.wavelength/(1+self.redshift)

			#instrumental resolution
			self.r_instrument = np.zeros(len(self.wavelength))

			for wi, w in enumerate(self.wavelength):
				self.r_instrument[wi] = 600

		except AttributeError: 
			_, ex, traceback = sys.exc_info()
			message = "FIREFLY ERROR - Call the model_input() function first to gain a redshift value."

			raise AttributeError(message)

	def settings(self,
				 models_key,
				 ageMin,
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
		self.ageMax     = self.cosmo.age(self.redshift).value
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
		emission_dict = {'HeII' : 3202.15,
						 'NeV'  : (3345.81, 3425.81),
						 'OII'  : (3726.03, 3728.73),
						 'NeIII': (3868.69, 3967.40),
						 'H5'   : 3889.05,
						 'He'   : 3970.07,
						 'Hd'   : 4101.73,
						 'Hg'   : 4340.46,
						 'OIII' : (4363.15, 4958.83, 5006.77),
						 'HeII' : 4685.74,
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


	def run(self, outputFolder, file_id):

		#set output folder and output filename in firefly directory 
		#and write output file

		t0 = time.time()

		#outputFolder = "/Users/User/Documents/University/Third_Year/Project/Webstie/firefly_website/media"
		try:
			output_file = join( outputFolder , 'spFly-' + os.path.basename( self.input_file )[0:-6] ) + ".fits"
		except(TypeError):
			output_file = join( outputFolder , 'spFly-' + self.input_file.name)[0:-6] + "_" +str(file_id) + ".fits"


		if os.path.isfile(output_file) and self.override_results == False:
			print()
			print('Warning: This object has already been processed, the file will be over-witten.')
			answer = input('** Do you want to continue? (Y/N)')    
			if (answer=='N' or answer=='n'):
				#sys.exit()
				return
			if os.name != 'nt':
				subprocess.call(['/bin/rm','-r',output_file])
			else:
				os.remove(output_file)
		if os.path.isdir(outputFolder)==False:
			os.mkdir(outputFolder)
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
		prihdr['HIERARCH age_universe']	= np.round(self.cosmo.age(self.redshift).value,3)
		prihdu = spm.pyfits.PrimaryHDU(header=prihdr)
		tables = [prihdu]

		#define input object to pass data on to firefly modules and initiate run
		spec=setup.firefly_setup(path_to_spectrum  = self.input_file, 
								 N_angstrom_masked = self. N_angstrom_masked)
		
		spec.openSingleSpectrum(self.wavelength, 
								self.flux, 
								self.error, 
								self.redshift, 
								self.ra, 
								self.dec, 
								self.vdisp, 
								self.lines_mask, 
								self.r_instrument)

		#spec.openMANGASpectrum(data_release, path_to_logcube, path_to_drpall, bin_number, plate_number, ifu_number)

		did_not_converge = 0.
		try :
			#prepare model templates
			model = spm.StellarPopulationModel(spec, 
											   output_file, 
											   self.cosmo, 
											   models = self.models_key, 
											   model_libs = self.model_libs, 
											   imfs = self.imfs, 
											   age_limits = [self.ageMin,self.ageMax], 
											   downgrade_models = self.downgrade_models, 
											   data_wave_medium = self.data_wave_medium, 
											   Z_limits = [self.ZMin, self.ZMax], 
											   use_downgraded_models = False, 
											   write_results = self.write_results, 
											   flux_units = self.flux_units)
			#initiate fit
			model.fit_models_to_data()
			tables.append( model.tbhdu )
		except (ValueError):
			tables.append( model.create_dummy_hdu() )
			did_not_converged +=1
			print('did not converge')
		if did_not_converge < 1 :
			complete_hdus = spm.pyfits.HDUList(tables)
			if os.path.isfile(output_file):
				os.remove(output_file)		
			complete_hdus.writeto(output_file)

		print()
		print ("Done... total time:", int(time.time()-t0) ,"seconds.")
		print()
		return output_file

