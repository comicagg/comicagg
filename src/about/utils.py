from django.shortcuts import redirect

from . import ConsentHttpRequest


def consent_show(original_function):
    """Decorate a view to show the consent dialog if cookies have not been accepted."""

    def wrapper(*args, **kwargs):
        request: ConsentHttpRequest = args[0] if len(args) == 1 else args[1]
        if not request.consent.accepted:
            request.consent.show = True
        return original_function(*args, **kwargs)

    return wrapper


def consent_required(original_function):
    """Decorate a function to require cookie consent. If not accepted,
    redirect to the cookie consent page."""

    def wrapper(*args, **kwargs):
        request: ConsentHttpRequest = args[0] if len(args) == 1 else args[1]
        if request.consent.accepted:
            return original_function(*args, **kwargs)
        # request.consent.required = True
        # request.consent.show = True
        request.consent.redirecting = True
        return redirect("about:cookies")

    return wrapper


class ConsentRequiredMixin:
    """Verify that the user has consented to cookies."""

    def dispatch(self, request, *args, **kwargs):
        if request.consent.accepted:
            return super().dispatch(request, *args, **kwargs)  # type: ignore
        # request.consent.required = True
        # request.consent.show = True
        request.consent.redirecting = True
        return redirect("about:cookies")
