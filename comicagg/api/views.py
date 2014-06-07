from comicagg.comics.models import Comic, ComicHistory, UnreadComic, active_comics
from comicagg.api.serializer import Serializer
from comicagg.logs import logmsg
from django import forms
from django.contrib.auth.models import AnonymousUser
from django.db import connection
from django.db.models import Max
from django.http import HttpResponse, HttpResponseForbidden, HttpResponseBadRequest, HttpResponseNotAllowed, HttpResponseNotFound
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

# Decorators

def write_required(f):
    """
    Check if the passed request has write permissions in the scope
    """
    def wrapper(*args, **kwargs):
        request = args[1]
        if request.scope == getattr(constants, "WRITE"):
            return f(*args, **kwargs)
        else:
            view = args[0]
            return view.error("Forbidden", "This access token does not have enough permissions", HttpResponseForbidden)
    return wrapper

# Forms

class ComicForm(forms.Form):
    def vote_validator(value):
        logger.debug("Vote validator: " + str(value))
        if value < -1 or value > 1:
            raise forms.ValidationError("Value not valid")

    vote = forms.IntegerField(validators=[vote_validator])

# Views

class APIView(View, FormMixin):
    """
    Base class for all API views.
    Handles the Accept header read by the middleware and chooses the content type to output.
    Sets up the seralizer too.
    """
    form_class = None
    content_type = "application/json; charset=utf-8"

    def dispatch(self, *args, **kwargs):
        request = args[0]
        logger.debug("API call: %s %s" % (request.method, request.path))
        xml = False
        if self.prefer_xml():
            xml = True
            self.content_type = "text/xml; charset=utf-8"
        self.serializer = Serializer(request.user, xml)
        self.serialize = self.serializer.serialize
        if not request.user.is_authenticated():
            return self.error("Forbidden", "You cannot access this resource", HttpResponseForbidden)
        return super(APIView, self).dispatch(*args, **kwargs)

    def render_response(self, body, response_class=HttpResponse):
        return response_class(body, self.content_type)

    def prefer_xml(self):
        """
        Inspect the list of accepted content types.
        Return a boolean if the request prefers XML over JSON.
        """
        try:
            xml_i = self.request.accept_list.index("text/xml")
        except:
            return False
        try:
            json_i = self.request.accept_list.index("application/json")
        except:
            return True
        return xml_i < json_i

    def get_context_data(self, **kwargs):
        context = super(APIView, self).get_context_data(**kwargs)
        form_class = self.get_form_class()
        context['form'] = self.get_form(form_class)
        return context

    def error(self, name, description, klass=HttpResponseBadRequest):
        data = {
            "error": name,
            "description": description
            }
        body = self.serialize(data, identifier='error')
        return self.render_response(body, response_class=klass)

class IndexView(APIView):
    pass

class ComicsView(APIView):
    form_class = ComicForm

    def get(self, request, **kwargs):
        if "comicid" in kwargs.keys():
            comicid = kwargs["comicid"]
            try:
                data = Comic.objects.get(pk=comicid)
            except:
                return self.error("NotFound", "Comic does not exist", HttpResponseNotFound)
            body = self.serialize(data, last_strip=True)
            return self.render_response(body)

        last_strip = "with_last" in kwargs.keys()
        body = self.serialize(list(active_comics()), last_strip=last_strip, identifier="comics")
        return self.render_response(body)

    @write_required
    def post(self, request, **kwargs):
        context = self.get_context_data(**kwargs)

        # Do not allow POST if there is not comic id
        if not 'comicid' in context.keys():
            return HttpResponseNotAllowed(['GET'])

        form = context["form"]

        if not form.is_valid():
            return self.error("BadRequest", "Invalid vote parameter")

        vote = form.cleaned_data["vote"]
        comicid = context["comicid"]
        try:
            comic = Comic.objects.get(pk=comicid)
        except:
            return self.error("NotFound", "Comic does not exist", HttpResponseNotFound)

        s = request.user.subscription_set.filter(comic=comic)
        if s.count() == 0:
            return self.error("BadRequest", "You are not subscribed to this comic")

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
            # Mark all unreads as read
            request.user.unreadcomic_set.filter(comic=comic).delete()
        return HttpResponse(status=204, content_type=self.content_type)

    @write_required
    def put(self, request, **kwargs):
        context = self.get_context_data(**kwargs)

        if not 'comicid' in context.keys():
            return HttpResponseNotAllowed(['GET'])

        comicid = context["comicid"]
        try:
            comic = Comic.objects.get(pk=comicid)
        except:
            return self.error("NotFound", "Comic does not exist", HttpResponseNotFound)

        if request.user.subscription_set.filter(comic=comic):
            # The comic is already there, finish here
            logger.debug("The user is already subscribed")
            return HttpResponse(status=204, content_type=self.content_type)

        # Calculate the position for the comic, it'll be the last
        max_position = request.user.subscription_set.aggregate(pos=Max('position'))['pos']
        if not max_position:
            # max_position can be None if there are no comics
            max_position = 0
        next_pos = max_position + 1
        request.user.subscription_set.create(comic=comic, position=next_pos)
        # Add the last strip to the user's unread list
        history = ComicHistory.objects.filter(comic=comic)
        if history:
            UnreadComic.objects.create(user=request.user, comic=comic, history=history[0])
        return HttpResponse(status=204, content_type=self.content_type)

    @write_required
    def delete(self, request, **kwargs):
        context = self.get_context_data(**kwargs)

        if not 'comicid' in context.keys():
            return HttpResponseNotAllowed(['GET'])

        comicid = context["comicid"]
        try:
            comic = Comic.objects.get(pk=comicid)
        except:
            return self.error("NotFound", "Comic does not exist", HttpResponseNotFound)

        s = request.user.subscription_set.filter(comic=comic)
        if s:
            logger.debug("Removing subscription")
            s.delete()
            request.user.unreadcomic_set.filter(comic=comic).delete()
        return HttpResponse(status=204, content_type=self.content_type)

class SubscriptionsView(APIView):
    pass

class StripsView(APIView):
    pass

class UnreadsView(APIView):
    pass

class UserView(APIView):
    pass

"""
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
"""
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
"""
        acursor = connection.cursor()
        acursor.execute(sql, [request.user.id, request.user.id])
        rows = acursor.fetchall()
        context["unreadcount"] = len(rows)
        return self.render_to_response(context)

    def put(self, request, *args, **kwargs):
        return HttpResponse(status=400)

    def delete(self, request, *args, **kwargs):
        return HttpResponse(status=400)
"""