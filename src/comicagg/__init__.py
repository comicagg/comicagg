# -*- coding: utf-8 -*-
import os
import re

from django.conf import settings
from django.db.models import Count
from django.http import (
    HttpResponse,
    HttpResponseNotFound,
    HttpResponseRedirect,
    HttpResponseServerError,
)
from django.template import RequestContext
from django.template.loader import render_to_string


def render(
    request,
    template,
    context,
    menu=None,
    xml=False,
    responseClass=HttpResponse,
    mime='text/html; charset="utf-8"',
):
    context["settings"] = settings
    try:
        user = request.user
    except:
        user = None
    try:
        unr = user.unreadcomic_set.exclude(
            comic__active=False, comic__ended=False
        ).aggregate(Count("comic", distinct=True))
        newc = user.newcomic_set.exclude(comic__active=False).count()
        newsc = user.newblog_set.count()
        comics = request.user.subscription_set.exclude(
            comic__active=False, comic__ended=False
        ).count()
        context["unread_count"] = unr["comic__count"]
        context["newcomic_count"] = newc
        context["news_count"] = newsc
        context["comic_count"] = comics
    except:
        pass

    context["user"] = user
    context["menu"] = menu

    # context = RequestContext(request, context)

    resp_text = render_to_string(template, context)
    response = responseClass(resp_text, content_type=mime)
    if xml:
        response = responseClass(resp_text, content_type='text/xml; charset="utf-8"')
    # ie no reconoce el mime que hay que usar para xhtml 1.1 :(
    # response = HttpResponse(resp_text, content_type="application/xhtml+xml")
    # response['Cache-Control'] = 'no-cache'
    response["Cache-Control"] = "max-age=1"
    response["Expires"] = "-1"
    return response


def error404(request, exception):
    return render(request, "errors/404.html", {}, responseClass=HttpResponseNotFound)


def error500(request):
    return render(request, "errors/500.html", {}, responseClass=HttpResponseServerError)


def robots_txt(request):
    return render(request, "robots.txt", {}, mime='text/plain; charset="utf-8"')
