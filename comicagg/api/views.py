"""View classes to render API responses."""

import logging
import xml.etree.ElementTree as ET
from django.db import transaction
from django.http import HttpResponse, HttpResponseBadRequest, HttpResponseNotAllowed, HttpResponseNotFound, HttpResponseServerError
from django.views.generic import View
from django.views.generic.edit import FormMixin
from comicagg.comics.models import Comic, ComicHistory, active_comics
from comicagg.api.decorators import write_required, parse_param
from comicagg.api.forms import VoteForm, StripForm
from comicagg.api.serializer import Serializer
from comicagg.logs import logmsg
import comicagg.logs.tags as logtags

logger = logging.getLogger(__name__)

# Helper classes

class HttpResponseUnauthorized(HttpResponse):
    status_code = 401

class HttpResponseNoContent(HttpResponse):
    status_code = 204

# Views

class APIView(View, FormMixin):
    """Base class for all API views.

    Handles the Accept header read by the middleware and chooses the content type to output.
    Sets up the serializer too.
    The rest of the API views inherit from this class.
    """

    def __init__(self, **kwargs):
        super(APIView, self).__init__(**kwargs)
        # FUTURE: what if we want to use several form classes?
        self.form_class = None
        self.content_type = "application/json; charset=utf-8"

    # FUTURE: Can we use JsonResponse from Django to render JSON instead?
    @transaction.atomic
    def dispatch(self, *args, **kwargs):
        """Setup the response content type and handle errors from the specific verb methods."""
        request = args[0]
        logger.debug("API call: %s %s", request.method, request.path)

        if request.client_prefers_xml:
            self.content_type = "text/xml; charset=utf-8"
        self.serialize = Serializer(request.user, request.client_prefers_xml).serialize

        if not request.user.is_authenticated():
            return self.error("Unauthorized", "You need to log in to access this resource", HttpResponseUnauthorized)
        response = None
        try:
            response = super(APIView, self).dispatch(*args, **kwargs)
        except Exception as exception:
            # TODO : log this exception
            response = self.error("Server error", "Internal server error", HttpResponseServerError)
        return response

    def render_response(self, body, response_class=HttpResponse):
        """Shortcut method to create the response object with the class and body parameters and the correct content type."""
        return response_class(body, self.content_type)

    def get_context_data(self, **kwargs):
        """Populates the form in the context if the inheriting class has specified a form"""
        context = super(APIView, self).get_context_data(**kwargs)
        # FUTURE: what if we want to use several form classes?
        if self.form_class:
            form_class = self.get_form_class()
            context['form'] = self.get_form(self.form_class)
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
            body = self.serialize(data, include_last_strip=True)
        else:
            simple = "simple" in kwargs.keys()
            body = self.serialize(list(active_comics()), include_last_strip=(not simple), identifier="comics")
        return self.render_response(body)

class StripsView(APIView):
    """Handles information about a comic strip."""

    def __init__(self, **kwargs):
        super(StripsView, self).__init__(**kwargs)
        self.form_class = StripForm

    @parse_param('strip_id')
    def get(self, request, **kwargs):
        """Get information about a certain strip."""
        try:
            strip = ComicHistory.objects.get(pk=self.strip_id)
        except:
            return self.error("NotFound", "That strip does not exist", HttpResponseNotFound)
        body = self.serialize(strip)
        return self.render_response(body)

    @write_required
    @parse_param('strip_id')
    def put(self, request, **kwargs):
        """Mark this strip as unread for the user doing the request."""
        try:
            strip = ComicHistory.objects.get(pk=self.strip_id)
        except:
            return self.error("NotFound", "The strip does not exist", HttpResponseNotFound)
        if not request.user.operations.is_subscribed(strip.comic):
            return self.error("BadRequest", "You are not subscribed to this comic")
        request.user.unreadcomic_set.create(user=request.user, comic=strip.comic, history=strip)
        return HttpResponseNoContent(content_type=self.content_type)

    @write_required
    @parse_param('strip_id')
    def delete(self, request, **kwargs):
        """Mark this strip as read for the user doing the request."""
        try:
            strip = ComicHistory.objects.get(pk=self.strip_id)
        except:
            return self.error("NotFound", "The strip does not exist", HttpResponseNotFound)
        if not request.user.operations.is_subscribed(strip.comic):
            return self.error("BadRequest", "You are not subscribed to this comic")
        request.user.unreadcomic_set.filter(history__id=self.strip_id).delete()
        return HttpResponseNoContent(content_type=self.content_type)

class SubscriptionsView(APIView):
    """Handles comic subscriptions. Add, modify or remove subscriptions to comics."""

    def get(self, request, **kwargs):
        """Get all the comics the user is following including the last strip fetched."""
        subs = request.user.operations.subscribed_comics()
        body = self.serialize(subs, include_last_strip=True, identifier='subscriptions')
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
        if isinstance(body, ET.Element):
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
        return HttpResponseNoContent(content_type=self.content_type)

    @write_required
    def put(self, request, **kwargs):
        """Modify the order of the subscribed comics.

        All the subscriptions will be ordered following the order of the IDs given in the body.

        Subscription/unsubscription operations should be done with this method.
        """
        if not request.processed_body:
            return self.error("BadRequest", "The request body is not valid")

        body = request.processed_body
        requested_idx = list()
        if isinstance(body, ET.Element):
            # this is a XML request
            if body.tag != 'subscriptions':
                return self.error("BadRequest", "The request XML body is not valid")
            try:
                for comicid in body.findall('comicid'):
                    requested_idx.append(int(comicid.text))
            except:
                return self.error("BadRequest", "Invalid comic ID list")
        else:
            # this should be a JSON request
            if 'subscriptions' not in body.keys():
                return self.error("BadRequest", "The request JSON body is not valid")
            try:
                requested_idx = [int(x) for x in body['subscriptions']]
            except:
                return self.error("BadRequest", "Invalid comic ID list")

        # 1. Remove possible duplicates from the input
        # These are all the comics the user wants to follow and in this order
        requested_idx_clean = []
        [requested_idx_clean.append(comic_id) for comic_id in requested_idx if comic_id not in requested_idx_clean]

        # 2. Get the comics the user is currently following
        current_active_idx = [comic.id for comic in request.user.operations.subscribed_comics()]

        # 3. Find comics to be removed
        deleted_idx = [comic_id for comic_id in current_active_idx if comic_id not in requested_idx_clean]
        request.user.operations.unsubscribe_comics(deleted_idx)

        # 4. Find comics to be added
        added_idx = [comic_id for comic_id in requested_idx_clean if comic_id not in current_active_idx]
        request.user.operations.subscribe_comics(added_idx)

        # 5. Update the position of the subcriptions
        subscribed_all = request.user.operations.subscribed_all()
        subscribed_all_dict = dict([(subscription.comic.id, subscription) for subscription in subscribed_all])

        if len(subscribed_all) < requested_idx_clean:
            # We have already added/removed the comics so this should never happen, something must have gone wrong.
            HttpResponse(status=500, content_type=self.content_type)

        position = 0
        for comic_id in requested_idx_clean:
            subscription = subscribed_all_dict[comic_id]
            subscription.position = position
            subscription.save()
            position += 1

        return HttpResponseNoContent(content_type=self.content_type)

    @write_required
    def delete(self, request, **kwargs):
        """Remove all the subscriptions, returning a list with the IDs of the comics the user used to follow."""
        subscribed_idx = [c.id for c in request.user.operations.subscribed_comics()]
        body = self.serialize(subscribed_idx, identifier="removed_subscriptions")
        request.user.operations.unsubscribe_all_comics()
        return self.render_response(body)

class UnreadsView(APIView):
    """Handles a user's unread comics.
    
    Mark comics as read or unread.
    """

    def __init__(self, **kwargs):
        super(UnreadsView, self).__init__(**kwargs)
        self.form_class = VoteForm

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
                body = self.serialize(comic, include_unread_strips=True)
            else:
                return self.error("BadRequest", "You are not subscribed to this comic")
        else:
            last_strip = 'with_strips' in context.keys()
            unreads = request.user.operations.unread_comics()
            body = self.serialize(unreads, include_last_strip=last_strip, identifier='unreads')

        return self.render_response(body)

    @write_required
    def post(self, request, **kwargs):
        """Mark a comic as unread."""
        context = self.get_context_data(**kwargs)

        # Do not allow POST if there is not comic id
        # TODO: wtf
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

        return HttpResponseNoContent(content_type=self.content_type)

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
        request.user.operations.mark_comic_read(comic, vote=vote)
        return HttpResponseNoContent(content_type=self.content_type)

    @write_required
    def delete(self, request, **kwargs):
        """Mark all comics as read."""
        context = self.get_context_data(**kwargs)
        if 'comic_id' not in context.keys():
            # Mark all comics as read
            request.user.operations.mark_all_read()
        else:
            # Mark just the one comic
            comic_id = context['comic_id']
            try:
                comic = Comic.objects.get(pk=comic_id)
            except:
                return self.error("NotFound", "Comic does not exist", HttpResponseNotFound)
            request.user.operations.mark_comic_read(comic)
        return HttpResponseNoContent(content_type=self.content_type)

class UserView(APIView):
    """Handles some user information."""

    def get(self, request, **kwargs):
        """Get some user information."""
        body = self.serialize()
        return self.render_response(body)
