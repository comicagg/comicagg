"""View classes to render API responses."""

import datetime
import logging
import re
import sys
import xml.etree.ElementTree as ET
from django import forms
from django.db import connection, transaction
from django.db.models import Max
from django.http import HttpResponse, HttpResponseForbidden, HttpResponseBadRequest, HttpResponseNotAllowed, HttpResponseNotFound, HttpResponseServerError
from django.shortcuts import get_object_or_404
from django.views.generic import View
from django.views.generic.base import TemplateView
from django.views.generic.edit import FormMixin
from provider import constants
from provider.forms import OAuthValidationError
from comicagg.comics.models import Comic, ComicHistory, UnreadComic, active_comics
from comicagg.api.decorators import write_required
from comicagg.api.forms import VoteForm
from comicagg.api.serializer import Serializer
from comicagg.logs import logmsg
import comicagg.logs.tags as logtags

logger = logging.getLogger(__name__)

# Helper classes

class HttpResponseUnauthorized(HttpResponse):
    status_code = 401

# Views

class APIView(View, FormMixin):
    """Base class for all API views.

    Handles the Accept header read by the middleware and chooses the content type to output.
    Sets up the serializer too.
    The rest of the API views inherit from this class.
    """

    form_class = None
    content_type = "application/json; charset=utf-8"

    # FUTURE: Can we use JsonResponse from Django to render JSON instead?

    @transaction.atomic
    def dispatch(self, *args, **kwargs):
        request = args[0]
        logger.debug("API call: %s %s", request.method, request.path)
        xml = False
        if self.prefers_xml():
            xml = True
            self.content_type = "text/xml; charset=utf-8"
        self.serializer = Serializer(request.user, xml)
        self.serialize = self.serializer.serialize
        if not request.user.is_authenticated():
            return self.error("Unauthorized", "You need to log in to access this resource", HttpResponseUnauthorized)
        response = None
        try:
            response = super(APIView, self).dispatch(*args, **kwargs)
        except:
            response = self.error("Server error", "Internal server error", HttpResponseServerError)
        return response

    def render_response(self, body, response_class=HttpResponse):
        return response_class(body, self.content_type)

    def prefers_xml(self):
        """Inspect the list of accepted content types and return a boolean if the request prefers XML over JSON."""
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

    def error(self, name, description, error_class=HttpResponseBadRequest):
        """Render an error response."""
        logger.debug("Returning an error (%s): %s", name, description)
        data = {
            "error": name,
            "description": description
            }
        body = self.serialize(data, identifier='error')
        return self.render_response(body, response_class=error_class)

class IndexView(APIView):
    """Welcome view."""

    def get(self, request, **kwargs):
        data = {
            'message': 'Hello %s.' % request.user.username,
            'message2': 'This is the comicagg API.',
        }
        body = self.serialize(data, identifier="welcome")
        return self.render_response(body)

class ComicsView(APIView):
    """Handles general comic related stuff. Get information about all the comics available in the service."""

    def get(self, request, **kwargs):
        """Get information about a specific comic or all the comics and optionally return the last strip fetched of the comics."""
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
    """Handles information about a comic strip."""

    def get(self, request, **kwargs):
        """Get information about a certain strip."""
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
        """Mark this strip as unread for the user doing the request."""
        context = self.get_context_data(**kwargs)
        strip_id = context['strip_id']
        try:
            strip = ComicHistory.objects.get(pk=strip_id)
        except:
            return self.error("NotFound", "The strip does not exist", HttpResponseNotFound)
        if not request.user.operations.is_subscribed(strip.comic):
            return self.error("BadRequest", "You are not subscribed to this comic")
        request.user.unreadcomic_set.create(user=request.user, comic=strip.comic, history=strip)
        return HttpResponse(status=204, content_type=self.content_type)

    @write_required
    def delete(self, request, **kwargs):
        """Mark this strip as read for the user doing the request."""
        context = self.get_context_data(**kwargs)
        strip_id = context['strip_id']
        try:
            strip = ComicHistory.objects.get(pk=strip_id)
        except:
            return self.error("NotFound", "The strip does not exist", HttpResponseNotFound)
        if not request.user.operations.is_subscribed(strip.comic):
            return self.error("BadRequest", "You are not subscribed to this comic")
        request.user.unreadcomic_set.filter(history__id=strip_id).delete()
        return HttpResponse(status=204, content_type=self.content_type)

class SubscriptionsView(APIView):
    """Handles comic subscriptions. Add, modify or remove subscriptions to comics."""

    def get(self, request, **kwargs):
        """Get all the comics the user is following including the last strip fetched."""
        subs = request.user.operations.all_comics()
        body = self.serialize(subs, last_strip=True, identifier='subscriptions')
        return self.render_response(body)

    @write_required
    def post(self, request, **kwargs):
        """Subscribe to several comics.

        The comics will be added at the end of the list of subscriptions.
        """
        if not request.processed_body:
            return self.error("BadRequest", "The request body is not valid")

        # Build the list of IDs
        body = request.processed_body
        id_list = list()
        if type(body) == ET.Element:
            # this is a XML request
            if body.tag != 'subscribe':
                return self.error("BadRequest", "The request XML body is not valid")
            try:
                for comic_id in body.findall('id'):
                    id_list.append(int(comic_id.text))
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

        # Remove possible duplicates
        id_list_clean = []
        [id_list_clean.append(x) for x in id_list if x not in id_list_clean]
        request.user.operations.subscribe_comics(id_list_clean)
        return HttpResponse(status=204, content_type=self.content_type)

    @write_required
    def put(self, request, **kwargs):
        """Modify the order of the subscribed comics.

        All the subscriptions will be ordered following the order of the IDs given in the body.

        Subscription/unsubscription operations should be done with this method.
        """
        if not request.processed_body:
            return self.error("BadRequest", "The request body is not valid")

        body = request.processed_body
        id_list = list()
        if type(body) == ET.Element:
            # this is a XML request
            if body.tag != 'subscriptions':
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

        # 1. Remove possible duplicates from the input
        # These are all the comics the user wants to follow and in this order
        id_list_clean = []
        [id_list_clean.append(x) for x in id_list if x not in id_list_clean]

        # 2. Get the comics the user is currently following
        current_active_idx = [c.id for c in request.user.operations.all_comics()]

        # 3. Find comics to be removed
        deleted_idx = [x for x in current_active_idx if x not in id_list_clean]
        request.user.operations.unsubscribe_comics(deleted_idx)

        # 4. Find comics to be added
        added_idx = [x for x in id_list_clean if x not in current_active_idx]
        request.user.operations.subscribe_comics(added_idx)

        # 5. Update the position of the subcriptions
        current_all = request.user.subscription_set.all()
        current_all_dict = dict([(s.comic.id, s) for s in current_all])

        if len(current_all) < id_list_clean:
            # This should never happen, something must have gone wrong
            HttpResponse(status=500, content_type=self.content_type)

        position = 0
        for comic_id in id_list_clean:
            s = current_all_dict[comic_id]
            s.position = position
            s.save()
            position += 1

        return HttpResponse(status=204, content_type=self.content_type)

    @write_required
    def delete(self, request, **kwargs):
        """Remove all the subscriptions, returning a list with the IDs of the comics the user used to follow."""
        # TODO: List of the IDs of the comics the user used to follow.
        # Needs the serializer to be able to render a list of integers
        # current_active_idx = [c.id for c in request.user.operations.all_comics()]
        request.user.subscription_set.all().delete()
        request.user.unreadcomic_set.all().delete()
        return HttpResponse(status=204, content_type=self.content_type)

class UnreadsView(APIView):
    """Handles a user's unread comics.
    
    Mark comics as read or unread.
    """
    form_class = VoteForm

    def get(self, request, **kwargs):
        """Get the unread comics followed by the user."""
        context = self.get_context_data(**kwargs)

        if 'comic_id' in context.keys():
            comic_id = context["comic_id"]
            try:
                comic = Comic.objects.get(pk=comic_id)
            except:
                return self.error("NotFound", "Comic does not exist", HttpResponseNotFound)

            if request.user.operations.is_subscribed(comic):
                body = self.serialize(comic, unread_strips=True)
            else:
                return self.error("BadRequest", "You are not subscribed to this comic")
        else:
            last_strip = 'with_strips' in context.keys()
            unreads = request.user.operations.unread_comics()
            body = self.serialize(unreads, last_strip=last_strip, identifier='unreads')

        return self.render_response(body)

    @write_required
    def post(self, request, **kwargs):
        """Mark a comic as unread."""
        context = self.get_context_data(**kwargs)

        # Do not allow POST if there is not comic id
        if 'comic_id' not in context.keys():
            return HttpResponseNotAllowed(['GET'])

        comic_id = context["comic_id"]
        try:
            comic = Comic.objects.get(pk=comic_id)
        except:
            return self.error("NotFound", "Comic does not exist", HttpResponseNotFound)

        if request.user.operations.is_subscribed(comic):
            ok = request.user.operations.mark_comic_unread(comic)
            if not ok:
                return self.error("ServerError", "There was an error setting this comic as unread")
        else:
            return self.error("BadRequest", "You are not subscribed to this comic")

        return HttpResponse(status=204, content_type=self.content_type)

    @write_required
    def put(self, request, **kwargs):
        """Mark a comic as read and optionally including a vote in the body."""
        context = self.get_context_data(**kwargs)

        # Do not allow PUT if there is not comic id
        if 'comic_id' not in context.keys():
            return HttpResponseNotAllowed(['GET'])

        form = context["form"]
        if not form.is_valid():
            return self.error("BadRequest", "Invalid vote parameter")

        vote = form.cleaned_data["vote"]
        comic_id = context["comic_id"]
        try:
            comic = Comic.objects.get(pk=comic_id)
        except:
            return self.error("NotFound", "Comic does not exist", HttpResponseNotFound)

        if not request.user.operations.is_subscribed(comic):
            return self.error("BadRequest", "You are not subscribed to this comic")

        # At this point we have confirmed that the comic exists and that the user is subscribed
        # FUTURE: do the voting in the comic operations and not here
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
        """Mark all comics as read."""
        context = self.get_context_data(**kwargs)
        if 'comic_id' not in context.keys():
            # Mark all comics as read
            request.user.unreadcomic_set.all().delete()
        else:
            # Mark just the one comic
            comic_id = context['comic_id']
            try:
                comic = Comic.objects.get(pk=comicid)
            except:
                return self.error("NotFound", "Comic does not exist", HttpResponseNotFound)
            # TODO: move this to the user operations class
            request.user.unreadcomic_set.filter(comic=comic).delete()
        return HttpResponse(status=204, content_type=self.content_type)

class UserView(APIView):
    """Handles some user information."""

    def get(self, request, **kwargs):
        """Get some user information."""
        body = self.serialize()
        return self.render_response(body)
