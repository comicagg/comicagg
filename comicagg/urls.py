from django.conf.urls.defaults import *
from django.conf import settings
from django.contrib import admin

admin.autodiscover()

handler404 = 'comic_ak.error404'
handler500 = 'comic_ak.error500'

urlpatterns = patterns('',
    url(r'^$', 'comic_ak.accounts.views.index', name='index'),
    url(r'^robots.txt$', 'comic_ak.robots_txt', name='robots'),
    (r'^comics/', include('comic_ak.agregator.urls')),
    (r'^accounts/', include('comic_ak.accounts.urls')),
    (r'^blog/', include('comic_ak.blog.urls')),
    (r'^help/', include('comic_ak.help.urls')),
    (r'^ws/', include('comic_ak.ws.urls')),
    (r'^admin/(.*)', admin.site.root),
    #comment this for production
    (r'^media/(?P<path>.*)$', 'django.views.static.serve', {'document_root': settings.MEDIA_ROOT, 'show_indexes':True}),
)
