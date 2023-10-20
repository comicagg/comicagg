from django.contrib.auth.decorators import login_required
from django.contrib.auth.models import User
from django.http import HttpResponseRedirect
from django.shortcuts import get_object_or_404
from django.urls import reverse

from comicagg.utils import render
from comicagg.comics.utils import UserOperations


def index(request):
    return render(request, "ws/index.html", {})


def unread_user(request, user):
    if not user:
        return HttpResponseRedirect(reverse("index"))
    user = get_object_or_404(User, username=user)
    context = {}

    unreads = UserOperations(user).unread_comics_count()

    context["unread_list"] = unreads
    context["count"] = len(unreads)
    context["username"] = user
    return render(request, "ws/unread_user.html", context, xml=True)


@login_required
def user_subscriptions(request, simple=False):
    context = {}
    context["subscriptions"] = request.user.subscription_set.order_by("position")
    if simple:
        template = "ws/user_subscriptions_simple.html"
    else:
        template = "ws/user_subscriptions.html"
    return render(request, template, context, xml=True)
