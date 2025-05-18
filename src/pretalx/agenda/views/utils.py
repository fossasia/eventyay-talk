import hashlib
import logging
from contextlib import suppress

from django.http import HttpResponse, HttpResponseNotModified
from django.utils.translation import activate

from pretalx.common.signals import register_data_exporters
from pretalx.common.text.path import safe_filename

logger = logging.getLogger(__name__)


def is_visible(exporter, request, public=False):
    if not public:
        return request.user.has_perm("schedule.orga_view_schedule", request.event)
    if not request.user.has_perm("schedule.list_schedule", request.event):
        return False
    if hasattr(exporter, "is_public"):
        with suppress(Exception):
            return exporter.is_public(request=request)
    return exporter.public


def get_schedule_exporters(request, public=False):
    exporters = [
        exporter(request.event)
        for _, exporter in register_data_exporters.send_robust(request.event)
    ]
    return [
        exporter
        for exporter in exporters
        if (
            not isinstance(exporter, Exception)
            and is_visible(exporter, request, public=public)
        )
    ]


def find_schedule_exporter(request, name, public=False):
    for exporter in get_schedule_exporters(request, public=public):
        if exporter.identifier == name:
            return exporter
    return None


def get_schedule_exporter_content(request, exporter_name, schedule):
    is_organiser = request.user.has_perm("schedule.orga_view_schedule", request.event)
    exporter = find_schedule_exporter(request, exporter_name, public=not is_organiser)
    if not exporter:
        return
    exporter.schedule = schedule
    exporter.is_orga = is_organiser
    lang_code = request.GET.get("lang")
    if lang_code and lang_code in request.event.locales:
        activate(lang_code)
    elif "lang" in request.GET:
        activate(request.event.locale)
    try:
        file_name, file_type, data = exporter.render(request=request)
        etag = hashlib.sha1(str(data).encode()).hexdigest()
    except Exception:
        logger.exception(
            f"Failed to use {exporter.identifier} for {request.event.slug}"
        )
        return
    if request.headers.get("If-None-Match") == etag:
        return HttpResponseNotModified()
    headers = {"ETag": f'"{etag}"'}
    if file_type not in ("application/json", "text/xml"):
        headers["Content-Disposition"] = (
            f'attachment; filename="{safe_filename(file_name)}"'
        )
    if exporter.cors:
        headers["Access-Control-Allow-Origin"] = exporter.cors
    return HttpResponse(data, content_type=file_type, headers=headers)
