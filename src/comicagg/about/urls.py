from django.urls import path
from django.views.generic.base import TemplateView

view_contact = TemplateView.as_view(template_name="about/index.html")
view_privacy = TemplateView.as_view(template_name="about/privacy.html")
view_cookies = TemplateView.as_view(template_name="about/cookies.html")

app_name = "about"
urlpatterns = [
    path("", view_contact, name="index"),
    path("privacy/", view_privacy, name="privacy"),
    path("cookies/", view_cookies, name="cookies"),
]
