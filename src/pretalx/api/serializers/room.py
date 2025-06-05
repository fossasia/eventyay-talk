from i18nfield.rest_framework import I18nAwareModelSerializer
from rest_framework.serializers import CharField, ModelSerializer, SerializerMethodField

from pretalx.api.versions import register_serializer
from pretalx.schedule.models import Availability, Room


@register_serializer()
class AvailabilitySerializer(ModelSerializer):
    allDay = SerializerMethodField()

    def get_allDay(self, obj):
        return obj.all_day

    class Meta:
        model = Availability
        fields = ("id", "start", "end", "allDay")


@register_serializer()
class RoomSerializer(I18nAwareModelSerializer):
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


@register_serializer()
class RoomOrgaSerializer(RoomSerializer):
    availabilities = AvailabilitySerializer(many=True)

    class Meta:
        model = Room
        fields = RoomSerializer.Meta.fields + ("speaker_info", "availabilities")
