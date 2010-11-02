# -*- coding: utf-8 -*-
from django.conf.urls.defaults import *

urlpatterns = patterns('comicagg.accounts.views',
    #url(r'^profile/$', 'edit_profile', name='edit_profile'),
    #url(r'^profile/saved/$', 'edit_profile', name='saved_profile', kwargs={'saved':True}),
    #url(r'^profile/save/$', 'save_profile', name='save_profile'),
    url(r'^login/$', 'login_view', name='login'),
    url(r'^logout/$', 'logout_view', name='logout'),
    url(r'^register/$', 'register', name='register'),
    #url(r'^password/change/$', 'password_change', name='change_password'),
    url(r'^password/reset/$', 'password_reset', name='reset_password'),
    #url(r'^email/$', 'email', name='change_email'),
    #url(r'^done_(?P<kind>\w+)/$', 'done', name='done'),
    url(r'activate/$', 'activate', name='accounts_activate'),
)
