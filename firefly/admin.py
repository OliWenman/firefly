from django.contrib import admin

from .models import Job_Submission, Example_Data

class Job_SubmissionAdmin(admin.ModelAdmin):

	search_filter = ['status', 'job_id']

	list_display = ('job_id',
					'input_file_',
					'output_file_',
					'status')

# Register your models here.
admin.site.register(Job_Submission, Job_SubmissionAdmin)
admin.site.register(Example_Data)