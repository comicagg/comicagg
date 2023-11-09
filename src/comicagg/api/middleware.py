import logging
import re
import sys
from datetime import datetime, timezone

from django.conf import settings
from django.http import HttpResponse

import comicagg.logs.tags as logtags
from comicagg.logs import logmsg
from provider import constants
from provider.forms import OAuthValidationError
from provider.oauth2.models import AccessToken

from .typings import OAuth2HttpRequest

logger = logging.getLogger(__name__)


class OAuth2Middleware:
    """Authenticates an anonymouse user using the Authorization header.

    Will set request.user and request.access_token according to the Authorization header.
    If access_token is not valid, it will return a 400.
    """

    def __init__(self, get_response):
        self.get_response = get_response

    def __call__(self, request: OAuth2HttpRequest):
        request.access_token = None
        if not request.user.is_authenticated:
            if not request.path.startswith("/api"):
                # Next middleware if anonymous and not /api endpoint
                return self.get_response(request)
            logger.debug("API request not authenticated, trying OAuth2")
            # Try OAuth2 authorization
            try:
                request.access_token = self.authenticate(request)
                if request.access_token:
                    logger.debug("Request authorized by OAuth2 access token")
                    request.user = request.access_token.user
                    request.scope = request.access_token.scope
                    # If the session cookie was in the request and it was not valid, then the Session middleware would send a valid cookie in the response
                    # With this cookie, someone would be able to access the account without limits
                    # For now, OAuth2 is only used in API and we'll not need the request.session
                    if settings.SESSION_COOKIE_NAME in request.COOKIES.keys():
                        request.session = None
            except OAuthValidationError:
                return HttpResponse(
                    sys.exc_info()[1],
                    status=400,
                    content_type="application/json;charset=UTF-8",
                )
        else:
            # Request authenticated by session
            request.scope = getattr(constants, "WRITE")
        return self.get_response(request)

    def authenticate(self, request):
        try:
            access_token_str = request.META["HTTP_AUTHORIZATION"]
        except KeyError:
            logger.debug(
                logmsg(
                    logtags.API_NO_AUTH_HEADER, "Request without Authorization header."
                )
            )
            return None

        # Check the format of the authorization header, must be Bearer
        if not re.match(r"Bearer \w{40}", access_token_str):
            logger.error(
                logmsg(
                    logtags.API_BAD_AUTH_HEADER_FORMAT,
                    "Format of the Authorization header is not valid.",
                )
            )
            return None

        access_token_str = access_token_str.replace("Bearer ", "")
        access_token = None
        try:
            access_token = AccessToken.objects.get(token=access_token_str)
        except:
            logger.warning(
                logmsg(
                    logtags.API_TOKEN_INVALID,
                    "Got Authorization header but no access token was found in the database.",
                )
            )
            return None

        if access_token:
            td = access_token.expires - datetime.now(timezone.utc)
            tds = (
                td.microseconds + (td.seconds + td.days * 24 * 3600) * 10**6
            ) / 10**6
            if tds < 0:
                logger.warning(
                    logmsg(logtags.API_TOKEN_EXPIRED, "The access token has expired")
                )
                raise OAuthValidationError(
                    """{"error": "invalid_grant", "error_description": "Your token has expired."}"""
                )
        logger.debug(
            logmsg(
                logtags.API_AUTH_OK,
                "Request successfully authenticated. Username="
                + access_token.user.username,
            )
        )
        return access_token
