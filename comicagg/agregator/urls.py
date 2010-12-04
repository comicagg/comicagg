# -*- coding: utf-8 -*-
from django.conf.urls.defaults import patterns, url

urlpatterns = patterns('comicagg.agregator.views',
	url(r'^$', 'read_view', name='read_index'),
	url(r'^read/$', 'read_view', name='read'),
	url(r'^add/$', 'organize', {'add': True}, name='organize_add'),
	url(r'^organize/$', 'organize', name='organize'),

    url(r'^request/$', 'request_index', name='request_index'),
	url(r'^request/ok/$', 'request_index', {'ok': True}, name='request_ok'),
    url(r'^request/save/$', 'request_index', name='request_save'),

	url(r'^li/(?P<cid>\d+)/', 'last_image_url', name='aggregator_last_image_url'),
    url(r'^hi/(?P<hid>\d+)/', 'history_image_url', name='aggregator_history_url'),
)

urlpatterns += patterns('comicagg.agregator.adminviews',
	url(r'^admin/check/$', 'admin_check', name='admin_check'),
	url(r'^admin/check/(?P<comic_id>\d+)/$', 'admin_check', name='admin_check_id'),
	url(r'^admin/reported/(?P<chids>[\w-]+)/$', 'admin_reported', name='admin_reported'),					
)

urlpatterns += patterns('comicagg.agregator.ajax',
	url(r'^ajax/add_comic/$', 'add_comic', name='ajax_add_comic'),
	url(r'^ajax/remove_comic/$', 'remove_comic', name='ajax_remove_comic'),
    url(r'^ajax/remove_comic_list/$', 'remove_comic_list', name='ajax_remove_comic_list'),
	url(r'^ajax/report_comic/$', 'report_comic', name='report_comic'),

	url(r'^ajax/organize/forget/(?P<comic_id>\d+)/$', 'forget_new_comic', name='forget_new_comic'),
	url(r'^ajax/organize/save/$', 'save_selection', name='save_selection'),

	url(r'^ajax/mark_read/$', 'mark_read', name='ajax_mark_read'),
	url(r'^ajax/mark_all_read/$', 'mark_all_read', name='ajax_mark_all_read'),
)