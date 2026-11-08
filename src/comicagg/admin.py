from django.apps import apps
from django.contrib import admin
from django.core.exceptions import PermissionDenied
from django.template.response import TemplateResponse
from django.urls import path, re_path
from django.utils.translation import gettext as _

from comics.admin_views import views as admin_views


class ComicaggAdminSite(admin.AdminSite):
    site_header = "Comicagg Admininstration"
    site_title = "Comicagg Admin"

    def get_urls(self):
        urls = super().get_urls()
        more_urls = [
            path(
                "database-statistics/",
                self.admin_view(self.database_statistics),
                name="database_statistics",
            ),
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

    def database_statistics(self, request):
        if not request.user.is_superuser:
            raise PermissionDenied

        statistics = [
            {
                "model": model._meta.label,
                "table": model._meta.db_table,
                "count": model._base_manager.count(),
            }
            for model in sorted(
                apps.get_models(include_auto_created=True),
                key=lambda model: model._meta.label_lower,
            )
            if model._meta.managed and not model._meta.proxy
        ]
        request.current_app = self.name
        context = {
            **self.each_context(request),
            "title": _("Database statistics"),
            "statistics": statistics,
        }
        return TemplateResponse(request, "admin/database_statistics.html", context)
