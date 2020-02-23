from django.db import models
from django import forms

from core_firefly import firefly_class

class SED(models.Model):

	file        = models.FileField(upload_to='')
	uploaded_at = models.DateTimeField(auto_now_add=True)
	results_id  = models.IntegerField(default = 0)

class FireflyResults(models.Model):

	file        = models.FileField(upload_to='')
	uploaded_at = models.DateTimeField(auto_now_add=True)


class FireflyTracker(models.Model):

	queue = models.IntegerField(default = 0)

	queuelist = []

	def __str__(self):
		return "Firefly_manager"

	def myturn(self, id):
		
		index = self.queuelist.index(id)
		
		if index != 0:
			return False
		else:
			return True



	