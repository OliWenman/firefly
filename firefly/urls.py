from django.urls import path

from django.conf.urls import * #patterns, include, url
from django.conf.urls.static import static
from django.conf import settings

from django.contrib import admin

from . import views

app_name = 'firefly'
urlpatterns = [
	path('', views.home, name = 'home'),
	path('<int:job_id>/', views.processed, name = 'processed'),
	path('download/<str:location>/<int:job_id>/', views.download, name = 'download'),
	] + static(settings.MEDIA_URL, document_root=settings.MEDIA_ROOT)