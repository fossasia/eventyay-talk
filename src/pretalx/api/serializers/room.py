from django.db import transaction
from rest_framework.serializers import (
    BooleanField,
    CharField,
    ModelSerializer,
    SerializerMethodField,
    UUIDField,
)

from pretalx.api.mixins import PretalxSerializer, ReadOnlySerializerMixin
from pretalx.api.versions import CURRENT_VERSION, register_serializer
from pretalx.schedule.models import Availability, Room


@register_serializer()
class AvailabilitySerializer(ModelSerializer):
    allDay = BooleanField(
        help_text="Computed field indicating if an availability fills an entire day.",
        read_only=True,
        source="all_day",
    )

    class Meta:
        model = Availability
        fields = ("start", "end", "allDay")


@register_serializer(versions=["LEGACY"], class_name="RoomSerializer")
class LegacyRoomSerializer(ReadOnlySerializerMixin, PretalxSerializer):
    url = SerializerMethodField()
    guid = CharField(source="uuid")

    def get_url(self, obj):
        return obj.urls.edit

    class Meta:
        model = Room
        fields = (
            "id",
            "guid",
            "name",
            "description",
            "capacity",
            "position",
            "url",
        )


@register_serializer(versions=["LEGACY"], class_name="RoomOrgaSerializer")
class LegacyRoomOrgaSerializer(LegacyRoomSerializer):
    availabilities = AvailabilitySerializer(many=True)

    class Meta:
        model = Room
        fields = LegacyRoomSerializer.Meta.fields + ("speaker_info", "availabilities")


@register_serializer(versions=[CURRENT_VERSION], class_name="RoomSerializer")
class RoomSerializer(PretalxSerializer):
    uuid = UUIDField(
        help_text="The uuid field is equal the the guid field if a guid has been set. Otherwise, it will contain a computed (stable) UUID.",
        read_only=True,
    )

    class Meta:
        model = Room
        fields = (
            "id",
            "name",
            "description",
            "uuid",
            "guid",
            "capacity",
            "position",
        )


@register_serializer(versions=[CURRENT_VERSION], class_name="RoomOrgaSerializer")
class RoomOrgaSerializer(RoomSerializer):
    availabilities = AvailabilitySerializer(many=True, required=False)

    def create(self, validated_data):
        availabilities_data = validated_data.pop("availabilities", None)
        validated_data["event"] = getattr(self.context.get("request"), "event", None)
        room = super().create(validated_data)
        if availabilities_data is not None:
            self._handle_availabilities(room, availabilities_data)
        return room

    def update(self, instance, validated_data):
        availabilities_data = validated_data.pop("availabilities", None)
        room = super().update(instance, validated_data)
        if availabilities_data is not None:
            self._handle_availabilities(room, availabilities_data)
        return room

    def _handle_availabilities(self, room, availabilities_data):
        # Create availability objects
        availabilities = []
        for avail_data in availabilities_data:
            avail = Availability(
                event=room.event,
                start=avail_data["start"],
                end=avail_data["end"],
            )
            # Set all_day attribute if allDay is provided in the API data
            if "allDay" in avail_data:
                avail.all_day = avail_data["allDay"]
            availabilities.append(avail)

        # Merge overlapping availabilities
        merged_availabilities = Availability.union(availabilities)

        # Set room reference
        for avail in merged_availabilities:
            avail.room = room

        # Replace existing availabilities
        with transaction.atomic():
            room.availabilities.all().delete()
            Availability.objects.bulk_create(merged_availabilities)

    class Meta:
        model = Room
        fields = RoomSerializer.Meta.fields + ("speaker_info", "availabilities")
