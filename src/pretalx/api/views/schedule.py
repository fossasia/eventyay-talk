import django_filters.rest_framework
from django.http import Http404, HttpResponse
from django.utils.functional import cached_property
from drf_spectacular.utils import extend_schema, extend_schema_view
from rest_framework import mixins, viewsets
from rest_framework.decorators import action
from rest_framework.filters import SearchFilter

from pretalx.api.documentation import build_expand_docs, build_search_docs
from pretalx.api.filters.schedule import TalkSlotFilter
from pretalx.api.mixins import PretalxViewSetMixin
from pretalx.api.serializers.legacy import LegacyScheduleSerializer
from pretalx.api.serializers.schedule import (
    ScheduleListSerializer,
    TalkSlotOrgaSerializer,
    TalkSlotSerializer,
)
from pretalx.schedule.models import Schedule, TalkSlot


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
            if query == "latest" and self.event.current_schedule:
                query = self.event.current_schedule.version
            schedule = schedules.filter(version__iexact=query).first()
        if not schedule:
            raise Http404
        return schedule

    def get_queryset(self):
        if not self.event:
            return self.queryset
        is_public = self.event.is_public and self.event.get_feature_flag(
            "show_schedule"
        )
        current_schedule = (
            self.event.current_schedule.pk if self.event.current_schedule else None
        )
        if self.request.user.has_perm("orga.view_schedule", self.event):
            return self.event.schedules.all()
        if is_public:
            return self.event.schedules.filter(pk=current_schedule)
        return self.queryset


@extend_schema_view(
    list=extend_schema(
        summary="List Talk Slots",
        description="This endpoint always returns a filtered list. If you don’t provide any filters of your own, it will be filtered to show only talk slots in the latest published schedule.",
        parameters=[
            build_search_docs("submission.title", "submission.speakers.name"),
            build_expand_docs(
                "room",
                "schedule",
                "submission",
                "submission.speakers",
                "submission.track",
                "submission.submission_type",
                "submission.answers",
                "submission.answers.question",
                "submission.resources",
            ),
        ],
    ),
    retrieve=extend_schema(
        summary="Show Talk Slot",
        parameters=[
            build_expand_docs(
                "room",
                "schedule",
                "submission",
                "submission.speakers",
                "submission.track",
                "submission.submission_type",
                "submission.answers",
                "submission.answers.question",
                "submission.resources",
            )
        ],
    ),
    update=extend_schema(
        summary="Update Talk Slot",
        description="Only talk slots in the WIP schedule can be changed – once a schedule version is frozen, its talk slots can’t be modified anymore.",
    ),
    partial_update=extend_schema(
        summary="Update Talk Slot (Partial Update)",
        description="Only talk slots in the WIP schedule can be changed – once a schedule version is frozen, its talk slots can’t be modified anymore.",
    ),
    ical=extend_schema(summary="Export Talk Slot as iCalendar file"),
)
class TalkSlotViewSet(
    PretalxViewSetMixin,
    mixins.RetrieveModelMixin,
    mixins.UpdateModelMixin,
    mixins.ListModelMixin,
    viewsets.GenericViewSet,
):
    serializer_class = TalkSlotSerializer
    queryset = TalkSlot.objects.none()
    endpoint = "slots"
    search_fields = ("submission__title", "submission__speakers__name")
    filter_backends = (
        django_filters.rest_framework.DjangoFilterBackend,
        SearchFilter,
    )
    filterset_class = TalkSlotFilter
    permission_map = {"ical": "schedule.view_talkslot"}

    @cached_property
    def is_orga(self):
        return self.event and self.request.user.has_perm(
            "orga.view_schedule", self.event
        )

    def get_unversioned_serializer_class(self):
        if self.is_orga:
            return TalkSlotOrgaSerializer
        return TalkSlotSerializer

    def get_queryset(self):
        if not self.event:
            return self.queryset

        queryset = TalkSlot.objects.filter(schedule__event=self.event).select_related(
            "submission", "room", "schedule"
        )
        if not self.is_orga:
            queryset = queryset.filter(is_visible=True).exclude(
                schedule__version__isnull=True
            )

        if fields := self.check_expanded_fields(
            "submission.speakers",
            "submission.resources",
            "submission.answers",
            "submission.question",
        ):
            queryset = queryset.prefetch_related(
                *[f.replace(".", "__") for f in fields]
            )
        if fields := self.check_expanded_fields(
            "submission.track", "submission.submission_type"
        ):
            queryset = queryset.select_related(*[f.replace(".", "__") for f in fields])

        if self.action != "list":
            return queryset

        # In the list view, fall back to filtering by current schedule if there is no
        # other filter present.
        # If there is no current schedule, that means an empty response.
        filter_params = self.filterset_class.get_fields().keys()
        is_any_filter_active = any(
            param in self.request.query_params for param in filter_params
        )

        if not is_any_filter_active:
            queryset = queryset.filter(schedule=self.event.current_schedule)

        return queryset

    @action(detail=True, methods=["get"])
    def ical(self, request, event, pk=None):
        """Export a single talk slot as an iCalendar file."""
        slot = self.get_object()
        if not slot.submission:
            raise Http404
        calendar_data = slot.full_ical()
        response = HttpResponse(calendar_data.serialize(), content_type="text/calendar")
        response["Content-Disposition"] = (
            f'attachment; filename="{request.event.slug}-{slot.submission.code}.ics"'
        )
        return response
