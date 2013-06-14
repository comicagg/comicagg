# Create your views here.
from comicagg.agregator.models import Comic, ComicHistory
from django import forms
from django.contrib.auth.models import AnonymousUser
from django.db import connection
from django.http import HttpResponse, HttpResponseForbidden, HttpResponseBadRequest
from django.shortcuts import get_object_or_404
from django.views.generic.base import TemplateView
from django.views.generic.edit import FormMixin
from comicagg.provider.forms import OAuthValidationError
from comicagg.provider.oauth2.models import AccessToken
from comicagg.provider import constants
import datetime, sys

# Will set request.user and request.access_token according to the Authorization header
# If the access_token is not present in headers or does not exist in server it will return 403
# If access_token is not valid, it will return 400

def OAuth2AccessToken(f):
    def authenticate(request):
        try:
            access_token_str = request.META["HTTP_AUTHORIZATION"]
        except KeyError:
            return None

        access_token = None
        try:
            access_token = AccessToken.objects.get(token=access_token_str)
        except:
            return None
        
        if access_token:
             td = access_token.expires - datetime.datetime.now()
             tds = (td.microseconds + (td.seconds + td.days * 24 * 3600) * 10**6) / 10**6
             if tds < 0:
                  raise OAuthValidationError({
                      "error": "invalid_grant", 
                      "error_description": "Your token has expired."})
        return access_token

    def new_f(klass, request, *args, **kwargs):
        try:
            request.access_token = authenticate(request)
            if request.access_token:
                request.user = request.access_token.user
            else:
                return HttpResponseForbidden()
        except OAuthValidationError:
            return HttpResponse(sys.exc_info()[1], status=400, content_type="application/json;charset=UTF-8")
        return f(klass, request, *args, **kwargs)
    
    return new_f

class BaseTemplateView(TemplateView, FormMixin):
    form_class = None

    def get_context_data(self, **kwargs):
        context = {}
        if self.form_class:
            form_class = self.get_form_class()
            form = self.get_form(form_class)
            context = {
                'form': form
            }
        context.update(kwargs)
        return super(BaseTemplateView, self).get_context_data(**context)

class IndexView(BaseTemplateView):
    template_name = "api/index.html"

    @OAuth2AccessToken
    def get(self, request, **kwargs):
        context = self.get_context_data(**kwargs)
        context["access_token"] = request.access_token
        scopes = dict(getattr(constants, 'SCOPES'))
        context["scope"] = scopes[request.access_token.scope]
        return self.render_to_response(context)

    @OAuth2AccessToken
    def post(self, request, *args, **kwargs):
        return HttpResponse("POST received, user: " + str(request.user))

    @OAuth2AccessToken
    def put(self, request, *args, **kwargs):
        return HttpResponse("PUT received, user: " + str(request.user))

    @OAuth2AccessToken
    def delete(self, request, *args, **kwargs):
        return HttpResponse("DELETE received, user: " + str(request.user))

class ComicForm(forms.Form):
    def vote_validator(value):
        if value < -1 or value > 1:
            raise forms.ValidationError("Value not valid")

    vote = forms.IntegerField(validators=[vote_validator])

class ComicView(BaseTemplateView):
    template_name = "api/comic.xml"
    form_class = ComicForm

    @OAuth2AccessToken
    def get(self, request, *args, **kwargs):
        context = self.get_context_data(**kwargs)
        if "comicid" in context["params"].keys():
            comicid = context["params"]["comicid"]
            comic = get_object_or_404(Comic, pk=comicid)
            context["comic"] = comic
        else:
            comics = Comic.objects.all()
            context["comics"] = comics
        return self.render_to_response(context)

    @OAuth2AccessToken
    def post(self, request, *args, **kwargs):
        if not request.access_token.scope == constants.READ_WRITE:
            return HttpResponseBadRequest()

        context = self.get_context_data(**kwargs)
        if not context["params"]["form"].is_valid():
            return HttpResponseBadRequest()
        vote = context["params"]["form"].cleaned_data["vote"]

        if "comicid" in context["params"].keys():
            comicid = context["params"]["comicid"]
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


class SubscriptionView(TemplateView):
    template_name = "api/subscription.xml"

    @OAuth2AccessToken
    def get(self, request, *args, **kwargs):
        context = self.get_context_data(**kwargs)
        subscriptions = request.user.subscription_set.all()
        context["subscriptions"] = subscriptions
        return self.render_to_response(context)

    @OAuth2AccessToken
    def put(self, request, *args, **kwargs):
        return HttpResponse("TODO, user: " + str(request.user))

    @OAuth2AccessToken
    def delete(self, request, *args, **kwargs):
        return HttpResponse("TODO, user: " + str(request.user))

class UnreadView(TemplateView):
    template_name = "api/unread.xml"

    @OAuth2AccessToken
    def get(self, request, *args, **kwargs):
        context = self.get_context_data(**kwargs)
        if "comicid" in context["params"].keys():
            comicid = context["params"]["comicid"]
            subscriptions = request.user.subscription_set.filter(comic=comicid)
        else:
            subscriptions = request.user.subscription_set.all()
        context["subscriptions"] = subscriptions
        return self.render_to_response(context)

    @OAuth2AccessToken
    def delete(self, request, *args, **kwargs):
        return HttpResponse("TODO, user: " + str(request.user))

class StripView(TemplateView):
    template_name = "api/strip.xml"

    @OAuth2AccessToken
    def get(self, request, *args, **kwargs):
        context = self.get_context_data(**kwargs)
        if not "historyid" in context["params"].keys():
            return HttpResponse(status=400)
        historyid = context["params"]["historyid"]
        history = get_object_or_404(ComicHistory, pk=historyid)
        context["history"] = history
        return self.render_to_response(context)

    @OAuth2AccessToken
    def put(self, request, *args, **kwargs):
        return HttpResponse("TODO, user: " + str(request.user))

    @OAuth2AccessToken
    def delete(self, request, *args, **kwargs):
        return HttpResponse("TODO, user: " + str(request.user))

class UserView(TemplateView):
    template_name = "api/user.xml"

    @OAuth2AccessToken
    def get(self, request, *args, **kwargs):
        context = self.get_context_data(**kwargs)
        #TODO Really need to change how to get this...
        sql = """
SELECT agregator_unreadcomic.comic_id, name, count(agregator_unreadcomic.id) as count
FROM agregator_unreadcomic
  INNER JOIN agregator_comic
    ON agregator_unreadcomic.comic_id=agregator_comic.id
  INNER JOIN agregator_subscription
    ON agregator_unreadcomic.comic_id=agregator_subscription.comic_id
WHERE
activo=1
AND
ended=0
AND
agregator_unreadcomic.user_id=%s
AND
agregator_subscription.user_id=%s
GROUP BY agregator_comic.id
ORDER BY agregator_subscription.position"""
        acursor = connection.cursor()
        acursor.execute(sql, [request.user.id, request.user.id])
        rows = acursor.fetchall()
        context["unreadcount"] = len(rows)
        return self.render_to_response(context)

    @OAuth2AccessToken
    def put(self, request, *args, **kwargs):
        return HttpResponse(status=400)

    @OAuth2AccessToken
    def delete(self, request, *args, **kwargs):
        return HttpResponse(status=400)
