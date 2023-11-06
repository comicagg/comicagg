from django.http import HttpResponse
from django.template.loader import render_to_string


def render(
    request,
    template,
    context,
    menu=None,
    xml=False,
    responseClass=HttpResponse,
    mime='text/html; charset="utf-8"',
):
    """
    Used to provide additional context variables to a template in order to render common items.
    """
    context["menu"] = menu

    resp_text = render_to_string(template, context, request)
    response = responseClass(resp_text, content_type=mime)
    if xml:
        response = responseClass(resp_text, content_type='text/xml; charset="utf-8"')
    response["Cache-Control"] = "max-age=1"
    response["Expires"] = "-1"
    return response
