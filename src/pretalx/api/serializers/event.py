from rest_framework.serializers import ModelSerializer
from urlman.serializers import UrlManField

from pretalx.api.versions import register_serializer
from pretalx.event.models import Event


@register_serializer()
class EventSerializer(ModelSerializer):
    urls = UrlManField(urls=["base", "schedule", "login", "feed"])

    class Meta:
        model = Event
        fields = (
            "name",
            "slug",
            "is_public",
            "date_from",
            "date_to",
            "timezone",
            "urls",
        )
