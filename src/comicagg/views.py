from django.shortcuts import redirect
from comicagg.utils import render
from django.http import HttpRequest


def index(request: HttpRequest):
    if request.user.is_authenticated:
        return redirect("comics:read")
    else:
        return redirect("accounts:login")


def robots_txt(request: HttpRequest):
    return render(request, "robots.txt", {}, mime='text/plain; charset="utf-8"')
