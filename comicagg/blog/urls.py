# -*- coding: utf-8 -*-
from django.conf.urls.defaults import patterns, url

urlpatterns = patterns('comicagg.blog.views',
    #Main view, the last 10 news items
	url(r'^$', 'index', name='blog_index'),
	#All the news items
	url(r'^all/$', 'index', name='blog_archive', kwargs={'archive':True}),
	#Ajax to forget the new news items
	url(r'^ajax/forget_news/$', 'forget_new_blogs', name='ajax_forget_new_blogs'),
)