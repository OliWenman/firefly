from django.contrib import admin

from .models import FireflyTracker, SED, FireflyResults
# Register your models here.
admin.site.register(FireflyTracker)
#admin.site.register(SED)
admin.site.register(FireflyResults)