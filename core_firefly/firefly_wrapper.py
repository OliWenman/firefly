#Import seperate background_tasks, allows for processing to be done in background
#and not risk a timeout requesting a page while processing.
from background_task import background
from background_task.models import Task
from background_task.models import CompletedTask

from django.conf import settings

#Import my model and forms
from firefly.models import Job_Submission, Example_Data

#Import firefly
from core_firefly import firefly_class

import numpy as np

import numpy as np
import random
import time
import os
import warnings
from io import BytesIO

from astropy.io import fits
import sys, traceback

time_in_database = 60*60
clean_db = True

def convert_to_fits_table(file_list,
						  output_file):

	n_spectra = 3

	wavelength    = np.array([])
	original_data = np.array([])
	firefly_model = np.array([])
	flux_error    = np.array([])

	max_length = 0

	#Loop through files, check which one has the largest array
	for file in file_list:
	    
	    hdulist = fits.open(file)

	    if max_length < len(hdulist[1].data['wavelength']):
	        max_length = len(hdulist[1].data['wavelength'])
	    
	    hdulist.close()

	zero_array = np.zeros(max_length)
	#Loop through the files
	for file in file_list:
	    
	    hdulist = fits.open(file)

	    #Find flux, pad it out with the last value if its smaller then the largest array so all are same length
	    #Append it to the flux array
	    #temp_flux = hdulist[1].data['flux']
	    #temp_flux = np.pad(hdulist[1].data['flux'], (0,max_length - len(temp_flux)), mode='constant', constant_values=0)
	    #flux = np.append(flux, temp_flux)


	    new_length      = max_length - len(hdulist[1].data['wavelength'])
	    temp_wavelength = np.append(hdulist[1].data['wavelength'], np.full(shape = new_length, fill_value = hdulist[1].data['wavelength'][-1]))
	    wavelength      = np.append(wavelength, temp_wavelength)

	    #Find loglam, pad it out with the last value if its smaller then the largest array so all are same length
	    #Append it to the loglam array
	    temp_original_data = np.append(hdulist[1].data['original_data'], np.full(shape = new_length, fill_value = hdulist[1].data['original_data'][-1]))
	    original_data      = np.append(original_data, temp_original_data)

	    #Find ivar, pad it out with the last value if its smaller then the largest array so all are same length
	    #Append it to the ivar array
	    temp_fierfly_model = np.append(hdulist[1].data['firefly_model'], np.full(shape = new_length, fill_value = hdulist[1].data['firefly_model'][-1]))
	    firefly_model      = np.append(firefly_model, temp_fierfly_model)

	    temp_flux_error = np.append(hdulist[1].data['flux_error'], np.full(shape = new_length, fill_value = hdulist[1].data['flux_error'][-1]))
	    flux_error = np.append(flux_error, temp_flux_error)
	    
	    """
	    #spectra_name = np.append(spectra_name, os.path.basename(file))
	    ra           = np.append(ra, hdulist[0].header['RA'])
	    dec          = np.append(dec, hdulist[0].header['DEC'])
	    redshift     = np.append(redshift, hdulist[2].data['Z']) 
	    vdisp        = np.append(vdisp, hdulist[2].data['VDISP'])
	    """
	    hdulist.close()
	    del hdulist

	#Reshape the arrays so they are 2D
	wavelength    = np.reshape(wavelength,    (len(file_list), max_length)) 
	original_data = np.reshape(original_data, (len(file_list), max_length))
	firefly_model = np.reshape(firefly_model, (len(file_list), max_length))
	flux_error    = np.reshape(flux_error,    (len(file_list), max_length))

	#Store the arrays in the correct format
	array_format = str(max_length) + 'D'

	#Create the columns for the fits table
	col0 = fits.Column(name ='wavelength',    format = array_format, array = wavelength)
	col1 = fits.Column(name ='original_data', format = array_format, array = original_data)
	col2 = fits.Column(name ='firefly_model', format = array_format, array = firefly_model)
	col3 = fits.Column(name ='flux_error',    format = array_format, array = flux_error)
	
	columns = [col0, col1, col2, col3]

	my_dict = {}
	i = 0

	for file in file_list:
		
		redshift_found = False
		hdul = fits.open(file)
		keys = list(hdul[1].header.keys())

		for key in keys:
			if key != 'redshift':
				pass
			else:
				redshift_found = True

			if redshift_found:
				if key in my_dict:
					my_dict[key][i] = hdul[1].header[key]
				else:
					thetype = type(hdul[1].header[key])
					if thetype == str:
						my_dict[key] = np.full((len(file_list)), 'N/A', dtype = 'S140')
					else:
						my_dict[key] = np.full((len(file_list)), np.NaN)
					my_dict[key][i] = hdul[1].header[key]

		i = i + 1
		"""
		for key in extra_info_dict:
			extra_info_dict[key] = np.append(extra_info_dict[key], float(hdul[1].header[key]))
		
		for key in extra_info_dict2:
			for i in range(hdul[1].header['ssp_number']):
				extra_info_dict2[key] = np.append(extra_info_dict2[key], float(hdul[1].header[key + str(i)]))
		"""
		hdul.close()
		del hdul

	for key in my_dict:
		myformat = 'D'
		try:
			for i in range(len(file_list)):
				float(my_dict[key][i])
		except:
			myformat = '20A'

		try:
			print(key, my_dict[key])
			columns.append(fits.Column(name = key, format = myformat, array = my_dict[key]))
		except:
			pass

	#Add the columns and save the table
	coldefs = fits.ColDefs(columns)

	hdul    = fits.BinTableHDU.from_columns(coldefs)

	hdul.writeto(output_file, overwrite=True)

	for file in file_list:
		os.remove(file)


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

		output_list = []

		path, file = os.path.split(input_file)

		for i in range(3):
			if os.path.splitext(input_file)[1] == ".ascii":
				
				firefly.model_input(redshift     = redshift,
									ra           = ra,
									dec          = dec,
									vdisp        = vdisp,
									r_instrument = r_instrument)

			output_file_i = os.path.join(path, "temp" + str(i) + "_" + file)

			#Run firefly to process the data
			output = firefly.run(input_file        = input_file, 
								 output_file       = output_file_i,
								 emissionline_list = emissionline_list,
								 N_angstrom_masked = N_angstrom_masked,
								 n_spectrum        = i)

			output_list.append(output)

		output_file = os.path.join(path, "output_" + file)
		convert_to_fits_table(file_list   = output_list,
							  output_file = output_file)



		#Get the Job_Submission and save it to the database.
		job_submission = Job_Submission.objects.get(job_id = job_id)
		if os.path.isfile(output_file):
			job_submission.output_file = output_file
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