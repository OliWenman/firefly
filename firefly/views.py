#Import Django related functions
from django.shortcuts import render, get_object_or_404, redirect
from django.http import HttpResponseRedirect, FileResponse, HttpResponse, Http404
from django.urls import reverse
from django.utils.text import slugify
from django.utils.datastructures import MultiValueDictKeyError
from django.core.files.storage import FileSystemStorage
from django.conf import settings
from django.utils import timezone

#Import seperate background_tasks, allows for processing to be done in background
#and not risk a timeout requesting a page while processing.
from background_task import background
from background_task.models import Task
from background_task.models import CompletedTask

#Import my model and forms
from .models import Job_Submission, Example_Data
from .forms import FireFlySettings_Form, SEDform, SEDfileform, Emissionlines_Form

#Import firefly
from core_firefly import firefly_class

import numpy as np
import random
import time
import os
import warnings
from io import BytesIO
import base64
import matplotlib.pyplot as plt
from astropy.io import fits
import sys, traceback

time_in_database = 60*60
clean_db = True

#Automatically delete job from databse after certain amount of time.
@background(name = 'clean_db', schedule=time_in_database, queue = 'my-queue')
def clean_database(job_id):

	try:
		job_submission = Job_Submission.objects.get(job_id = job_id)
		job_submission.delete()
		print("deleted", job_submission.job_id)
	except:
		print("Failed to delete", job_submission.job_id)

@background(name = 'firefly', queue = 'my-queue')
def firefly_run(input_file, 
				job_id,
				ageMin,
				ZMin,
				ZMax,
				flux_units,
				error,
				models_key,
				model_libs,
				imfs,
				wave_medium,
				downgrade_models,
				emissionline_list):

	#warnings.filterwarnings("error")

	#Setup firefly settings
	firefly = firefly_class.Firefly()
	firefly.model_input()
	firefly.file_input(input_file = input_file)

	firefly.settings(ageMin           = 0,
					 ZMin             =  ZMin,
					 ZMax             = ZMax,
					 flux_units       = flux_units,
					 models_key       = models_key,
					 model_libs       = model_libs,
					 imfs             = imfs,
					 data_wave_medium = wave_medium,
					 downgrade_models = downgrade_models)
	try:
		firefly.mask_emissionlines(element_emission_lines = emissionline_list,
								   N_angstrom_masked = 20)

		#Run firefly to process the data
		output = firefly.run(settings.MEDIA_ROOT, job_id)

		#Get the Job_Submission and save it to the database.
		job_submission             = Job_Submission.objects.get(job_id = job_id)
		job_submission.output_file = output
		job_submission.status      = "complete"
		job_submission.save()

		#After completion, remove files from database after certain amount of time
		#so we don't have to store files.
		if clean_db:
			clean_database(job_id)
			
	except:
		exc_type, exc_value, exc_traceback = sys.exc_info()
		print(exc_type)
		print(exc_value)
		print(exc_traceback)

		#Get the Job_Submission and save it to the database.
		job_submission             = Job_Submission.objects.get(job_id = job_id)
		job_submission.status      = "failed"
		job_submission.save()

		clean_database(job_id)


def home(request):

	#Post method shows submitting form data
	if request.method == 'POST':

		#try:
		n = request.POST.get('extra_field_count')
		print(request.POST)
		#except:
		#	n = 1

		#Get the form submitted and check it's valid for use
		emissionlines_form  = Emissionlines_Form(request.POST, extra = n)
		settings_form       = FireFlySettings_Form(request.POST)
		sedfile_form        = SEDfileform(request.POST, request.FILES)

		if 'submit' in request.POST:	

			#sedfile_form = SEDfileform(request.POST, request.FILES, extra = True)
			sedfile_form.fields['input_file'].required = True

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
				models_key       = request.POST['model_key']
				model_libs       = request.POST['model_libs']
				imfs             = request.POST['imfs']
				wave_medium      = request.POST['wave_medium']
				try:
					downgrade_models = request.POST['downgrade_models']
				except MultiValueDictKeyError:
					downgrade_models = False

				emissionlines = []
				for i in range(int(n)):
					emissionlines.append(request.POST['Emission_line_' + str(i +1)])

				print (emissionlines)
				#Create Job_Submission instance to save to database
				job_submission = Job_Submission.objects.create(job_id     = job_id,
															   status     = 'processing',
															   input_file = sed_file_path)  

				#Run firefly task in the background
				firefly_run(input_file       = sed_file_path, 
							job_id           = job_id,
							ageMin           = 0,
							ZMin             = float(ZMin),
							ZMax             = float(ZMax),
							flux_units       = float(flux_units),
							error            = float(error),
							models_key       = models_key,
							model_libs       = model_libs,
							imfs             = imfs,
							wave_medium      = wave_medium,
							downgrade_models = downgrade_models,
							emissionline_list= emissionlines)

				#Use HttpResponseRedirect when submitting forms to stop resubmitting
				return HttpResponseRedirect(reverse('firefly:processed', args=(job_id,)))

			#Otherwise redirect back to form page with the form that was used, display errors to user
			else:
				return render(request, 
							 'firefly/home2.html', 
							 {'form':settings_form, 
							 'SED':sedfile_form,
							 'emissionlines_form' : emissionlines_form})

		elif 'add' in request.POST:

			sedfile_form.fields['input_file'].required = False
			return render(request, 
						 'firefly/home2.html', 
						 {'form':settings_form, 
						 'SED':sedfile_form,
						 'emissionlines_form' : emissionlines_form})

	#Create a new form instance if first time visiting site
	emissionlines_form = Emissionlines_Form(extra = 1)
	settings_form = FireFlySettings_Form()
	sedfile_form  = SEDfileform()

	#Dispaly a new form to user if first time on site.
	return render(request, 
				 'firefly/home2.html', 
				 {'form': settings_form, 
				 'SED'  : sedfile_form,
				 'emissionlines_form' : emissionlines_form})



from django.db.models import Q

def processed(request, job_id):

	"""
	running_tasks_qs = Task.objects.filter()
	completed_tasks_qs = CompletedTask.objects.all()

	found = False
	#Check if task with job_id is running
	for running_task in running_tasks_qs:

		if running_task.task_params.find(str(job_id)) != -1:
			found = True
			print("running job_id", job_id)
			break

	#If it can't find it, check completed tasks 
	error = False
	if found == False:
		for completed_task in completed_tasks_qs:
			if completed_task.task_params.find(str(job_id)) != -1:
				error = True
				print("found error for job_id", bool(completed_task.last_error))
				break
	"""

	#Find the the id in databse, if it can't then catch exception and
	#redirect user to page saying the id they want doesn't exist.
	if Job_Submission.objects.filter(job_id = job_id):

		#Checks if output_file exists, if it does display the results
		job_submission = Job_Submission.objects.get(job_id = job_id)

		if job_submission.status == "failed":
			return render(request, 'firefly/error.html', {'job_id': job_id})

		plot_size = (8,5)
		fig       = plt.figure(figsize = plot_size)
		ax        = fig.add_subplot(111)
		ax.set_xlabel('Wavelength (Å)')
		ax.set_ylabel('Flux')
		plt.ticklabel_format(style='sci', axis='y', scilimits=(0,0))

		buffer = BytesIO()

		if job_submission.output_file.name:

			hdul        = fits.open(os.path.join(settings.MEDIA_ROOT, job_submission.output_file.name))
			data        = hdul[1].data
			wavelength  = data['wavelength']
			flux        = data['original_data']
			model       = data['firefly_model']

			hdul.close()
			"""
			csp_age=np.ndarray(hdul[1].header['ssp_number'])
			csp_Z=np.ndarray(hdul[1].header['ssp_number'])
			csp_light=np.ndarray(hdul[1].header['ssp_number'])
			csp_mass=np.ndarray(hdul[1].header['ssp_number'])
			for i in range(len(csp_age)):
				csp_age[i]=hdul[1].header['log_age_ssp_'+str(i)]
				csp_Z[i]=hdul[1].header['metal_ssp_'+str(i)]
				csp_light[i]=hdul[1].header['weightLight_ssp_'+str(i)]
				csp_mass[i]=hdul[1].header['weightMass_ssp_'+str(i)]
			"""
			age         = str(np.around(10**hdul[1].header['age_lightW'],decimals=2))+' Gyr'
			metallicity = str(np.around(hdul[1].header['metallicity_lightW'],decimals=2))+' dex'
			mass        = str(np.around(hdul[1].header['stellar_mass'],decimals=2))
			light       = str(np.around(hdul[1].header['EBV'],decimals=2))+' mag'

			ax.plot(wavelength, flux, label = 'Original data')
			ax.plot(wavelength, model, label = 'Fitted data')
			ax.set_title('Output: '+ os.path.basename(job_submission.output_file.name) + '\n')
			ax.set_xlim(left = wavelength[0])
			ax.set_xlim(right = wavelength[-1])
			ax.legend()
			ax.grid()

			plt.savefig(buffer, format='png')
			buffer.seek(0)
			image_png = buffer.getvalue()
			buffer.close()

			graphic = base64.b64encode(image_png)
			graphic = graphic.decode('utf-8')

			return render(request, 
						  'firefly/processed.html', 
						 {'job_id': job_id, 
						  'plot':graphic,
						  'age': age,
						  'metallicity': metallicity,
						  'mass': mass,
						  'light': light})

		#If it doesn't display a loading page
		else:

			data = np.loadtxt(job_submission.input_file, unpack=True)
			lamb = data[0,:]

			redshift = 1.33
			wavelength = data[0,:][np.where(lamb > 3600 * (1 + redshift))]
			flux = data[1,:][np.where(lamb > 3600 * (1 + redshift))]

			ax.plot(wavelength, flux, label = 'Original data')
			ax.set_title('Input: ' + os.path.basename(job_submission.input_file.name))
			ax.set_xlim(left = wavelength[0])
			ax.set_xlim(right = wavelength[-1])
			ax.legend()
			ax.grid()

			plt.savefig(buffer, format='png')
			buffer.seek(0)
			image_png = buffer.getvalue()
			buffer.close()

			graphic = base64.b64encode(image_png)
			graphic = graphic.decode('utf-8')

			return render(request, 'firefly/processing.html', {'job_id': job_id, 'plot':graphic})
	else:
		return render(request, 'firefly/not_found.html', {'job_id': job_id})

#Allow user to download file
def download(request, location, job_id):

	if location == 'results':
		data = Job_Submission.objects.get(job_id = job_id)
		file = data.output_file.name
	elif location == 'example':
		data = Example_Data.objects.get(example_id = job_id)
		file = data.input_file.name
	
	file_path = os.path.join(settings.MEDIA_ROOT, file)

	if os.path.exists(file_path):
		with open(file_path, 'rb') as fh:
			response = HttpResponse(fh.read(), content_type="application/vnd.ms-excel")
			response['Content-Disposition'] = 'inline; filename=' + os.path.basename(file_path)
			return response
	raise Http404

