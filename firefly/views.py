#Import Django related functions
from django.shortcuts import render, get_object_or_404, redirect
from django.http import HttpResponseRedirect, FileResponse, HttpResponse, Http404
from django.urls import reverse
from django.utils.text import slugify
from django.core.files.storage import FileSystemStorage
from django.conf import settings
from django.utils import timezone

#Import seperate background_tasks, allows for processing to be done in background
#and not risk a timeout requesting a page while processing.
from background_task import background
from background_task.models import Task
from background_task.models import CompletedTask

#Import my model and forms
from .models import Job_Submission
from .forms import FireFlySettings_Form, SEDform, SEDfileform

#Import firefly
from core_firefly import firefly_class

import numpy as np
import random
import time
import os
import warnings

time_in_database = 60*10

#Automatically delete job from databse after certain amount of time.
@background(schedule=time_in_database, queue = 'my-queue')
def clean_database(job_id):

	job_submission = Job_Submission.objects.get(job_id = job_id)
	job_submission.delete()

@background(queue = 'my-queue')
def firefly_run(input_file, 
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

	#Setup firefly settings
	firefly = firefly_class.Firefly()
	firefly.model_input()
	firefly.file_input(input_file = input_file)
	firefly.settings()
	
	#Run firefly to process the data
	output = firefly.run(settings.MEDIA_ROOT, job_id)
	
	warnings.filterwarnings("error")

	#try:

	#Get the Job_Submission and save it to the database.
	job_submission             = Job_Submission.objects.get(job_id = job_id)
	job_submission.output_file = output
	job_submission.status      = "complete"
	job_submission.save()

	#After completion, remove files from database after certain amount of time
	#so we don't have to store files.
	clean_database(job_id)
		
	#os.remove(input_file)
	#except:
	#	print("Aborted,", job_id)

def home(request):

	#Post method shows submitting form data
	if request.method == 'POST':

		#Get the form submitted and check it's valid for use
		settings_form = FireFlySettings_Form(request.POST)
		sedfile_form  = SEDfileform(request.POST, request.FILES)

		#if settings_form.is_valid() and sedfile_form.is_valid(sed_file):
		if settings_form.is_valid() and sedfile_form.is_valid():

			#Use the date and time to make unique job_id via scrambling the digits.
			time_stamp = time.strftime("%Y%m%d%H%M%S")
			job_id = int(''.join(random.sample(time_stamp,len(time_stamp))))

			#Get the SED input_file
			sed_file = request.FILES.get('input_file')
			
			#Create a new input_file name to make it unique.
			sed_file_name = sed_file.name[0:-6] + "_" +str(job_id) + ".ascii"
			sed_file_path = os.path.join(settings.MEDIA_ROOT, sed_file_name)

			#Save the input_file to disk
			file_destination = open(sed_file_path, 'wb+')
			for chunk in sed_file.chunks():
				file_destination.write(chunk)
			file_destination.close()

			#Get the variables from the form.
			ZMin             = request.POST['ZMin']
			ZMax             = request.POST['ZMax']
			flux_units       = request.POST['flux_units']
			error            = request.POST['error']
			model_key        = request.POST['model_key']
			model_libs       = request.POST['model_libs']
			imfs             = request.POST['imfs']
			wave_medium      = request.POST['wave_medium']
			downgrade_models = request.POST['downgrade_models']

			#Create Job_Submission instance to save to database
			job_submission = Job_Submission.objects.create(job_id     = job_id,
														   status     = 'processing',
														   input_file = sed_file_path)  

			"""
			job_submission.process_input(input_file             = sed_file_path, 
										 job_id          = job_id,
										 ZMin             = ZMin,
										 ZMax             = ZMax,
										 flux_units       = flux_units,
										 error            = error,
										 model_key        = model_key,
										 model_libs       = model_libs,
										 imfs             = imfs,
										 wave_medium      = wave_medium,
										 downgrade_models = downgrade_models)
			"""
			#Run firefly task in the background
			firefly_run(input_file       = sed_file_path, 
						job_id           = job_id,
						ZMin             = ZMin,
						ZMax             = ZMax,
						flux_units       = flux_units,
						error            = error,
						model_key        = model_key,
						model_libs       = model_libs,
						imfs             = imfs,
						wave_medium      = wave_medium,
						downgrade_models = downgrade_models)

			#Use HttpResponseRedirect when submitting forms to stop resubmitting
			return HttpResponseRedirect(reverse('firefly:processed', args=(job_id,)))
			
		#Otherwise redirect back to form page with the form that was used, display errors to user
		else:
			return render(request, 'firefly/home2.html', {'form':settings_form, 'SED':sedfile_form})
	
	#Create a new form instance if first time visiting site
	settings_form = FireFlySettings_Form()
	sedfile_form  = SEDfileform()

	#Dispaly a new form to user if first time on site.
	return render(request, 'firefly/home2.html', {'form':settings_form, 'SED':sedfile_form})

def processed(request, job_id):

	#Find the the id in databse, if it can't then catch exception and
	#redirect user to page saying the id they want doesn't exist.
	if Job_Submission.objects.filter(job_id = job_id):

		#Checks if output_file exists, if it does display the results
		job_submission = Job_Submission.objects.get(job_id = job_id)
		if job_submission.output_file.name:
			return render(request, 'firefly/processed.html', {'job_id': job_id})

		#If it doesn't display a loading page
		else:
			return render(request, 'firefly/processing.html', {'job_id': job_id})

	else:
		raise Http404

#Allow user to download file
def download(request, job_id):
	results = Job_Submission.objects.get(job_id = job_id)
	file_path = os.path.join(settings.MEDIA_ROOT, results.input_file.name)
	if os.path.exists(file_path):
		with open(file_path, 'rb') as fh:
			response = HttpResponse(fh.read(), content_type="application/vnd.ms-excel")
			response['Content-Disposition'] = 'inline; filename=' + os.path.basename(file_path)
			return response
	raise Http404
