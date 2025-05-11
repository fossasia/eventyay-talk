from rest_framework.serializers import SerializerMethodField

from pretalx.api.mixins import PretalxSerializer
from pretalx.api.versions import CURRENT_VERSION, register_serializer
from pretalx.schedule.models import Schedule


@register_serializer()
class ScheduleListSerializer(PretalxSerializer):
    version = SerializerMethodField()

    @staticmethod
    def get_version(obj):
        return obj.version or "wip"

    class Meta:
        model = Schedule
        fields = ("version", "published")
