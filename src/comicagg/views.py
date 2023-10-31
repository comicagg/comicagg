from comicagg.utils import render
from django.http import HttpResponseNotFound, HttpResponseServerError


def robots_txt(request):
    return render(request, "robots.txt", {}, mime='text/plain; charset="utf-8"')
