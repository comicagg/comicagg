from django.conf.urls.defaults import patterns, url
from comicagg.api.views import IndexView
from django.views.decorators.csrf import csrf_exempt

urlpatterns = patterns('comicagg.api.views',
    url(r'^$', csrf_exempt(IndexView.as_view()), name='index'),
)