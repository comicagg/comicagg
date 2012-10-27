# Create your views here.
from provider.views import OAuthView, Mixin
from django.http import HttpResponse
from django.views.generic.base import TemplateView
from provider.oauth2.models import AccessToken
from django.contrib.auth.models import AnonymousUser
from provider.forms import OAuthValidationError
import datetime, sys

#Custom app to try and authorize clients

def OAuth2UserFromAuthorizationToken(f):
    def authenticate(request):
        u = AnonymousUser()
        try:
            access_token_str = request.META["HTTP_AUTHORIZATION"]
        except KeyError:
            return u
        access_token = None
        try:
            access_token = AccessToken.objects.get(token=access_token_str)
        except:
            print "There was an error: ", sys.exc_info()
        
        if access_token:
             td = access_token.expires - datetime.datetime.now()
             tds = (td.microseconds + (td.seconds + td.days * 24 * 3600) * 10**6) / 10**6
             if tds < 0:
                  raise OAuthValidationError({
                      "error": "invalid_grant", 
                      "error_description": "Your token has expired."})
             u = access_token.user
        return u

    def new_f(klass, request):
        try:
            request.user = authenticate(request)
            if request.user == AnonymousUser:
                return HttpResponse()
        except OAuthValidationError:
            return HttpResponse(sys.exc_info(), status=400, content_type="application/json;charset=UTF-8")
        return f(klass, request)
    
    return new_f

class IndexView(TemplateView):
    template_name = "index.html"

    @OAuth2UserFromAuthorizationToken
    def get(self, request):
        return HttpResponse("GET user: " + str(request.user))

    @OAuth2UserFromAuthorizationToken
    def post(self, request):
        return HttpResponse("POST user: " + str(request.user))

    @OAuth2UserFromAuthorizationToken
    def put(self, request):
        return HttpResponse("PUT user: " + str(request.user))

    @OAuth2UserFromAuthorizationToken
    def delete(self, request):
        return HttpResponse("DELETE user: " + str(request.user))

