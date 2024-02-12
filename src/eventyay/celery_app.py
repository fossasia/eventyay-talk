import os

from celery import Celery

os.environ.setdefault("DJANGO_SETTINGS_MODULE", "eventyay.settings")

from django.conf import settings  # noqa

app = Celery("eventyay")
app.config_from_object("django.conf:settings", namespace="CELERY")
app.autodiscover_tasks(lambda: settings.INSTALLED_APPS)
