from comicagg.api.views import *
from django.conf.urls import patterns, url
from django.views.decorators.csrf import csrf_exempt

urlpatterns = patterns('comicagg.api.views',
    url(r'^$', csrf_exempt(IndexView.as_view()), name='index'),

    url(r'^comics/simple$', csrf_exempt(ComicsView.as_view()), {'simple':True}, name='comics_simple'),
    url(r'^comics$', csrf_exempt(ComicsView.as_view()), name='comics'),
    url(r'^comics/(?P<comic_id>\d+)$', csrf_exempt(ComicsView.as_view()), name='comic_info'),

    url(r'^strips/(?P<strip_id>\d+)$', csrf_exempt(StripsView.as_view()), name='strip_info'),

    url(r'^subscriptions$', csrf_exempt(SubscriptionsView.as_view()), name='subscriptions'),

    url(r'^unread/$', csrf_exempt(UnreadsView.as_view()), name='unread'),
    url(r'^unread/withstrips/$', csrf_exempt(UnreadsView.as_view()), {'withstrips':True}, name='unreadswithstrips'),
    url(r'^unread/(?P<comicid>\d+)/$', csrf_exempt(UnreadsView.as_view()), {'withstrips':True}, name='unreadsforacomic'),

    url(r'^user/$', csrf_exempt(UserView.as_view()), name='userinfo'),
)
