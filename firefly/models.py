from django.db import models
from django import forms

from django.db.models.signals import post_delete
from django.dispatch import receiver

from core_firefly import firefly_class
from astropy.io import fits

#Import seperate background_tasks, allows for processing to be done in background
#and not risk a timeout requesting a page while processing.
from background_task import background
from background_task.models import Task
from background_task.models import CompletedTask

from django.conf import settings

from datetime import datetime
import os
#from django.utils.timezone import now

"""
def wrapper(method):
    @background(method)
    def _impl(self, *method_args, **method_kwargs):
        pass
    return _impl
"""
class SED(models.Model):

	output_file = models.FileField(upload_to='', blank =True)
	uploaded_at = models.DateTimeField(auto_now_add=True)
	job_id      = models.IntegerField(default = 0)

	def __str__(self):
		return str(self.job_id)

#Job_Submissions contains the input and output files for firefly. 
#Each job identified by a unique job_id.
class Job_Submission(models.Model):

	job_id           = models.IntegerField(default = 0)
	input_file       = models.FileField(upload_to='input_files', blank = False, editable = False)
	output_file      = models.FileField(upload_to='output_files', blank = True)
	n_spectra        = models.IntegerField(default = 1, verbose_name='Number of spectra')
	ageMin           = models.FloatField(default = None, null=True)
	ageMax		     = models.CharField(default = None, null=True, max_length = 10)
	Zmin			 = models.FloatField(default = None, null=True)
	Zmax			 = models.FloatField(default = None, null=True)
	flux_units		 = models.FloatField(default = None, null=True)
	model            = models.CharField(max_length = 16, null=True)
	imf              = models.CharField(max_length = 15, null=True)	
	wave_medium      = models.CharField(max_length = 10, null=True)
	downgrade_models = models.BooleanField(default = None, null=True)
	width_masking    = models.FloatField(default = None, null=True)
	emission_lines   = models.CharField(max_length = 50, null=True)
	submitted        = models.DateTimeField(default=datetime.now, blank=True)

	#created_date = models.DateTimeField(default=now, editable=False)
	#updated_at = models.DateTimeField(auto_now=True)

	#Status will show what state its in. 
	#1)queued
	#2)processing
	#3)complete/failed
	status      = models.CharField(default = 'preprocessing', max_length=20)

	def __str__(self):
		return str(self.job_id)

	#def delete(self, using=None, keep_parents=False):
	#	self.input_file.storage.delete(self.input_file.name)
	#	self.output_file.storage.delete(self.output_file.name)
	#	super().delete()

	class Meta:
		verbose_name = 'Job Submission'

class Example_Data(models.Model):

	input_file  = models.FileField(upload_to="example_files", blank = False, unique = False)
	title       = models.CharField(max_length = 50, null = True)
	description = models.TextField(max_length = 1000) 
	example_id  = models.IntegerField(unique = True)

	def __str__(self):
		return self.input_file.name

	def header_list0(self):

		n = 0

		header = []

		if os.path.splitext(self.input_file.name)[1] == ".fits": 

			with fits.open(os.path.join(settings.EXAMPLE_FILES,self.input_file.path)) as hdul:

				for i in hdul[n].header:
					header.append(str(i) + " = " + str(hdul[n].header[i]) + " / " + str(hdul[n].header.comments[i]))

			header.append("END")
		
		return header

	def header_list1(self):

		n = 1

		header = []

		if os.path.splitext(self.input_file.name)[1] == ".fits": 

			with fits.open(os.path.join(settings.EXAMPLE_FILES,self.input_file.path)) as hdul:

				for i in hdul[n].header:
					header.append(str(i) + " = " + str(hdul[n].header[i]) + " / " + str(hdul[n].header.comments[i]))

			header.append("END")
		
		return header

	def file_type(self):
		return os.path.splitext(self.input_file.name)[1]


	class Meta:
		verbose_name = 'Example data'
		verbose_name_plural = verbose_name


@receiver(models.signals.post_delete, sender = Job_Submission)
def auto_delete_file_on_delete(sender, instance, **kwargs):

	instance.input_file.delete(False)
	instance.output_file.delete(False) 

@receiver(models.signals.post_delete, sender = Example_Data)
def auto_delete_input_file_on_delete(sender, instance, **kwargs):

	instance.input_file.delete(False)