import importlib
from contextlib import suppress

from django.apps import apps
from django.conf import settings
from django.conf.urls.static import static
from django.urls import include, path

from eventyay.common.views import error_view

plugin_patterns = []
for app in apps.get_app_configs():
    if getattr(app, "EventyayPluginMeta", None):
        if importlib.util.find_spec(app.name + ".urls"):
            urlmod = importlib.import_module(app.name + ".urls")
            single_plugin_patterns = []
            urlpatterns = getattr(urlmod, "urlpatterns", None)
            if urlpatterns:
                single_plugin_patterns += urlpatterns
            plugin_patterns.append(
                path("", include((single_plugin_patterns, app.label)))
            )

urlpatterns = [
    path("400", error_view(400)),
    path("403", error_view(403)),
    path("403/csrf", error_view(4031)),
    path("404", error_view(404)),
    path("500", error_view(500)),
    path("orga/", include("eventyay.orga.urls", namespace="orga")),
    path("api/", include("eventyay.api.urls", namespace="api")),
    # Root patterns are ordered by precedence:
    # Plugins last, so that they cannot break anything
    path("", include("eventyay.agenda.urls", namespace="agenda")),
    path("", include("eventyay.cfp.urls", namespace="cfp")),
    path("", include((plugin_patterns, "plugins"))),
]

handler500 = "eventyay.common.views.handle_500"

if settings.DEBUG:
    with suppress(ImportError):
        import debug_toolbar

        urlpatterns += [
            path("__debug__/", include(debug_toolbar.urls)),
        ]
    urlpatterns += static(settings.MEDIA_URL, document_root=settings.MEDIA_ROOT)
