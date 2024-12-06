import logging

import jwt
from django.conf import settings
from django.http import Http404
from django_scopes import scopes_disabled
from pretalx_venueless.forms import VenuelessSettingsForm
from rest_framework import viewsets
from rest_framework.authentication import get_authorization_header
from rest_framework.decorators import (
    api_view,
    authentication_classes,
    permission_classes,
)
from rest_framework.response import Response

from pretalx.api.serializers.event import EventSerializer
from pretalx.common import exceptions
from pretalx.common.exceptions import AuthenticationFailedError
from pretalx.event.models import Event

logger = logging.getLogger(__name__)


class EventViewSet(viewsets.ReadOnlyModelViewSet):
    serializer_class = EventSerializer
    queryset = Event.objects.none()
    lookup_field = "slug"
    lookup_url_kwarg = "event"
    pagination_class = None
    permission_required = "cfp.view_event"

    def get_queryset(self):
        return [
            event
            for event in Event.objects.all().order_by("-date_from")
            if self.request.user.has_perm(self.permission_required, event)
        ]

    def get_object(self):
        if self.request.user.has_perm(self.permission_required, self.request.event):
            return self.request.event
        raise Http404()


@api_view(http_method_names=["POST"])
@authentication_classes([])
@permission_classes([])
def configure_video_settings(request):
    """
    Configure video settings for an event
    @param request: request object
    @return response object
    """
    video_settings = request.data.get("video_settings")
    payload = get_payload_from_token(request, video_settings)
    event_slug = payload.get("event_slug")
    video_tokens = payload.get("video_tokens")

    if not video_tokens:
        raise ValueError("Video tokens not found in the payload")

    try:
        with scopes_disabled():
            event_instance = Event.objects.get(slug=event_slug)
            save_video_settings_information(event_slug, video_tokens, event_instance)
    except Event.DoesNotExist:
        logger.error("Event with slug %s does not exist.", event_slug)
        return Response(
            {
                "status": "error",
                "message": "Event with slug {} not found.".format(event_slug),
            },
            status=404,
        )
    except ValueError as e:
        logger.error("Error configuring video settings: %s", e)
        return Response(
            {"status": "error", "message": "Error configuring video settings."},
            status=400,
        )
    except AuthenticationFailedError as e:
        logger.error("Authentication failed: %s", e)
        return Response(
            {"status": "error", "message": "Authentication failed."}, status=401
        )


def get_payload_from_token(request, video_settings):
    """
    Verify the token and return the payload
    @param request: request object
    @param video_settings: dict containing video settings
    @return: dict containing payload data from the token
    """
    try:
        auth_header = get_authorization_header(request).split()
        if not auth_header:
            raise exceptions.AuthenticationFailedError("No authorization header")

        if len(auth_header) != 2 or auth_header[0].lower() != b"bearer":
            raise exceptions.AuthenticationFailedError(
                "Invalid token format. Must be 'Bearer <token>'"
            )

        token_decode = jwt.decode(
            auth_header[1], video_settings.get("secret"), algorithms=["HS256"]
        )

        event_slug = token_decode.get("slug")
        video_tokens = token_decode.get("video_tokens")

        if not event_slug or not video_tokens:
            raise exceptions.AuthenticationFailedError("Invalid token payload")

        return {"event_slug": event_slug, "video_tokens": video_tokens}

    except jwt.ExpiredSignatureError:
        raise exceptions.AuthenticationFailedError("Token has expired")
    except jwt.InvalidTokenError:
        raise exceptions.AuthenticationFailedError("Invalid token")


def save_video_settings_information(event_slug, video_tokens, event_instance):
    video_settings_data = {
        "token": video_tokens[0],
        "url": "{}/api/v1/worlds/{}/".format(
            settings.EVENTYAY_VIDEO_BASE_PATH, event_slug
        ),
    }

    video_settings_form = VenuelessSettingsForm(
        event=event_instance, data=video_settings_data
    )

    if video_settings_form.is_valid():
        video_settings_form.save()
        logger.info("Video settings configured successfully for event %s.", event_slug)
        return Response({"status": "success"}, status=200)
    else:
        logger.error(
            "Failed to configure video settings for event %s - Validation errors: %s.",
            event_slug,
            video_settings_form.errors,
        )
        return Response(
            {
                "status": "error",
                "message": "Validation errors",
                "errors": video_settings_form.errors,
            },
            status=400,
        )
