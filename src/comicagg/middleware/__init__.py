import logging
import sys
from datetime import datetime, timezone

from django.conf import settings
from django.core.exceptions import ObjectDoesNotExist
from django.http import HttpRequest
from django.shortcuts import render
from django.views.debug import technical_500_response

from comicagg.accounts.models import User, UserProfile
from comicagg.typings import AuthenticatedHttpRequest

logger = logging.getLogger(__name__)


class UserBasedExceptionMiddleware:
    """If there's a 500 error, show a detailed error page if the user is a super user."""

    def __init__(self, get_response):
        self.get_response = get_response

    def process_exception(self, request: AuthenticatedHttpRequest, exception):
        try:
            user = request.user
        except Exception:
            user = None
        if user and user.is_superuser:
            return technical_500_response(request, *sys.exc_info())


class MaintenanceMiddleware:
    """
    Display a maintenance page if the current user is not a super user.
    Allows anonymous users to navigate the site.
    """

    def __init__(self, get_response):
        self.get_response = get_response

    def __call__(self, request: AuthenticatedHttpRequest):
        if (
            settings.MAINTENANCE
            and request.user.is_authenticated
            and not request.user.is_superuser
        ):
            return render(request, "maintenance.html", {})
        return self.get_response(request)


class ActiveUserMiddleware:
    """
    Updates the user's profile last access time.
    Checks if the user is active or not and redirects to the reactivate page.
    """

    def __init__(self, get_response):
        self.get_response = get_response

    def __call__(self, request: AuthenticatedHttpRequest):
        if request.user.is_authenticated:
            # Update the user's profile last access time
            # We do it here so all requests can be traced (api, web, etc)
            try:
                request.user.user_profile.last_read_access = datetime.now(timezone.utc)
                # FUTURE: can this be saved async?
                request.user.user_profile.save()
            except ObjectDoesNotExist:
                user_profile = UserProfile(
                    user=request.user, last_read_access=datetime.now(timezone.utc)
                )
                user_profile.save()
            # Check if the user is active or not and redirect to the reactivate page.
            if not request.user.is_active:
                try:
                    request.POST["activate"]
                except Exception:
                    return render(request, "accounts/activate.html", {})
        return self.get_response(request)


class UserProxyOverwriteMiddleware:
    """Overwrite the user object with our own User proxy model"""

    def __init__(self, get_response):
        self.get_response = get_response

    def __call__(self, request: HttpRequest):
        if request.user.is_authenticated:
            request.user = User.objects.get(pk=request.user.pk)
        return self.get_response(request)
