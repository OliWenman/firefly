from django.shortcuts import render, get_object_or_404
from django.http import HttpResponseRedirect
from django.urls import reverse
from django.views.generic import FormView, DetailView, ListView
from core_firefly import firefly_class
import time

from django.core.files.storage import FileSystemStorage

from .models import FireflyTracker, SED
from .forms import FireFlyModel_Form, SEDform

from django.shortcuts import redirect

import numpy as np
import random

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

	#Find the file with the id, create context for it so user can see it.
	results = SED.objects.get(results_id = results_id)
	
	return render(request, 'firefly/processed.html', {'results': results})

def home(request):

	#Post method shows submitting form data
	if request.method == 'POST':

		#Get the form submitted and check it's valid for use
		form = FireFlyModel_Form(request.POST)
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
	
	#Create a FireFlyModel_form instance if first time visiting site
	form = FireFlyModel_Form()
	sed_form = SEDform()

	#Dispaly a new form to user if first time on site.
	return render(request, 'firefly/home2.html', {'form':form, 'SED':sed_form})

