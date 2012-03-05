from django.conf.urls.defaults import patterns, url

urlpatterns = patterns('comicagg.ws.views',
  url(r'^(?P<user>.*)/unread$', 'unread_user', name='unread_user'),
  url(r'^subscriptionssimple/$', 'user_subscriptions', {'simple':True},name='user_subscriptions_simple'),
  url(r'^subscriptions/$', 'user_subscriptions', name='user_subscriptions'),
)