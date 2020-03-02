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

	input_file = forms.FileField(widget=forms.FileInput(attrs={'accept' : '.ascii'}), validators = [validate_file_okay])
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
