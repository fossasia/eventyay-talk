from django.http import Http404
from django.utils.functional import cached_property
from django_filters import rest_framework as filters
from django_scopes import scopes_disabled
from drf_spectacular.utils import OpenApiResponse, extend_schema, extend_schema_view
from rest_framework import serializers, status, viewsets
from rest_framework.authentication import SessionAuthentication
from rest_framework.decorators import (
    action,
    api_view,
    authentication_classes,
    permission_classes,
)
from rest_framework.exceptions import PermissionDenied
from rest_framework.permissions import IsAuthenticated
from rest_framework.response import Response

from pretalx.api.documentation import build_expand_docs, build_search_docs
from pretalx.api.mixins import PretalxViewSetMixin
from pretalx.api.serializers.legacy import (
    LegacySubmissionOrgaSerializer,
    LegacySubmissionReviewerSerializer,
    LegacySubmissionSerializer,
)
from pretalx.api.serializers.submission import (
    SubmissionOrgaSerializer,
    SubmissionSerializer,
    SubmissionTypeSerializer,
    TagSerializer,
    TrackSerializer,
)
from pretalx.api.versions import LEGACY
from pretalx.common.auth import TokenAuthentication
from pretalx.common.exceptions import SubmissionError
from pretalx.submission.models import (
    QuestionTarget,
    Submission,
    SubmissionStates,
    SubmissionType,
    Tag,
    Track,
)
from pretalx.submission.rules import (
    questions_for_user,
    speaker_profiles_for_user,
    submissions_for_user,
)


class AddSpeakerSerializer(serializers.Serializer):
    email = serializers.EmailField(required=True)
    name = serializers.CharField(required=False, allow_null=True, allow_blank=True)
    locale = serializers.CharField(required=False, allow_null=True, allow_blank=True)


class RemoveSpeakerSerializer(serializers.Serializer):
    user = serializers.CharField(required=True)


with scopes_disabled():

    class SubmissionFilter(filters.FilterSet):
        state = filters.MultipleChoiceFilter(choices=SubmissionStates.get_choices())

        class Meta:
            model = Submission
            fields = ("state", "content_locale", "submission_type", "is_featured")


@extend_schema_view(
    list=extend_schema(
        summary="List Submissions",
        parameters=[
            build_search_docs("title", "speaker.name"),
            build_expand_docs(
                "speakers",
                "speakers.answers",
                "track",
                "submission_type",
                "tags",
                "slots",
                "slots.room",
                "answers",
                "answers.question",
                "resources",
            ),
        ],
    ),
    retrieve=extend_schema(
        summary="Show Submission",
        parameters=[
            build_expand_docs(
                "speakers",
                "track",
                "submission_type",
                "tags",
                "slots",
                "slots.room",
                "answers",
                "resources",
            ),
        ],
    ),
    create=extend_schema(
        summary="Create Submission",
        description="Note that a submission created via the API will start in the submitted state and without speakers. No notification emails will be sent, and the submission may be in an invalid state (e.g. if the event has required custom fields).",
        request=SubmissionOrgaSerializer,
        responses={200: SubmissionOrgaSerializer},
    ),
    update=extend_schema(
        summary="Update Submission",
        request=SubmissionOrgaSerializer,
        responses={200: SubmissionOrgaSerializer},
    ),
    partial_update=extend_schema(
        summary="Update Submission (Partial Update)",
        request=SubmissionOrgaSerializer,
        responses={200: SubmissionOrgaSerializer},
    ),
    destroy=extend_schema(
        summary="Delete Submission",
        description="This endpoint is only available to server administrators.",
    ),
    accept=extend_schema(summary="Accept Submission"),
    reject=extend_schema(summary="Reject Submission"),
    confirm=extend_schema(summary="Confirm Submission"),
    cancel=extend_schema(summary="Cancel Submission"),
    make_submitted=extend_schema(summary="Make Submission Submitted"),
    add_speaker=extend_schema(
        summary="Add Speaker to Submission",
        request=AddSpeakerSerializer,
        responses={200: SubmissionOrgaSerializer},
    ),
    remove_speaker=extend_schema(
        summary="Remove Speaker from Submission",
        request=RemoveSpeakerSerializer,
        responses={200: SubmissionOrgaSerializer},
    ),
)
class SubmissionViewSet(PretalxViewSetMixin, viewsets.ModelViewSet):
    serializer_class = SubmissionSerializer
    queryset = Submission.objects.none()
    lookup_field = "code__iexact"
    search_fields = ("title", "speakers__name")
    filterset_class = SubmissionFilter
    permission_map = {
        "make_submitted": "submission.state_change_submission",
        "add_speaker": "submission.update_submission",
        "remove_speaker": "submission.update_submission",
    }
    endpoint = "submissions"

    def get_legacy_queryset(self):  # pragma: no cover
        base_qs = self.event.submissions.all().order_by("code")
        if not self.request.user.has_perm(
            "submission.orga_list_submission", self.event
        ):
            if (
                not self.request.user.has_perm("schedule.list_schedule", self.event)
                or not self.event.current_schedule
            ):
                return Submission.objects.none()
            return base_qs.filter(
                pk__in=self.event.current_schedule.talks.filter(
                    is_visible=True
                ).values_list("submission_id", flat=True)
            )
        return base_qs

    def get_legacy_serializer_class(self):  # pragma: no cover
        if self.request.user.has_perm("submission.orga_update_submission", self.event):
            return LegacySubmissionOrgaSerializer
        if self.request.user.has_perm("submission.orga_list_submission", self.event):
            return LegacySubmissionReviewerSerializer
        return LegacySubmissionSerializer

    def get_legacy_serializer(self, *args, **kwargs):  # pragma: no cover
        serializer_questions = (self.request.query_params.get("questions") or "").split(
            ","
        )
        can_view_speakers = self.request.user.has_perm(
            "schedule.list_schedule", self.event
        ) or self.request.user.has_perm("person.orga_list_speakerprofile", self.event)
        if self.request.query_params.get("anon"):
            can_view_speakers = False
        return super().get_serializer(
            *args,
            can_view_speakers=can_view_speakers,
            event=self.event,
            questions=serializer_questions,
            **kwargs,
        )

    def get_serializer_class(self):
        if self.api_version == LEGACY:  # pragma: no cover
            return self.get_legacy_serializer_class()
        return super().get_serializer_class()

    def get_unversioned_serializer_class(self):
        if self.is_orga:
            return SubmissionOrgaSerializer
        return SubmissionSerializer

    @cached_property
    def is_orga(self):
        return self.event and self.request.user.has_perm(
            "submission.orga_list_submission", self.event
        )

    def get_serializer(self, *args, **kwargs):
        if self.api_version == LEGACY:  # pragma: no cover
            return self.get_legacy_serializer(*args, **kwargs)
        return super().get_serializer(*args, **kwargs)

    @cached_property
    def speaker_profiles_for_user(self):
        if not self.event:
            return
        return speaker_profiles_for_user(self.event, self.request.user)

    def get_serializer_context(self):
        context = super().get_serializer_context()
        if not self.event:
            return context
        context["questions"] = questions_for_user(self.event, self.request.user).filter(
            target=QuestionTarget.SUBMISSION
        )
        context["speakers"] = self.speaker_profiles_for_user
        context["schedule"] = self.event.current_schedule
        context["public_slots"] = not self.has_perm("delete")
        return context

    def get_queryset(self):
        if self.api_version == LEGACY:  # pragma: no cover
            return self.get_legacy_queryset()
        if not self.event:
            # This is just during api doc creation
            return self.queryset
        queryset = (
            submissions_for_user(self.event, self.request.user)
            .select_related("event", "track", "submission_type")
            .prefetch_related("speakers", "answers", "slots")
        )
        if self.check_expanded_fields("speakers.user"):
            queryset = queryset.prefetch_related("speakers__profiles")
        if fields := self.check_expanded_fields(
            "answers.question",
            "answers.question.tracks",
            "answers.question.submission_types",
            "slots.room",
        ):
            queryset = queryset.prefetch_related(
                *[field.replace(".", "__") for field in fields]
            )
        return queryset

    def perform_destroy(self, request, *args, **kwargs):
        self.get_object().remove(force=True, person=self.request.user)

    @action(detail=True, methods=["POST"])
    def accept(self, request, **kwargs):
        try:
            submission = self.get_object()
            submission.accept(person=request.user, orga=True)
            return Response(SubmissionOrgaSerializer(submission).data)
        except SubmissionError as e:
            return Response({"detail": str(e)}, status=status.HTTP_400_BAD_REQUEST)
        except Exception as e:
            return Response(
                {"detail": str(e)}, status=status.HTTP_500_INTERNAL_SERVER_ERROR
            )

    @action(detail=True, methods=["POST"])
    def reject(self, request, **kwargs):
        try:
            submission = self.get_object()
            submission.reject(person=request.user, orga=True)
            return Response(SubmissionOrgaSerializer(submission).data)
        except SubmissionError as e:
            return Response({"detail": str(e)}, status=status.HTTP_400_BAD_REQUEST)
        except Exception as e:
            return Response(
                {"detail": str(e)}, status=status.HTTP_500_INTERNAL_SERVER_ERROR
            )

    @action(detail=True, methods=["POST"])
    def confirm(self, request, **kwargs):
        try:
            submission = self.get_object()
            submission.confirm(person=request.user, orga=True)
            return Response(SubmissionOrgaSerializer(submission).data)
        except SubmissionError as e:
            return Response({"detail": str(e)}, status=status.HTTP_400_BAD_REQUEST)
        except Exception as e:
            return Response(
                {"detail": str(e)}, status=status.HTTP_500_INTERNAL_SERVER_ERROR
            )

    @action(detail=True, methods=["POST"])
    def cancel(self, request, **kwargs):
        try:
            submission = self.get_object()
            submission.cancel(person=request.user, orga=True)
            return Response(SubmissionOrgaSerializer(submission).data)
        except SubmissionError as e:
            return Response({"detail": str(e)}, status=status.HTTP_400_BAD_REQUEST)
        except Exception as e:
            return Response(
                {"detail": str(e)}, status=status.HTTP_500_INTERNAL_SERVER_ERROR
            )

    @action(detail=True, methods=["POST"], url_path="make-submitted")
    def make_submitted(self, request, **kwargs):
        try:
            submission = self.get_object()
            submission.make_submitted(person=request.user, orga=True)
            return Response(SubmissionOrgaSerializer(submission).data)
        except SubmissionError as e:
            return Response({"detail": str(e)}, status=status.HTTP_400_BAD_REQUEST)
        except Exception as e:
            return Response(
                {"detail": str(e)}, status=status.HTTP_500_INTERNAL_SERVER_ERROR
            )

    @action(detail=True, methods=["POST"], url_path="add-speaker")
    def add_speaker(self, request, **kwargs):
        serializer = AddSpeakerSerializer(data=request.data)
        serializer.is_valid(raise_exception=True)
        data = serializer.validated_data
        submission = self.get_object()
        submission.add_speaker(
            email=data["email"], name=data.get("name"), locale=data.get("locale")
        )
        submission.refresh_from_db()
        return Response(SubmissionOrgaSerializer(submission).data)

    @action(detail=True, methods=["POST"], url_path="remove-speaker")
    def remove_speaker(self, request, **kwargs):
        serializer = RemoveSpeakerSerializer(data=request.data)
        serializer.is_valid(raise_exception=True)
        submission = self.get_object()
        speaker = submission.speakers.filter(
            code=serializer.validated_data["user"]
        ).first()
        if not speaker:  # pragma: no cover
            return Response(
                {"detail": "Speaker not found."}, status=status.HTTP_400_BAD_REQUEST
            )
        submission.remove_speaker(speaker, user=self.request.user)
        submission.refresh_from_db()
        return Response(SubmissionOrgaSerializer(submission).data)


@extend_schema(
    summary="List favourite submissions",
    description="This endpoint is used by the schedule widget and uses session authentication.",
    responses={
        status.HTTP_200_OK: list[str],
    },
)
@api_view(["GET"])
@permission_classes([IsAuthenticated])
@authentication_classes((SessionAuthentication, TokenAuthentication))
def favourites_view(request, event):
    if not request.user.has_perm("schedule.list_schedule", request.event):
        raise PermissionDenied()
    return Response(
        [
            sub.code
            for sub in Submission.objects.filter(
                favourites__user__in=[request.user], event=request.event
            )
        ]
    )


@extend_schema(
    summary="Add or remove a submission from favourites",
    description="This endpoint is used by the schedule widget and uses session authentication.",
    request=None,
    responses={
        status.HTTP_200_OK: {},
        status.HTTP_404_NOT_FOUND: OpenApiResponse(description="Submission not found."),
    },
)
@api_view(["POST", "DELETE"])
@permission_classes([IsAuthenticated])
@authentication_classes((SessionAuthentication, TokenAuthentication))
def favourite_view(request, event, code):
    if not request.user.has_perm("schedule.list_schedule", request.event):
        raise PermissionDenied()
    submission = (
        submissions_for_user(request.event, request.user)
        .filter(code__iexact=code)
        .first()
    )
    if not submission:
        raise Http404

    if request.method == "POST":
        submission.add_favourite(request.user)
    else:
        submission.remove_favourite(request.user)
    return Response({})


@extend_schema_view(
    list=extend_schema(summary="List tags", parameters=[build_search_docs("tag")]),
    retrieve=extend_schema(summary="Show Tags"),
    create=extend_schema(summary="Create Tags"),
    update=extend_schema(summary="Update Tags"),
    partial_update=extend_schema(summary="Update Tags (Partial Update)"),
    destroy=extend_schema(summary="Delete Tags"),
)
class TagViewSet(PretalxViewSetMixin, viewsets.ModelViewSet):
    serializer_class = TagSerializer
    queryset = Tag.objects.none()
    endpoint = "tags"
    search_fields = ("tag",)

    def get_queryset(self):
        return self.event.tags.all()


@extend_schema_view(
    list=extend_schema(
        summary="List Submission Types", parameters=[build_search_docs("name")]
    ),
    retrieve=extend_schema(summary="Show Submission Types"),
    create=extend_schema(summary="Create Submission Types"),
    update=extend_schema(summary="Update Submission Types"),
    partial_update=extend_schema(summary="Update Submission Types (Partial Update)"),
    destroy=extend_schema(summary="Delete Submission Types"),
)
class SubmissionTypeViewSet(PretalxViewSetMixin, viewsets.ModelViewSet):
    serializer_class = SubmissionTypeSerializer
    queryset = SubmissionType.objects.none()
    endpoint = "submission-types"
    search_fields = ("name",)

    def get_queryset(self):
        return self.event.submission_types.all()


@extend_schema_view(
    list=extend_schema(summary="List Tracks", parameters=[build_search_docs("name")]),
    retrieve=extend_schema(summary="Show Tracks"),
    create=extend_schema(summary="Create Tracks"),
    update=extend_schema(summary="Update Tracks"),
    partial_update=extend_schema(summary="Update Tracks (Partial Update)"),
    destroy=extend_schema(summary="Delete Tracks"),
)
class TrackViewSet(PretalxViewSetMixin, viewsets.ModelViewSet):
    serializer_class = TrackSerializer
    queryset = Track.objects.none()
    endpoint = "tracks"
    search_fields = ("name",)

    def get_queryset(self):
        return self.event.tracks.all()
