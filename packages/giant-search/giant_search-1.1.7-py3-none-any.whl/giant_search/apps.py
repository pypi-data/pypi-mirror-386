from django.apps import AppConfig



class GiantSearchAppConfig(AppConfig):
    name = "giant_search"

    def ready(self) -> None:
        from . import signals

