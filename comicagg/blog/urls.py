# -*- coding: utf-8 -*-
from django.conf.urls import include, patterns, url

ajax_patterns = patterns('comicagg.blog.views',
    url(r'^forget_news/$', 'forget_new_blogs', name='forget_new_blogs'),
)

urlpatterns = patterns('comicagg.blog.views',
	url(r'^$', 'index', name='index'),
	url(r'^all/$', 'index', name='archive', kwargs={'archive':True}),

    (r'^ajax/', include(ajax_patterns, namespace="ajax")),
)
