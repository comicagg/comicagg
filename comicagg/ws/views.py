from comicagg import render
from django.core.urlresolvers import reverse
from django.contrib.auth.models import User
from django.db import connection
from django.http import HttpResponseRedirect
from django.shortcuts import get_object_or_404

def unread_user(request, user):
    if not user:
        return HttpResponseRedirect(reverse('index'))
    user = get_object_or_404(User, username=user)
    context = {}

    sql = """
SELECT agregator_unreadcomic.comic_id, name, count(agregator_unreadcomic.id) as count
FROM agregator_unreadcomic
  INNER JOIN agregator_comic
    ON agregator_unreadcomic.comic_id=agregator_comic.id
  INNER JOIN agregator_subscription
    ON agregator_unreadcomic.comic_id=agregator_subscription.comic_id
WHERE
activo=1
AND
ended=0
AND
agregator_unreadcomic.user_id=%s
AND
agregator_subscription.user_id=%s
GROUP BY agregator_comic.id
ORDER BY agregator_subscription.position"""
    acursor = connection.cursor()
    acursor.execute(sql, [user.id, user.id])
    rows = acursor.fetchall()
    count = len(rows)
    context['unread_list'] = rows
    context['count'] = count
    context['username'] = user
    return render(request, 'ws/unread_user.html', context, xml=True)

