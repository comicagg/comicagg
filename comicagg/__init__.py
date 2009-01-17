from django.http import HttpResponse, HttpResponseRedirect, HttpResponseNotFound, HttpResponseServerError
from django.template.loader import render_to_string
from django.conf import settings
from django.utils.version import get_svn_revision
from comicagg import __path__ as comicagg_path
import os, re

def render(request, template, context, menu=None, xml=False, responseClass=HttpResponse, mime='text/html; charset="utf-8"'):
  context['settings'] = settings
  try:
    user = request.user
  except:
    user = None
  context['user'] = user
  context['menu'] = menu
  context['svn_revision'] = get_svn()

  resp_text = render_to_string(template, context)
  #ie no reconoce el mime que hay que usar para xhtml 1.1 :(
  #response = HttpResponse(resp_text, mimetype="application/xhtml+xml")
  response = responseClass(resp_text, mimetype=mime)
  if xml:
    response = responseClass(resp_text, mimetype='text/xml; charset="utf-8"')
  #response['Cache-Control'] = 'no-cache'
  response['Cache-Control'] = 'max-age=1'
  response['Expires'] = '-1'
  return response

def error404(request):
  return render(request, '404.html', {}, responseClass=HttpResponseNotFound)

def error500(request):
  return render(request, '500.html', {}, responseClass=HttpResponseServerError)

"""
details = {
  from
  to
  subject
  message
}
"""

def send_email(details):
  #ruta a sendmail
  MAIL = '/usr/sbin/sendmail'
  #mensaje a enviar
  msg = """To: %(to)s
From: %(from)s
Subject: %(subject)s

%(message)s

""" % details
  #abrir pipe a sendmail
  p = os.popen("%s -t" % MAIL, 'w')
  p.write(msg)
  exitcode = p.close()
  if exitcode:
    print "Exit code: %s" % exitcode
  return exitcode

def robots_txt(request):
  return render(request, 'robots.txt', {}, mime='text/plain; charset="utf-8"')

def get_svn():
  return get_svn_revision(comicagg_path[0])

from django.views.debug import technical_500_response
import sys

class UserBasedExceptionMiddleware(object):
  def process_exception(self, request, exception):
    try:
      user = request.user
    except:
      user = None
    if user and user.is_superuser:
      return technical_500_response(request, *sys.exc_info())
