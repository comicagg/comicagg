# -*- coding: utf-8 -*-
from django.conf.urls import include, patterns, url

ajaxpatterns = patterns('comicagg.blog.views',
    #Ajax to forget the new news items
    url(r'^forget_news/$', 'forget_new_blogs', name='forget_new_blogs'),                        
)

urlpatterns = patterns('comicagg.blog.views',
    #Main view, the last 10 news items
	url(r'^$', 'index', name='index'),
	#All the news items
	url(r'^all/$', 'index', name='archive', kwargs={'archive':True}),

    (r'^ajax/', include(ajaxpatterns, namespace="ajax")),
)