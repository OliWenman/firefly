#Import Django related functions
from django.shortcuts import render, get_object_or_404, redirect
from django.http import HttpResponseRedirect, FileResponse, HttpResponse, Http404
from django.urls import reverse
from django.utils.text import slugify
from django.utils.datastructures import MultiValueDictKeyError
from django.core.files.storage import FileSystemStorage
from django.conf import settings
from django.utils import timezone
from django.db.models import Q

#Import seperate background_tasks, allows for processing to be done in background
#and not risk a timeout requesting a page while processing.
from background_task import background
from background_task.models import Task
from background_task.models import CompletedTask

#Import my model and forms
from .models import Job_Submission, Example_Data
from .forms import FireFlySettings_Form, SEDform, SEDfileform, Emissionlines_Form, ASCCI_additional_inputs

#Import firefly
from core_firefly import firefly_class
from core_firefly.firefly_wrapper import firefly_run

import numpy as np
import random
import time
import os
import warnings
from io import BytesIO
import base64
import matplotlib.pyplot as plt
import matplotlib.gridspec as gridspec
from astropy.io import fits
import sys, traceback
from .fits_table import Fits_Table
import astropy.cosmology as co
from multiprocessing import Process

time_in_database = 60*60
clean_db = True

#Automatically delete job from databse after certain amount of time.
@background(name = 'clean_db', schedule=time_in_database, queue = 'my-queue')
def clean_database(job_id):

	try:
		job_submission = Job_Submission.objects.get(job_id = job_id)
		job_id = job_submission.job_id
		job_submission.delete()
		print("deleted", job_id)
	except:
		print("Failed to delete", job_id)

def home(request):

	#Post method shows submitting form data
	if request.method == 'POST':
		print(request.POST)

		#Get the form submitted and check it's valid for use
		emissionlines_form  = Emissionlines_Form(request.POST)
		settings_form       = FireFlySettings_Form(request.POST)
		sedfile_form        = SEDfileform(request.POST, request.FILES)
		additional_inputs   =  ASCCI_additional_inputs(request.POST)

		#If the forms are valid, process the data
		if settings_form.is_valid() and sedfile_form.is_valid() and additional_inputs.is_valid() and emissionlines_form.is_valid():

			#Use the date and time to make unique job_id via scrambling the digits.
			time_stamp = time.strftime("%Y%m%d%H%M%S")
			job_id = int(''.join(random.sample(time_stamp,len(time_stamp))))

			#Get the SED input_file
			sed_file = request.FILES.get('input_file')
			
			#Create a new input_file name to make it unique.
			file_extension = os.path.splitext(sed_file.name)[1]	

			if file_extension == ".ascii":
				n = -6
			elif file_extension == ".fits":
				n = -5		

			sed_file_name = sed_file.name[0:n] + "_" +str(job_id) + file_extension
			sed_file_path = os.path.join(settings.INPUT_FILES, sed_file_name)

			#Save the input_file to disk
			file_destination = open(sed_file_path, 'wb+')
			for chunk in sed_file.chunks():
				file_destination.write(chunk)
			file_destination.close()

			hdulist      = fits.open(sed_file_path)
			n_spectra    = len(hdulist[1].data["spectra"])
			hdulist.close()
		
			#Get the variables from the form.
			ageMin, ageMax, ZMin, ZMax, flux_units = settings_form.check_values(ageMin     = request.POST['ageMin'],
																				 ageMax     = request.POST['ageMax'],
																				 ZMin       = request.POST['ZMin'],
																				 ZMax       = request.POST['ZMax'],
																				 flux_units = request.POST['flux_units'])

			#print("ageMin =",ageMin, "ageMax =", ageMax, "ZMin =", ZMin, "ZMax = ", ZMax, "flux_units =", flux_units)
			ageMin			 = float(request.POST['ageMin'])
			print(ageMin)
			#ageMax           = request.POST['ageMax']
			ZMin             = float(request.POST['ZMin'])
			ZMax             = float(request.POST['ZMax'])
			flux_units       = float(request.POST['flux_units'])
			#error            = float(request.POST['error'])
			models_key       = request.POST['model_key']
			model_libs       = request.POST['model_libs']
			imfs             = request.POST['imfs']
			wave_medium      = request.POST['wave_medium']
			try:
				request.POST['downgrade_models']
				downgrade_models = True
			except MultiValueDictKeyError:
				downgrade_models = False

			emissionlines = []
			emission_lines_str = ""
			for i in range(emissionlines_form.max_emissionlines):
				if request.POST['Emission_line_' + str(i +1)] != '':
					emissionlines.append(request.POST['Emission_line_' + str(i +1)])
					emission_lines_str = emission_lines_str + ", "+ request.POST['Emission_line_' + str(i +1)]
			N_angstrom_masked = float(request.POST['N_angstrom_masked'])

			#ASCII inputs
			try:
				redshift     = float(request.POST['redshift'])
				ra           = float(request.POST['ra'])
				dec          = float(request.POST['dec'])
				vdisp        = float(request.POST['vdisp'])
				r_instrument = float(request.POST['r_instrument'])
			except(ValueError):
				redshift = ra = dec = vdisp = r_instrument = None

			if model_libs == "MILES":
				temp_model_libs = model_libs + " - "+ models_key
			else:
				temp_model_libs = model_libs
		
			"""
			if ageMax == None:
				if file_extension == ".fits":
					hdul = fits.open(sed_file_path)
					true_redshift = hdul[1].data['Z']
					hdul.close()
				else:
					true_redshift = redshift
				ageMax = co.Planck15.age(true_redshift).value
				print(ageMax)
				print(true_redshift)
			else:
				ageMax = float(ageMax)
			"""

			place_holder = 0

			#Create Job_Submission instance to save to database
			job_submission = Job_Submission.objects.create(job_id     = job_id,
														   status     = 'queued',
														   input_file = os.path.relpath(sed_file_path, settings.MEDIA_ROOT),
														   n_spectra  = n_spectra,
														   ageMin     = ageMin,
														   ageMax     = place_holder,
														   Zmin       = ZMin,
														   Zmax       = ZMax,
														   flux_units = flux_units,
														   imf        = imfs,
														   model      = temp_model_libs,
														   wave_medium = wave_medium,
														   downgrade_models = downgrade_models,
														   width_masking = N_angstrom_masked,
														   emission_lines = emission_lines_str)  
			#Run firefly task in the background
			p = Process(target = firefly_run, args = (sed_file_path, 
													  job_id,
													  ageMin,
													  ageMax,
													  ZMin,
													  ZMax,
													  flux_units,
													  0,
													  models_key,
													  model_libs,
													  imfs,
													  wave_medium,
													  downgrade_models,
													  emissionlines,
													  N_angstrom_masked,
													  #Additional ascii file inputs
													  redshift,
													  ra,
													  dec,
													  vdisp,
													  r_instrument))
			p.run()

			"""
			firefly_run(input_file        = sed_file_path, 
						job_id            = job_id,
						#Model inputs
						ageMin            = ageMin,
						ageMax			  = ageMax,
						ZMin              = ZMin,
						ZMax              = ZMax,
						flux_units        = flux_units,
						error             = 0,
						models_key        = models_key,
						model_libs        = model_libs,
						imfs              = imfs,
						wave_medium       = wave_medium,
						downgrade_models  = downgrade_models,
						emissionline_list = emissionlines,
						N_angstrom_masked = N_angstrom_masked,
						#Additional ascii file inputs
						redshift          = redshift,
						ra                = ra,
						dec               = dec,
						vdisp             = vdisp,
						r_instrument      = r_instrument)
			"""

			#Use HttpResponseRedirect when submitting forms to stop resubmitting
			return HttpResponseRedirect(reverse('firefly:processed', args=(job_id,)))

		#Otherwise redirect back to form page with the forms that were used, display errors to user
		else:
			return render(request, 
						 'firefly/home2.html', 
						 {'form':settings_form, 
						 'SED':sedfile_form,
						 'emissionlines_form' : emissionlines_form,
						 'ascii_additional_inputs': additional_inputs})

	#Create a new form instance if first time visiting site
	emissionlines_form = Emissionlines_Form()
	settings_form      = FireFlySettings_Form()
	sedfile_form       = SEDfileform()
	additional_inputs  = ASCCI_additional_inputs()

	#Dispaly a new form to user if first time on site.
	return render(request, 
				 'firefly/home2.html', 
				 {'form': settings_form, 
				 'SED'  : sedfile_form,
				 'emissionlines_form' : emissionlines_form,
				 'ascii_additional_inputs': additional_inputs})

import matplotlib as mpl
def processed(request, job_id):

	mpl.use('Agg')

	#Find the the id in databse, if it can't then catch exception and
	#redirect user to page saying the id they want doesn't exist.
	if Job_Submission.objects.filter(job_id = job_id):

		#Checks if output_file exists, if it does display the results
		job_submission = Job_Submission.objects.get(job_id = job_id)

		if job_submission.status == "failed":
			return render(request, 'firefly/error.html', {'job_id': job_id})

		plot_size = (7, 5)
		
		if job_submission.output_file.name and job_submission.status == "complete":

			hdul = fits.open(job_submission.output_file.path)

			n_spectra = len(hdul[1].data['wavelength'])

			graphic_array      = []	
			metallicity_array  = []
			stellar_mass_array = []
			age_array          = []
			light_array        = []
			converged_array    = []
			#imf_array          = []
			#model_array        = []
			for i in range(n_spectra):
				
				fig    = plt.figure(figsize = plot_size)
				buffer = BytesIO()

				wavelength  = hdul[1].data['wavelength'][i]
				flux        = hdul[1].data['original_data'][i]
				model       = hdul[1].data['firefly_model'][i]
				spectra     = hdul[1].data['spectra'][i]
				converged   = hdul[1].data['converged'][i]
				#imf         = hdul[1].data['IMF'][i]
				#model_used  = hdul[1].data['Model'][i]

				#imf_array.append(imf)
				#model_array.append(model_used)

				if converged == 'False':
					converged = False
				elif converged == 'True':
					converged = True

				converged_array.append(converged)

				if converged:

					csp_age=np.ndarray(int(hdul[1].data['ssp_number'][i]))
					csp_Z=np.ndarray(int(hdul[1].data['ssp_number'][i]))
					csp_light=np.ndarray(int(hdul[1].data['ssp_number'][i]))
					csp_mass=np.ndarray(int(hdul[1].data['ssp_number'][i]))
					
					age         = str(np.around(10**hdul[1].data['age_lightW'][i],decimals=2))+' Gyr'
					metallicity = str(np.around(hdul[1].data['metallicity_lightW'][i],decimals=2))+' dex'
					mass        = str(np.around(hdul[1].data['stellar_mass'][i],decimals=2))
					light       = str(np.around(hdul[1].data['EBV'][i],decimals=2))+' mag'

					for n in range(len(csp_age)):
						csp_age[n]=hdul[1].data['log_age_ssp_'+str(n)][i]
						csp_Z[n]=hdul[1].data['metal_ssp_'+str(n)][i]
						csp_light[n]=hdul[1].data['weightLight_ssp_'+str(n)][i]
						csp_mass[n]=hdul[1].data['weightMass_ssp_'+str(n)][i]
				else:
					age         = None
					metallicity = None
					mass        = None
					light       = None

				age_array.append(age)
				metallicity_array.append(metallicity)
				stellar_mass_array.append(mass)
				light_array.append(light)

				gridspec.GridSpec(2,2)
				gridsize = (2,2)

				#Mainplot
				plt.subplot2grid(gridsize, (0,0), colspan = 2, rowspan = 1)
				plt.xlabel('Wavelength (Å)')
				plt.ylabel('Flux')
				plt.ticklabel_format(style='sci', axis='y', scilimits=(0,0))
				plt.plot(wavelength, flux, label = 'Original data')
				if converged:
					plt.plot(wavelength, model, label = 'Fitted data')
				plt.title(spectra)
				plt.xlim(left = wavelength[0], right = wavelength[-1])
				plt.ylim(bottom = 0)
				plt.legend()
				plt.grid()

				if converged == True:
					#Small subplot 1
					plt.subplot2grid(gridsize, (1,0))
					plt.bar(10**(csp_age),
							csp_light,
							width=0.3,
							align='center',
							alpha=0.5)
					plt.xlabel('Age')
					plt.ylabel('frequency/Gyr')
					#plt.title() 

					#Small subplot 2
					plt.subplot2grid(gridsize, (1,1))
					plt.bar(csp_Z, 
							csp_light, 
							width=0.1, 
							align='center', 
							alpha=0.5)
					plt.xlabel('Z')
					plt.ylabel('frequency/Gyr')
					#plt.title()

				fig.tight_layout()

				plt.savefig(buffer, format='png')
				buffer.seek(0)
				image_png = buffer.getvalue()
				buffer.close()
				plt.close()

				graphic = base64.b64encode(image_png)
				graphic = graphic.decode('utf-8')

				graphic_array.append(graphic)	

			hdul.close()
			input_array = []

			return render(request, 
						  'firefly/processed.html', 
						 {'job_id':           job_id, 
						  'plot':             graphic_array,
						  'converged':        converged_array,
						  'model':            job_submission.model,
						  'imf':              job_submission.imf,
						  'ageMin':           job_submission.ageMin,
						  'ageMax':           job_submission.ageMax,
						  'Zmin'  :           job_submission.Zmin,
						  'Zmax'  :           job_submission.Zmax,
						  'flux_units':       job_submission.flux_units,
						  'wave_medium':      job_submission.wave_medium,
						  'downgrade_models': job_submission.downgrade_models,
						  'width_masking':    job_submission.width_masking,
						  'emission_lines':   job_submission.emission_lines,
						  'age':              age_array,
						  'metallicity':      metallicity_array,
						  'mass':             stellar_mass_array,
						  'light':            light_array})

		#If it doesn't, display a loading page
		else:
			file_extension = os.path.splitext(job_submission.input_file.name)[1]
			
			if file_extension == ".ascii":
				data = np.loadtxt(job_submission.input_file.path, unpack=True)
				lamb = data[0,:]

				wavelength = data[0,:]
				flux       = data[1,:]
				spectra    = os.path.basename(job_submission.input_file.name)
				n_spectra  = 1
			else:

				hdul = fits.open(job_submission.input_file.path)

				n_spectra = len(hdul[1].data['flux'])

				flux_array       = hdul[1].data['flux']
				wavelength_array = 10**hdul[1].data['loglam']
				spectra_array    = hdul[1].data['spectra']
				hdul.close()

			graphic_array = []
			for i in range(n_spectra):

				buffer = BytesIO()

				fig = plt.figure(figsize = plot_size)

				if file_extension == ".fits":
					left  = wavelength_array[i][0]
					right = wavelength_array[i][-1]
					wavelength = wavelength_array[i]
					flux = flux_array[i]
					spectra = spectra_array[i]
				else:
					left  = wavelength[0]
					right = wavelength[-1]

				gridspec.GridSpec(2,2)
				gridsize = (2,2)

				#Mainplot
				plt.subplot2grid(gridsize, (0,0), colspan = 2, rowspan = 1)
				plt.xlabel('Wavelength (Å)')

				plt.plot(wavelength, flux, label = 'Original data')
				plt.title(spectra)

				plt.xlim(left = left, right = right)
				plt.legend()
				plt.grid()
				plt.xlabel('Wavelength (Å)')
				plt.ylabel('Flux')
				plt.tight_layout()

				plt.savefig(buffer, format='png')
				buffer.seek(0)
				image_png = buffer.getvalue()
				buffer.close()
				plt.close()

				graphic = base64.b64encode(image_png)
				graphic = graphic.decode('utf-8')
				graphic_array.append(graphic)				
			

			#Find where the user is in the queue
			running_tasks_qs = Task.objects.filter(task_name = 'firefly')

			found = False
			queue = 0

			for running_task in running_tasks_qs:

				if running_task.task_params.find(str(job_id)) != -1:
					found = True
					break

				queue = queue + 1

			if queue == 0 and found:
				queue = 'You are next - processing your data!'

			return render(request, 
						  'firefly/processing.html', 
						  {'job_id':          job_id, 
						  'plot'   :          graphic_array,
						  'model':            job_submission.model,
						  'imf':              job_submission.imf,
						  'ageMin':           job_submission.ageMin,
						  'ageMax':           job_submission.ageMax,
						  'Zmin'  :           job_submission.Zmin,
						  'Zmax'  :           job_submission.Zmax,
						  'flux_units':       job_submission.flux_units,
						  'wave_medium':      job_submission.wave_medium,
						  'downgrade_models': job_submission.downgrade_models,
						  'width_masking':    job_submission.width_masking,
						  'emission_lines':   job_submission.emission_lines,
						  'queue'  :          queue})
	else:
		return render(request, 'firefly/not_found.html', {'job_id': job_id})

#Allow user to download file
def download(request, location, job_id):

	if location == 'results':
		data = Job_Submission.objects.get(job_id = job_id)
		file_path = data.output_file.path

	elif location == 'example':
		data = Example_Data.objects.get(example_id = job_id)
		file_path = data.input_file.path

	if os.path.exists(file_path):
		with open(file_path, 'rb') as fh:
			response = HttpResponse(fh.read(), content_type="application/vnd.ms-excel")
			response['Content-Disposition'] = 'inline; filename=' + os.path.basename(file_path)
			return response
	raise Http404

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

def fits_format(request):

	data = Example_Data.objects.get(example_id = 0)

	hdul = fits.open(os.path.join(settings.EXAMPLE_FILES, data.input_file.path))

	header0 = []
	header1 = [] 
	for i in hdul[0].header:
		header0.append(str(i) + " = " + str(hdul[0].header[i]) + " / " +str(hdul[0].header.comments[i]))
	
	for i in hdul[1].header:
		header1.append(str(i) + " = " + str(hdul[1].header[i]) + " / " +str(hdul[1].header.comments[i]))

	header0.append("END")
	header1.append("END")
	hdul.close()
	
	return render(request, 'firefly/fits_format.html', {'header0': header0,
														'header1': header1,})