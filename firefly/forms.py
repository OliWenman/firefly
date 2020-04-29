from django import forms
from django.core.exceptions import ValidationError
from django.conf import settings

from .models import SED

import time
import numpy as np
import os
from astropy.io import fits
import string

from core_firefly.emission_lines import emissionline_choices

from django.utils.safestring import mark_safe


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

wave_medium_choices = [('air','air'), 
					   ('vacuum','vacuum')]

class SEDfileform(forms.Form):
	
	
	flux_units       = forms.DecimalField(initial   = 1, 
										  min_value = 0.,
										  widget    = forms.TextInput({ "placeholder": 1 }), 
										  help_text = "Assumes flux units of [erg/s]/[A/cm^2]. Choose factor if flux is scaled (e.g. flux_units = 1e-17 for SDSS).")

	wave_medium      = forms.CharField(label = "Wave medium", 
									   widget = forms.Select(choices = wave_medium_choices), 
									   help_text = "Specify whether your data is in air or vaccum." )

	def filename_okay(filename):

		valid_chars = "-_() %s%s" % (string.ascii_letters, string.digits)

		filename_check = ''.join(c for c in filename if c in valid_chars)

		if filename != filename_check:
			raise ValidationError("Invalid output file name.")

	output_name = forms.CharField(required   = False,
								  max_length = 20, 
								  validators = [filename_okay,],
								  widget     = forms.TextInput({ "placeholder": "Optional" }),
								  help_text  = "Choose an output file name (don't include extension). If left blank will auto generate one.")


	input_file = forms.FileField(required = True, 
								 widget=forms.ClearableFileInput(attrs={'multiple': True}), 
								 label = "Upload files",
								 help_text = "Can upload multiple '.fits' files or a single '.ascii' file. For more information, please visit the file format page.")
	#widget=forms.ClearableFileInput(attrs={'multiple': True})


model_key_choices   = [('m11','m11'), 
					   #('m09', 'm09'), 
					   #('bc03', 'bc03')
					   ("MaStar", "MaStar"),
					   ]

model_libs_choices  = [('MILES', 'MILES'), 
					   #('MILES_revisednearIRslope', 'MILES_revisednearIRslope'), 
					   #('MILES_UVextended', 'MILES_UVextended'),
					   ('STELIB', 'STELIB'),
					   ('ELODIE', 'ELODIE'),
					   ('MARCS', 'MARCS'),
					   ('Th','Th')]
					   
imf_choices         = [('Kroupa','Kroupa'), 
					   ('Salpeter', 'Salpeter'), 
					   ('Chabrier', 'Chabrier')]

class FireFlySettings_Form(forms.Form):

	ageMin           = forms.DecimalField(initial   = 0, 
										  label     = mark_safe("Minimum age [Gyr]"), 
										  min_value = 0, 
										  widget    = forms.TextInput({ "placeholder": 0 }))
	
	ageMax           = forms.DecimalField(label     = "Maximum age [Gyr]", 
										  min_value = 0, 
										  required  = False, 
										  widget    = forms.TextInput({ "placeholder": "Default"}),
										  help_text = "If left blank, Firefly will calculate a value based on the provided redshift.")
	
	ZMin             = forms.DecimalField(initial   = 0.0001,
										  label     = "Minimum metalicity", 
										  min_value = 0,
										  widget    = forms.TextInput({ "placeholder": 0.0001 }))
	
	ZMax             = forms.DecimalField(initial   = 10, 
										  label     = "Maximum metalicity", 
										  min_value = 0,
										  widget    = forms.TextInput({ "placeholder": 10 }))
	"""
	flux_units       = forms.DecimalField(initial   = 1, 
										  min_value = 0.,
										  widget    = forms.TextInput({ "placeholder": 1 }), 
										  help_text = "Firefly assumes flux units of erg/s/A/cm^2. Choose factor in case flux is scaled (e.g. flux_units=10**(-17) for SDSS")
	"""
	model_key        = forms.CharField(widget = forms.Select(choices = model_key_choices),
									   help_text = "Pick a model to fit to your data. m11: Maraston and Stromback 2011, MaStar: 'placeholder'")
	
	model_libs       = forms.CharField(label = "Model library", 
									   widget = forms.Select(choices = model_libs_choices), 
									   help_text = "If model_key is m11, all are empirical libraries except for MARCS which is a theoretical library. MaStar has the option between a theoretical library or an empirical one.")

	imfs             = forms.CharField(label = "IMF", 
									   widget = forms.Select(choices = imf_choices), 
									   help_text = "Describes the initial distribution of masses for a population of stars.")
	"""
	wave_medium      = forms.CharField(label = "Wave medium", 
									   widget = forms.Select(choices = wave_medium_choices), 
									   help_text = "Specify whether data is in air or vaccum" )
	"""
	downgrade_models = forms.BooleanField(initial = True, 
										  required = False, 
										  help_text = "Specify whether models should be downgraded to the instrumental resolution and galaxy velocity dispersion")

class Emissionlines_Form(forms.Form):

	def __init__(self, *args, **kwargs):

		self.emissionline_choices = emissionline_choices

		super(Emissionlines_Form, self).__init__(*args, **kwargs)

		for index in range(len(emissionline_choices)):

			self.fields[emissionline_choices[index][0]] = forms.BooleanField(required = False, label = emissionline_choices[index][1]) 

		self.fields["N_angstrom_masked"] = forms.IntegerField(initial = 10,
															  label = "Width of masking",
															  help_text = "Firefly will ignore (mask) the data points corrosponding to the emission lines selected. Select the width of this masking around each point.")

class ASCCI_additional_inputs(forms.Form):

	redshift     = forms.DecimalField(label = 'Redshift', required = False)
	ra           = forms.DecimalField(label = 'Right ascension [degrees]', required = False)
	dec          = forms.DecimalField(label = 'Declination [degrees]', required = False)
	vdisp        = forms.DecimalField(label = 'Velocity dispersion [km/s]', required = False) 
	r_instrument = forms.IntegerField(label = 'Instrument resolution', min_value = 1, required = False, help_text = "Resolution of the instrument at each wavelength observed")