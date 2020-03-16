from django import forms
from django.core.exceptions import ValidationError

from .models import SED

import numpy as np
import os
from astropy.io import fits

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
		"""
		elif ext == '.fits':
			try:
				hdul = fits.open(input_file)
				data_set0 = hdul[0].data
				data_set1 = hdul[1].data
				data_set2 = hdul[2].data

				#Variables from fits file?
				redshift = float(data_set2['Z'])
				ra       = float(data_set2['PLUG_RA'])  #Not consistant, RA or PLUG_RA?
				dec      = float(data_set2['PLUG_DEC']) #Not consistant, DEC or PLUG_DEC?
				vdisp    = float(data_set2['VDISP'])

				lamb            = 10**data_set1['loglam']
				wavelength = lamb[np.where(lamb > 3600 * (1 + self.redshift))]
				flux       = data_set1['flux'][np.where(lamb > 3600 * (1 + self.redshift))]
				error      = data_set1['ivar'] #??
			except:
				raise ValidationError(u'Fits file not correct format!')
		"""
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
										  widget    = forms.TextInput({ "placeholder": "Default"}))
	
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

	model_libs       = forms.CharField(label = "Model library", 
									   widget = forms.Select(choices = model_libs_choices), 
									   help_text = "The model flavour")
	
	model_key        = forms.CharField(widget = forms.Select(choices = model_key_choices))
	
	imfs             = forms.CharField(label = "IMF", 
									   widget = forms.Select(choices = imf_choices), 
									   help_text = "Initial mass function model")
	
	wave_medium      = forms.CharField(label = "Wave medium", 
									   widget = forms.Select(choices = wave_medium_choices), 
									   help_text = "Specify whether data is in air or vaccum" )
	
	downgrade_models = forms.BooleanField(initial = True, 
										  required = False, 
										  help_text = "Specify whether models should be downgraded to the instrumental resolution and galaxy velocity dispersion")


emissionline_choices = [(None, '-') ,
						('HeII','He II'), 
					    ('NeV','Ne V'),
					    ('OII', 'O II'),
					    ('NeIII', 'Ne III'),
					    ('H5', 'H5'),
					    ('He', 'He'),
					    ('Hd', 'Hd'),
					    ('Hg', 'Hg'),
					    ('OIII', 'O III'),
					    ('ArIV', 'Ar IV'),
					    ('Hb', 'Hb'),
					    ('HI', 'H I'),
					    ('HeI', 'He I'),
					    ('OI', 'O I'),
					    ('NII', 'N II'),
					    ('SII', 'S II'),
					    ('ArIII', 'Ar III')]

class Emissionlines_Form(forms.Form):
	
	extra_field_count = forms.IntegerField(initial = 1,
										   min_value = 0,
										   max_value = 10)

	N_angstrom_masked = forms.IntegerField(initial = 20,
										   label = "Width of masking (Å)",
										   widget=forms.TextInput(attrs={'size': '3'}))

	def __init__(self, *args, **kwargs):

		self.max_emissionlines = 10

		super(Emissionlines_Form, self).__init__(*args, **kwargs)

		for index in range(self.max_emissionlines):
			# generate extra fields in the number specified via extra_fields
			self.fields['Emission_line_{index}'.format(index=index+1)] = forms.CharField(required=False, 
																						 widget = forms.Select(choices = emissionline_choices),
																						 initial = '')

class ASCCI_additional_inputs(forms.Form):

	redshift     = forms.DecimalField(label = 'Redshift', required = False)
	ra           = forms.DecimalField(label = 'Right ascension', required = False)
	dec          = forms.DecimalField(label = 'dec', required = False)
	vdisp        = forms.DecimalField(label = 'Velocity dispersion', required = False) 
	r_instrument = forms.IntegerField(label = 'Instrument resolution', min_value = 1, required = False)