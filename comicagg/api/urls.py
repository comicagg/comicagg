from django.conf.urls import patterns, url
from django.views.decorators.csrf import csrf_exempt
from comicagg.api.views import (IndexView, ComicsView, StripsView,
    SubscriptionsView, UnreadsView, UserView)

urlpatterns = patterns('comicagg.api.views',
    url(r'^$', IndexView.as_view(), name='index'),

    url(r'^comics$', ComicsView.as_view(), name='comics'),
    url(r'^comics/(?P<comic_id>\d+)$', ComicsView.as_view(), name='comic_info'),

    url(r'^subscriptions$', csrf_exempt(SubscriptionsView.as_view()),
        name='subscriptions'),

    url(r'^unreads$', UnreadsView.as_view(), name='unreads'),
    url(r'^unreads/(?P<comic_id>\d+)$', csrf_exempt(UnreadsView.as_view()),
        name='unreads_comic'),
    url(r'^strips/(?P<strip_id>\d+)$', csrf_exempt(StripsView.as_view()),
        name='strip_info'),

    url(r'^user$', UserView.as_view(), name='user_info'),
)
