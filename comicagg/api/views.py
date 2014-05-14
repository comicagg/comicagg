from comicagg.comics.models import Comic, ComicHistory
from comicagg.api.serializer import Serializer
from comicagg.logs import logmsg
from django import forms
from django.contrib.auth.models import AnonymousUser
from django.db import connection
from django.http import HttpResponse, HttpResponseForbidden, HttpResponseBadRequest
from django.shortcuts import get_object_or_404
from django.views.generic import View
from django.views.generic.base import TemplateView
from django.views.generic.edit import FormMixin
from provider import constants
from provider.forms import OAuthValidationError
from provider.oauth2.models import AccessToken
import comicagg.logs.tags as logtags
import datetime, sys, re, logging

logger = logging.getLogger(__name__)

class APIView(View, FormMixin):
    form_class = None
    content_type = "application/json; charset=utf-8"

    def dispatch(self, *args, **kwargs):
        request = args[0]
        if not request.user.is_authenticated():
            return HttpResponseForbidden()
        logger.debug("API call: %s %s" % (request.method, request.path))
        xml = False
        if self.prefer_xml():
            xml = True
            self.content_type = "text/xml; charset=utf-8"
        self.serializer = Serializer(request.user, xml)
        return super(APIView, self).dispatch(*args, **kwargs)

    def render_response(self, body):
        return HttpResponse(body, self.content_type)

    def prefer_xml(self):
        try:
            xml_i = self.request.accept_list.index("text/xml")
        except:
            return False
        try:
            json_i = self.request.accept_list.index("application/json")
        except:
            return True
        return xml_i < json_i

class ComicsView(APIView):
    def get(self, request, **kwargs):
        if "comicid" in kwargs.keys():
            comicid = kwargs["comicid"]
            data = Comic.objects.get(pk=comicid)
            return self.render_response(self.serializer.serialize(data))

class OAuth2TemplateView(TemplateView, FormMixin):
    form_class = None
    content_type = "text/xml; charset=utf-8"

    def dispatch(self, *args, **kwargs):
        request = args[0]
        if not request.user.is_authenticated():
            return HttpResponseForbidden()
        logger.debug("API call: %s %s" % (request.method, request.path))
        return super(OAuth2TemplateView, self).dispatch(*args, **kwargs)

    def get_context_data(self, **kwargs):
        context = super(OAuth2TemplateView, self).get_context_data(**kwargs)
        if self.form_class:
            form_class = self.get_form_class()
            form = self.get_form(form_class)
            context["form"] = form
        context.update(kwargs)
        return context

class IndexView(OAuth2TemplateView):
    template_name = "api/index.xml"

    def get(self, request, **kwargs):
        logger.debug("API Index")
        context = self.get_context_data(**kwargs)
        if (request.access_token):
            context["access_token"] = request.access_token
        scopes = dict(getattr(constants, 'SCOPES'))
        context["scope"] = scopes[request.scope]
        return self.render_to_response(context)

    def post(self, request, *args, **kwargs):
        return HttpResponse("POST received, user: " + str(request.user))

    def put(self, request, *args, **kwargs):
        return HttpResponse("PUT received, user: " + str(request.user))

    def delete(self, request, *args, **kwargs):
        return HttpResponse("DELETE received, user: " + str(request.user))

class ComicForm(forms.Form):
    def vote_validator(value):
        if value < -1 or value > 1:
            raise forms.ValidationError("Value not valid")

    vote = forms.IntegerField(validators=[vote_validator])

class ComicView(OAuth2TemplateView):
    template_name = "api/comic.xml"
    form_class = ComicForm

    def get(self, request, *args, **kwargs):
        context = self.get_context_data(**kwargs)
        # Do you want all the comics or just one?
        if "comicid" in context.keys():
            comicid = context["comicid"]
            comic = get_object_or_404(Comic, pk=comicid)
            context["comic"] = comic
        else:
            comics = Comic.objects.exclude(activo=False,ended=True)
            context["comics"] = comics
        return self.render_to_response(context)

    def post(self, request, *args, **kwargs):
        if not request.access_token.scope == constants.WRITE:
            logger.warning("API-4 The current access token does not have enough permissions for this operation.")
            return HttpResponseBadRequest()

        context = self.get_context_data(**kwargs)
        form = context["form"]
        if not form.is_valid():
            logger.warning("API call, form did not pass validation")
            return HttpResponseBadRequest()
        vote = form.cleaned_data["vote"]

        if "comicid" in context.keys():
            comicid = context["comicid"]
            comic = get_object_or_404(Comic, pk=comicid)
        else:
            return HttpResponseBadRequest()

        s = request.user.subscription_set.filter(comic=comic)
        if s.count() == 0:
            return HttpResponseBadRequest()

        if request.user.unreadcomic_set.filter(comic=comic).count():
            if vote == -1:
                votes = 1
                value = 0
            elif vote == 0:
                votes = 0
                value = 0
            else:
                votes = 1
                value = 1
            comic.votes += votes
            comic.rating += value
            comic.save()
            request.user.unreadcomic_set.filter(comic=comic).delete()
        return HttpResponse()


class SubscriptionView(OAuth2TemplateView):
    template_name = "api/subscription.xml"

    def get(self, request, *args, **kwargs):
        context = self.get_context_data(**kwargs)
        subscriptions = request.user.subscription_set.all()
        context["subscriptions"] = subscriptions
        return self.render_to_response(context)

    def put(self, request, *args, **kwargs):
        return HttpResponse("TODO, user: " + str(request.user))

    def delete(self, request, *args, **kwargs):
        return HttpResponse("TODO, user: " + str(request.user))

class UnreadView(OAuth2TemplateView):
    template_name = "api/unread.xml"

    def get(self, request, *args, **kwargs):
        context = self.get_context_data(**kwargs)
        if "comicid" in context.keys():
            comicid = context["comicid"]
            subscriptions = request.user.subscription_set.filter(comic=comicid)
        else:
            subscriptions = request.user.subscription_set.all()
        context["subscriptions"] = subscriptions
        return self.render_to_response(context)

    def delete(self, request, *args, **kwargs):
        return HttpResponse("TODO, user: " + str(request.user))

class StripView(OAuth2TemplateView):
    template_name = "api/strip.xml"

    def get(self, request, *args, **kwargs):
        context = self.get_context_data(**kwargs)
        if not "historyid" in context.keys():
            return HttpResponse(status=400)
        historyid = context["historyid"]
        history = get_object_or_404(ComicHistory, pk=historyid)
        context["history"] = history
        return self.render_to_response(context)

    def put(self, request, *args, **kwargs):
        return HttpResponse("TODO, user: " + str(request.user))

    def delete(self, request, *args, **kwargs):
        return HttpResponse("TODO, user: " + str(request.user))

class UserView(OAuth2TemplateView):
    template_name = "api/user.xml"

    def get(self, request, *args, **kwargs):
        context = self.get_context_data(**kwargs)
        #TODO Really need to change how to get this...
        sql = """
SELECT comics_unreadcomic.comic_id, name, count(comics_unreadcomic.id) as count
FROM comics_unreadcomic
  INNER JOIN comics_comic ON comics_unreadcomic.comic_id=comics_comic.id
  INNER JOIN comics_subscription ON comics_unreadcomic.comic_id=comics_subscription.comic_id
WHERE activo=TRUE
  AND ended=FALSE
  AND comics_unreadcomic.user_id=%s
  AND comics_subscription.user_id=%s
GROUP BY comics_comic.id, comics_unreadcomic.comic_id, name, comics_subscription.position
ORDER BY comics_subscription.position"""
        acursor = connection.cursor()
        acursor.execute(sql, [request.user.id, request.user.id])
        rows = acursor.fetchall()
        context["unreadcount"] = len(rows)
        return self.render_to_response(context)

    def put(self, request, *args, **kwargs):
        return HttpResponse(status=400)

    def delete(self, request, *args, **kwargs):
        return HttpResponse(status=400)
