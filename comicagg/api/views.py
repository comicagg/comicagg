# Create your views here.
from comicagg.agregator.models import Comic, ComicHistory
from django.contrib.auth.models import AnonymousUser
from django.http import HttpResponse, HttpResponseForbidden
from django.shortcuts import get_object_or_404
from django.views.generic.base import TemplateView
from comicagg.provider.forms import OAuthValidationError
from comicagg.provider.oauth2.models import AccessToken
from comicagg.provider import constants
import datetime, sys

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
            return HttpResponse(sys.exc_info(), status=400, content_type="application/json;charset=UTF-8")
        return f(klass, request, *args, **kwargs)
    
    return new_f

class IndexView(TemplateView):
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

class ComicView(TemplateView):
    template_name = "api/comic.xml"

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

