# -*- coding: utf-8 -*-
from django.conf import settings
from django.db.models import Count
from django.http import HttpResponse, HttpResponseRedirect, HttpResponseNotFound, HttpResponseServerError
from django.template.loader import render_to_string
import os, re

def render(request, template, context, menu=None, xml=False, responseClass=HttpResponse, mime='text/html; charset="utf-8"'):
    context['settings'] = settings
    try:
        user = request.user
    except:
        user = None
    try:
        unr = user.unreadcomic_set.filter(comic__activo=True).filter(comic__ended=False).aggregate(Count('comic', distinct=True))
        context['unread_count'] = unr['comic__count']
        newc = user.newcomic_set.count()
        context['newcomic_count'] = newc
        newsc = user.newblog_set.count()
        context['newnews_count'] = newsc
    except:
        pass

    context['user'] = user
    context['menu'] = menu
    context['mediaurl'] = settings.MEDIA_URL

    resp_text = render_to_string(template, context)
    response = responseClass(resp_text, mimetype=mime)
    if xml:
        response = responseClass(resp_text, mimetype='text/xml; charset="utf-8"')
    #ie no reconoce el mime que hay que usar para xhtml 1.1 :(
    #response = HttpResponse(resp_text, mimetype="application/xhtml+xml")
    #response['Cache-Control'] = 'no-cache'
    response['Cache-Control'] = 'max-age=1'
    response['Expires'] = '-1'
    return response

def error404(request):
    return render(request, '404.html', {}, responseClass=HttpResponseNotFound)

def error500(request):
    return render(request, '500.html', {}, responseClass=HttpResponseServerError)

def robots_txt(request):
    return render(request, 'robots.txt', {}, mime='text/plain; charset="utf-8"')
