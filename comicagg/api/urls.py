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

    url(r'^unreads/simple$', csrf_exempt(UnreadsView.as_view()), name='unreads'),
    url(r'^unreads$', csrf_exempt(UnreadsView.as_view()), {'with_strips':True}, name='unreads_with_strips'),
    url(r'^unreads/(?P<comic_id>\d+)$', csrf_exempt(UnreadsView.as_view()), {'with_strips':True}, name='unreads_for_a_comic'),

    url(r'^user$', csrf_exempt(UserView.as_view()), name='user_info'),
)
