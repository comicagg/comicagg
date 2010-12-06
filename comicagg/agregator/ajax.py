# -*- coding: utf-8 -*-
from comicagg.agregator.models import Comic, ComicHistory, NewComic, UnreadComic, Subscription
from django.conf import settings
from django.contrib.auth.decorators import login_required
from django.core.mail import mail_admins
from django.core.urlresolvers import reverse
from django.db import IntegrityError
from django.db.models import Max
from django.http import HttpResponse, Http404, HttpResponseForbidden
from django.shortcuts import get_object_or_404, redirect
from django.utils.translation import ugettext as _

@login_required
def add_comic(request):
    if request.POST:
        try:
            comic_id = int(request.POST['id'])
        except:
            comic_id = -1
        comic = get_object_or_404(Comic, pk=comic_id)
        try:
            request.user.subscription_set.get(comic=comic)
        except:
            next = request.user.subscription_set.aggregate(pos=Max('position'))['pos'] + 1
            request.user.subscription_set.create(comic=comic, position=next)
        try:
            history = ComicHistory.objects.filter(comic=comic)[0]
            u = UnreadComic(user=request.user, comic=comic, history=history)
            u.save()
        except:
            pass
        return HttpResponse('0')
    raise Http404

@login_required
def remove_comic(request):
    if request.POST:
        try:
            comic_id = int(request.POST['id'])
        except:
            comic_id = -1
        comic = get_object_or_404(Comic, pk=comic_id)
        s = request.user.subscription_set.get(comic=comic)
        s.delete()
        return HttpResponse('0')
    raise Http404

@login_required
def remove_comic_list(request):
    if request.POST:
        try:
            ids = request.POST['ids'].split(",")
        except:
            raise Http404
        s = request.user.subscription_set.filter(comic__id__in=ids)
        s.delete()
        return HttpResponse('0')
    raise Http404

@login_required
def report_comic(request):
    if not request.POST:
        raise Http404
    comic_id = int(request.POST['id'])
    chids = request.POST.getlist('chids[]')
    comic = get_object_or_404(Comic, pk=comic_id)
    message = 'El usuario %s dice que hay una imagen rota en el comic %s en alguna de las siguientes actualizaciones:\n' % (request.user, comic.name)
    url = reverse('aggregator:admin:reported', kwargs={'chids':'-'.join(chids)})
    message += '%s%s' % (settings.DOMAIN, url)
    mail_admins('Imagen rota', message)
    return HttpResponse("0")

@login_required
def forget_new_comic(request, comic_id=None):
    comic = get_object_or_404(Comic, pk=comic_id)
    NewComic.objects.filter(user=request.user, comic=comic).delete()
    count = request.user.newcomic_set.exclude(comic__activo=False).count()
    return HttpResponse(str(count))


@login_required
def save_selection(request):
    if not request.POST:
        return HttpResponseForbidden('')
    #get selection
    selection = request.POST['selected'].split(',')
    #remove duplicates
    selection_clean = list()
    for item in selection:
        if len(item)>0:
            #try to get an index, if it fails, item is not in the list so we append the item to the list
            try:
                selection_clean.index(int(item))
            except:
                selection_clean.append(int(item))
    #primero vemos qué comics nuevos se han elegido
    subscriptions = [s.comic.id for s in request.user.subscription_set.all()]
    nuevos = list()
    for s in selection_clean:
        if s not in subscriptions:
            nuevos.append(s)
    #comics que ahora no se seleccionan
    quitar = list()
    for s in subscriptions:
        if s not in selection_clean:
            quitar.append(s)
    #hay que quitar los unread de los comics que ya no leemos
    for cid in quitar:
        c = Comic.objects.get(pk=cid)
        request.user.unreadcomic_set.filter(comic=c).delete()
    #quitamos todas las suscripciones primero
    try:
        request.user.subscription_set.all().delete()
    except Exception:
        return HttpResponse('-1')
    #si la seleccion esta vacia salimos
    if len(selection_clean)==0:
        return HttpResponse(_('Saved =)'))
    pos = 0
    for comic_id in selection_clean:
        c = Comic.objects.get(pk=comic_id)
        s = Subscription(user=request.user, comic=c, position=pos)
        s.save()
        #si es un comic nuevo lo marcamos como unread
        if c.id in nuevos:
            try:
                history = ComicHistory.objects.filter(comic=c)[0]
                u = UnreadComic(user=request.user, comic=c, history=history)
                u.save()
            except:
                pass
        try:
            #borra el objeto newcomic si hubiera
            n = NewComic.objects.get(user=request.user, comic=c)
            n.delete()
        except IntegrityError:
            pass
        except Exception:
            pass
        pos += 1
    if NewComic.objects.filter(user=request.user).count() == 0:
        up = request.user.get_profile()
        up.new_comics = False
        up.save()
    return HttpResponse(_('Saved =)'))

@login_required
def mark_read(request):
    if not request.POST:
        return redirect('index')
    comic_id = request.POST['id']
    try:
        value = int(request.POST['value'])
    except:
        value = False
    if value:
        rate_comic(request)
    comic = get_object_or_404(Comic, pk=comic_id)
    un = UnreadComic.objects.filter(user=request.user, comic=comic)
    un.delete()
    return HttpResponse('0')

@login_required
def rate_comic(request):
    if request.POST:
        id = int(request.POST['id'])
        value = int(request.POST['value'])
        comic = get_object_or_404(Comic, pk=id)
        if value == -1:
            value = 0
        elif value == 1:
            value = 1
        else:
            raise Http404
        comic.rating += value
        comic.votes += 1
        comic.save()
        return HttpResponse("0")
    raise Http404

@login_required
def mark_all_read(request):
    un = UnreadComic.objects.filter(user=request.user)
    un.delete()
    return HttpResponse("OK")
