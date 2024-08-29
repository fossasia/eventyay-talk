from django.http import Http404
from rest_framework import viewsets

from pretalx.api.serializers.event import EventSerializer
from pretalx.event.models import Event


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
