from comicagg import *
from comicagg.blog.models import *
from django.http import HttpResponse, HttpResponseRedirect
from django.core.urlresolvers import reverse
from django.contrib.auth.decorators import login_required
from django.shortcuts import get_object_or_404
from datetime import datetime

# Create your views here.
def index(request, archive=False):
  try:
    user = request.user
  except:
    user = None
  context = { 'archive':archive }
  posts = Post.objects.all()
  if not archive:
    posts = posts[:10]
  context['posts'] = posts
  #ocultar mensaje de nuevos posts
  hide_new_blogs(request)
  if user:
    context['new_posts'] = NewBlog.objects.filter(user=user)
  return render(request, 'blog/index.html', context)

def forget_new_blogs(request):
  try:
    user = request.user
  except:
    user = None
  if user and user.is_authenticated():
    NewBlog.objects.filter(user=user).delete()
  return HttpResponse('0')

def hide_new_blogs(request):
  try:
    user = request.user
  except:
    user = None
  if user and user.is_authenticated():
    try:
      up = user.get_profile()
    except:
      up = UserProfile(user=user, last_read_access=datetime.now())
    up.new_blogs = False
    up.save()
  return HttpResponse("0")

def is_new_for(post, user):
  return NewBlog.objects.filter(user=user, post=post)
