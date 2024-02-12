from django.apps import AppConfig


class CfPConfig(AppConfig):
    name = "eventyay.cfp"

    def ready(self):
        from . import permissions  # noqa
        from .phrases import CfPPhrases  # noqa
