"""Decorators used in the API views."""
from django.http import HttpResponseForbidden
from provider import constants

def write_required(original_function):
    """Check if the passed request has write permissions in the scope."""
    def wrapper(*args, **kwargs):
        request = args[1]
        if request.scope == getattr(constants, "WRITE"):
            return original_function(*args, **kwargs)
        else:
            view = args[0]
            return view.error("Forbidden", "This access token does not have enough permissions", HttpResponseForbidden)
    return wrapper

# FUTURE: decorator to force a certain query string parameter
# FUTURE: decorator to automatically parse a query string parameter in a class field

