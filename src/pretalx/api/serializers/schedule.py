from rest_flex_fields.serializers import FlexFieldsSerializerMixin
from rest_framework.exceptions import ValidationError
from rest_framework.serializers import (
    DateTimeField,
    SerializerMethodField,
    SlugRelatedField,
)

from pretalx.api.mixins import PretalxSerializer
from pretalx.api.versions import CURRENT_VERSION, register_serializer
from pretalx.schedule.models import Schedule, TalkSlot


@register_serializer()
class ScheduleListSerializer(PretalxSerializer):
    version = SerializerMethodField()

    @staticmethod
    def get_version(obj):
        return obj.version or "wip"

    class Meta:
        model = Schedule
        fields = ("version", "published")


@register_serializer(versions=[CURRENT_VERSION])
class ScheduleSerializer(FlexFieldsSerializerMixin, PretalxSerializer):
    version = SerializerMethodField()
    # TODO slots etc

    @staticmethod
    def get_version(obj) -> str:
        return obj.version or "wip"

    class Meta:
        model = Schedule
        fields = ("version", "published")


@register_serializer(versions=[CURRENT_VERSION])
class TalkSlotSerializer(FlexFieldsSerializerMixin, PretalxSerializer):
    submission = SlugRelatedField(slug_field="code", read_only=True)
    end = DateTimeField(source="local_end")

    class Meta:
        model = TalkSlot
        fields = [
            "id",
            "room",
            "start",
            "end",
            "submission",
            "schedule",
            "description",
            "duration",
        ]
        read_only_fields = ["submission", "schedule"]
        expandable_fields = {
            "submission": (
                "pretalx.api.serializers.submission.SubmissionSerializer",
                {"read_only": True, "omit": ("slots",)},
            ),
            "schedule": (
                "pretalx.api.serializers.schedule.ScheduleSerializer",
                {"read_only": True, "omit": ("slots", "speakers")},
            ),
            "room": (
                "pretalx.api.serializers.room.RoomSerializer",
                {"read_only": True},
            ),
        }


@register_serializer(versions=[CURRENT_VERSION])
class TalkSlotOrgaSerializer(TalkSlotSerializer):
    class Meta(TalkSlotSerializer.Meta):
        fields = TalkSlotSerializer.Meta.fields + ["is_visible"]
        read_only_fields = TalkSlotSerializer.Meta.read_only_fields + ["is_visible"]
        expandable_fields = TalkSlotSerializer.Meta.expandable_fields

    def validate_end(self, value):
        if self.instance and self.instance.submission:
            raise ValidationError(
                "End can only be edited if there is no submission associated with the slot. Otherwise, update the submission duration."
            )
        return value

    def validate_description(self, value):
        if self.instance and self.instance.submission:
            raise ValidationError(
                "Description can only be edited if there is no submission associated with the slot. Otherwise, update the submission abstract."
            )
        return value
