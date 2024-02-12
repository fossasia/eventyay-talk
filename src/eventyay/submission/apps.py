from django.apps import AppConfig


class SubmissionConfig(AppConfig):
    name = "eventyay.submission"

    def ready(self):
        from . import exporters  # noqa
        from . import permissions  # noqa
        from . import signals  # noqa
