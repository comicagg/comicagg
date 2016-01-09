from django.conf.urls import patterns, url

urlpatterns = patterns('comicagg.help.views',
  url(r'^$', 'index', name='help_index'),
  #url(r'^faq/$', 'view_faq', name='faq'),
  #url(r'^tickets/new$', 'new_ticket', name='new_ticket'),
  #url(r'^tickets/(?P<ticket_id>\d+)/reply$', 'reply_ticket', name='reply_ticket'),
  #url(r'^tickets/(?P<ticket_id>\d+)$', 'view_ticket', name='view_ticket'),
  #url(r'^tickets/close/(?P<ticket_id>\d+)$', 'close_ticket', name='close_ticket'),
)
