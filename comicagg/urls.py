# -*- coding: utf-8 -*-
from django.conf import settings
from django.conf.urls.defaults import patterns, url, include
from django.contrib import admin

admin.autodiscover()

handler404 = 'comicagg.error404'
handler500 = 'comicagg.error500'

urlpatterns = patterns('',
	url(r'^$', 'comicagg.accounts.views.index', name='index'),
	url(r'^robots.txt$', 'comicagg.robots_txt', name='robots'),
	url(r'^stats/$', 'comicagg.agregator.views.stats', name='stats'),
	(r'^accounts/', include('comicagg.accounts.urls', namespace="accounts")),
	(r'^admin/', include(admin.site.urls)),
	(r'^comics/', include('comicagg.agregator.urls', namespace="aggregator")),
#	(r'^help/', include('comicagg.help.urls')),
	(r'^news/', include('comicagg.blog.urls', namespace="news")),
	(r'^ws/', include('comicagg.ws.urls', namespace="ws")),
)

extra = {
	'mediaurl':settings.MEDIA_URL
}

urlpatterns += patterns('django.views.generic.simple',
	url(r'^docs/custom_func/$', 'direct_to_template', {'template': 'admin/custom_func.html'}, name="docs_custom"),
	url(r'^contact/$', 'direct_to_template', {'template': 'contact.html', 'extra_context':extra}, name="contact"),
)
