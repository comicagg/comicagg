# -*- coding: utf-8 -*-
from comicagg import render
from comicagg.comics.models import Comic, ComicHistory, NewComic, Request, RequestForm, Subscription
from datetime import datetime
from django.conf import settings
from django.contrib.auth.decorators import login_required
from django.contrib import messages
from django.core.mail import mail_managers
from django.http import HttpResponse, HttpResponseRedirect, Http404
from django.shortcuts import get_object_or_404, redirect
from django.template import RequestContext
from django.template.defaultfilters import slugify
from django.utils.translation import ugettext as _
from django.views.decorators.cache import cache_page
from hashlib import md5
from urllib.request import urlopen, Request
from urllib.error import HTTPError
import os, random

###################
# Read page related

@login_required
def read_view(request):
    if request.user and request.user.is_authenticated():
        profile = request.user.get_profile()
        comic_list = [(comic, comic.unread_comics_for(request.user)) for comic in profile.all_comics()]
        unread_list = [(comic, comic.unread_comics_for(request.user)) for comic in profile.unread_comics()]
        random = random_comic(request.user)
        context = RequestContext(request, {
            'comic_list': comic_list,
            'unread_list': unread_list,
            'random': random
        })
        return render(request, 'comics/read.html', context, 'read')

def random_comic(user, xhtml=False, request=None):
    not_in_list = Comic.objects.exclude(activo=False).exclude(id__in=[s.comic.id for s in Subscription.objects.filter(user=user)])
    if not_in_list:
        try:
            comic = not_in_list[random.randint(0, len(not_in_list) - 1)]
            history = comic.comichistory_set.all()
            history = history[random.randint(0, len(history) - 1)]
        except:
            history = None
        if xhtml and history:
            return render(request, 'comics/read_random.html', {'random_comic':history})
        return history
    return None

@login_required
def random_comic_view(request):
    resp = random_comic(request.user, xhtml=True, request=request)
    if resp:
        return resp
    else:
        raise Http404

#######################
# Organize page related

@login_required
def organize(request, add=False):
    context = {}
    #all of the comics
    all_comics = list(Comic.objects.exclude(activo=False))
    all_comics.sort(comic_sort_name)
    #build available list depending on selected comics
    user_subs = request.user.subscription_set.all().exclude(comic__activo=False, comic__ended=False)
    user_comics = list()
    for sub in user_subs:
        lst = request.user.unreadcomic_set.filter(comic=sub.comic)
        if not lst and sub.comic.ended: continue
        user_comics.append(sub.comic)
    context['user_comics'] = user_comics
    
    if add:
        context['new_comics'] = NewComic.objects.filter(user=request.user).exclude(comic__activo=False)
        context['all_comics'] = all_comics
        #quitar aviso de nuevos comics
        hide_new_comics(request)
        template = 'comics/organize_add.html'
    else:
        template = 'comics/organize_organize.html'
    return render(request, template, context)

#ascendente
def comic_sort_name(x, y):
    a = slugify(x.name)
    b = slugify(y.name)
    if a < b:
        return -1
    elif a == b:
        return 0
    return 1

@login_required
def hide_new_comics(request):
    """
    Oculta el aviso de nuevos comics
    """
    up = request.user.get_profile()
    up.new_comics = False;
    up.save()
    return HttpResponse("0")

######################
# Request page related

@login_required
def request_index(request):
    if request.POST:
        form = RequestForm(request.POST)
        if form.is_valid():
            url = form.cleaned_data['url']
            comment = form.cleaned_data['comment']
            req = Request(user=request.user, url=url, comment=comment)
            req.save()
            message = '%s\n%s\n%s' %(req.user, req.url, req.comment)
            mail_managers('Nuevo request', message)
            messages.info(request, _("Your request has been saved. Thanks!"))
            return redirect('comics:requests')
    else:
        form = RequestForm()
    context = {}
    context['form'] = form
    context['count'] = Request.objects.all().count()
    context['accepted'] = request.user.request_set.filter(done__exact=1).filter(rejected__exact=0)
    context['rejected'] = request.user.request_set.filter(rejected__exact=1)
    context['pending'] = request.user.request_set.filter(done__exact=0).filter(rejected__exact=0)
    return render(request, 'comics/request_index.html', context)

########
# Others

@cache_page(24 * 3600)
def stats(request):
    """
    Genera una página de estadísticas para cada comic ordenada según la puntuación de cada comic
    """
    comics = list(Comic.objects.all())
    comics.sort(sort_rate)
    return render(request, 'stats.html', {'comics':comics})

def sort_rate(a, b):
    """
    Ordenar únicamente por la puntuación de los comics
    """
    c = b.get_rating() - a.get_rating()
    if c > 0: return 1
    elif c < 0: return -1
    else: return 0

def last_image_url(request, cid):
    """
    Redirecciona a la url de la ultima imagen de  un comic
    """
    comic = get_object_or_404(Comic, pk=cid)
    url = comic.last_image
    ref = comic.referer
    return image_url(url, ref)

def history_image_url(request, hid):
    """
    Redirecciona a la url de un objeto comic_history
    """
    ch = get_object_or_404(ComicHistory, pk=hid)
    url = ch.url
    ref = ch.comic.referer
    return image_url(url, ref)

def image_url(url, ref):
    hash = md5(url).hexdigest()
    ldst = os.path.join(settings.MEDIA_ROOT, 'strips', hash)
    dst = ldst
    if not os.path.exists(ldst):
        #the link doesnt exist, download the image
        dst = download_image(url, ref, dst)
        if dst:
            #the download went ok, we get the filename back
            os.symlink(dst, ldst)
        else:
            #the download returned None? return an error
            raise Http404
    return HttpResponseRedirect(settings.MEDIA_URL + 'strips/' + hash)

def download_image(url, ref, dest):
    headers = {
        'referer':ref,
        'user-agent':settings.USER_AGENT
    }
    try:
        r = Request(url, None, headers)
        o = urlopen(r)
        ct = o.info()['Content-Type']
        if ct.startswith("image/"):
            #we got an image, thats good
            ext = ct.replace("image/", "")
            dest += "." + ext
            f = open(dest, 'w+b')
            f.writelines(o.readlines())
            f.close()
        else:
            #no image mime? not cool
            dest = None
    except HTTPError:
        dest = None
    return dest

