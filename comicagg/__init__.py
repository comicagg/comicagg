from django.http import HttpResponse, HttpResponseRedirect, HttpResponseNotFound, HttpResponseServerError
from django.template.loader import render_to_string
from django.conf import settings
import os, re

def render(request, template, context, menu=None, xml=False, responseClass=HttpResponse, mime='text/html; charset="utf-8"'):
  context['settings'] = settings
  try:
    user = request.user
  except:
    user = None
  context['user'] = user
  context['menu'] = menu

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

def robots_txt(request):
  return render(request, 'robots.txt', {}, mime='text/plain; charset="utf-8"')

