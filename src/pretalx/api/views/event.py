from drf_spectacular.utils import extend_schema, extend_schema_view
from rest_framework import permissions, viewsets

from pretalx.api.documentation import build_search_docs
from pretalx.api.mixins import PretalxViewSetMixin
from pretalx.api.serializers.event import EventListSerializer, EventSerializer
from pretalx.event.models import Event
from pretalx.event.rules import get_events_for_user


@extend_schema_view(
    list=extend_schema(
        summary="List Events", parameters=[build_search_docs("name")], tags=["events"]
    ),
    retrieve=extend_schema(summary="Show Events", tags=["events"]),
)
class EventViewSet(PretalxViewSetMixin, viewsets.ReadOnlyModelViewSet):
    serializer_class = EventSerializer
    queryset = Event.objects.none()
    lookup_field = "slug"
    lookup_url_kwarg = "event"
    pagination_class = None
    permission_classes = [permissions.AllowAny]
    search_fields = ("name",)
    filterset_fields = ("is_public",)

    def get_unversioned_serializer_class(self):
        if self.action == "list":
            return EventListSerializer
        return EventSerializer

    def get_queryset(self):
        return get_events_for_user(self.request.user).order_by("-date_from")
