# -*- coding: utf-8 -*-
from django.conf import settings
from django.http import HttpResponse
from django.views.debug import technical_500_response
import datetime, json, logging, re, sys
from comicagg import render
from comicagg.accounts.utils import get_profile
from comicagg.comics.utils import UserOperations

logger = logging.getLogger(__name__)

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
        if user.is_authenticated():
            if settings.MAINTENANCE and not user.is_superuser:
                return render(request, "maintenance.html", {})
        return None

class UserProfileMiddleware(object):
    """
    Adds the fields user_profile to the Request object and the operations field to the User object.
    """
    def process_request(self, request):
        if request.user.is_authenticated():
            request.user_profile = get_profile(request.user)
            request.user.operations = UserOperations(request.user)

class ActiveUserMiddleware(object):
    """
    Updates the user's profile last access time.
    Checks if the user is active or not and redirects to the reactivate page.
    """
    def process_request(self, request):
        if request.user.is_authenticated():
            # Update the user's profile last access time
            # We do it here so all requests can be traced (api, web, etc)
            request.user_profile.last_read_access = datetime.datetime.now()
            request.user_profile.save()

            # Check if the user is active or not and redirect to the reactivate page.
            if not request.user.is_active:
                try:
                    request.POST['activate']
                except:
                    return render(request, "accounts/activate.html", {})

