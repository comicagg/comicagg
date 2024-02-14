from django.conf import settings
from django.http import HttpResponse, HttpResponseRedirect

from . import ConsentHttpRequest


def set_consent(request: ConsentHttpRequest) -> HttpResponse:
    response = HttpResponseRedirect(request.META.get("HTTP_REFERER", "/"))
    if request.method == "POST":
        accepted = request.POST.get(settings.COOKIE_CONSENT_COOKIE_NAME) == "1"
        if accepted:
            request.consent.accepted = True
        else:
            request.consent.rejected = True
        response.set_cookie(
            settings.COOKIE_CONSENT_COOKIE_NAME,
            "1" if accepted else "0",
            max_age=365 * 24 * 3600,
        )
    return response
