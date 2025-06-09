from django.apps import AppConfig


class PersonConfig(AppConfig):
    name = "pretalx.person"

    def ready(self):
        from . import rules  # NOQA
        from . import signals  # noqa
        from . import tasks  # NOQA
