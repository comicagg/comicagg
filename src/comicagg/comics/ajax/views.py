"""These are views for ajax requests.

If they need any parameters, they always have to be sent via POST.
Response status:
- Everything OK: 200 (of course). Response is JSON with several counters
- Bad parameters: 400
- Not found or no POST: 404
"""

from typing import List
from comicagg.comics.models import (
    Comic,
    ComicHistory,
    NewComic,
    Subscription,
    UnreadComic,
)
from comicagg.comics.utils import ComicsService
from django.conf import settings
from django.contrib.auth.decorators import login_required
from django.core.mail import mail_managers
from django.db.models import Count, Max
from django.http import (
    Http404,
    HttpRequest,
    HttpResponse,
    HttpResponseBadRequest,
    JsonResponse,
)
from django.shortcuts import get_object_or_404
from django.urls import reverse


def ok_response(request: HttpRequest):
    comic_count = request.user.subscription_set.exclude(
        comic__active=False, comic__ended=False
    ).count()
    unread_count = request.user.unreadcomic_set.exclude(
        comic__active=False, comic__ended=False
    ).aggregate(Count("comic", distinct=True))["comic__count"]
    new_comics_count = ComicsService(request.user).new_comics().count()
    news_count = request.user.newblog_set.count()
    response_data = {
        "comics": comic_count,
        "new_comics": new_comics_count,
        "unreads": unread_count,
        "news": news_count,
    }
    # TODO: Use JsonResponse?
    return JsonResponse(response_data)


@login_required
def add_comic(request: HttpRequest):
    try:
        comic_id = int(request.POST["id"])
    except Exception:
        return HttpResponseBadRequest("Check the parameters")
    comic = get_object_or_404(Comic, pk=comic_id)
    if request.user.subscription_set.filter(comic=comic):
        # the comic is already added, finish here
        return ok_response(request)
    # continue adding the comic
    # calculate position for the comic, it'll be the last
    max_position = (
        request.user.subscription_set.aggregate(pos=Max("position"))["pos"] or 0
    )
    next_pos = max_position + 1
    request.user.subscription_set.create(comic=comic, position=next_pos)
    # add the last strip to the user's unread list
    if history := ComicHistory.objects.filter(comic=comic):
        UnreadComic.objects.create(user=request.user, comic=comic, history=history[0])
    return ok_response(request)


@login_required
def forget_new_comic(request: HttpRequest):
    try:
        comic_id = int(request.POST["id"])
    except Exception:
        return HttpResponseBadRequest("Check the parameters")
    comic = get_object_or_404(Comic, pk=comic_id)
    NewComic.objects.filter(user=request.user, comic=comic).delete()
    return ok_response(request)


@login_required
def mark_read(request: HttpRequest):
    try:
        comic_id = request.POST["id"]
        value = int(request.POST["value"])
    except Exception:
        return HttpResponseBadRequest("Check the parameters")
    if value != 0:
        rate_comic(request)
    comic = get_object_or_404(Comic, pk=comic_id)
    UnreadComic.objects.filter(user=request.user, comic=comic).delete()
    return ok_response(request)


@login_required
def mark_all_read(request: HttpRequest):
    UnreadComic.objects.filter(user=request.user).delete()
    return ok_response(request)


@login_required
def remove_comic(request: HttpRequest):
    try:
        comic_id = int(request.POST["id"])
    except Exception:
        return HttpResponseBadRequest("Check the parameters")
    comic = get_object_or_404(Comic, pk=comic_id)
    request.user.subscription_set.filter(comic=comic).delete()
    request.user.unreadcomic_set.filter(comic=comic).delete()
    return ok_response(request)


@login_required
def remove_comic_list(request: HttpRequest):
    try:
        ids = request.POST["ids"].split(",")
    except Exception:
        return HttpResponseBadRequest("Check the parameters")
    request.user.subscription_set.filter(comic__id__in=ids).delete()
    request.user.unreadcomic_set.filter(comic__id__in=ids).delete()
    return ok_response(request)


@login_required
def report_comic(request: HttpRequest):
    try:
        comic_id = int(request.POST["id"])
        chids = request.POST.getlist("chids[]")
    except Exception:
        return HttpResponseBadRequest("Check the parameters")
    comic = get_object_or_404(Comic, pk=comic_id)
    message = (
        "El usuario %s dice que hay una imagen rota en el comic %s en alguna de las siguientes actualizaciones:\n"
        % (request.user, comic.name)
    )
    url = reverse("comics:admin:reported", kwargs={"chids": "-".join(chids)})
    message += f"{settings.SITE_DOMAIN}{url}"
    try:
        mail_managers("Imagen rota: " + comic.name, message)
    except Exception:
        # TODO log this error
        pass
    return ok_response(request)


@login_required
def save_selection(request: HttpRequest):
    try:
        selected_raw = request.POST["selected"]
        if not isinstance(selected_raw, str):
            return HttpResponseBadRequest("Check the parameters")
        selected_comics = selected_raw.split(",")
    except Exception:
        return HttpResponseBadRequest("Check the parameters")

    # If there's nothing selected, we're finished
    if not selected_comics:
        return ok_response(request)

    # Remove posible duplicates
    # This will keep the first appearance of an item and remove later ones
    selection_clean: list[int] = []
    for selected_comic_id in selected_comics:
        if not selected_comic_id:
            continue
        # try to get an index, if it fails, item is not in the list so we append the item to the list
        try:
            selection_clean.index(int(selected_comic_id))
        except Exception:
            selection_clean.append(int(selected_comic_id))

    # subsc_dict is a dictionary, key=comic.id value=subscription.id
    subsc_dict = dict(
        [
            (subscription.comic.id, subscription.id)
            for subscription in request.user.subscription_set.all()
        ]
    )
    # subscriptions is the list of comic ids already added
    subscriptions = subsc_dict.keys()

    # Unsubscribe the removed comics
    if removed := [
        subscription
        for subscription in subscriptions
        if subscription not in selection_clean
    ]:
        request.user.subscription_set.filter(comic__id__in=removed).delete()
        request.user.unreadcomic_set.filter(comic__id__in=removed).delete()

    # Change the position of the selected comics
    # Make the list of subscriptions we want to change
    sids = [subsc_dict[cid] for cid in selection_clean]
    # for cid in selection_clean:
    # get the subscription id
    # sids.append(subsc_dict[cid])
    # ss is a dictionary key:id value=subscription
    ss = Subscription.objects.in_bulk(sids)
    # now change the position
    position = 0
    for sid in sids:
        position += 1
        if ss[sid].position == position:
            continue
        ss[sid].position = position
        ss[sid].save()
    return ok_response(request)


@login_required
def rate_comic(request: HttpRequest):
    try:
        comic_id = int(request.POST["id"])
        value = int(request.POST["value"])
    except Exception:
        return HttpResponseBadRequest("Check the parameters")
    comic = get_object_or_404(Comic, pk=comic_id)
    if value == -1:
        value = 0
    elif value == 1:
        value = 1
    else:
        return HttpResponseBadRequest("Check the parameters")
    comic.positive_votes += value
    comic.total_votes += 1
    comic.save()
    return ok_response(request)
