from django.contrib import admin
from django.urls import path, re_path

from comicagg.comics.admin_views import views as admin_views


class ComicaggAdminSite(admin.AdminSite):
    site_header = "Comicagg Admininstration"
    site_title = "Comicagg Admin"

    def get_urls(self):
        urls = super().get_urls()
        more_urls = [
            path(
                "docs/custom_update/",
                self.admin_view(admin_views.docs_custom_update),
                name="docs_custom",
            ),
            path(
                "update/",
                self.admin_view(admin_views.admin_update_view),
                name="update_comics",
            ),
            path(
                "update/<int:comic_id>/",
                self.admin_view(admin_views.admin_update_view),
                name="update_comic",
            ),
            re_path(
                r"^reported/(?P<id_list>[\w-]+)/$",
                self.admin_view(admin_views.admin_reported),
                name="reported",
            ),
        ]
        return more_urls + urls
