# -*- coding: utf-8 -*-
import logging
import sys
from datetime import datetime, timezone

from django.conf import settings
from django.views.debug import technical_500_response

from comicagg import render
from comicagg.accounts.utils import get_profile
from comicagg.comics.utils import UserOperations

logger = logging.getLogger(__name__)


class UserBasedExceptionMiddleware:
    def __init__(self, get_response):
        self.get_response = get_response

    # def __call__(self, request):
    #     return self.get_response(request)

    def process_exception(self, request, exception):
        try:
            user = request.user
        except:
            user = None
        if user and user.is_superuser:
            return technical_500_response(request, *sys.exc_info())


class MaintenanceMiddleware:
    def __init__(self, get_response):
        self.get_response = get_response

    def __call__(self, request):
        try:
            user = request.user
        except:
            user = None
        if user.is_authenticated:
            if settings.MAINTENANCE and not user.is_superuser:
                return render(request, "maintenance.html", {})
        return self.get_response(request)


class UserProfileMiddleware:
    def __init__(self, get_response):
        self.get_response = get_response

    """
    Adds the fields user_profile to the Request object and the operations field to the User object.
    """

    def __call__(self, request):
        if request.user.is_authenticated:
            request.user_profile = get_profile(request.user)
            request.user.operations = UserOperations(request.user)
        return self.get_response(request)


class ActiveUserMiddleware:
    def __init__(self, get_response):
        self.get_response = get_response

    """
    Updates the user's profile last access time.
    Checks if the user is active or not and redirects to the reactivate page.
    """

    def __call__(self, request):
        if request.user.is_authenticated:
            # Update the user's profile last access time
            # We do it here so all requests can be traced (api, web, etc)
            request.user_profile.last_read_access = datetime.now(timezone.utc)
            request.user_profile.save()

            # Check if the user is active or not and redirect to the reactivate page.
            if not request.user.is_active:
                try:
                    request.POST["activate"]
                except:
                    return render(request, "accounts/activate.html", {})
        return self.get_response(request)
