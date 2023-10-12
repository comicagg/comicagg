from django.contrib.admin.apps import AdminConfig


class ComicaggAdminConfig(AdminConfig):
    default_site = "comicagg.admin.ComicaggAdminSite"
