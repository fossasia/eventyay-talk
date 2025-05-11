from django.http import Http404
from rest_framework import viewsets

from pretalx.api.mixins import PretalxViewSetMixin
from pretalx.api.serializers import LegacyScheduleSerializer
from pretalx.api.serializers.schedule import ScheduleListSerializer
from pretalx.schedule.models import Schedule


class ScheduleViewSet(PretalxViewSetMixin, viewsets.ReadOnlyModelViewSet):
    serializer_class = LegacyScheduleSerializer
    queryset = Schedule.objects.none()
    lookup_value_regex = "[^/]+"
    endpoint = "schedules"

    def get_unversioned_serializer_class(self):
        if self.action == "list":
            return ScheduleListSerializer
        return LegacyScheduleSerializer  # self.action == 'retrieve'

    def get_object(self):
        schedules = self.get_queryset()
        query = self.kwargs.get(self.lookup_field)
        if query == "wip":
            schedule = schedules.filter(version__isnull=True).first()
        else:
            if query == "latest" and self.request.event.current_schedule:
                query = self.request.event.current_schedule.version
            schedule = schedules.filter(version__iexact=query).first()
        if not schedule:
            raise Http404
        return schedule

    def get_queryset(self):
        qs = self.queryset
        is_public = (
            self.request.event.is_public
            and self.request.event.get_feature_flag("show_schedule")
        )
        current_schedule = (
            self.request.event.current_schedule.pk
            if self.request.event.current_schedule
            else None
        )
        if self.request.user.has_perm("orga.view_schedule", self.request.event):
            return self.request.event.schedules.all()
        if is_public:
            return self.request.event.schedules.filter(pk=current_schedule)
        return qs
