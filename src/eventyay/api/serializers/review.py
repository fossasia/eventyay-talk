from rest_framework.serializers import (
    ModelSerializer,
    SerializerMethodField,
    SlugRelatedField,
)

from eventyay.api.serializers.question import AnswerSerializer
from eventyay.submission.models import Answer, Review


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
