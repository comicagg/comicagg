from comicagg.api.views import *
from django.conf.urls.defaults import patterns, url
from django.views.decorators.csrf import csrf_exempt

urlpatterns = patterns('comicagg.api.views',
    url(r'^$', csrf_exempt(IndexView.as_view()), name='index'),
    url(r'^comic/$', csrf_exempt(ComicView.as_view()), name='comics'),
    url(r'^comic/(?P<comicid>\d+)/$', csrf_exempt(ComicView.as_view()), name='comicinfo'),
    url(r'^strip/(?P<historyid>\d+)/$', csrf_exempt(StripView.as_view()), name='strips'),
    url(r'^subscription/$', csrf_exempt(SubscriptionView.as_view()), name='subscriptions'),
    url(r'^unread/$', csrf_exempt(UnreadView.as_view()), name='unread'),
    url(r'^unread/withstrips/$', csrf_exempt(UnreadView.as_view()), {'withstrips':True}, name='unreadswithstrips'),
    url(r'^unread/(?P<comicid>\d+)/$', csrf_exempt(UnreadView.as_view()), {'withstrips':True}, name='unreadsforacomic'),
    url(r'^user/$', csrf_exempt(UserView.as_view()), name='userinfo'),
)
