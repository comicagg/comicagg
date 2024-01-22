from django.http import HttpRequest
from django.shortcuts import redirect


def cookie_consent_required(original_function):
    def wrapper(*args, **kwargs):
        request: HttpRequest = args[0] if len(args) == 1 else args[1]
        if request.session['cookie_consent_accepted']:
            return original_function(*args, **kwargs)
        request.session['cookie_consent_required'] = True
        request.session['show_cookie_consent'] = True
        request.session['cookie_consent_redirecting'] = True
        return redirect("about:cookies")

    return wrapper

class CookieConsentRequiredMixin:
    """Verify that the user has consented to cookies."""

    def dispatch(self, request, *args, **kwargs):
        if request.session['cookie_consent_accepted']:
            return super().dispatch(request, *args, **kwargs)
        request.session['cookie_consent_required'] = True
        request.session['show_cookie_consent'] = True
        request.session['cookie_consent_redirecting'] = True
        return redirect("about:cookies")
