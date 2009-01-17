from django.conf.urls.defaults import *

urlpatterns = patterns('comicagg.blog.views',
  url(r'^$', 'index', name='blog_index'),
  url(r'^all/$', 'index', name='blog_archive', kwargs={'archive':True}),
  url(r'^hide_new_blogs/$', 'hide_new_blogs', name='hide_new_blogs'),
  url(r'^forget_new_blogs/$', 'forget_new_blogs', name='forget_new_blogs'),
  #url(r'^faq/$', 'view_faq', name='faq'),
  #url(r'^tickets/new$', 'new_ticket', name='new_ticket'),
  #url(r'^tickets/(?P<ticket_id>\d+)/reply$', 'reply_ticket', name='reply_ticket'),
  #url(r'^tickets/(?P<ticket_id>\d+)$', 'view_ticket', name='view_ticket'),
  #url(r'^tickets/close/(?P<ticket_id>\d+)$', 'close_ticket', name='close_ticket'),
)