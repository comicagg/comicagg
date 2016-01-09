# -*- coding: utf-8 -*-
from django.conf import settings
from django.conf.urls import patterns, url, include
from django.contrib import admin
from comicagg.common.views import BaseTemplateView

admin.autodiscover()

handler404 = 'comicagg.error404'
handler500 = 'comicagg.error500'

urlpatterns = patterns('',
	url(r'^$', 'comicagg.accounts.views.index', name='index'),
	url(r'^robots.txt$', 'comicagg.robots_txt', name='robots'),
	url(r'^stats/$', 'comicagg.comics.views.stats', name='stats'),

	(r'^accounts/', include('comicagg.accounts.urls', namespace="accounts")),
	(r'^admin/', include(admin.site.urls)),
	(r'^api/', include('comicagg.api.urls', namespace="api")),
	(r'^comics/', include('comicagg.comics.urls', namespace="comics")),
	(r'^news/', include('comicagg.blog.urls', namespace="news")),
	(r'^oauth2/', include('provider.oauth2.urls', namespace='oauth2')),
	(r'^ws/', include('comicagg.ws.urls', namespace="ws")),
)

urlpatterns += patterns(
	url(r'^docs/custom_func/$', BaseTemplateView.as_view(template_name='admin/custom_func.html'), name="docs_custom"),
	url(r'^contact/$', BaseTemplateView.as_view(template_name='contact.html'), name="contact"),
)
