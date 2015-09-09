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
import xml.etree.ElementTree as ET

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

class VoteForm(forms.Form):
    """
    Form used to validate the input of the Vote for a comic
    """
    def vote_validator(value):
        """
        A vote is only valid if it's -1 <= vote <= 1
        """
        logger.debug("Vote validator: " + str(value))
        if value < -1 or value > 1:
            raise forms.ValidationError("Value not valid")

    vote = forms.IntegerField(validators=[vote_validator])

# Helper classes

class HttpResponseUnauthorized(HttpResponse):
    status_code = 401

# Views

class APIView(View, FormMixin):
    """
    Base class for all API views.
    Handles the Accept header read by the middleware and chooses the content type to output.
    Sets up the serializer too.
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
            return self.error("Unauthorized", "You need to log in to access this resource", HttpResponseUnauthorized)
        # TODO: Should wrap this call with try/except and handle any unexpected error
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
        if self.form_class:
            form_class = self.get_form_class()
            context['form'] = self.get_form(form_class)
        return context

    def error(self, name, description, klass=HttpResponseBadRequest):
        logger.debug("Returning an error (%s): %s" % (name, description))
        data = {
            "error": name,
            "description": description
            }
        body = self.serialize(data, identifier='error')
        return self.render_response(body, response_class=klass)

class IndexView(APIView):
    """
    Welcome view.
    """
    def get(self, request, **kwargs):
        data = {
            'message': 'Hello %s.' % request.user.username,
            'message2': 'This is the comicagg API.',
        }
        body = self.serialize(data, identifier="welcome")
        return self.render_response(body)

class ComicsView(APIView):
    """
    Handles comic related stuff. Get information about all the comics available in the service.
    """
    def get(self, request, **kwargs):
        """
        Get information about a comic or all the comics. May or may not return the last strip fetched of the comics.
        """
        if "comic_id" in kwargs.keys():
            comic_id = kwargs["comic_id"]
            try:
                data = Comic.objects.get(pk=comic_id)
            except:
                return self.error("NotFound", "The comic does not exist", HttpResponseNotFound)
            body = self.serialize(data, last_strip=True)
        else:
            simple = "simple" in kwargs.keys()
            body = self.serialize(list(active_comics()), last_strip=(not simple), identifier="comics")
        return self.render_response(body)

class StripsView(APIView):
    """
    Handles information about a comic strip.
    """
    def get(self, request, **kwargs):
        """
        Get information about a certain strip.
        """
        context = self.get_context_data(**kwargs)
        strip_id = context['strip_id']
        try:
            strip = ComicHistory.objects.get(pk=strip_id)
        except:
            return self.error("NotFound", "That strip does not exist", HttpResponseNotFound)
        body = self.serialize(strip)
        return self.render_response(body)

    @write_required
    def put(self, request, **kwargs):
        """
        Mark this strip as unread for the user doing the request.
        """
        context = self.get_context_data(**kwargs)
        strip_id = context['strip_id']
        try:
            strip = ComicHistory.objects.get(pk=strip_id)
        except:
            return self.error("NotFound", "The strip does not exist", HttpResponseNotFound)
        if not request.user.get_profile().is_subscribed(strip.comic):
            return self.error("BadRequest", "You are not subscribed to this comic")
        request.user.unreadcomic_set.create(user=request.user, comic=strip.comic, history=strip)
        return HttpResponse(status=204, content_type=self.content_type)

    @write_required
    def delete(self, request, **kwargs):
        """
        Mark this strip as read for the user doing the request.
        """
        context = self.get_context_data(**kwargs)
        strip_id = context['strip_id']
        try:
            strip = ComicHistory.objects.get(pk=strip_id)
        except:
            return self.error("NotFound", "The strip does not exist", HttpResponseNotFound)
        if not request.user.get_profile().is_subscribed(strip.comic):
            return self.error("BadRequest", "You are not subscribed to this comic")
        request.user.unreadcomic_set.filter(history__id=strip_id).delete()
        return HttpResponse(status=204, content_type=self.content_type)

class SubscriptionsView(APIView):
    """
    Handles comic subscriptions. Add, modify or remove subscriptions to comics.
    """
    def get(self, request, **kwargs):
        subs = request.user.get_profile().all_comics()
        body = self.serialize(subs, last_strip=True, identifier='subscriptions')
        return self.render_response(body)

    @write_required
    def post(self, request, **kwargs):
        """
        If the user is currently subscribed to a inactive/broken comic after executing this, that broken comic will be unsubscribed.
        """
        if not request.processed_body:
            return self.error("BadRequest", "The request body is not valid")

        body = request.processed_body
        id_list = list()
        if type(body) == ET.Element:
            # this is a XML request
            if 'subscriptions' != body.tag:
                return self.error("BadRequest", "The request XML body is not valid")
            try:
                for comicid in body.findall('comicid'):
                    id_list.append(int(comicid.text))
            except:
                return self.error("BadRequest", "Invalid comic ID list")
        else:
            # this should be a JSON request
            if 'subscriptions' not in body.keys():
                return self.error("BadRequest", "The request JSON body is not valid")
            try:
                id_list = [int(x) for x in body['subscriptions']]
            except:
                return self.error("BadRequest", "Invalid comic ID list")

        id_list_clean = []
        [id_list_clean.append(x) for x in id_list if not x in id_list_clean]

        # Now process the comic id list
        current_active_idx = [c.id for c in request.user.get_profile().all_comics()]
        # find deleted
        deleted_idx = [x for x in current_active_idx if not x in id_list_clean]
        request.user.get_profile().unsubscribe_comics(deleted_idx)
        # unsubscribe deleted
        # find added
        added_idx = [x for x in id_list_clean if not x in current_active_idx]
        request.user.get_profile().subscribe_comics(added_idx)
        # subscribe added
        # reorder
        current_all = request.user.subscription_set.all()
        current_all_d = dict([(s.comic.id, s) for s in current_all])

        if len(current_all) < id_list_clean:
            # This should never happen, something must have gone wrong
            HttpResponse(status=500, content_type=self.content_type)

        position = 0
        for cid in id_list_clean:
            s = current_all_d[cid]
            s.position = position
            s.save()
            position += 1

        return HttpResponse(status=204, content_type=self.content_type)

    @write_required
    def put(self, request, **kwargs):
        if not request.processed_body:
            return self.error("BadRequest", "The request body is not valid")

        body = request.processed_body
        id_list = list()
        if type(body) == ET.Element:
            # this is a XML request
            if 'subscribe' != body.tag:
                return self.error("BadRequest", "The request XML body is not valid")
            try:
                for comicid in body.findall('comicid'):
                    id_list.append(int(comicid.text))
            except:
                return self.error("BadRequest", "Invalid comic ID list")
        else:
            # this should be a JSON request
            if 'subscribe' not in body.keys():
                return self.error("BadRequest", "The request JSON body is not valid")
            try:
                id_list = [int(x) for x in body['subscribe']]
            except:
                return self.error("BadRequest", "Invalid comic ID list")

        id_list_clean = []
        [id_list_clean.append(x) for x in id_list if not x in id_list_clean]
        request.user.get_profile().subscribe_comics(id_list_clean)
        return HttpResponse(status=204, content_type=self.content_type)

    @write_required
    def delete(self, request, **kwargs):
        request.user.subscription_set.all().delete()
        request.user.unreadcomic_set.all().delete()
        return HttpResponse(status=204, content_type=self.content_type)

class UnreadsView(APIView):
    """
    Handles a user's unread comics. Mark comics as read or unread.
    """
    form_class = VoteForm

    def get(self, request, **kwargs):
        context = self.get_context_data(**kwargs)

        if 'comicid' in context.keys():
            comicid = context["comicid"]
            try:
                comic = Comic.objects.get(pk=comicid)
            except:
                return self.error("NotFound", "Comic does not exist", HttpResponseNotFound)

            if request.user.subscription_set.filter(comic__id=comicid).count():
                body = self.serialize(comic, unread_strips=True)
            else:
                return self.error("BadRequest", "You are not subscribed to this comic")
        else:
            last_strip = 'withstrips' in context.keys()
            unreads = request.user.get_profile().unread_comics()
            body = self.serialize(unreads, last_strip=last_strip, identifier='unreads')

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
    def delete(self, request, **kwargs):
        context = self.get_context_data(**kwargs)
        if not 'comicid' in context.keys():
            # Mark all comics as read
            request.user.unreadcomic_set.all().delete()
        else:
            # Mark just the one comic
            comicid = context['comicid']
            try:
                comic = Comic.objects.get(pk=comicid)
            except:
                return self.error("NotFound", "Comic does not exist", HttpResponseNotFound)
            request.user.unreadcomic_set.filter(comic=comic).delete()
        return HttpResponse(status=204, content_type=self.content_type)

class UserView(APIView):
    """
    Handles some user information.
    """
    def get(self, request, **kwargs):
        body = self.serialize()
        return self.render_response(body)
