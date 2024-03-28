from django.contrib.sites.shortcuts import get_current_site
from django.core.mail import EmailMultiAlternatives
from django.http import HttpRequest
from django.template import loader

from .env import Env


def send_email(
    request: HttpRequest, to_email: str, subject: str, email_template: str, context: dict | None = None
):
    if context is None:
        context = {}
    protocol = "https://" if request.is_secure else "http://"
    current_site = get_current_site(request)
    site_url = protocol + current_site.domain
    final_context = {"site_name": current_site.name, "site_url": site_url}
    final_context |= context
    body = loader.render_to_string(email_template, final_context).strip()
    email_message = EmailMultiAlternatives(subject, body, to=[to_email])
    email_message.send()
