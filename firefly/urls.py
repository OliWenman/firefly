from django.urls import path

from django.conf.urls import * #patterns, include, url
from django.conf.urls.static import static
from django.conf import settings

from django.contrib import admin

from . import views

app_name = 'firefly'
urlpatterns = [
	path('', views.home2, name = 'home'),
	path('processing/<int:results_id>', views.processing, name = 'processing'),
	path('processed/<int:results_id>/', views.processed, name = 'processed'),
	path('download/<int:results_id>/', views.download, name = 'download'),
	#url(r'^download/(?P<path>.*)$', views.download, {'document_root': settings.MEDIA_ROOT})
	] + static(settings.MEDIA_URL, document_root=settings.MEDIA_ROOT)