from django.conf.urls.defaults import *

urlpatterns = patterns('comic_ak.ws.views',
  url(r'^(?P<user>.*)/unread$', 'unread_user', name='ws_unread_user'),
)