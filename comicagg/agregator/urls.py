# -*- coding: utf-8 -*-
from django.conf.urls.defaults import *

urlpatterns = patterns('comicagg.agregator.views',
	# Example:
	url(r'^$', 'read_view', name='read_index'),
	url(r'^read/$', 'read_view', name='read'),
	url(r'^configure/forget/$', 'forget_new_comics', name='forget_new_comics'),
	url(r'^configure/quickforget/$', 'forget_new_comics', name='forget_new_comics_quick', kwargs={'quick':True}),
	url(r'^configure/forget/(?P<comic_id>\d+)/$', 'forget_new_comic', name='forget_new_comic'),
	url(r'^configure/save/$', 'save_selection', name='save_selection'),
	url(r'^configure/$', 'configure', name='configure'),
	url(r'^configure/(?P<tag>.*)/', 'configure', name='configure_with_tags'),

	url(r'^get_tags/$', 'get_tags', name='get_tags'),
	url(r'^save_tags/$', 'save_tags', name='save_tags'),

	url(r'^mark_read/$', 'mark_read', name='mark_read'),
	url(r'^mark_all_read/$', 'mark_all_read', name='mark_all'),
	url(r'^rate/$', 'rate_comic', name='rate'),

	url(r'^request_comic/$', 'request_comic', name='request'),
	url(r'^done_request/$', 'request_comic', {'done':True}, name='done_request'),

	url(r'^list/$', 'comic_list', name='comic_list'),
	url(r'^list/comic/$', 'comic_list_load', name='comic_list_load'),
	url(r'^list/(?P<sortby>\w+)/$', 'comic_list', name='comic_list_sorted'),
	url(r'^list/tag/(?P<tag>[^/]+)/$', 'comic_list', name='view_tag'),
	url(r'^list/tag/(?P<tag>[^/]+)/(?P<sortby>\w+)/$', 'comic_list', name='view_tag_sorted'),

	url(r'^admin/check/$', 'admin_check', name='admin_check'),
	url(r'^admin/check/(?P<comic_id>\d+)/$', 'admin_check', name='check'),

	url(r'^hide_new_comics/$', 'hide_new_comics', name='hide_new_comics'),

	url(r'^add_comic/$', 'add_comic_ajax', name='add_comic_ajax'),
	url(r'^add_comic/(?P<comic_id>\d+)/$', 'add_comic', name='add_comic'),
	url(r'^add_comic/(?P<comic_id>\d+)/random/$', 'add_comic', {"next":"read"}, name='add_comic_random'),
	url(r'^remove_comic/$', 'remove_comic_ajax', name='remove_comic_ajax'),
	url(r'^remove_comic/(?P<comic_id>\d+)/$', 'remove_comic', name='remove_comic'),
	url(r'^report_comic/$', 'report_comic', name='report_comic'),

	url(r'^random_comic/$', 'random_comic_view', name='random_comic'),
)

