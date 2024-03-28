from django.http import HttpRequest


class CookieConsent:

    def __init__(self, *args, **kwargs):
        self.accepted = False
        self.rejected = False
        self.show = False
        self.required = False
        self.redirecting = False


class ConsentHttpRequest(HttpRequest):
    consent: CookieConsent
