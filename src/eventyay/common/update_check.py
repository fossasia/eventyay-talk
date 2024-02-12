import datetime as dt
import sys
import uuid

import requests
from django.conf import settings
from django.dispatch import receiver
from django.urls import reverse
from django.utils.timezone import now
from django.utils.translation import gettext_lazy as _
from django.utils.translation import gettext_noop
from django_scopes import scopes_disabled
from i18nfield.strings import LazyI18nString

from eventyay import __version__ as pretalx_version
from eventyay.celery_app import app
from eventyay.common.mail import mail_send_task
from eventyay.common.models.settings import GlobalSettings
from eventyay.common.plugins import get_all_plugins
from eventyay.common.signals import minimum_interval, periodic_task
from eventyay.event.models import Event


@receiver(signal=periodic_task)
@minimum_interval(minutes_after_success=60 * 23)
def run_update_check(sender, **kwargs):
    gs = GlobalSettings()
    if not gs.settings.update_check_enabled:
        return

    if (
        not gs.settings.update_check_last
        or now() - gs.settings.update_check_last > dt.timedelta(hours=23)
    ):
        update_check.apply_async()


@app.task
@scopes_disabled()
def update_check():
    gs = GlobalSettings()

    if not gs.settings.update_check_enabled:
        return

    if not gs.settings.update_check_id:
        gs.settings.set("update_check_id", uuid.uuid4().hex)

    if "runserver" in sys.argv:  # pragma: no cover
        gs.settings.set("update_check_last", now())
        gs.settings.set("update_check_result", {"error": "development"})
        return

    check_payload = {
        "id": gs.settings.update_check_id,
        "version": pretalx_version,
        "events": {
            "total": Event.objects.count(),
            "public": Event.objects.filter(is_public=True).count(),
        },
        "plugins": [
            {"name": p.module, "version": p.version} for p in get_all_plugins()
        ],
    }
    try:
        response = requests.post(
            "https://eventyay.com/.update_check/",
            json=check_payload,
        )
    except requests.RequestException:  # pragma: no cover
        gs.settings.set("update_check_last", now())
        gs.settings.set("update_check_result", {"error": "unavailable"})
        return

    gs.settings.set("update_check_last", now())
    if response.status_code != 200:
        gs.settings.set("update_check_result", {"error": "http_error"})
        return

    rdata = response.json()
    update_available = rdata["version"]["updatable"] or any(
        p["updatable"] for p in rdata["plugins"].values()
    )
    gs.settings.set("update_check_result_warning", update_available)
    if update_available and rdata != gs.settings.update_check_result:
        send_update_notification_email()
    gs.settings.set("update_check_result", rdata)


def send_update_notification_email():
    gs = GlobalSettings()
    if not gs.settings.update_check_email:
        return

    mail_send_task.apply_async(
        kwargs={
            "to": [gs.settings.update_check_email],
            "subject": _("eventyay update available"),
            "body": str(
                LazyI18nString.from_gettext(
                    gettext_noop(
                        "Hi!\n\nAn update is available for eventyay or for one of the plugins you installed in your "
                        "eventyay installation at {base_url}.\nPlease follow this link for more information:\n\n {url} \n\n"
                        "You can always find information on the latest updates in the changelog:\n\n"
                        "  https://docs.eventyay.org/changelog.html\n\n"
                        "Larger updates are also announced with upgrade notes on the eventyay.com blog:\n\n"
                        "  https://eventyay.com/p/news"
                        "\n\nBest regards,\nyour eventyay developers"
                    ),
                )
            ).format(
                base_url=settings.SITE_URL,
                url=settings.SITE_URL + reverse("orga:admin.update"),
            ),
            "html": None,
        }
    )


def check_result_table():
    gs = GlobalSettings()
    res = gs.settings.update_check_result
    if not res:
        return {"error": "no_result"}

    if "error" in res:
        return res

    table = []
    table.append(
        (
            "eventyay",
            pretalx_version,
            res["version"]["latest"],
            res["version"]["updatable"],
        )
    )
    for p in get_all_plugins():
        if p.module in res["plugins"]:
            pdata = res["plugins"][p.module]
            table.append(
                (
                    _("Plugin: {}").format(p.name),
                    p.version,
                    pdata["latest"],
                    pdata["updatable"],
                )
            )
        else:
            table.append((_("Plugin: {}").format(p.name), p.version, "?", False))

    return table
