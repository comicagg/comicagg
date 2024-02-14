from typing import Callable

from django.conf import settings
from django.http import HttpRequest, HttpResponse

from . import ConsentHttpRequest, CookieConsent


class CookieConsentMiddleware:
    """
    Set variables in the session object depending on the user rejecting cookies or not.
    """

    def __init__(self, get_response: Callable[[HttpRequest], HttpResponse]):
        self.get_response = get_response

    def __call__(self, request: ConsentHttpRequest):
        request.consent = CookieConsent()
        accepted = False
        rejected = False
        if consent := request.COOKIES.get(settings.COOKIE_CONSENT_COOKIE_NAME):
            # 1, 0, None
            accepted = consent == "1"
            rejected = not accepted

        if accepted:
            request.consent.accepted = True
        elif rejected:
            request.consent.rejected = True
        else:
            # Cookie consent pending
            request.consent.show = True
            if settings.SESSION_COOKIE_NAME in request.COOKIES:
                # The user already has a session, but they haven't accepted the cookies yet.
                # We will redirect to login with consent being displayed.
                request.COOKIES.pop(settings.SESSION_COOKIE_NAME)
                request.consent.redirecting = True

        response = self.get_response(request)

        if request.consent.rejected or request.consent.redirecting:
            response.delete_cookie(settings.SESSION_COOKIE_NAME)
            # CSRF should not be removed in case the user needs to submit the consent
            # response.delete_cookie(settings.CSRF_COOKIE_NAME)
        return response
