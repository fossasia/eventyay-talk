from rest_framework.serializers import (
    ModelSerializer,
    SerializerMethodField,
    SlugRelatedField,
)

from pretalx.api.serializers.question import AnswerSerializer
from pretalx.api.versions import register_serializer
from pretalx.submission.models import Answer, Review


@register_serializer()
class AnonymousReviewSerializer(ModelSerializer):
    """Does not include the user and answer fields."""

    submission = SlugRelatedField(slug_field="code", read_only=True)

    class Meta:
        model = Review
        fields = [
            "id",
            "submission",
            "text",
            "score",
            "created",
            "updated",
        ]


@register_serializer()
class ReviewSerializer(AnonymousReviewSerializer):
    user = SlugRelatedField(slug_field="name", read_only=True)
    answers = SerializerMethodField()

    def get_answers(self, obj):
        return AnswerSerializer(Answer.objects.filter(review=obj), many=True).data

    class Meta(AnonymousReviewSerializer.Meta):
        model = Review
        fields = AnonymousReviewSerializer.Meta.fields + [
            "answers",
            "user",
        ]
