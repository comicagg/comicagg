# -*- coding: utf-8 -*-
from django.conf.urls.defaults import patterns, url

urlpatterns = patterns('comicagg.accounts.views',
    url(r'^profile/$', 'edit_profile', name='profile'),
    #url(r'^profile/saved/$', 'edit_profile', name='saved_profile', kwargs={'saved':True}),
    #url(r'^profile/save/$', 'save_profile', name='save_profile'),
    url(r'^login/$', 'login_view', name='login'),
    url(r'^logout/$', 'logout_view', name='logout'),
    url(r'^register/$', 'register', name='register'),
    url(r'^password/change/$', 'password_change', name='password_change'),
    url(r'^password/reset/$', 'password_reset', name='password_reset'),
    url(r'^email/$', 'email', name='email_change'),
    url(r'^done_(?P<kind>\w+)/$', 'done', name='done'),
    url(r'^activate/$', 'activate', name='activate'),
)
