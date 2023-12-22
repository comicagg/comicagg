from django.contrib.auth.decorators import login_required
from django.db.models import Count
from django.http import HttpRequest, HttpResponseRedirect
from django.shortcuts import get_object_or_404, render
from django.urls import reverse

from comicagg.accounts.models import User
from comicagg.typings import AuthenticatedHttpRequest


def index(request: HttpRequest):
    return render(request, "ws/index.html", {})


def unread_user(request: HttpRequest, user: User):
    if not user:
        return HttpResponseRedirect(reverse("index"))
    user = get_object_or_404(User, username=user)

    unread_list = list(
        # This returns a query set like
        # <QuerySet [{'comic': 8, 'unread_strips': 4}, {'comic': 532, 'unread_strips': 29}]>
        user.unread_strips()
        .values("comic")
        .annotate(unread_strips=Count("comic"))
    )
    unread_counts = {comic["comic"]: comic["unread_strips"] for comic in unread_list}
    unreads = [(comic, unread_counts[comic.id]) for comic in user.comics_unread()]
    context = {"unread_list": unreads}
    return render(request, "ws/unread_user.html", context, content_type="text/xml")


@login_required
def user_subscriptions(request: AuthenticatedHttpRequest, simple=False):
    context = {"subscriptions": request.user.subscriptions()}
    if simple:
        template = "ws/user_subscriptions_simple.html"
    else:
        template = "ws/user_subscriptions.html"
    return render(request, template, context, content_type="text/xml")
