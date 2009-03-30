# -*- coding: utf-8 -*-
from django.contrib.auth.models import User
from django.db import models

# Create your models here.
class Task(models.Model):
	user = models.ForeignKey(User, default=1)
	state = models.BooleanField('¿Está terminado?', default=False)
	title = models.CharField('Título', max_length=255)
	date = models.DateTimeField('Fecha creación', auto_now_add=True)
	notes = models.TextField('Notas')
	
	class Meta:
		ordering = ['state']

	def __unicode__(self):
		return self.title
