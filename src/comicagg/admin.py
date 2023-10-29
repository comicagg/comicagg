from comicagg.comics.admin_views import views as admin_views
from django.contrib import admin
from django.urls import path, re_path


class ComicaggAdminSite(admin.AdminSite):
    site_header = "Comicagg Admininstration"
    site_title = "Comicagg Admin"

    def get_urls(self):
        urls = super().get_urls()
        more_urls = [
            path(
                "update/",
                self.admin_view(admin_views.admin_update_view),
                # Send the current AdminSite so that the view can use AdminSite.each_context to get the proper variables
                {"admin_site": self},
                name="update_comics",
            ),
            path(
                "update/<int:comic_id>/",
                self.admin_view(admin_views.admin_update_view),
                {"admin_site": self},
                name="update_comic",
            ),
            re_path(
                r"^reported/(?P<id_list>[\w-]+)/$",
                self.admin_view(admin_views.admin_reported),
                {"admin_site": self},
                name="reported",
            ),
        ]
        return more_urls + urls
