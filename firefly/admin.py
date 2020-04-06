from django.contrib import admin

from .models import Job_Submission, Example_Data

class Job_SubmissionAdmin(admin.ModelAdmin):

	search_filter = ['status', 'job_id']
	#list_filter = ['n_spectra', 'imf', 'status']

	#fields = ['input_file', 'output_file']
	readonly_fields = ['job_id', 
					   'input_file', 
					   'output_file', 
					   'n_spectra', 
					   'imf', 
					   'model', 
					   'status', 
					   'submitted']
			
	list_display = ('job_id',
					'input_file',
					'output_file',
					'submitted',
					'n_spectra',
					'imf',
					'model',
					'status')

	def has_add_permission(self, request, obj=None):
		return False
	#list_display_links = (None,)

# Register your models here.
admin.site.register(Job_Submission, Job_SubmissionAdmin)
admin.site.register(Example_Data)