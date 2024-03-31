from django.http import HttpRequest
from django.shortcuts import redirect
from django.views.generic.base import TemplateView

robots = TemplateView.as_view(template_name="robots.txt", content_type="text/plain")


def welcome(request: HttpRequest):
    if request.user.is_authenticated:
        return redirect("comics:read")
    else:
        return redirect("accounts:login")
