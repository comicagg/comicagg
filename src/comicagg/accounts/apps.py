from django.apps import AppConfig


class AccountsConfig(AppConfig):
    name = "comicagg.accounts"
    verbose_name = "User accounts"

    def ready(self):
        from . import receivers
