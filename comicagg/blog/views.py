# -*- coding: utf-8 -*-
from comicagg import *
from comicagg.blog.models import *
from django.http import HttpResponse, HttpResponseRedirect
from django.core.urlresolvers import reverse
from django.contrib.auth.decorators import login_required
from datetime import datetime

def index(request, archive=False):
    """It will render either the last 10 news items or all of them, depending on
    the keyword archive.
    """
    try:
        user = request.user
    except:
        user = None
    context = { 'archive':archive }
    posts = Post.objects.all()
    if not archive:
        posts = posts[:10]
    context['posts'] = posts
    if user:
        #These are the new news items the logged in user has
        context['new_posts'] = NewBlog.objects.filter(user=user)
    return render(request, 'blog/index.html', context)

@login_required
def forget_new_blogs(request):
    """Will mark as read the new news items of the logged in user.
    """
    try:
        user = request.user
    except:
        user = None
    if user:
        NewBlog.objects.filter(user=user).delete()
    return HttpResponse('0')

def is_new_for(post, user):
    """Returns the NewBlog object for a user and a news item.
    """
    return NewBlog.objects.filter(user=user, post=post)
