# -*- coding: utf-8 -*-
from comicagg.agregator.models import Comic, ComicHistory, NewComic, UnreadComic, Subscription
from django.conf import settings
from django.contrib.auth.decorators import login_required
from django.core.mail import mail_managers
from django.core.urlresolvers import reverse
from django.db.models import Count, Max
from django.http import HttpResponse, Http404, HttpResponseBadRequest
from django.shortcuts import get_object_or_404

"""
These are views for ajax requests.
If they need any parameters, they always have to be sent via POST.
Response status:
- Everything OK: 200 (of course). Response is JSON with several counters
- Bad parameters: 400
- Not found or no POST: 404
"""

def ok_response(request):
    comics = request.user.subscription_set.exclude(comic__activo=False, comic__ended=False).count()
    unread = request.user.unreadcomic_set.exclude(comic__activo=False, comic__ended=False).aggregate(Count('comic', distinct=True))['comic__count']
    new_comics = request.user.newcomic_set.exclude(comic__activo=False).count()
    news = request.user.newblog_set.count()
    response ='{"comics":%d, "new_comics":%d, "unreads":%d, "news":%d}' % (comics, new_comics, unread, news)
    return HttpResponse(response, mimetype="application/json")

@login_required
def add_comic(request):
    if not request.POST:
        raise Http404
    try:
        comic_id = int(request.POST['id'])
    except:
        return HttpResponseBadRequest("Check the parameters")
    comic = get_object_or_404(Comic, pk=comic_id)
    s = request.user.subscription_set.filter(comic=comic)
    if s:
        #the comic is already added, finish here
        return ok_response(request)
    #continue adding the comic
    #calculate position for the comic, it'll be the last
    max_position = request.user.subscription_set.aggregate(pos=Max('position'))['pos']
    if not max_position: #max_position can be None if there are no comics
        max_position = 0
    next_pos = max_position + 1
    request.user.subscription_set.create(comic=comic, position=next_pos)
    #add the last strip to the user's unread list
    history = ComicHistory.objects.filter(comic=comic)
    if history:
        UnreadComic.objects.create(user=request.user, comic=comic, history=history[0])
    return ok_response(request)

@login_required
def forget_new_comic(request):
    if not request.POST:
        raise Http404
    try:
        comic_id = int(request.POST['id'])
    except:
        return HttpResponseBadRequest("Check the parameters")
    comic = get_object_or_404(Comic, pk=comic_id)
    NewComic.objects.filter(user=request.user, comic=comic).delete()
    return ok_response(request)

@login_required
def mark_read(request):
    if not request.POST:
        raise Http404
    try:
        comic_id = request.POST['id']
        value = int(request.POST['value'])
    except:
        return HttpResponseBadRequest("Check the parameters")
    if value != 0:
        rate_comic(request)
    comic = get_object_or_404(Comic, pk=comic_id)
    UnreadComic.objects.filter(user=request.user, comic=comic).delete()
    return ok_response(request)

@login_required
def mark_all_read(request):
    UnreadComic.objects.filter(user=request.user).delete()
    return ok_response(request)

@login_required
def remove_comic(request):
    if not request.POST:
        raise Http404
    try:
        comic_id = int(request.POST['id'])
    except:
        return HttpResponseBadRequest("Check the parameters")
    comic = get_object_or_404(Comic, pk=comic_id)
    request.user.subscription_set.filter(comic=comic).delete()
    request.user.unreadcomic_set.filter(comic=comic).delete()
    return ok_response(request)

@login_required
def remove_comic_list(request):
    if not request.POST:
        raise Http404
    try:
        ids = request.POST['ids'].split(",")
    except:
        return HttpResponseBadRequest("Check the parameters")
    request.user.subscription_set.filter(comic__id__in=ids).delete()
    request.user.unreadcomic_set.filter(comic__id__in=ids).delete()
    return ok_response(request)

@login_required
def report_comic(request):
    if not request.POST:
        raise Http404
    try:
        comic_id = int(request.POST['id'])
        chids = request.POST.getlist('chids[]')
    except:
        return HttpResponseBadRequest("Check the parameters")
    comic = get_object_or_404(Comic, pk=comic_id)
    message = 'El usuario %s dice que hay una imagen rota en el comic %s en alguna de las siguientes actualizaciones:\n' % (request.user, comic.name)
    url = reverse('aggregator:admin:reported', kwargs={'chids':'-'.join(chids)})
    message += '%s%s' % (settings.DOMAIN, url)
    mail_managers('Imagen rota', message)
    return ok_response(request)

@login_required
def save_selection(request):
    if not request.POST:
        raise Http404
    #get selection
    try:
        selection = request.POST['selected'].split(',')
    except:
        return HttpResponseBadRequest("Check the parameters")

    #remove posible duplicates, can't use a set, cos its order is undefined
    #this will keep first appearances and delete later ones
    selection_clean = list()
    for item in selection:
        if len(item) == 0: continue
        #try to get an index, if it fails, item is not in the list so we append the item to the list
        try:
            selection_clean.index(int(item))
        except:
            selection_clean.append(int(item))

    #if there's nothing selected, we're finished
    if len(selection_clean) == 0:
        return ok_response(request)

    #subsc_dict is a dictionary, key=comic.id value=subscription.id
    subsc_dict = {s.comic.id:s.id for s in request.user.subscription_set.all()}
    #subscriptions is the list of comic ids already added
    subscriptions = subsc_dict.keys()

    #guess what comics have been removed
    removed = list()
    for s in subscriptions:
        if s not in selection_clean:
            removed.append(s)
    #unsubscribe the removed comics 
    request.user.subscription_set.filter(comic__id__in=removed).delete()
    request.user.unreadcomic_set.filter(comic__id__in=removed).delete()

    #now change the position of the selected comics
    #make the list of subscriptions we want to change
    sids = list()
    for cid in selection_clean:
        #get the subscription id
        sids.append(subsc_dict[cid])
    #ss is a dictionary key:id value=subscription
    ss = Subscription.objects.in_bulk(sids)
    #now change the position
    pos = 0
    for sid in sids:
        if ss[sid].position == pos: continue
        ss[sid].position = pos
        ss[sid].save()
        pos += 1
    return ok_response(request)

@login_required
def rate_comic(request):
    if not request.POST:
        raise Http404
    try:
        id = int(request.POST['id'])
        value = int(request.POST['value'])
    except:
        return HttpResponseBadRequest("Check the parameters")
    comic = get_object_or_404(Comic, pk=id)
    if value == -1:
        value = 0
    elif value == 1:
        value = 1
    else:
        return HttpResponseBadRequest("Check the parameters")
    comic.rating += value
    comic.votes += 1
    comic.save()
    return ok_response(request)
