from django.db import models
from django import forms

from django.db.models.signals import post_delete
from django.dispatch import receiver

from core_firefly import firefly_class

#Import seperate background_tasks, allows for processing to be done in background
#and not risk a timeout requesting a page while processing.
from background_task import background
from background_task.models import Task
from background_task.models import CompletedTask

import os
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

	job_id      = models.IntegerField(default = 0)
	#Need to add
	input_file  = models.FileField(upload_to='', blank = True)
	output_file = models.FileField(upload_to='', blank = True)

	#Status will show what state its in. 
	#1)pre-processing
	#2)processing
	#3)complete/failed
	status      = models.CharField(default = 'preprocessing', max_length=14)
	
	def output_file_(self):
		return os.path.basename(self.output_file.name)

	def input_file_(self):
		return os.path.basename(self.input_file.name)

	def __str__(self):
		return str(self.job_id)

	"""
	def process_input(self,
					  input_file, 
					  job_id,
					  ZMin,
					  ZMax,
					  flux_units,
					  error,
					  model_key,
					  model_libs,
					  imfs,
					  wave_medium,
					  downgrade_models):

		firefly = firefly_class.Firefly()
		firefly.model_input()
		firefly.file_input(input_file = input_file)
		firefly.settings()
		
		output = firefly.run(settings.MEDIA_ROOT, self.job_id)
		
		self.output_file = output
		#warnings.filterwarnings("error")

		#try:

		#job_submission      = Job_Submission.objects.get(job_id = job_id)
		#job_submission.input_file = output
		#job_submission.save()
			
		#os.remove(input_file)
		#except:
		#	print("Aborted,", job_id)
	"""
	class Meta:
		verbose_name = 'Job Submission'

class Example_Data(models.Model):

	input_file  = models.FileField(upload_to='', blank = False)
	description = models.CharField(max_length = 100) 
	example_id     = models.IntegerField(default = 0)

	def __str__(self):
		return self.input_file.name

	class Meta:
		verbose_name = 'Example data'
		verbose_name_plural = verbose_name
	
#Automatically delete the files Job_Submitted had when itself is 
#deleted from database. 
@receiver(post_delete, sender=Example_Data)
@receiver(post_delete, sender=Job_Submission)
def submission_delete(sender, instance, **kwargs):
	try:
		instance.input_file.delete(False)
		instance.output_file.delete(False) 
	except:
		pass