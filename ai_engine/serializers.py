from rest_framework import serializers

from .models import (
    AIChatHistory,
    ChatSession,
    ChatMessage,
    KnowledgeDocument,
)


class AskAIRequestSerializer(serializers.Serializer):
    prompt = serializers.CharField(required=True, allow_blank=False)
    model = serializers.CharField(required=False, allow_blank=True)


class AskAIResponseSerializer(serializers.Serializer):
    prompt = serializers.CharField()
    model = serializers.CharField()
    answer = serializers.CharField()


class AIChatHistorySerializer(serializers.ModelSerializer):
    class Meta:
        model = AIChatHistory
        fields = [
            "id",
            "model_name",
            "prompt",
            "response",
            "created_at",
        ]


class ChatMessageSerializer(serializers.ModelSerializer):
    class Meta:
        model = ChatMessage
        fields = [
            "id",
            "role",
            "content",
            "created_at",
        ]


class ChatSessionSerializer(serializers.ModelSerializer):
    message_count = serializers.SerializerMethodField()

    class Meta:
        model = ChatSession
        fields = [
            "id",
            "title",
            "model_name",
            "message_count",
            "created_at",
            "updated_at",
        ]

    def get_message_count(self, obj):
        return obj.messages.count()


class ChatSessionDetailSerializer(serializers.ModelSerializer):
    messages = ChatMessageSerializer(many=True, read_only=True)

    class Meta:
        model = ChatSession
        fields = [
            "id",
            "title",
            "model_name",
            "messages",
            "created_at",
            "updated_at",
        ]


class CreateChatSessionSerializer(serializers.Serializer):
    title = serializers.CharField(required=False, allow_blank=True)
    model = serializers.CharField(required=False, allow_blank=True)


class RenameChatSessionSerializer(serializers.Serializer):
    title = serializers.CharField(required=True, allow_blank=False)


class SendSessionMessageSerializer(serializers.Serializer):
    message = serializers.CharField(required=True, allow_blank=False)
    model = serializers.CharField(required=False, allow_blank=True)


class KnowledgeDocumentSerializer(serializers.ModelSerializer):
    class Meta:
        model = KnowledgeDocument
        fields = [
            "id",
            "title",
            "file",
            "uploaded_at",
        ]


class SendSessionRAGMessageSerializer(serializers.Serializer):
    message = serializers.CharField(required=True, allow_blank=False)
    model = serializers.CharField(required=False, allow_blank=True)
    top_k = serializers.IntegerField(required=False, min_value=1, max_value=10)