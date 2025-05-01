from django.db import transaction
from django.db.models.deletion import ProtectedError
from django_filters import rest_framework as filters
from drf_spectacular.utils import extend_schema, extend_schema_view
from rest_framework import exceptions, viewsets
from rest_framework.permissions import SAFE_METHODS

from pretalx.api.documentation import build_expand_docs, build_search_docs
from pretalx.api.mixins import PretalxViewSetMixin
from pretalx.api.serializers.question import (
    AnswerSerializer,
    AnswerWriteSerializer,
    QuestionOrgaSerializer,
    QuestionSerializer,
)
from pretalx.submission.models import Answer, Question
from pretalx.submission.rules import questions_for_user

OPTIONS_HELP = (
    "Please note that any update to the options field will delete the "
    "existing question options (if still possible) and replace them with the new ones. "
    "Use the AnswerOption API for granular question option modifications."
)


@extend_schema_view(
    list=extend_schema(
        summary="List Questions",
        parameters=[
            build_search_docs("question"),
            build_expand_docs("options", "tracks", "submission_types"),
        ],
    ),
    retrieve=extend_schema(
        summary="Show Question",
        parameters=[build_expand_docs("options", "tracks", "submission_types")],
    ),
    create=extend_schema(summary="Create Question"),
    update=extend_schema(summary="Update Question", description=OPTIONS_HELP),
    partial_update=extend_schema(
        summary="Update Question (Partial Update)", description=OPTIONS_HELP
    ),
    destroy=extend_schema(summary="Delete Question"),
)
class QuestionViewSet(PretalxViewSetMixin, viewsets.ModelViewSet):
    queryset = Question.objects.none()
    serializer_class = QuestionSerializer
    filterset_fields = ("is_public", "is_visible_to_reviewers", "target", "variant")
    search_fields = ("question",)
    endpoint = "questions"

    def get_queryset(self):
        queryset = questions_for_user(
            self.request.event, self.request.user
        ).select_related("event")
        if fields := self.check_expanded_fields(
            "tracks", "submission_types", "options"
        ):
            queryset = queryset.prefetch_related(*fields)
        return queryset

    def get_unversioned_serializer_class(self):
        if self.request.method not in SAFE_METHODS or self.has_perm("update"):
            return QuestionOrgaSerializer
        return self.serializer_class

    def perform_destroy(self, instance):
        try:
            with transaction.atomic():
                instance.options.all().delete()
                instance.logged_actions().delete()
                return super().perform_destroy(instance)
        except ProtectedError:
            raise exceptions.ValidationError(
                "You cannot delete a question object that has answers."
            )


class AnswerFilterSet(filters.FilterSet):
    question = filters.NumberFilter(field_name="question_id")
    submission = filters.CharFilter(
        field_name="submission__code",
        lookup_expr="iexact",
    )
    person = filters.CharFilter(
        field_name="person__code",
        lookup_expr="iexact",
    )
    review = filters.NumberFilter(field_name="review_id")

    class Meta:
        model = Answer
        fields = ("question", "submission", "person", "review")


class AnswerViewSet(PretalxViewSetMixin, viewsets.ModelViewSet):
    queryset = Answer.objects.none()
    serializer_class = AnswerSerializer
    write_permission_required = "orga.change_submissions"
    filterset_class = AnswerFilterSet
    search_fields = ("answer",)
    endpoint = "answers"

    def get_queryset(self):
        return (
            Answer.objects.filter(
                question_id__in=questions_for_user(
                    self.request.event, self.request.user
                ).values_list("id", flat=True)
            )
            .prefetch_related("options")
            .select_related("question", "person", "review", "submission")
        )

    def get_unversioned_serializer_class(self):
        if self.request.method in SAFE_METHODS:
            return self.serializer_class
        return AnswerWriteSerializer

    def perform_create(self, serializer):
        # We don't want duplicate answers
        answer, _ = Answer.objects.update_or_create(
            question=serializer.validated_data["question"],
            review=serializer.validated_data.get("review"),
            submission=serializer.validated_data.get("submission"),
            person=serializer.validated_data.get("person"),
            defaults={"answer": serializer.validated_data["answer"]},
        )
        return answer
