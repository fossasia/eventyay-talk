from django.db import transaction
from rest_flex_fields.serializers import FlexFieldsSerializerMixin
from rest_framework.serializers import ModelSerializer, SlugRelatedField

from pretalx.api.mixins import PretalxSerializer, ReadOnlySerializerMixin
from pretalx.api.versions import CURRENT_VERSION, register_serializer
from pretalx.person.models import User
from pretalx.submission.models import (
    Answer,
    AnswerOption,
    Question,
    Submission,
    SubmissionType,
    Track,
)


@register_serializer()
class AnswerOptionSerializer(ModelSerializer):
    class Meta:
        model = AnswerOption
        fields = ("id", "answer")


@register_serializer(versions=["LEGACY"], class_name="QuestionSerializer")
class LegacyQuestionSerializer(ReadOnlySerializerMixin, PretalxSerializer):
    options = AnswerOptionSerializer(many=True, required=False)

    class Meta:
        model = Question
        fields = (
            "id",
            "variant",
            "question",
            "question_required",
            "deadline",
            "required",
            "read_only",
            "freeze_after",
            "target",
            "options",
            "help_text",
            "default_answer",
            "contains_personal_data",
            "min_length",
            "max_length",
            "is_public",
            "is_visible_to_reviewers",
        )


@register_serializer(versions=[CURRENT_VERSION], class_name="QuestionSerializer")
class QuestionSerializer(FlexFieldsSerializerMixin, PretalxSerializer):
    class Meta:
        model = Question
        fields = (
            "id",
            "question",
            "help_text",
            "default_answer",
            "variant",
            "target",
            "deadline",
            "freeze_after",
            "question_required",
            "position",
            "tracks",
            "submission_types",
            "options",
            "min_length",
            "max_length",
            "min_number",
            "max_number",
            "min_date",
            "max_date",
            "min_datetime",
            "max_datetime",
        )
        expandable_fields = {
            "options": (
                "pretalx.api.serializers.question.AnswerOptionSerializer",
                {"many": True, "read_only": True},
            ),
            "tracks": (
                "pretalx.api.serializers.submission.TrackSerializer",
                {"many": True, "read_only": True},
            ),
            "submission_types": (
                "pretalx.api.serializers.submission.SubmissionTypeSerializer",
                {"many": True, "read_only": True},
            ),
        }


@register_serializer(versions=[CURRENT_VERSION], class_name="QuestionOrgaSerializer")
class QuestionOrgaSerializer(QuestionSerializer):
    options = AnswerOptionSerializer(many=True, required=False)

    class Meta(QuestionSerializer.Meta):
        fields = QuestionSerializer.Meta.fields + (
            "active",
            "is_public",
            "contains_personal_data",
            "is_visible_to_reviewers",
        )

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        request = kwargs.get("context", {}).get("request")
        if request and hasattr(request, "event"):
            self.fields["tracks"].queryset = request.event.tracks.all()
            self.fields["submission_types"].queryset = (
                request.event.submission_types.all()
            )
        else:
            self.fields["tracks"].queryset = Track.objects.none()
            self.fields["submission_types"].queryset = SubmissionType.objects.none()

    def create(self, validated_data):
        options_data = validated_data.pop("options", None)
        validated_data["event"] = getattr(self.context.get("request"), "event", None)
        question = super().create(validated_data)
        if options_data:
            self._handle_options(question, options_data)
        return question

    def update(self, instance, validated_data):
        options_data = validated_data.pop("options", None)
        question = super().update(instance, validated_data)
        if options_data is not None:
            self._handle_options(question, options_data)
        return question

    def _handle_options(self, question, options_data):
        # Replace existing options
        with transaction.atomic():
            question.options.all().delete()
            for option_data in options_data:
                AnswerOption.objects.create(question=question, **option_data)


@register_serializer()
class AnswerWriteSerializer(ModelSerializer):
    submission = SlugRelatedField(
        queryset=Submission.objects.none(),
        slug_field="code",
        required=False,
        style={"input_type": "text", "base_template": "input.html"},
    )
    person = SlugRelatedField(
        queryset=User.objects.all(),
        slug_field="code",
        required=False,
        style={"input_type": "text", "base_template": "input.html"},
    )
    options = AnswerOptionSerializer(many=True, required=False)

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        request = self.context.get("request")
        if not request:
            return
        self.fields["question"].queryset = request.event.questions.all()
        self.fields["submission"].queryset = request.event.submissions.all()
        self.fields["review"].queryset = request.event.reviews.all()
        self.fields["review"].style = {
            "input_type": "number",
            "base_template": "input.html",
        }
        self.fields["question"].style = {
            "input_type": "number",
            "base_template": "input.html",
        }

    class Meta:
        model = Answer
        fields = (
            "id",
            "question",
            "answer",
            "answer_file",
            "submission",
            "review",
            "person",
            "options",
        )


@register_serializer()
class AnswerSerializer(AnswerWriteSerializer):
    question = QuestionSerializer(Question.objects.none(), fields=("id", "question"))

    class Meta(AnswerWriteSerializer.Meta):
        pass
