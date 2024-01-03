import logging
import os
import random
from hashlib import md5
from urllib.error import HTTPError
from urllib.parse import urljoin
from urllib.request import Request, urlopen

from django.conf import settings
from django.contrib import messages
from django.contrib.auth.decorators import login_required
from django.core.mail import mail_managers
from django.http import Http404, HttpRequest, HttpResponseRedirect
from django.shortcuts import get_object_or_404, redirect, render
from django.template.defaultfilters import slugify
from django.utils.translation import gettext as _
from django.views.decorators.cache import cache_page

from comicagg.typings import AuthenticatedHttpRequest

from .forms import RequestForm
from .models import Comic
from .models import Request as ComicRequest
from .models import Strip

logger = logging.getLogger(__name__)

# ##########################
# #   Reading page views   #
# ##########################


def _find_random_comic(request: AuthenticatedHttpRequest, xhtml=False):
    subscribed_ids = [comic.id for comic in request.user.comics_subscribed()]
    if not_in_list := Comic.objects.available().exclude(id__in=subscribed_ids):
        try:
            comic = not_in_list[random.randint(0, len(not_in_list) - 1)]
            strip = comic.strip_set.all()
            strip = strip[random.randint(0, len(strip) - 1)]
        except Exception:
            strip = None
        if xhtml and strip:
            return render(request, "comics/read_random.html", {"random_comic": strip})
        return strip
    return None


@login_required
def read_view(request: AuthenticatedHttpRequest):
    comics = request.user.comics_subscribed()
    unread_strips_db = (
        request.user.unread_strips()
        .select_related("strip")
        .select_related("strip__comic")
    )
    unread_strips = {comic.id: [] for comic in comics}
    unread_list: set[int] = set()
    for strip in unread_strips_db:
        unread_strips[strip.comic_id].append(strip)
        unread_list.add(strip.comic_id)
    comic_list = [(comic, unread_strips[comic.id]) for comic in comics]
    random = _find_random_comic(request)
    context = {"comic_list": comic_list, "unread_list": unread_list, "random": random}
    return render(request, "comics/read.html", context)


@login_required
def random_comic_view(request: AuthenticatedHttpRequest):
    if resp := _find_random_comic(request, xhtml=True):
        return resp
    else:
        raise Http404


#######################
# Organize page views #
#######################


@login_required
def add_comics(request: AuthenticatedHttpRequest):
    # all of the comics
    all_comics = list(Comic.objects.available().prefetch_related("subscription_set"))
    all_comics.sort(key=_slugify_comic)

    # build the available list depending on selected comics
    user_comics = request.user.comics_subscribed()
    new_comics = request.user.comics_new()
    context = {
        "all_comics": all_comics,
        "user_comics": user_comics,
        "new_comics": new_comics,
    }
    return render(request, "comics/add.html", context)


@login_required
def organize(request: AuthenticatedHttpRequest):
    """Comics shown in the organize page are those that are active or ended with unread strips."""
    comics_with_unread_strips = request.user.comics_unread()
    subscriptions = request.user.subscriptions()
    visible_comics = []
    for subscription in subscriptions:
        # Remove ended comics without unread strips
        has_unread_strips = subscription.comic in comics_with_unread_strips
        if not has_unread_strips and subscription.comic.ended:
            continue
        visible_comics.append(subscription.comic)
    context = {"user_comics": visible_comics}
    return render(request, "comics/organize.html", context)


def _slugify_comic(comic: Comic) -> str:
    return slugify(str(comic))


# ############################
# #   Request page related   #
# ############################


@login_required
def request_index(request: AuthenticatedHttpRequest):
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
                logger.error("Failure sending mail to managers")
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
    Redirect to the URL of a comic's last image.
    """
    comic = get_object_or_404(Comic, pk=comic_id)
    url = comic.last_image
    referrer = comic.referrer or ""
    return _image_url(url, referrer)


def strip_image_url(request: HttpRequest, strip_id):
    """
    Redirect to the URL of a Strip object.
    """
    strip = get_object_or_404(Strip, pk=strip_id)
    url = strip.url
    referrer = strip.comic.referrer or ""
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
