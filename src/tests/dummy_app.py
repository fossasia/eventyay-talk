from django.apps import AppConfig


class PluginApp(AppConfig):
    name = "tests"
    verbose_name = "test app for eventyay"

    def ready(self):
        from .dummy_signals import footer_link_test  # noqa

    def is_available(self, event):
        return event != "totally hidden"

    class EventyayPluginMeta:
        name = "test plugin for eventyay"
        author = "Tobias Kunze"
        description = "Helps to test plugin related things for eventyay"
        visible = True
        version = "0.0.0"
