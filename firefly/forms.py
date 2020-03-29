from django import forms
from django.core.exceptions import ValidationError
from django.conf import settings

from .models import SED

import time
import numpy as np
import os
from astropy.io import fits
from .fits_table import Fits_Table

class SEDform(forms.ModelForm):
	class Meta:
		model = SED
		fields = ('output_file',)

	def is_valid(self, file):
		
		valid = super(SEDform, self).is_valid()
		try:
			np.loadtxt(file, unpack=True)
			valid2 = True
		except(ValueError):
			valid2 = False
		
		if valid and valid2 == True:
			return True
		else:
			return False


class SEDfileform(forms.Form):
	
	def __init__(self, *args, **kwargs):

		super(SEDfileform, self).__init__(*args, **kwargs)
		extra_inputs = kwargs.pop('extra', None)

		if extra_inputs != None:
		
			for i in range(len(extra_inputs)):
				# generate extra fields
				self.fields[extra_inputs[i]] = forms.DecimalField(required=True)

	def validate_file_okay(value):
		
		ext = os.path.splitext(value.name)[1]
		valid_extensions = ['.ascii', '.fits']
		if not ext in valid_extensions:
			raise ValidationError(u'File not supported!')
		if ext == '.ascii':
			try:
				np.loadtxt(value, unpack=True)
			except(ValueError):
				raise ValidationError(u'File is corrupted!')
		
		elif ext == '.fits':

			sed_file_path = os.path.join(settings.MEDIA_ROOT, value.name)

			with open(sed_file_path, 'wb+') as destination:
				for chunk in value.chunks():
					destination.write(chunk)
			hdul = fits.open(sed_file_path)
			
			"""
			try:
				
				hdul[0].header['RA']
				hdul[0].header['DEC']

				hdul[1].data['loglam']
				hdul[1].data['flux']
				hdul[1].data['ivar']
				hdul[2].data['Z'][0] 
				hdul[2].data['VDISP'][0]

				hdul.close()
				os.remove(sed_file_path)

			except(IndexError):
				hdul.close()
				#time.sleep(0.01)
				os.remove(sed_file_path)
				raise ValidationError(u'Fits file not correct format!')
			"""

			try:
				
				hdul[1].data['spectra']
				hdul[1].data['flux']
				hdul[1].data['loglam']
				hdul[1].data['ivar']

				hdul[1].data['Z']
				hdul[1].data['vdisp']
				hdul[1].data['ra']
				hdul[1].data['dec']

				hdul.close()
				os.remove(sed_file_path)

			except:
				hdul.close()
				#time.sleep(0.01)
				os.remove(sed_file_path)
				raise ValidationError(u'Fits file not correct format!')

	input_file = forms.FileField(required = True, 
								 widget=forms.FileInput(attrs={'accept' : ('.ascii','.fits',)}), 
								 validators = [validate_file_okay])



model_key_choices   = [('m11','m11'), 
					   ('m09', 'm09'), 
					   ('bc03', 'bc03')]
imf_choices         = [('kr','kr'), 
					   ('ss', 'ss'), 
					   ('cha', 'cha')]
wave_medium_choices = [('air','air'), 
					   ('vacuum','vacuum')]
model_libs_choices  = [('MILES', 'MILES'), 
					   ('MILES_revisednearIRslope', 'MILES_revisednearIRslope'), 
					   ('MILES_UVextended', 'MILES_UVextended'),
					   ('STELIB', 'STELIB'),
					   ('ELODIE', 'ELODIE'),
					   ('MARCS', 'MARCS')]

class FireFlySettings_Form(forms.Form):

	ageMin           = forms.DecimalField(initial   = 0, 
										  label     = "Minimum age", 
										  min_value = 0, 
										  widget    = forms.TextInput({ "placeholder": 0 }))
	
	ageMax           = forms.DecimalField(label     = "Maximum age", 
										  min_value = 0, 
										  required  = False, 
										  widget    = forms.TextInput({ "placeholder": "Default"}),
										  help_text = "If left blank, Firefly will calculate a value based on the redshift using the astropy library.")
	
	ZMin             = forms.DecimalField(initial   = 0.0001, 
										  min_value = 0,
										  widget    = forms.TextInput({ "placeholder": 0.0001 }))
	
	ZMax             = forms.DecimalField(initial   = 10, 
										  min_value = 0,
										  widget    = forms.TextInput({ "placeholder": 10 }))
	
	flux_units       = forms.DecimalField(initial   = 1, 
										  min_value = 0.,
										  widget    = forms.TextInput({ "placeholder": 1 }), 
										  help_text = "Firefly assumes flux units of erg/s/A/cm^2. Choose factor in case flux is scaled (e.g. flux_units=10**(-17) for SDSS")
	
	error            = forms.DecimalField(label     = "Error(%)", 
										  initial   = 10, 
										  min_value = 0., 
										  max_value = 100.)
	
	model_key        = forms.CharField(widget = forms.Select(choices = model_key_choices),
									   help_text = "m11: Maraston and Stromback 2011, m09: Maraston et al. 2009, bc03: Bruzual and Charlot 2003")
	
	model_libs       = forms.CharField(label = "Model library", 
									   widget = forms.Select(choices = model_libs_choices), 
									   help_text = "Only necessary if using m11. All are empirical libraries except for MARCS which is a theoretical library.")

	imfs             = forms.CharField(label = "IMF", 
									   widget = forms.Select(choices = imf_choices), 
									   help_text = "Initial mass function model")
	
	wave_medium      = forms.CharField(label = "Wave medium", 
									   widget = forms.Select(choices = wave_medium_choices), 
									   help_text = "Specify whether data is in air or vaccum" )
	
	downgrade_models = forms.BooleanField(initial = True, 
										  required = False, 
										  help_text = "Specify whether models should be downgraded to the instrumental resolution and galaxy velocity dispersion")

	def check_values(self,
					 ageMin,
					 ageMax,
					 ZMin,
					 ZMax,
					 flux_units):

		if ageMin == '':
			ageMin = 0
		if ageMax == '':
			ageMax = None
		if ZMin == '':
			ZMin = 0.0001
		if ZMax == '':
			ZMax = 10
		if flux_units == '':
			flux_units = 1
		
		return ageMin, ageMax, ZMin, ZMax, flux_units

emissionline_choices = [(None, '-') ,
						('HeII', 'He-II:  3202.15A, 4685.74 [Å]'), 
					    ('NeV',  'Ne-V:   3345.81, 3425.81 [Å]'),
					    ('OII',  'O-II:   3726.03, 3728.73 [Å]'),
					    ('NeIII','Ne-III: 3868.69, 3967.40 [Å]'),
					    ('H5',   'H-ζ:     3889.05 [Å]'),
					    ('He',   'H-ε:     3970.07 [Å]'),
					    ('Hd',   'H-δ:     4101.73 [Å]'),
					    ('Hg',   'H-γ:     4340.46 [Å]'),
					    ('OIII', 'O-III:  4363.15, 4958.83, 5006.77 [Å]'),
					    ('ArIV', 'Ar-IV:  4711.30, 4740.10 [Å]'),
					    ('Hb',   'H-β:     4861.32 [Å]'),
					    ('HI',   'H-I:    5197.90, 5200.39 [Å]'),
					    ('HeI',  'He-I:   5875.60 [Å]'),
					    ('OI',   'O-I:    6300.20, 6363.67 [Å]'),
					    ('Ha',   'H-α:     6562.80 [Å]'),
					    ('NII',  'N-II:   6547.96, 6583.34 [Å]'),
					    ('SII',  'S-II:   6716.31, 6730.68 [Å]'),
					    ('ArIII','Ar-III: 7135.67 [Å]')]

class Emissionlines_Form(forms.Form):
	
	extra_field_count = forms.IntegerField(initial = 1,
										   min_value = 0,
										   max_value = 10)

	N_angstrom_masked = forms.IntegerField(initial = 20,
										   label = "Width of masking [Å]",
										   widget=forms.TextInput(attrs={'size': '3'}))

	def __init__(self, *args, **kwargs):

		self.max_emissionlines = 10

		super(Emissionlines_Form, self).__init__(*args, **kwargs)

		for index in range(self.max_emissionlines):
			# generate extra fields in the number specified via extra_fields
			self.fields['Emission_line_{index}'.format(index=index+1)] = forms.CharField(required=False, 
																						 widget = forms.Select(choices = emissionline_choices),
																						 initial = '',
																						 max_length=100)

class ASCCI_additional_inputs(forms.Form):

	redshift     = forms.DecimalField(label = 'Redshift', required = False)
	ra           = forms.DecimalField(label = 'Right ascension [degrees]', required = False)
	dec          = forms.DecimalField(label = 'Declination [degrees]', required = False)
	vdisp        = forms.DecimalField(label = 'Velocity dispersion [km/s]', required = False) 
	r_instrument = forms.IntegerField(label = 'Instrument resolution', min_value = 1, required = False, help_text = "Resolution of the instrument at each wavelength observed")