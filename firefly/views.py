from django.shortcuts import render, get_object_or_404
from django.http import HttpResponseRedirect
from django.urls import reverse
from django.views.generic import FormView, DetailView, ListView
from core_firefly import firefly_class
import time

from .models import FireflyTracker

def processing(request):

	if request.method == 'POST':

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

			#fireflytracker.queue -= 1
			#fireflytracker.save()
			return HttpResponseRedirect('/processed/')

		except(KeyError):

			error_message = "You didn't select a file to fit data too."

			return render(request, 'firefly/home.html', {"error_message" : error_message})

	else:
		return HttpResponseRedirect('/')


def home(request):

	manager = get_object_or_404(FireflyTracker)
	context = {'manager' : manager}
	print(manager.queue)
	manager.queue = 0
	manager.save()

	if request.method == 'POST':
		result = processing(request)
		return result


	return render(request, 'firefly/home.html', context)


def processed(request):
	return render(request, 'firefly/processed.html')