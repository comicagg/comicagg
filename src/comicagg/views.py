from django.http import HttpRequest
from django.shortcuts import redirect


def welcome(request: HttpRequest):
    if request.user.is_authenticated:
        return redirect("comics:read")
    else:
        return redirect("accounts:login")
