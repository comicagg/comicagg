import os
import random
from hashlib import md5
from urllib.error import HTTPError
from urllib.parse import urljoin
from urllib.request import Request, urlopen

from comicagg.utils import render
from django.conf import settings
from django.contrib import messages
from django.contrib.auth.decorators import login_required
from django.contrib.auth.models import User
from django.core.mail import mail_managers
from django.http import Http404, HttpRequest, HttpResponse, HttpResponseRedirect
from django.shortcuts import get_object_or_404, redirect
from django.template.defaultfilters import slugify
from django.utils.translation import gettext as _
from django.views.decorators.cache import cache_page

from .forms import RequestForm
from .models import Comic, ComicHistory
from .models import Request as ComicRequest
from .models import Subscription
from .utils import ComicsService

# ##########################
# #   Reading page views   #
# ##########################


@login_required
def read_view(request: HttpRequest):
    # comic_list and unread_list are lists of tuples of (comic, QuerySet of UnreadComic)
    comic_list = [
        (comic, comic.unread_comics_for(request.user))
        for comic in ComicsService(request.user).subscribed_comics()
    ]
    unread_list = [
        (comic, comic.unread_comics_for(request.user))
        for comic in ComicsService(request.user).unread_comics()
    ]
    random = _random_comic(request.user)
    context = {"comic_list": comic_list, "unread_list": unread_list, "random": random}
    return render(request, "comics/read.html", context, "read")


def _random_comic(user: User, xhtml=False, request=None):
    subscribed_ids = [s.comic.id for s in Subscription.objects.filter(user=user)]
    if not_in_list := Comic.objects.exclude(active=False).exclude(
        id__in=subscribed_ids
    ):
        try:
            comic = not_in_list[random.randint(0, len(not_in_list) - 1)]
            history = comic.comichistory_set.all()
            history = history[random.randint(0, len(history) - 1)]
        except Exception:
            history = None
        if xhtml and history:
            return render(request, "comics/read_random.html", {"random_comic": history})
        return history
    return None


@login_required
def random_comic_view(request: HttpRequest):
    if resp := _random_comic(request.user, xhtml=True, request=request):
        return resp
    else:
        raise Http404


#######################
# Organize page views #
#######################


@login_required
def organize(request: HttpRequest, add=False):
    # all of the comics
    all_comics = list(Comic.objects.exclude(active=False))
    all_comics.sort(key=_slugify_comic)

    # build the available list depending on selected comics
    user_subs = request.user.subscription_set.all().exclude(
        comic__active=False, comic__ended=False
    )
    user_comics = []
    for sub in user_subs:
        lst = request.user.unreadcomic_set.filter(comic=sub.comic)
        if not lst and sub.comic.ended:
            continue
        user_comics.append(sub.comic)
    context = {"user_comics": user_comics}
    if add:
        context["new_comics"] = ComicsService(request.user).new_comics()
        context["all_comics"] = all_comics
        # quitar aviso de nuevos comics
        hide_new_comics(request)
        template = "comics/organize_add.html"
    else:
        template = "comics/organize_organize.html"
    return render(request, template, context)


def _slugify_comic(comic: Comic) -> str:
    return slugify(str(comic))


@login_required
def hide_new_comics(request: HttpRequest):
    """
    Hides the new comics alert
    """
    user_profile = request.user.user_profile
    user_profile.new_comics = False
    user_profile.save()
    return HttpResponse("0")


# ############################
# #   Request page related   #
# ############################


@login_required
def request_index(request: HttpRequest):
    if request.POST:
        form = RequestForm(request.POST)
        if form.is_valid():
            url = form.cleaned_data["url"]
            comment = form.cleaned_data["comment"]
            req = ComicRequest(user=request.user, url=url, comment=comment)
            req.save()
            message = "%s\n%s\n%s" % (req.user, req.url, req.comment)
            try:
                mail_managers("Nuevo request", message)
            except Exception:
                # TODO log the error
                pass
            messages.info(request, _("Your request has been saved. Thanks!"))
            return redirect("comics:requests")
    else:
        form = RequestForm()
    context = {
        "form": form,
        "count": ComicRequest.objects.all().count(),
        "accepted": request.user.request_set.filter(done__exact=1).filter(
            rejected__exact=0
        ),
        "rejected": request.user.request_set.filter(rejected__exact=1),
        "pending": request.user.request_set.filter(done__exact=0).filter(
            rejected__exact=0
        ),
    }
    return render(request, "comics/request_index.html", context)


# ##############
# #   Others   #
# ##############


@cache_page(24 * 3600)
def stats(request: HttpRequest):
    """
    Genera una página de estadísticas para cada comic ordenada según la puntuación de cada comic
    """
    comics = sorted(Comic.objects.all())
    return render(request, "stats.html", {"comics": comics})


STRIPS_FOLDER = ""


def last_image_url(request: HttpRequest, comic_id):
    """
    Redirecciona a la url de la ultima imagen de  un comic
    """
    comic = get_object_or_404(Comic, pk=comic_id)
    url = comic.last_image
    referrer = comic.referrer or ""
    return _image_url(url, referrer)


def history_image_url(request: HttpRequest, history_id):
    """
    Redirecciona a la url de un objeto comic_history
    """
    comic_history = get_object_or_404(ComicHistory, pk=history_id)
    url = comic_history.url
    referrer = comic_history.comic.referrer or ""
    return _image_url(url, referrer)


def _image_url(url: str, referrer: str):
    url_hash = md5(url.encode()).hexdigest()
    link_path = os.path.join(settings.MEDIA_ROOT, STRIPS_FOLDER, url_hash)
    if not os.path.exists(link_path):
        if file_path := _download_image(url, referrer, link_path):
            # the download went ok, we get the filename back
            os.symlink(file_path, link_path)
        else:
            # the download returned None? return an error
            raise Http404
    url_path = f"{STRIPS_FOLDER}/{url_hash}" if STRIPS_FOLDER else url_hash
    return HttpResponseRedirect(urljoin(settings.MEDIA_URL, url_path))


def _download_image(url: str, referrer: str, file_path):
    headers = {"referer": referrer, "user-agent": settings.USER_AGENT}
    try:
        request = Request(url, None, headers)
        response = urlopen(request)
        content_type = response.info()["Content-Type"]
        if content_type.startswith("image/"):
            # we got an image, that's good
            extension = content_type.replace("image/", "")
            file_path += f".{extension}"
            with open(file_path, "w+b") as file:
                file.writelines(response.readlines())
        else:
            # no image mime? not cool
            file_path = None
    except HTTPError:
        file_path = None
    return file_path
