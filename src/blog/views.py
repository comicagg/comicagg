from django.contrib.auth.decorators import login_required
from django.contrib.auth.models import User
from django.http import HttpRequest
from django.shortcuts import render

from comicagg.typings import AuthenticatedHttpRequest
from comics.ajax.views import ok_response

from .models import NewBlog, Post


def index(request: HttpRequest, all=False):
    """It will render either the last 10 news items or all of them, depending on
    the keyword all."""
    posts = Post.objects.all().select_related("user")
    context = {
        "archive": all,
        "posts": posts if all else posts[:10],
        # These are the new news items the logged in user has
        "new_posts": (NewBlog.objects.filter(user=request.user) if request.user.is_authenticated else False),
    }
    return render(request, "blog/index.html", context)


@login_required
def forget_new_blogs(request: AuthenticatedHttpRequest):
    """Will mark as read the new news items of the logged in user."""
    if request.user:
        request.user.posts_forget_all()
    return ok_response(request)
