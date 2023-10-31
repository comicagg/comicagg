"""View classes to render API responses."""

import logging
import xml.etree.ElementTree as ET
from typing import Dict, Type

import comicagg.logs.tags as logtags
from comicagg.api.decorators import body_not_empty, request_param, write_required
from comicagg.api.forms import StripForm, SubscriptionForm, VoteForm
from comicagg.api.serializer import Serializer
from comicagg.comics.models import Comic, ComicHistory, active_comics
from comicagg.comics.utils import ComicsService
from comicagg.logs import logmsg
from django.db import transaction
from django.http import (
    HttpRequest,
    HttpResponse,
    HttpResponseBadRequest,
    HttpResponseNotAllowed,
    HttpResponseNotFound,
    HttpResponseServerError,
    JsonResponse,
)
from django.views.generic import View
from django.views.generic.edit import FormMixin

logger = logging.getLogger(__name__)

# Helper classes


class HttpResponseUnauthorized(HttpResponse):
    status_code = 401


class HttpResponseCreated(HttpResponse):
    status_code = 201


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

    @transaction.atomic
    def dispatch(self, *args, **kwargs):
        """Handle exception from the specific verb methods."""
        request = args[0]
        logger.debug("API call: %s %s", request.method, request.path)

        self.serialize = Serializer(request.user).serialize

        if not request.user.is_authenticated:
            return self.response_error(
                "You need to log in to access this resource",
                "Unauthorized",
                HttpResponseUnauthorized,
            )
        response = None
        try:
            response = super(APIView, self).dispatch(*args, **kwargs)
        except Exception as exception:
            # TODO : log this exception
            response = self.response_error(
                "Internal Server error", "ServerError", HttpResponseServerError
            )
        return response

    def get_context_data(self, **kwargs):
        """Populates the form in the context if the inheriting class has specified a form"""
        context = super(APIView, self).get_context_data(**kwargs)
        if "form" in context.keys():
            self.form = context["form"]
        return context

    def response_error(
        self,
        description="",
        name="BadRequest",
        error_class: Type[HttpResponse] = HttpResponseBadRequest,
    ):
        """Render an error response."""
        logger.debug("Returning an error (%s): %s", name, description)
        data = {"error": name, "description": description}
        body = self.serialize(data, identifier="error")
        return self.response_content(body, response_class=error_class)

    def response_not_found(self, message: str):
        return self.response_error(message, "NotFound", HttpResponseNotFound)

    def response_no_content(self):
        return HttpResponseNoContent(content_type=self.content_type)

    def response_created(self):
        return HttpResponseCreated(content_type=self.content_type)

    def response_content(
        self, data: Dict, response_class: Type[HttpResponse] = JsonResponse
    ):
        """Helper method to wrap the response data."""
        # FUTURE: we may want to change this so that we can change the status code in meta
        final_data = self.wrap_data(data)
        return response_class(final_data)

    def wrap_data(self, data: Dict):
        """In case we want to do JSONP in the future."""
        return {"meta": {"status": 200, "text": "OK", "response": data}}


class IndexView(APIView):
    """Welcome view."""

    def get(self, request: HttpRequest):
        data = {
            "message": f"Hello {request.user.username}.",
            "message2": "This is the comicagg API.",
        }
        body = self.serialize(data, identifier="welcome")
        return self.response_content(body)


class ComicsView(APIView):
    """Handles general comic related stuff.
    Get information about all the comics available in the service."""

    @request_param("comic_id")  # url path
    def get(self, request: HttpRequest, **kwargs):
        """Get information about a specific comic or all the comics
        and optionally return the last strip fetched of the comics."""
        # if self.comic_id is not None:
        if hasattr(self, "comic_id"):
            try:
                data = Comic.objects.get(pk=getattr(self, "comic_id"))
                if not data.active and not data.ended:
                    return self.response_not_found("The comic is disabled")
            except Exception:
                return self.response_not_found("The comic does not exist")
            body = self.serialize(data, include_last_strip=True)
        else:
            simple = "simple" in kwargs
            body = self.serialize(
                list(active_comics()),
                include_last_strip=(not simple),
                identifier="comics",
            )
        return self.response_content(body)


class StripsView(APIView):
    """Handles information about a comic strip."""

    def __init__(self, **kwargs):
        super(StripsView, self).__init__(**kwargs)
        self.form_class = StripForm

    @request_param("strip_id")  # url path
    def get(self, request: HttpRequest, **kwargs):
        """Get information about a certain strip."""
        try:
            strip = ComicHistory.objects.get(pk=getattr(self, "strip_id"))
        except Exception:
            return self.response_not_found("That strip does not exist")
        body = self.serialize(strip)
        return self.response_content(body)

    @write_required
    @request_param("strip_id")  # url path
    def put(self, request: HttpRequest, **kwargs):
        """Mark this strip as unread for the user doing the request."""
        try:
            strip = ComicHistory.objects.get(pk=getattr(self, "strip_id"))
        except Exception:
            return self.response_not_found("The strip does not exist")
        if not ComicsService(request.user).is_subscribed(strip.comic):
            return self.response_error("You are not subscribed to this comic")
        request.user.unreadcomic_set.create(
            user=request.user, comic=strip.comic, history=strip
        )
        return self.response_no_content()

    @write_required
    @request_param("strip_id")  # url path
    def delete(self, request: HttpRequest, **kwargs):
        """Mark this strip as read for the user doing the request."""
        try:
            strip_id = getattr(self, "strip_id")
            strip = ComicHistory.objects.get(pk=strip_id)
        except Exception:
            return self.response_not_found("The strip does not exist")
        if not ComicsService(request.user).is_subscribed(strip.comic):
            return self.response_error("You are not subscribed to this comic")
        request.user.unreadcomic_set.filter(history__id=strip_id).delete()
        return self.response_no_content()


class SubscriptionsView(APIView):
    """Handles comic subscriptions. Add, modify or remove subscriptions to comics."""

    def __init__(self, **kwargs):
        super(SubscriptionsView, self).__init__(**kwargs)
        self.form_class = SubscriptionForm

    def get(self, request: HttpRequest, **kwargs):
        """Get all the comics the user is following including the last strip fetched."""
        subs = ComicsService(request.user).subscribed_comics()
        body = self.serialize(subs, include_last_strip=True, identifier="subscriptions")
        return self.response_content(body)

    @write_required
    @body_not_empty
    @request_param("subscribe")  # form
    def post(self, request: HttpRequest, **kwargs):
        """Subscribe to several comics.

        The comics will be added at the end of the list of subscriptions.
        """
        if not hasattr(self, "subscribe"):
            return self.response_error("Empty list.")

        subscribe = getattr(self, "subscribe")
        id_list = [int(x) for x in subscribe.split(",") if len(x) > 0]

        # Remove possible duplicates
        id_list_clean = []
        [id_list_clean.append(x) for x in id_list if x not in id_list_clean]
        ComicsService(request.user).subscribe_comics(id_list_clean)
        return self.response_created()

    @write_required
    @body_not_empty
    @request_param("subscriptions")  # PUT body
    def put(self, request: HttpRequest, **kwargs):
        """Modify the order of the subscribed comics.

        All the subscriptions will be ordered with the same order
        of the IDs given in the body.

        Subscription/unsubscription operations can be done with this method.
        """
        # FUTURE: move this to the user operations
        if not hasattr(self, "subscriptions"):
            return self.response_error("Invalid body.")

        subscriptions = getattr(self, "subscriptions")
        subscriptions_split = subscriptions[0].split(",")
        requested_idx = [int(x) for x in subscriptions_split if len(x) > 0]

        # 1. Remove possible duplicates from the input
        # These are all the comics the user wants to follow and in this order
        requested_idx_clean = []
        [
            requested_idx_clean.append(comic_id)
            for comic_id in requested_idx
            if comic_id not in requested_idx_clean
        ]

        # 2. Get the comics the user is currently following
        current_active_idx = [
            comic.id for comic in ComicsService(request.user).subscribed_comics()
        ]

        # 3. Find comics to be removed
        if deleted_idx := [
            comic_id
            for comic_id in current_active_idx
            if comic_id not in requested_idx_clean
        ]:
            ComicsService(request.user).unsubscribe_comics(deleted_idx)

        # 4. Find comics to be added
        if added_idx := [
            comic_id
            for comic_id in requested_idx_clean
            if comic_id not in current_active_idx
        ]:
            ComicsService(request.user).subscribe_comics(added_idx)

        # 5. Update the position of the subcriptions
        subscribed_all = ComicsService(request.user).subscribed_all()
        subscribed_all_dict = dict(
            [(subscription.comic.id, subscription) for subscription in subscribed_all]
        )

        if len(subscribed_all) < len(requested_idx_clean):
            # We have already added/removed the comics so this should never happen
            # something must have gone wrong
            return self.response_error(
                "Internal server error", "ServerError", HttpResponseServerError
            )

        for position, comic_id in enumerate(requested_idx_clean):
            subscription = subscribed_all_dict[comic_id]
            subscription.position = position
            subscription.save()

        return self.response_no_content()

    @write_required
    def delete(self, request: HttpRequest, **kwargs):
        """Remove all the subscriptions, returning a list with the IDs of the comics
        the user used to follow."""
        subscribed_idx = [c.id for c in ComicsService(request.user).subscribed_comics()]
        body = self.serialize(subscribed_idx, identifier="removed_subscriptions")
        ComicsService(request.user).unsubscribe_all_comics()
        return self.response_content(body)


class UnreadsView(APIView):
    """Handles a user's unread comics.

    Mark comics as read or unread.
    """

    def __init__(self, **kwargs):
        super(UnreadsView, self).__init__(**kwargs)
        self.form_class = VoteForm

    @request_param("comic_id")  # url path
    @request_param("with_strips")  # url path
    def get(self, request: HttpRequest, **kwargs):
        """Get the unread comics followed by the user."""
        if hasattr(self, "comic_id"):
            try:
                comic = Comic.objects.get(pk=getattr(self, "comic_id"))
            except Exception:
                return self.response_not_found("Comic does not exist")

            if ComicsService(request.user).is_subscribed(comic):
                body = self.serialize(comic, include_unread_strips=True)
            else:
                return self.response_error("You are not subscribed to this comic")
        else:
            unreads = ComicsService(request.user).unread_comics()
            body = self.serialize(
                unreads,
                include_last_strip=getattr(self, "with_strips"),
                identifier="unreads",
            )

        return self.response_content(body)

    @write_required
    @request_param("comic_id")  # url path
    def post(self, request: HttpRequest, **kwargs):
        """Mark a comic as unread."""
        # Do not allow POST if there is not comic id
        if not hasattr(self, "comic_id"):
            return HttpResponseNotAllowed(["GET"])

        try:
            comic = Comic.objects.get(pk=getattr(self, "comic_id"))
        except Exception:
            return self.response_not_found("Comic does not exist")

        if not ComicsService(request.user).is_subscribed(comic):
            return self.response_error("You are not subscribed to this comic")

        if ComicsService(request.user).mark_comic_unread(comic):
            return self.response_created()
        else:
            return self.response_error(
                "There was an error setting this comic as unread", "ServerError"
            )

    @write_required
    @body_not_empty
    @request_param("comic_id")  # url path
    @request_param("vote")  # form
    def put(self, request: HttpRequest, **kwargs):
        """Mark a comic as read and optionally including a vote in the body."""
        # Do not allow PUT if there is not comic id
        if not hasattr(self, "comic_id"):
            return HttpResponseNotAllowed(["GET"])

        # Vote will be None if there was no vote or it was invalid
        if not hasattr(self, "vote"):
            return self.response_error("Invalid vote parameter")

        try:
            comic = Comic.objects.get(pk=getattr(self, "comic_id"))
        except Exception:
            return self.response_not_found("Comic does not exist")

        if not ComicsService(request.user).is_subscribed(comic):
            return self.response_error("You are not subscribed to this comic")

        # At this point we have confirmed that the comic exists and
        # that the user is subscribed to it
        ComicsService(request.user).mark_comic_read(comic, vote=getattr(self, "vote"))
        return self.response_no_content()

    @write_required
    @request_param("comic_id")  # url path
    def delete(self, request: HttpRequest, **kwargs):
        """Mark all comics as read."""
        if not hasattr(self, "comic_id"):
            # Mark all comics as read
            ComicsService(request.user).mark_all_read()
        else:
            # Mark just the one comic
            try:
                comic = Comic.objects.get(pk=getattr(self, "comic_id"))
            except Exception:
                return self.response_not_found("Comic does not exist")
            ComicsService(request.user).mark_comic_read(comic)
        return self.response_no_content()


class UserView(APIView):
    """Handles some user information."""

    def get(self, request: HttpRequest, **kwargs):
        """Get some user information."""
        body = self.serialize()
        return self.response_content(body)
