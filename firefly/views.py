from django.shortcuts import render, get_object_or_404
from django.http import HttpResponseRedirect
from django.urls import reverse
from django.views.generic import FormView, DetailView, ListView
from core_firefly import firefly_class
import time

from .models import FireflyTracker

def home(request):

	manager = get_object_or_404(FireflyTracker)
	context = {manager : 'manager'}
	print(manager.queue)

	return render(request, 'firefly/home.html', context)

def processing(request):

	if request.method == 'POST':
		
		fireflytracker = get_object_or_404(FireflyTracker)
		timestamp = time.strftime("%Y%m%d%H%M%S")

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
		
		ff = firefly_class.Firefly()

		file_input = "/Users/User/Documents/University/Third_Year/Project/Webstie/firefly_website/core_firefly/example_data/CDFS022490.ascii"

		ff.model_input()
		ff.file_input(file = file_input)
		ff.settings()
		ff.run()

		fireflytracker.queuelist.remove(timestamp)

		#fireflytracker.queue -= 1
		#fireflytracker.save()
		return HttpResponseRedirect('/processed/')

	else:
		return HttpResponseRedirect('/')


def processed(request):
	return render(request, 'firefly/processed.html')