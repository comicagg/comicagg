# -*- coding: utf-8 -*-
from django.conf.urls.defaults import *

urlpatterns = patterns('comicagg.blog.views',
	url(r'^$', 'index', name='blog_index'),
	url(r'^all/$', 'index', name='blog_archive', kwargs={'archive':True}),
	url(r'^ajax/hide_new_blogs/$', 'hide_new_blogs', name='hide_new_blogs'),
	url(r'^ajax/forget_new_blogs/$', 'forget_new_blogs', name='forget_new_blogs'),
	#url(r'^faq/$', 'view_faq', name='faq'),
)