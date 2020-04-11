# -*- coding: utf-8 -*-
"""
Created on Thu Mar 26 20:24:04 2020

@author: Oli
"""
from astropy.io import fits
import numpy as np
import os

def create_fitstable(input_files, output_file):

    print("starting...")
    spectra_name = np.array([])
    flux         = np.array([])
    loglam       = np.array([])
    ivar         = np.array([])
    redshift     = np.array([])
    vdisp        = np.array([])
    ra           = np.array([])
    dec          = np.array([])

    max_length = 0

    file_type = []
    total_spectra = len(input_files)

    #Loop through files, check which one has the largest array
    #and what type of fits file it is
    try:
        for file in input_files:

            with fits.open(file) as hdulist:

                    #Classify type of fits file by checking flux array is 1D or 2D
                    if len(hdulist[1].data['flux'].shape) == 1:

                        if max_length < len(hdulist[1].data['flux']):
                            max_length = len(hdulist[1].data['flux'])
                        file_type.append("SDSS")

                    elif len(hdulist[1].data['flux'].shape) == 2:

                        if max_length < len(hdulist[1].data['flux'][0]):
                            max_length = len(hdulist[1].data['flux'][0])
                        file_type.append("multi-spectra")

                    else:
                        raise Exception("File '" + os.path.basename(file) + "' column should not be greater than 2D.")

    except:
        raise Exception("Fits file '" + os.path.basename(file) + "' not correct format.")

    zero_array = np.zeros(max_length)

    counter = 0
    #Loop through the files
    try:
        for file in input_files:
           
            with fits.open(file) as hdulist:

                #Find flux, pad it out with the last value if its smaller then the largest array so all are same length
                #Append it to the flux array
                #temp_flux = hdulist[1].data['flux']
                #temp_flux = np.pad(hdulist[1].data['flux'], (0,max_length - len(temp_flux)), mode='constant', constant_values=0)
                #flux = np.append(flux, temp_flux)
                if file_type[counter] == "SDSS":
                    new_length = max_length - len(hdulist[1].data['flux'])
                    temp_flux = np.append(hdulist[1].data['flux'], np.full(shape = new_length, fill_value = hdulist[1].data['loglam'][-1]))
                    flux = np.append(flux, temp_flux)

                    #Find loglam, pad it out with the last value if its smaller then the largest array so all are same length
                    #Append it to the loglam array
                    temp_loglam = np.append(hdulist[1].data['loglam'], np.full(shape = new_length, fill_value = hdulist[1].data['loglam'][-1]))
                    loglam = np.append(loglam, temp_loglam)

                    #Find ivar, pad it out with the last value if its smaller then the largest array so all are same length
                    #Append it to the ivar array
                    temp_ivar = np.append(hdulist[1].data['ivar'], np.full(shape = new_length, fill_value = hdulist[1].data['ivar'][-1]))
                    ivar = np.append(ivar, temp_ivar)
                    
                    spectra_name = np.append(spectra_name, os.path.basename(file))

                    #Check if data is in original SDSS format or firefly format 
                    ra = np.append(ra, hdulist[0].header['RA'])
                    dec = np.append(dec, hdulist[0].header['DEC'])
                    redshift = np.append(redshift, hdulist[2].data['Z']) 
                    vdisp = np.append(vdisp, hdulist[2].data['VDISP'])

                
                elif file_type[counter] == "multi-spectra":

                    for i in range(len(hdulist[1].data['spectra'])):

                        new_length = max_length - len(hdulist[1].data['flux'][i])
                        temp_flux = np.append(hdulist[1].data['flux'][i], np.full(shape = new_length, fill_value = hdulist[1].data['loglam'][i][-1]))
                        flux = np.append(flux, temp_flux)

                        #Find loglam, pad it out with the last value if its smaller then the largest array so all are same length
                        #Append it to the loglam array
                        temp_loglam = np.append(hdulist[1].data['loglam'][i], np.full(shape = new_length, fill_value = hdulist[1].data['loglam'][i][-1]))
                        loglam = np.append(loglam, temp_loglam)

                        #Find ivar, pad it out with the last value if its smaller then the largest array so all are same length
                        #Append it to the ivar array
                        temp_ivar = np.append(hdulist[1].data['ivar'][i], np.full(shape = new_length, fill_value = hdulist[1].data['ivar'][i][-1]))
                        ivar = np.append(ivar, temp_ivar)
                        
                        spectra_name = np.append(spectra_name, hdulist[1].data['spectra'][i])

                        ra       = np.append(ra,       hdulist[1].data['RA'][i])
                        dec      = np.append(dec,      hdulist[1].data['DEC'][i])
                        redshift = np.append(redshift, hdulist[1].data['Z'][i])
                        vdisp    = np.append(vdisp,    hdulist[1].data['VDISP'][i])

                        total_spectra = total_spectra + 1
                    
                    total_spectra = total_spectra - 1

            counter = counter + 1
    except:
        raise Exception("Fits file '" + os.path.basename(file) + "' not correct format.")

    #Reshape the arrays so they are 2D
    try:
        flux   = np.reshape(flux,   (total_spectra, max_length)) 
        loglam = np.reshape(loglam, (total_spectra, max_length))
        ivar   = np.reshape(ivar,   (total_spectra, max_length))
    except:
        Exception("Fits file not correct format.")

    #Store the arrays in the correct format
    array_format = str(max_length) + 'D'

    #Create the columns for the fits table
    col0 = fits.Column(name ='spectra',format = '20A', array = spectra_name)
    col1 = fits.Column(name ='flux',   format = array_format, array = flux)
    col2 = fits.Column(name ='loglam', format = array_format, array = loglam)
    col3 = fits.Column(name ='ivar',   format = array_format, array = ivar)
    col4 = fits.Column(name ='Z',      format = 'D', array = redshift)
    col5 = fits.Column(name ='vdisp',  format = 'D', array = vdisp)
    col6 = fits.Column(name ='ra',     format = 'D', array = ra)
    col7 = fits.Column(name ='dec',    format = 'D', array = dec)

    #Add the columns and save the table
    coldefs = fits.ColDefs([col0, col1, col2, col3, col4, col5, col6, col7])
    hdul    = fits.BinTableHDU.from_columns(coldefs)
    #hdul.header['OBSERVER'] = 'Edwin Hubble'

    hdul.writeto(output_file, overwrite=True)

    print("wrote to", output_file)

    """
    hdul = fits.open(output_file)

    flux_array = hdul[1].data['flux']

    print(hdul[1].header)

    max_spectra = 100
    for i in range(len(flux_array)):

        if i >= max_spectra:
            i = max_spectra
            break

        flux   = flux_array[i]
        loglam = hdul[1].data['loglam'][i]
        ivar   = hdul[1].data['ivar'][i]

        redshift = hdul[1].data['Z'][i]
        vdisp    = hdul[1].data['vdisp'][i]
        ra       = hdul[1].data['ra'][i]
        dec      = hdul[1].data['dec'][i]
    """

    return output_file

def check_file_extensions(filelist):

    extension_list = []

    for file in filelist:

        try:
            file_extension = os.path.splitext(file.name)[1] 
        except:
            file_extension = os.path.splitext(file)[1] 

        if file_extension == ".fits" or file_extension == ".ascii": 
            extension_list.append(file_extension)
        else:
            raise Exception("'"+ file_extension + "' not supported. Supported file uploads are a single '.ascii' file or multiple '.fits' files.")

    if all(extension_list) == False:
        raise Exception("Only '.fits' are supported for multi file upload.")

    if extension_list[0] == ".ascii" and len(extension_list) > 1:
        raise Exception("Processing more than one '.ascii' file not supported.")
    
    elif extension_list[0] == ".ascii" and len(extension_list) == 1:
        filetype = ".ascii"
    
    elif extension_list[0] == ".fits":
        filetype = ".fits" 

    return filetype

if __name__ == '__main__':
    input_files = ["/Users/User/Documents/University/Third_Year/Project/Webstie/firefly_website/core_firefly/example_data/spectra/0266/spec-0266-51602-0573.fits", 
                   "/Users/User/Documents/University/Third_Year/Project/Webstie/firefly_website/core_firefly/example_data/spectra/0266/spec-0266-51630-0623.fits",
                   "/Users/User/Documents/University/Third_Year/Project/Webstie/firefly_website/core_firefly/example_data/spectra/1045/spec-1045-52725-0628.fits",
                   "/Users/User/Documents/University/Third_Year/Project/Webstie/firefly_website/core_firefly/example_data/spectra/3586/spec-3586-55181-0003.fits",
                   "/Users/User/Documents/University/Third_Year/Project/Webstie/firefly_website/media/input_files/input_8021059020400.fits",
                   "/Users/User/Desktop/Doc1.docx"
    ]

    print("running...")
    #create_fitstable(input_files = input_files, output_file = "/Users/User/Documents/test.fits")
    #check_file_extensions(filelist = input_files)
    print("finished.")