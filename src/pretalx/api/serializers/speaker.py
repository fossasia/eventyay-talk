from pathlib import Path

from drf_spectacular.utils import extend_schema_field
from rest_flex_fields.serializers import FlexFieldsSerializerMixin
from rest_framework import exceptions
from rest_framework.serializers import (
    CharField,
    EmailField,
    ModelSerializer,
    SerializerMethodField,
    URLField,
)

from pretalx.api.mixins import PretalxSerializer
from pretalx.api.serializers.fields import UploadedFileField
from pretalx.api.serializers.question import AnswerSerializer
from pretalx.api.serializers.room import AvailabilitySerializer
from pretalx.api.versions import CURRENT_VERSION, register_serializer
from pretalx.person.models import SpeakerProfile, User
from pretalx.schedule.models import Availability


class LegacySubmitterSerializer(ModelSerializer):
    biography = SerializerMethodField()

    def __init__(self, *args, **kwargs):
        self.event = kwargs.pop("event", None)
        super().__init__(*args, **kwargs)

    class Meta:
        model = User
        fields = ("code", "name", "biography", "avatar")

    def get_biography(self, obj):
        if self.event:
            return getattr(
                obj.profiles.filter(event=self.event).first(), "biography", ""
            )
        return ""


class LegacySubmitterOrgaSerializer(LegacySubmitterSerializer):
    class Meta(LegacySubmitterSerializer.Meta):
        fields = LegacySubmitterSerializer.Meta.fields + ("email",)


class LegacySpeakerSerializer(ModelSerializer):
    code = CharField(source="user.code")
    name = CharField(source="user.name")
    avatar = SerializerMethodField()
    submissions = SerializerMethodField()
    answers = SerializerMethodField()

    def __init__(self, *args, **kwargs):
        questions = kwargs.pop("questions", [])
        self.questions = (
            questions
            if questions in ("all", ["all"])
            else [question for question in questions if question.isnumeric()]
        )
        super().__init__(*args, **kwargs)

    @staticmethod
    def get_avatar(obj):
        if obj.event.cfp.request_avatar:
            return obj.avatar_url

    @staticmethod
    def get_submissions(obj):
        talks = (
            obj.event.current_schedule.talks.all() if obj.event.current_schedule else []
        )
        return obj.user.submissions.filter(
            event=obj.event, slots__in=talks
        ).values_list("code", flat=True)

    def answers_queryset(self, obj):
        return obj.answers.all().filter(
            question__is_public=True, question__active=True, question__target="speaker"
        )

    def get_answers(self, obj):
        if not self.questions:
            return []
        queryset = self.answers_queryset(obj)
        if self.questions not in ("all", ["all"]):
            queryset = queryset.filter(question__in=self.questions)
        return AnswerSerializer(queryset, many=True).data

    class Meta:
        model = SpeakerProfile
        fields = ("code", "name", "biography", "submissions", "avatar", "answers")


class LegacySpeakerOrgaSerializer(LegacySpeakerSerializer):
    email = CharField(source="user.email")
    availabilities = AvailabilitySerializer(
        Availability.objects.none(), many=True, read_only=True
    )

    def answers_queryset(self, obj):
        return obj.answers.all()

    def get_submissions(self, obj):
        return obj.user.submissions.filter(event=obj.event).values_list(
            "code", flat=True
        )

    class Meta(LegacySpeakerSerializer.Meta):
        fields = LegacySpeakerSerializer.Meta.fields + ("email", "availabilities")


class LegacySpeakerReviewerSerializer(LegacySpeakerOrgaSerializer):
    def answers_queryset(self, obj):
        return obj.reviewer_answers.all()

    class Meta(LegacySpeakerOrgaSerializer.Meta):
        pass


@register_serializer(versions=[CURRENT_VERSION])
class SpeakerSerializer(FlexFieldsSerializerMixin, PretalxSerializer):
    code = CharField(source="user.code", read_only=True)
    name = CharField(source="user.name")
    avatar_url = URLField(read_only=True)
    answers = SerializerMethodField()
    submissions = SerializerMethodField()

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        self.event = getattr(self.context.get("request"), "event", None)
        if self.event and not self.event.cfp.request_avatar:
            self.fields.pop("avatar_url")

    @extend_schema_field(list[str])
    def get_submissions(self, obj):
        submissions = self.context.get("submissions")
        if not submissions:
            return []
        submissions = submissions.filter(speakers__in=[obj.user])
        if serializer := self.get_extra_flex_field("submissions", submissions):
            return serializer.data
        return submissions.values_list("code", flat=True)

    @extend_schema_field(list[int])
    def get_answers(self, obj):
        questions = self.context.get("questions", [])
        qs = obj.answers.filter(question__in=questions, question__event=self.event)
        if serializer := self.get_extra_flex_field("answers", qs):
            return serializer.data
        return qs.values_list("pk", flat=True)

    class Meta:
        model = SpeakerProfile
        fields = ("code", "name", "biography", "submissions", "avatar_url", "answers")
        expandable_fields = {
            "submissions": (
                "pretalx.api.serializers.submission.SubmissionSerializer",
                {"read_only": True, "many": True},
            ),
        }
        extra_expandable_fields = {
            "answers": (
                "pretalx.api.serializers.question.AnswerSerializer",
                {
                    "many": True,
                    "read_only": True,
                },
            ),
            "submissions": (
                "pretalx.api.serializers.submission.SubmissionSerializer",
                {
                    "many": True,
                    "read_only": True,
                },
            ),
        }


@register_serializer(versions=[CURRENT_VERSION])
class SpeakerOrgaSerializer(SpeakerSerializer):
    email = EmailField(source="user.email")
    timezone = CharField(source="user.timezone", read_only=True)
    locale = CharField(source="user.locale", read_only=True)

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        if self.event:
            for field in ("avatar", "availabilities"):
                if not getattr(self.event.cfp, f"request_{field}"):
                    self.fields.pop(field, None)
                elif getattr(self.event.cfp, f"require_{field}"):
                    self.fields[field].required = True

    class Meta(SpeakerSerializer.Meta):
        fields = SpeakerSerializer.Meta.fields + (
            "email",
            "timezone",
            "locale",
            "has_arrived",
        )


@register_serializer(versions=[CURRENT_VERSION])
class SpeakerUpdateSerializer(SpeakerOrgaSerializer):
    avatar = UploadedFileField(required=False, source="speaker.user")

    def update(self, instance, validated_data):
        avatar = validated_data.pop("avatar", None)
        user_fields = validated_data.pop("user", None) or {}
        instance = super().update(instance, validated_data)
        for key, value in user_fields.items():
            setattr(instance.user, key, value)
            instance.user.save(update_fields=[key])
        if avatar:
            instance.avatar.save(Path(avatar.name).name, avatar)
            instance.user.process_image("avatar", generate_thumbnail=True)
        return instance

    def validate_email(self, value):
        value = value.lower()
        if (
            User.objects.exclude(pk=self.instance.pk)
            .filter(email__iexact=value)
            .exists()
        ):
            raise exceptions.ValidationError("Email already exists in system.")
        return value

    class Meta(SpeakerOrgaSerializer.Meta):
        fields = SpeakerOrgaSerializer.Meta.fields + ("avatar",)
