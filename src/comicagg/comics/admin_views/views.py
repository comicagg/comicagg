from django.contrib import admin
from django.http import HttpRequest
from django.shortcuts import render
from django.utils.translation import gettext as _

from comicagg.comics.models import Comic, ComicHistory
from comicagg.comics.update import update_comic


def docs_custom_update(request: HttpRequest):
    """Show the custom update function documentation."""
    request.current_app = "comics"
    context = dict(admin.site.each_context(request))
    context["title"] = _("Docs - Custom update")
    return render(request, "admin/custom_func.html", context)


def admin_update_view(request: HttpRequest, comic_id=0):
    """Trigger an an update for a comic.
    If a comic_id is passed as parameter it will update that comic.
    If no comic_id is passed, it will show the list of comics to update.
    """
    request.current_app = "comics"
    context = dict(admin.site.each_context(request))
    context["title"] = _("Update comic")
    # create a dict with the initials of the comics.
    # so {'a':list, 'b':list, ...}
    comic_list = Comic.objects.all().order_by("name")
    comic_dict = {}
    for comic in comic_list:
        initial = comic.name[0].upper()
        if initial in comic_dict:
            comic_dict[initial].append(comic)
        else:
            comic_dict[initial] = [comic]
    context["list"] = comic_dict
    if comic_id:
        # if a comic_id is passed, update that comic
        comic = Comic.objects.get(pk=comic_id)
        context["last"] = comic
        context["changed"] = update_comic(comic)
    return render(request, "admin/update_comic.html", context)


def admin_reported(request: HttpRequest, id_list: str):
    """Show a page with the images of the reported strips."""
    request.current_app = "comics"
    context = dict(admin.site.each_context(request))
    context["title"] = _("Review reported images")
    strip_list_url = list(map(int, id_list.split("-")))
    strips = ComicHistory.objects.in_bulk(strip_list_url)
    strip_ids = {id: strips.get(id, None) for id in strip_list_url}
    context["strips"] = strip_ids
    return render(request, "admin/reported.html", context)
