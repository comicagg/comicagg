# -*- coding: utf-8 -*-
from comicagg import render
from django.conf import settings
from django.views.debug import technical_500_response
import sys

class UserBasedExceptionMiddleware(object):
	def process_exception(self, request, exception):
		try:
			user = request.user
		except:
			user = None
		if user and user.is_superuser:
			return technical_500_response(request, *sys.exc_info())

class MaintenanceMiddleware(object):
	def process_request(self, request):
		try:
			user = request.user
		except:
			user = None
		if settings.MAINTENANCE:
			if not(user and user.is_superuser):
				return render(request, "maintenance.html", {})
