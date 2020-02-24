from django.shortcuts import render, get_object_or_404, redirect
from django.http import HttpResponseRedirect, FileResponse, HttpResponse, Http404
from django.urls import reverse
from django.utils.text import slugify
from core_firefly import firefly_class
from django.core.files.storage import FileSystemStorage
from django.conf import settings

from .models import FireflyTracker, SED, FireflyResults
from .forms import FireFlySettings_Form, SEDform, SEDfileform

from background_task import background
from background_task.models import Task
#from background_task.models_completed import CompletedTask
#from background_task.models_completed import CompletedTask

import numpy as np
import random
import time
import os

@background(queue = 'my-queue')
def firefly_run(file, id):
	
	firefly = firefly_class.Firefly()
	firefly.model_input()
	firefly.file_input(file = file)
	firefly.settings()
	#firefly.ZMax = request.POST.get('ZMax')
			
	results = firefly.run(settings.MEDIA_ROOT, id)
	ffoutput = FireflyResults(file       = results,
							  results_id = id)

	ffoutput.save()
	os.remove(file)

def processing(request, results_id):

	if request.method == 'POST':

		form = Firefly_form(request.POST)

		if form.is_valid():
			print("success")
		else:
			return render(request, 'firefly/home2.html', {'form':form})

		try: 
		
			fireflytracker = get_object_or_404(FireflyTracker)
			timestamp = time.strftime("%Y%m%d%H%M%S")

			"""
			try:
				fireflytracker.queuelist.append(timestamp)
			except NameError:
				
				fireflytracker.queuelist = []
				fireflytracker.queuelist.append(timestamp)

			while fireflytracker.myturn(timestamp) != True:
				time.sleep(10)
				print("sleeping", timestamp, "not my turn")
				print (fireflytracker.queuelist)

			#fireflytracker.queue += 1
			#fireflytracker.save()

			#print ("You are", fireflytracker.queue, "in line")
			"""

			"""
			ff = firefly_class.Firefly()

			ff.model_input()
			try:
				ff.file_input(file = request.FILES.get('SED'))
			except(ValueError):
				error_message_SED = "Error loading file. Check to see if columns are equal lengths and contain only numbers."
				return render(request, 'firefly/home.html', {"error_message_SED" : error_message_SED})

			ff.settings()
			ff.ZMax = request.POST.get('ZMax')

			ff.run()

			#fireflytracker.queuelist.remove(timestamp)
			"""
			#fireflytracker.queue -= 1
			#fireflytracker.save()
			return HttpResponseRedirect('/processed/')

		except(KeyError):

			error_message = "You didn't select a file to fit data too."

			return render(request, 'firefly/home2.html', {"error_message" : error_message})

	else:
		return HttpResponseRedirect('/')

def processed(request, results_id):

	try:
		#Find the file with the id, create context for it so user can see it.
		results = FireflyResults.objects.get(results_id = results_id)
		return render(request, 'firefly/processed.html', {'results': results})
	except:
		return render(request, 'firefly/processing.html')

	#return render(request, 'firefly/processed.html', {'results': results})

def home(request):

	#Post method shows submitting form data
	if request.method == 'POST':

		#Get the form submitted and check it's valid for use
		form = FireFlySettings_Form(request.POST)
		sed_file = request.FILES['file']

		sed_form = SEDform(request.POST, request.FILES)
		print(sed_file)
		
		if form.is_valid() and sed_form.is_valid(sed_file):

			request.POST['ZMin']
			request.POST['ZMax']
			request.POST['flux_units']
			request.POST['error']
			request.POST['model_key']
			request.POST['model_libs']
			request.POST['imfs']
			request.POST['wave_medium']
			request.POST['downgrade_models']

			#Get an instance of the model object
			sed = sed_form.save()

			#Use the data and scramble it to create a unique id for the users file
			time_stamp = time.strftime("%Y%m%d%H%M%S")
			file_id = int(''.join(random.sample(time_stamp,len(time_stamp))))

			#Save the unique id to the file
			sed.results_id = file_id
			sed.save()

			#Use HttpResponseRedirect when submitting forms to stop resubmitting
			return HttpResponseRedirect(reverse('firefly:processed', args=(file_id,)))
			
		#Otherwise redirect back to form page with the form that was used, display errors to user
		elif form.is_valid():
			return render(request, 'firefly/home2.html', {'form':form, 'SED':sed_form, 'SED_ERROR':'Invalid file.'})
		else:
			return render(request, 'firefly/home2.html', {'form':form, 'SED':sed_form})
	
	#Create a FireFlySettings_form instance if first time visiting site
	form = FireFlySettings_Form()
	sed_form = SEDform()

	#Dispaly a new form to user if first time on site.
	return render(request, 'firefly/home2.html', {'form':settings_form, 'SED':sed_form})

def home2(request):

	#Post method shows submitting form data
	if request.method == 'POST':

		#Get the form submitted and check it's valid for use
		settings_form = FireFlySettings_Form(request.POST)
		sedfile_form  = SEDfileform(request.POST, request.FILES)
		#sed_file = File(sed_file)

		#sed_file.save(file_path)
		#sed_file.close()

		#if settings_form.is_valid() and sedfile_form.is_valid(sed_file):
		if settings_form.is_valid() and sedfile_form.is_valid():

			#Use the date and scramble it to create a unique id for the users file
			time_stamp = time.strftime("%Y%m%d%H%M%S")
			file_id = int(''.join(random.sample(time_stamp,len(time_stamp))))
			sed_file = request.FILES.get('file')
			sed_file_name = sed_file.name[0:-6] + "_" +str(file_id) + ".ascii"
			sed_file_path = os.path.join(settings.MEDIA_ROOT, sed_file_name)

			destination = open(sed_file_path, 'wb+')
			for chunk in sed_file.chunks():
				destination.write(chunk)
			destination.close()

			request.POST['ZMin']
			request.POST['ZMax']
			request.POST['flux_units']
			request.POST['error']
			request.POST['model_key']
			request.POST['model_libs']
			request.POST['imfs']
			request.POST['wave_medium']
			request.POST['downgrade_models']

			"""
			firefly = firefly_class.Firefly()
			firefly.model_input()
			firefly.file_input(file = sed_file)
			firefly.settings()
			#firefly.ZMax = request.POST.get('ZMax')
			
			results = firefly.run(settings.MEDIA_ROOT, file_id)

			ffoutput = FireflyResults(file       = results,
									  results_id = file_id)

			ffoutput.save()
			"""
			firefly_run(file = sed_file_path, id = file_id)
			#Use HttpResponseRedirect when submitting forms to stop resubmitting
			return HttpResponseRedirect(reverse('firefly:processed', args=(file_id,)))
			
		#Otherwise redirect back to form page with the form that was used, display errors to user
		elif settings_form.is_valid():
			return render(request, 'firefly/home2.html', {'form':settings_form, 'SED':sedfile_form, 'SED_ERROR':'Invalid file.'})
		else:
			return render(request, 'firefly/home2.html', {'form':settings_form, 'SED':sedfile_form})
	
	#Create a new form instance if first time visiting site
	settings_form = FireFlySettings_Form()
	sedfile_form = SEDfileform()

	#Dispaly a new form to user if first time on site.
	return render(request, 'firefly/home2.html', {'form':settings_form, 'SED':sedfile_form})

def download(request, results_id):
	results = FireflyResults.objects.get(results_id = results_id)
	file_path = os.path.join(settings.MEDIA_ROOT, results.file.name)
	if os.path.exists(file_path):
		with open(file_path, 'rb') as fh:
			response = HttpResponse(fh.read(), content_type="application/vnd.ms-excel")
			response['Content-Disposition'] = 'inline; filename=' + os.path.basename(file_path)
			return response
	raise Http404
