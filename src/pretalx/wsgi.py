"""WSGI config for pretalx.

Use with gunicorn or uwsgi.
"""

import os

os.environ.setdefault("DJANGO_SETTINGS_MODULE", "pretalx.settings")

from django.core.wsgi import get_wsgi_application  # NOQA

application = get_wsgi_application()
