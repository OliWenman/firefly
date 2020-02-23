from django.urls import path

from django.conf.urls import * #patterns, include, url
from django.conf.urls.static import static
from django.conf import settings

from django.contrib import admin

from . import views

app_name = 'firefly'
urlpatterns = [
	path('', views.home, name = 'home'),
	path('processing/', views.processing, name = 'processing'),
	path('processed/<int:results_id>/', views.processed, name = 'processed')
	] + static(settings.MEDIA_URL, document_root=settings.MEDIA_ROOT)