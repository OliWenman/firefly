from django import forms
from django.core.exceptions import ValidationError

from .models import SED

import numpy as np
import os

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

model_key_choices   = [('m11','m11')]
imf_choices         = [('kr','kr')]
wave_medium_choices = [('air','air'), ('vacuum','vacuum')]
model_libs_choices  = [('MILES', 'MILES')]

class SEDfileform(forms.Form):

	def validate_file_okay(value):
		ext = os.path.splitext(value.name)[1]
		valid_extensions = ['.ascii']
		if not ext in valid_extensions:
			raise ValidationError(u'File not supported!')

		try:
			np.loadtxt(value, unpack=True)
		except(ValueError):
			raise ValidationError(u'File is corrupted!')

	input_file = forms.FileField(required = False, 
								 widget=forms.FileInput(attrs={'accept' : '.ascii'}), 
								 validators = [validate_file_okay])
	
	#def __init__(self, *args, **kwargs):

	#	file_required = kwargs.pop('extra', False)
	#	super(SEDfileform, self).__init__(*args, **kwargs)
	#	self.fields['input_file'].required = file_required
	"""
	def is_valid(self, file):
		
		valid = super(SEDfileform, self).is_valid()
		try:
			np.loadtxt(file, unpack=True)
			valid2 = True
		except(ValueError):
			valid2 = False
		
		if valid and valid2 == True:
			return True
		else:
			return False
	"""

emissionline_choices2 = [('HeII','HeII'), 
					    ('NeV','NeV'),
					    ('OII', 'OII'),
					    ('NeIII', 'NeIII'),
					    ('H5', 'H5'),
					    ('He', 'He'),
					    ('Hd', 'Hd'),
					    ('Hg', 'Hg'),
					    ('OIII', 'OIII'),
					    ('ArIV', 'ArIV'),
					    ('Hb', 'Hb'),
					    ('NI', 'HI'),
					    ('HeI', 'HeI'),
					    ('OI', 'OI'),
					    ('NII', 'NII'),
					    ('SII', 'SII'),
					    ('ArIII', 'ArIII')]

class FireFlySettings_Form(forms.Form):

	ageMin           = forms.DecimalField(initial = 0, label = "Minimum age", min_value = 0)
	#ageMax
	ZMin             = forms.DecimalField(initial = 0, min_value = 0)
	ZMax             = forms.DecimalField(initial = 10, min_value = 0)
	flux_units       = forms.DecimalField(initial = 1, min_value = 0., help_text = "Firefly assumes flux units of erg/s/A/cm^2. Choose factor in case flux is scaled (e.g. flux_units=10**(-17) for SDSS")
	error            = forms.DecimalField(label = "Error(%)", initial   = 10, min_value = 0., max_value = 100.)
	model_key        = forms.CharField(widget = forms.Select(choices = model_key_choices))
	model_libs       = forms.CharField(label = "Model library", widget = forms.Select(choices = model_libs_choices), help_text = "The model flavour")
	imfs             = forms.CharField(label = "IMF", widget = forms.Select(choices = imf_choices), help_text = "Initial mass function model")
	wave_medium      = forms.CharField(label = "Wave medium", widget = forms.Select(choices = wave_medium_choices), help_text = "Specify whether data is in air or vaccum" )
	downgrade_models = forms.BooleanField(initial = True, required = False, help_text = "Specify whether models should be downgraded to the instrumental resolution and galaxy velocity dispersion")

	#extra_field_count = forms.CharField(widget=forms.HiddenInput())

	"""
	def __init__(self, *args, **kwargs):
		extra_fields = kwargs.pop('extra', 0)

		super(FireFlySettings_Form, self).__init__(*args, **kwargs)
		self.fields['extra_field_count'].initial = extra_fields

		
		for index in range(int(extra_fields)):
			# generate extra fields in the number specified via extra_fields
			self.fields['extra_field_{index}'.format(index=index)] = forms.CharField(label = "Emission line", widget = forms.Select(choices = emissionline_choices2))
	"""

emissionline_choices = [('HeII','He_II'), 
					    ('NeV','Ne_V'),
					    ('OII', 'O_II'),
					    ('NeIII', 'Ne_III'),
					    ('H5', 'H5'),
					    ('He', 'He'),
					    ('Hd', 'Hd'),
					    ('Hg', 'Hg'),
					    ('OIII', 'O_III'),
					    ('ArIV', 'Ar_IV'),
					    ('Hb', 'Hb'),
					    ('HI', 'H_I'),
					    ('HeI', 'He_I'),
					    ('OI', 'O_I'),
					    ('NII', 'N_II'),
					    ('SII', 'S_II'),
					    ('ArIII', 'Ar_III')]

class Emissionlines_Form(forms.Form):
	
	extra_field_count = forms.IntegerField(initial = 1,
										   min_value = 0,
										   max_value = 10,
										   label = "Number of emissions lines")

	def __init__(self, *args, **kwargs):

		extra_fields = kwargs.pop('extra', 0)

		super(Emissionlines_Form, self).__init__(*args, **kwargs)
		self.fields['extra_field_count'].initial = extra_fields

		for index in range(int(extra_fields)):
			# generate extra fields in the number specified via extra_fields
			self.fields['Emission_line_{index}'.format(index=index+1)] = forms.CharField(required=False, widget = forms.Select(choices = emissionline_choices))

