from comicagg.blog.models import NewBlog, Post
from comicagg.comics.ajax.views import ok_response
from django.contrib.auth.decorators import login_required
from django.contrib.auth.models import User
from django.http import HttpRequest
from django.shortcuts import render


def index(request: HttpRequest, all=False):
    """It will render either the last 10 news items or all of them, depending on
    the keyword all.
    """
    posts = Post.objects.all()
    context = {
        "archive": all,
        "posts": posts if all else posts[:10],
        # These are the new news items the logged in user has
        "new_posts": (
            NewBlog.objects.filter(user=request.user)
            if request.user.is_authenticated
            else False
        ),
    }
    return render(request, "blog/index.html", context)


@login_required
def forget_new_blogs(request: HttpRequest):
    """Will mark as read the new news items of the logged in user."""
    if request.user:
        NewBlog.objects.filter(user=request.user).delete()
    return ok_response(request)


def is_new_for(post: Post, user: User):
    """Returns the NewBlog object for a user and a news item."""
    return NewBlog.objects.filter(user=user, post=post)
