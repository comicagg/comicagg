# -*- coding: utf-8 -*-
from django.conf.urls.defaults import *

urlpatterns = patterns('comicagg.agregator.views',
	# Example:
	url(r'^$', 'read_view', name='read_index'),
	url(r'^read/$', 'read_view', name='read'),
	url(r'^organize/forget/$', 'forget_new_comics', name='forget_new_comics'),
	url(r'^add/$', 'organize', {'add':True}, name='organize_add'),
	url(r'^organize/$', 'organize', name='organize'),
	url(r'^organize/(?P<tag>.*)/', 'organize', name='configure_with_tags'),

    url(r'^request/$', 'request_index', name='request_index'),
	url(r'^request/ok/$', 'request_index', {'ok':True}, name='request_ok'),
    url(r'^request/save/$', 'request_index', name='request_save'),

	url(r'^list/$', 'comic_list', name='comic_list'),
	url(r'^list/comic/$', 'comic_list_load', name='comic_list_load'),
	url(r'^list/(?P<sortby>\w+)/$', 'comic_list', name='comic_list_sorted'),
	url(r'^list/tag/(?P<tag>[^/]+)/$', 'comic_list', name='view_tag'),
	url(r'^list/tag/(?P<tag>[^/]+)/(?P<sortby>\w+)/$', 'comic_list', name='view_tag_sorted'),

	url(r'^admin/check/$', 'admin_check', name='admin_check'),
	url(r'^admin/check/(?P<comic_id>\d+)/$', 'admin_check', name='check'),
	url(r'^admin/reported/(?P<chids>[\w-]+)/$', 'admin_reported', name='admin_reported'),

	url(r'^ajax/hide_new_comics/$', 'hide_new_comics', name='hide_new_comics'),

	url(r'^add_comic/(?P<comic_id>\d+)/random/$', 'add_comic', {"next":"read"}, name='add_comic_random'),
	url(r'^random_comic/$', 'random_comic_view', name='random_comic'),

	url(r'^ajax/add_comic/$', 'add_comic', name='add_comic_ajax'),
	url(r'^ajax/remove_comic/$', 'remove_comic', name='remove_comic_ajax'),
    url(r'^ajax/remove_comic_list/$', 'remove_comic_list', name='ajax_remove_comic_list'),
	url(r'^ajax/report_comic/$', 'report_comic', name='report_comic'),

	url(r'^ajax/organize/quickforget/$', 'forget_new_comics', name='forget_new_comics_quick', kwargs={'quick':True}),
	url(r'^ajax/organize/forget/(?P<comic_id>\d+)/$', 'forget_new_comic', name='forget_new_comic'),
	url(r'^ajax/organize/save/$', 'save_selection', name='save_selection'),

	url(r'^ajax/get_tags/$', 'get_tags', name='get_tags'),
	url(r'^ajax/save_tags/$', 'save_tags', name='save_tags'),
	url(r'^ajax/mark_read/$', 'mark_read', name='mark_read'),
	url(r'^ajax/mark_all_read/$', 'mark_all_read', name='mark_all_read'),
	url(r'^ajax/rate/$', 'rate_comic', name='rate'),

	url(r'^li/(?P<cid>\d+)/', 'last_image_url', name='aggregator_last_image_url'),
    url(r'^hi/(?P<hid>\d+)/', 'history_image_url', name='aggregator_history_url'),
)

