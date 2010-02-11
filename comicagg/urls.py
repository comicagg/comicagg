# -*- coding: utf-8 -*-
from django.conf.urls.defaults import *
from django.conf import settings
from django.contrib import admin

admin.autodiscover()

handler404 = 'comicagg.error404'
handler500 = 'comicagg.error500'

urlpatterns = patterns('',
	url(r'^$', 'comicagg.accounts.views.index', name='index'),
	url(r'^robots.txt$', 'comicagg.robots_txt', name='robots'),
	url(r'^stats$', 'comicagg.agregator.views.stats', name='stats'),
	(r'^comics/', include('comicagg.agregator.urls')),
	(r'^accounts/', include('comicagg.accounts.urls')),
	(r'^blog/', include('comicagg.blog.urls')),
	(r'^help/', include('comicagg.help.urls')),
	(r'^ws/', include('comicagg.ws.urls')),
	(r'^admin/(.*)', admin.site.root),
	#comment this for production
	(r'^media/(?P<path>.*)$', 'django.views.static.serve', {'document_root': settings.MEDIA_ROOT, 'show_indexes':True}),
)

urlpatterns += patterns('django.views.generic.simple',
	url(r'^docs/custom_func/$', 'direct_to_template', {'template': 'admin/custom_func.html'}, name="docs_custom"),
)