import os
import random
from hashlib import md5
from urllib.error import HTTPError
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
    random = random_comic(request.user)
    context = {"comic_list": comic_list, "unread_list": unread_list, "random": random}
    return render(request, "comics/read.html", context, "read")


def random_comic(user: User, xhtml=False, request=None):
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
def random_comic_view(request):
    if resp := random_comic(request.user, xhtml=True, request=request):
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
    all_comics.sort(key=slugify_comic)

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


def slugify_comic(comic: Comic) -> str:
    return slugify(str(comic))


def comic_sort_name(x, y):
    """
    Sort the comics by their name, ascending
    """
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
    Hides the new comics alert
    """
    up = request.user.user_profile
    up.new_comics = False
    up.save()
    return HttpResponse("0")


# ############################
# #   Request page related   #
# ############################


@login_required
def request_index(request):
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
def stats(request):
    """
    Genera una página de estadísticas para cada comic ordenada según la puntuación de cada comic
    """
    comics = sorted(Comic.objects.all())
    return render(request, "stats.html", {"comics": comics})


def last_image_url(request: HttpRequest, comic_id):
    """
    Redirecciona a la url de la ultima imagen de  un comic
    """
    comic = get_object_or_404(Comic, pk=comic_id)
    url = comic.last_image
    ref = comic.referer or ""
    return image_url(url, ref)


def history_image_url(request: HttpRequest, history_id):
    """
    Redirecciona a la url de un objeto comic_history
    """
    ch = get_object_or_404(ComicHistory, pk=history_id)
    url = ch.url
    ref = ch.comic.referer or ""
    return image_url(url, ref)


def image_url(url: str, ref: str):
    url_hash = md5(url.encode()).hexdigest()
    ldst = os.path.join(settings.MEDIA_ROOT, "strips", url_hash)
    dst = ldst
    if not os.path.exists(ldst):
        if dst := download_image(url, ref, dst):
            # the download went ok, we get the filename back
            os.symlink(dst, ldst)
        else:
            # the download returned None? return an error
            raise Http404
    return HttpResponseRedirect(f"{settings.MEDIA_URL}strips/{url_hash}")


def download_image(url: str, ref: str, dest):
    headers = {"referer": ref, "user-agent": settings.USER_AGENT}
    try:
        r = Request(url, None, headers)
        o = urlopen(r)
        ct = o.info()["Content-Type"]
        if ct.startswith("image/"):
            # we got an image, thats good
            ext = ct.replace("image/", "")
            dest += f".{ext}"
            with open(dest, "w+b") as f:
                f.writelines(o.readlines())
        else:
            # no image mime? not cool
            dest = None
    except HTTPError:
        dest = None
    return dest
