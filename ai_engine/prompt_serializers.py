from rest_framework import serializers

from .models import PromptTemplate


class PromptTemplateSerializer(serializers.ModelSerializer):
    class Meta:
        model = PromptTemplate
        fields = (
            "id",
            "title",
            "category",
            "prompt",
            "is_pinned",
            "created_at",
            "updated_at",
        )
        read_only_fields = (
            "id",
            "created_at",
            "updated_at",
        )


class PromptTemplateCreateUpdateSerializer(serializers.Serializer):
    title = serializers.CharField(max_length=150)
    category = serializers.ChoiceField(
        choices=[
            "study",
            "coding",
            "writing",
            "assistant",
            "other",
        ],
        required=False,
        default="other",
    )
    prompt = serializers.CharField()
    is_pinned = serializers.BooleanField(required=False, default=False)