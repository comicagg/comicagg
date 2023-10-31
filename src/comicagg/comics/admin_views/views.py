# -*- coding: utf-8 -*-
from typing import Optional
from comicagg.comics.models import Comic, ComicHistory
from comicagg.comics.update import update_comic
from comicagg.utils import render
from django.contrib.admin import AdminSite
from django.contrib.auth.decorators import login_required
from django.http import Http404, HttpRequest
from django.utils.translation import gettext as _


@login_required
def admin_update_view(request: HttpRequest, admin_site: AdminSite, comic_id=None):
    """Trigger an an update for a comic.
    If a comic_id is passed as parameter it will update that comic.
    If no comic_id is passed, it will show the list of comics to update.
    """
    if request.user.is_staff:
        request.current_app = "comics"
        context = dict(admin_site.each_context(request))
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
        context["title"] = _("Update comic")
        return render(request, "admin/update_comic.html", context)
    raise Http404


def admin_reported(request: HttpRequest, admin_site: AdminSite, id_list: str):
    """See the strips reported.
    Present a page with the images of the reported strips.
    """
    if request.user.is_staff:
        request.current_app = "comics"
        ch_list = list(map(int, id_list.split("-")))
        objects = ComicHistory.objects.in_bulk(ch_list)
        ids = {id: objects.get(id, None) for id in ch_list}
        context = {"chs": ids}
        return render(request, "admin/reported.html", context)
    raise Http404
