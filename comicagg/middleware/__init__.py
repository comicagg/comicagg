# -*- coding: utf-8 -*-
from comicagg import render
from comicagg.logs import logmsg
from django.conf import settings
from django.http import HttpResponse
from django.views.debug import technical_500_response
from provider import constants
from provider.forms import OAuthValidationError
from provider.oauth2.models import AccessToken
import comicagg.logs.tags as logtags
import datetime, logging, re, sys

logger = logging.getLogger(__name__)

class UserBasedExceptionMiddleware(object):
    def process_exception(self, request, exception):
        try:
            user = request.user
        except:
            user = None
        if user and user.is_superuser:
            return technical_500_response(request, *sys.exc_info())

class MaintenanceMiddleware(object):
    def process_request(self, request):
        try:
            user = request.user
        except:
            user = None
        if user.is_authenticated():
            if settings.MAINTENANCE and not(user.is_superuser):
                return render(request, "maintenance.html", {})
        return None

class ActiveUserMiddleware(object):
    def process_request(self, request):
        try:
            user = request.user
        except:
            user = None
        if user.is_authenticated():
            # Update the user's profile last access time
            # We do it here so all requests can be traced (api, web, etc)
            profile = request.user.get_profile()
            profile.last_read_access = datetime.datetime.now()
            profile.save()

            # Check if the user is active or not and redirect to the reactivate page.
            if not user.is_active:
                try:
                    request.POST['activate']
                except:
                    return render(request, "accounts/activate.html", {})

mime_valid = re.compile('[\w]+/[\w.\-+]+')

class AcceptHeaderProcessingMiddleware(object):
    def process_request(self, request):
        request.accept_list = list()
        if 'HTTP_ACCEPT' in request.META.keys():
            accept_str = request.META["HTTP_ACCEPT"]
            l = accept_str.split(',')
            request.accept_list = [ct.strip() for ct in l if mime_valid.match(ct.strip())]


class OAuth2Middleware(object):
    """
    Will set request.user and request.access_token according to the Authorization header
    If access_token is not valid, it will return a 400
    """
    def process_request(self, request):
        request.access_token = None
        if not request.user.is_authenticated():
            if not request.path.startswith('/api'):
                return None
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
                return HttpResponse(sys.exc_info()[1], status=400, content_type="application/json;charset=UTF-8")
        else:
            # Request authenticated by session
            request.scope = getattr(constants, 'WRITE')

    def authenticate(self, request):
        try:
            access_token_str = request.META["HTTP_AUTHORIZATION"]
        except KeyError:
            logger.debug(logmsg(logtags.API_NO_AUTH_HEADER, "Request without Authorization header."))
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
        logger.debug(logmsg(logtags.API_AUTH_OK, "Request successfully authenticated. Username=" + access_token.user.username))
        return access_token
