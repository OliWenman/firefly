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

"""
@background(name = 'firefly', queue = 'my-queue')
def firefly_run(input_file, 
				job_id,
				ageMin,
				ageMax,
				ZMin,
				ZMax,
				flux_units,
				error,
				models_key,
				model_libs,
				imfs,
				wave_medium,
				downgrade_models,
				emissionline_list,
				N_angstrom_masked,
				redshift     = None,
				ra           = None,
				dec          = None,
				vdisp        = None,
				r_instrument = None):

	#warnings.filterwarnings("error")

	#Setup firefly settings
	firefly = firefly_class.Firefly()

	firefly.settings(ageMin           = ageMin,
					 ageMax			  = ageMax,
					 ZMin             = ZMin,
					 ZMax             = ZMax,
					 flux_units       = flux_units,
					 models_key       = models_key,
					 model_libs       = model_libs,
					 imfs             = imfs,
					 data_wave_medium = wave_medium,
					 downgrade_models = downgrade_models)
	try:
		if os.path.splitext(input_file)[1] == ".ascii":
			
			firefly.model_input(redshift     = redshift,
								ra           = ra,
								dec          = dec,
								vdisp        = vdisp,
								r_instrument = r_instrument)

		#Run firefly to process the data
		output = firefly.run(input_file             = input_file, 
							 outputFolder           = settings.MEDIA_ROOT,
							 emissionline_list      = emissionline_list,
							 N_angstrom_masked      = N_angstrom_masked)

		#Get the Job_Submission and save it to the database.
		job_submission = Job_Submission.objects.get(job_id = job_id)
		if os.path.isfile(output):
			job_submission.output_file = output
			job_submission.status = "complete"
		else:
			job_submission.status = "did_not_converge"
		job_submission.save()

		#After completion, remove files from database after certain amount of time
		#so we don't have to store files.
		if clean_db:
			clean_database(job_id)
			
	except:

		traceback.print_exc()

		#Get the Job_Submission and save it to the database.
		job_submission        = Job_Submission.objects.get(job_id = job_id)
		job_submission.status = "failed"
		job_submission.save()

		clean_database(job_id)
"""

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
			sed_file_path = os.path.join(settings.MEDIA_ROOT, sed_file_name)

			#Save the input_file to disk
			file_destination = open(sed_file_path, 'wb+')
			for chunk in sed_file.chunks():
				file_destination.write(chunk)
			file_destination.close()
		
			#Get the variables from the form.
			ageMin, ageMax, ZMin, ZMax, flux_units = settings_form.check_values(ageMin     = request.POST['ageMin'],
																				 ageMax     = request.POST['ageMax'],
																				 ZMin       = request.POST['ZMin'],
																				 ZMax       = request.POST['ZMax'],
																				 flux_units = request.POST['flux_units'])

			#print("ageMin =",ageMin, "ageMax =", ageMax, "ZMin =", ZMin, "ZMax = ", ZMax, "flux_units =", flux_units)
			ageMin			 = float(request.POST['ageMin'])
			#ageMax           = request.POST['ageMax']
			ZMin             = float(request.POST['ZMin'])
			ZMax             = float(request.POST['ZMax'])
			flux_units       = float(request.POST['flux_units'])
			error            = float(request.POST['error'])
			models_key       = request.POST['model_key']
			model_libs       = request.POST['model_libs']
			imfs             = request.POST['imfs']
			wave_medium      = request.POST['wave_medium']
			try:
				downgrade_models = request.POST['downgrade_models']
			except MultiValueDictKeyError:
				downgrade_models = False

			emissionlines = []
			for i in range(emissionlines_form.max_emissionlines):
				if request.POST['Emission_line_' + str(i +1)] != '':
					emissionlines.append(request.POST['Emission_line_' + str(i +1)])
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
		
			#Create Job_Submission instance to save to database
			job_submission = Job_Submission.objects.create(job_id     = job_id,
														   status     = 'processing',
														   input_file = sed_file_path)  
			#Run firefly task in the background
			firefly_run(input_file        = sed_file_path, 
						job_id            = job_id,
						#Model inputs
						ageMin            = ageMin,
						ageMax			  = ageMax,
						ZMin              = ZMin,
						ZMax              = ZMax,
						flux_units        = flux_units,
						error             = error,
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


def processed(request, job_id):

	#Find the the id in databse, if it can't then catch exception and
	#redirect user to page saying the id they want doesn't exist.
	if Job_Submission.objects.filter(job_id = job_id):

		#Checks if output_file exists, if it does display the results
		job_submission = Job_Submission.objects.get(job_id = job_id)

		if job_submission.status == "failed":
			return render(request, 'firefly/error.html', {'job_id': job_id})

		if job_submission.status == "did_not_converge":
			return render(request, 'firefly/did_not_converge.html', {'job_id': job_id})

		plot_size = (7, 5)
		
		if job_submission.output_file.name and job_submission.status == "complete":

			hdul = fits.open(job_submission.output_file.name)

			n_spectra = len(hdul[1].data['wavelength'])

			graphic_array = []	
			for i in range(n_spectra):
				
				fig    = plt.figure(figsize = plot_size)
				buffer = BytesIO()

				data        = hdul[1].data
				wavelength  = data['wavelength'][i]
				flux        = data['original_data'][i]
				model       = data['firefly_model'][i]

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


				gridspec.GridSpec(2,2)
				gridsize = (2,2)

				#Mainplot
				plt.subplot2grid(gridsize, (0,0), colspan = 2, rowspan = 1)
				plt.xlabel('Wavelength (Å)')
				plt.ylabel('Flux')
				plt.ticklabel_format(style='sci', axis='y', scilimits=(0,0))
				plt.plot(wavelength, flux, label = 'Original data')
				plt.plot(wavelength, model, label = 'Fitted data')
				plt.title('Output: '+ os.path.basename(job_submission.output_file.name) + '\n')
				plt.xlim(left = wavelength[0])
				plt.xlim(right = wavelength[-1])
				plt.legend()
				plt.grid()

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

			return render(request, 
						  'firefly/processed.html', 
						 {'job_id': job_id, 
						  'plot':graphic_array,
						  'age': age,
						  'metallicity': metallicity,
						  'mass': mass,
						  'light': light})

		#If it doesn't display a loading page
		else:
			file_extension = os.path.splitext(job_submission.input_file.name)[1]
			
			if file_extension == ".ascii":
				data = np.loadtxt(job_submission.input_file, unpack=True)
				lamb = data[0,:]

				wavelength = data[0,:]
				flux       = data[1,:]
				spectra    = os.path.basename(job_submission.input_file.name)
				n_spectra  = 1
			else:

				hdul = fits.open(job_submission.input_file.name)

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

				plt.plot(wavelength, flux, label = 'Original data')
				plt.title(spectra)

				plt.xlim(left = left, right = right)
				plt.legend()
				plt.grid()
				plt.xlabel('Wavelength (Å)')
				plt.ylabel('Flux')

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
						  {'job_id': job_id, 
						  'plot'   : graphic_array,
						  'queue'  : queue})
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

	HDUL1 = [ "XTENSION= 'BINTABLE'           / binary table extension",
			  "BITPIX  =                    8 / array data type",                                
			  "NAXIS   =                    2 / number of array dimensions",
			  "NAXIS1  =                   32 / length of dimension 1",                          
			  "NAXIS2  =                 3818 / length of dimension 2",
			  "PCOUNT  =                    0 / number of group parameters",                     
			  "GCOUNT  =                    1 / number of groups",                               
			  "TFIELDS =                    8 / number of table fields",                         
			  "TTYPE1  = flux    " ,                                                           
			  "TFORM1  = E       ",                                                            
			  "TTYPE2  = loglam  ",                                                            
			  "TFORM2  = E       ",                                                            
			  "TTYPE3  = ivar    ",                                                            
			  "TFORM3  = E       ",
			  "END   "
	]

	HDUL2 = [ "Z = /The redshift value",
			  ""

	]


	return render(request, 'firefly/fits_format.html', {'HDUL1': HDUL1})