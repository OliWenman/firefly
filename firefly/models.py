from django.db import models
from django import forms

from core_firefly import firefly_class

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




	