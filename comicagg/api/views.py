from comicagg.comics.models import Comic, ComicHistory
from comicagg.logs import logmsg
from django import forms
from django.contrib.auth.models import AnonymousUser
from django.db import connection
from django.http import HttpResponse, HttpResponseForbidden, HttpResponseBadRequest
from django.shortcuts import get_object_or_404
from django.views.generic.base import TemplateView
from django.views.generic.edit import FormMixin
from provider import constants
from provider.forms import OAuthValidationError
from provider.oauth2.models import AccessToken
import comicagg.logs.tags as logtags
import datetime, sys, re, logging

logger = logging.getLogger(__name__)

# Will set request.user and request.access_token according to the Authorization header
# If the access_token is not present in headers or does not exist in server it will return 403
# If access_token is not valid, it will return 400

def OAuth2AccessToken(f):
    def authenticate(request):
        try:
            access_token_str = request.META["HTTP_AUTHORIZATION"]
        except KeyError:
            logger.debug(logmsg(logtags.API_NO_AUTH_HEADER, "API call without Authorization header."))
            return None

        # Check the format of the authorization header, must be Bearer
        if not re.match('Bearer \w{40}', access_token_str):
            logger.error(logmsg(logtags.API_BAD_AUTH_HEADER_FORMAT, "Format of the Authorization header is not valid."))
            return None

        access_token_str = access_token_str.replace("Bearer ", "")
        access_token = None
        try:
            access_token = AccessToken.objects.get(token=access_token_str)
        except:
            logger.warning(logmsg(logtags.API_TOKEN_INVALID, "Got Authorization header but no access token was found in the database."))
            return None
        
        if access_token:
             td = access_token.expires - datetime.datetime.now()
             tds = (td.microseconds + (td.seconds + td.days * 24 * 3600) * 10**6) / 10**6
             if tds < 0:
                 logger.warning(logmsg(logtags.API_TOKEN_EXPIRED, "The access token has expired"))
                 raise OAuthValidationError("""{"error": "invalid_grant", "error_description": "Your token has expired."}""")
        logger.debug(logmsg(logtags.API_AUTH_OK, "API call successfully authenticated. Username=" + access_token.user.username))
        return access_token

    def wrapper(klass, request, *args, **kwargs):
        try:
            request.access_token = authenticate(request)
            if request.access_token:
                request.user = request.access_token.user
            else:
                return HttpResponseForbidden("No access token has been received or not a valid one. Check you Authorization header.")
        except OAuthValidationError:
            return HttpResponse(sys.exc_info()[1], status=400, content_type="application/json;charset=UTF-8")
        return f(klass, request, *args, **kwargs)
    
    return wrapper

class OAuth2TemplateView(TemplateView, FormMixin):
    form_class = None

    @OAuth2AccessToken
    def dispatch(self, *args, **kwargs):
        return super(OAuth2TemplateView, self).dispatch(*args, **kwargs)

    def get_context_data(self, **kwargs):
        context = {}
        if self.form_class:
            form_class = self.get_form_class()
            form = self.get_form(form_class)
            context = {
                'form': form
            }
        context.update(kwargs)
        return super(OAuth2TemplateView, self).get_context_data(**context)

class IndexView(OAuth2TemplateView):
    template_name = "api/index.html"

    def get(self, request, **kwargs):
        logger.debug("API call Index")
        context = self.get_context_data(**kwargs)
        context["access_token"] = request.access_token
        scopes = dict(getattr(constants, 'SCOPES'))
        context["scope"] = scopes[request.access_token.scope]
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
        if "comicid" in context["params"].keys():
            comicid = context["params"]["comicid"]
            comic = get_object_or_404(Comic, pk=comicid)
            context["comic"] = comic
        else:
            comics = Comic.objects.exclude(activo=False,ended=True)
            context["comics"] = comics
        return self.render_to_response(context)

    def post(self, request, *args, **kwargs):
        if not request.access_token.scope == constants.READ_WRITE:
            logger.warning("API-4 The current access token does not have enough permissions for this operation.")
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
        if "comicid" in context["params"].keys():
            comicid = context["params"]["comicid"]
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
        if not "historyid" in context["params"].keys():
            return HttpResponse(status=400)
        historyid = context["params"]["historyid"]
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
