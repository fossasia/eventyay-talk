from django.db import transaction
from rest_framework.serializers import BooleanField, ModelSerializer, UUIDField

from pretalx.api.mixins import PretalxSerializer
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
        availabilities = []
        for avail_data in availabilities_data:
            avail = Availability(
                event=room.event,
                start=avail_data["start"],
                end=avail_data["end"],
            )
            availabilities.append(avail)

        merged_availabilities = Availability.union(availabilities)
        for avail in merged_availabilities:
            avail.room = room

        with transaction.atomic():
            room.availabilities.all().delete()
            Availability.objects.bulk_create(merged_availabilities)

    class Meta:
        model = Room
        fields = RoomSerializer.Meta.fields + ("speaker_info", "availabilities")
