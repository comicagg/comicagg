from django.contrib import admin
from django.template.response import TemplateResponse
from django.urls import re_path

from comicagg.comics.admin_views import views as admin_views


class ComicaggAdminSite(admin.AdminSite):
    site_header = "Comicagg Admininstration"
    site_title = "Comicagg Admin"

    def get_urls(self):
        urls = super().get_urls()
        more_urls = [
            re_path(
                r"^update/((?P<comic_id>\d+)/)?$",
                self.admin_view(admin_views.admin_update_view),
                {"admin_site": self},
                name="update_comics"
            )
        ]
        return more_urls + urls

    def my_view(self, request):
        # ...
        context = dict(
            # Include common variables for rendering the admin template.
            self.each_context(request),
            # Anything else you want in the context...
        )
        return TemplateResponse(request, "admin/reported.html", context)
