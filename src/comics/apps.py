from django.apps import AppConfig


class AccountsConfig(AppConfig):
    name = "comics"
    verbose_name = "Aggregator"

    def ready(self):
        pass
