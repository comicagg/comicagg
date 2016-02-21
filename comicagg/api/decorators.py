"""Decorators used in the API views.

In the decorator parameters we can find:
 args[0] is the View
 args[1] is the Request
 kwargs are the query string parameters
"""
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

def parse_param(param_name):
    """Add the argument named param_name as an attribute in the view class."""
    def wrapper(original_function):
        def wrapped(*args, **kwargs):
            view = args[0]
            request = args[1]
            context = view.get_context_data(**kwargs)
            # NOTE: For the moment we'll allow this to throw KeyError if the parameter does not exist
            value = context[param_name]
            setattr(view, param_name, value)
            return original_function(*args, **kwargs)
        return wrapped
    return wrapper
