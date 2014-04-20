from comicagg import render
from django.core.urlresolvers import reverse
from django.contrib.auth.decorators import login_required
from django.contrib.auth.models import User
from django.db import connection
from django.http import HttpResponseRedirect
from django.shortcuts import get_object_or_404

def index(request):
    return render(request, 'ws/index.html', {})

def unread_user(request, user):
    if not user:
        return HttpResponseRedirect(reverse('index'))
    user = get_object_or_404(User, username=user)
    context = {}

    sql = """
SELECT comics_unreadcomic.comic_id, name, count(comics_unreadcomic.id) as count
FROM comics_unreadcomic
  INNER JOIN comics_comic ON comics_unreadcomic.comic_id=comics_comic.id
  INNER JOIN comics_subscription ON comics_unreadcomic.comic_id=comics_subscription.comic_id
WHERE activo=TRUE
  AND ended=FALSE
  AND comics_unreadcomic.user_id=%s
  AND comics_subscription.user_id=%s
GROUP BY comics_comic.id, comics_unreadcomic.comic_id, name, comics_subscription.position
ORDER BY comics_subscription.position"""

    acursor = connection.cursor()
    acursor.execute(sql, [user.id, user.id])
    rows = acursor.fetchall()
    count = len(rows)
    context['unread_list'] = rows
    context['count'] = count
    context['username'] = user
    return render(request, 'ws/unread_user.html', context, xml=True)

@login_required
def user_subscriptions(request, simple=False):
    context = {}
    context['subscriptions'] = request.user.subscription_set.order_by('position')
    if simple:
        template = 'ws/user_subscriptions_simple.html'
    else:
        template = 'ws/user_subscriptions.html'
    return render(request, template, context, xml=True)
