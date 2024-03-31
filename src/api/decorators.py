"""Decorators used in the API views.

In the decorator parameters we can find:
 args[0] is the View
 args[1] is the Request
 kwargs are the query string parameters
"""

from urllib.parse import parse_qs
from django.http import HttpResponseForbidden

from provider import constants


def write_required(original_function):
    """Check if the passed request has write permissions in the scope."""

    def wrapper(*args, **kwargs):
        view = args[0]
        request = args[1]
        if request.scope == getattr(constants, "WRITE"):
            return original_function(*args, **kwargs)
        else:
            return view.response_error(
                "This token does not have enough permissions to perform this action",
                "Forbidden",
                HttpResponseForbidden,
            )

    return wrapper


def body_not_empty(original_function):
    """Check that the request has a body."""

    def wrapper(*args, **kwargs):
        request = args[1]
        view = args[0]
        if len(request.body) == 0:
            return view.response_error("This method requires a body")
        return original_function(*args, **kwargs)

    return wrapper


# TODO: add a required parameter that makes the method throw if the parameter is not found
# TODO: separate in different methods to specify where the parameter must be found
def request_param(param_name):
    """Add the argument named param_name as an attribute in the view class.

    The parameter are looked for in this order:
    1. Keyword argument
    2. Query String
    3. PUT body
    4. If the class has a form_class, a form.
    If the parameter is not found the value is None."""

    def wrapper(original_function):
        def wrapped(*args, **kwargs):
            view = args[0]
            request = args[1]
            value = None
            # Search in kwargs
            if param_name in kwargs:
                value = kwargs[param_name]
            # Search in query string
            elif param_name in request.GET.keys():
                value = request.GET[param_name]
            # Search in PUT body
            elif request.method == "PUT":
                original = request.body.decode("utf-8")
                data = parse_qs(original, True)
                if param_name in data.keys():
                    value = data[param_name]
            # Search in form
            elif view.form_class is not None:
                context = view.get_context_data(**kwargs)
                form = context["form"]
                if form.is_valid():
                    value = form.cleaned_data[param_name]
            setattr(view, param_name, value)
            return original_function(*args, **kwargs)

        return wrapped

    return wrapper
