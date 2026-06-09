from rest_framework import serializers

from .models import (
    AIChatHistory,
    AIUsageLog,
    ChatSession,
    ChatMessage,
    ChatSessionTag,
    KnowledgeDocument,
)

class ChatSessionTagSerializer(serializers.ModelSerializer):
    class Meta:
        model = ChatSessionTag
        fields = ["id", "name", "color", "created_at"]


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
            "is_important",
            "created_at",
        ]


class ChatSessionSerializer(serializers.ModelSerializer):
    message_count = serializers.SerializerMethodField()
    tags = ChatSessionTagSerializer(many=True, read_only=True)
    class Meta:
        model = ChatSession
        fields = [
            "id",
            "title",
            "model_name",
            "is_pinned",
            "is_archived",
            "is_deleted",
            "deleted_at",
            "message_count",
            "created_at",
            "updated_at",
            "tags",
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
            "is_pinned",
            "is_archived",
            "is_deleted",
            "deleted_at",
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
    
class AIUsageLogSerializer(serializers.ModelSerializer):
    class Meta:
        model = AIUsageLog
        fields = [
            "id",
            "endpoint",
            "model_name",
            "prompt",
            "success",
            "error_message",
            "response_time_ms",
            "created_at",
        ]
class BulkSessionIdsSerializer(serializers.Serializer):
    session_ids = serializers.ListField(
        child=serializers.IntegerField(),
        required=True,
        allow_empty=False,
    )
class BulkMessageIdsSerializer(serializers.Serializer):
    message_ids = serializers.ListField(
        child=serializers.IntegerField(),
        required=True,
        allow_empty=False,
    )
    
class CopyMessagesSerializer(serializers.Serializer):
    message_ids = serializers.ListField(
        child=serializers.IntegerField(),
        required=True,
        allow_empty=False,
    )
    target_session_id = serializers.IntegerField(required=True)


class MergeSessionsSerializer(serializers.Serializer):
    source_session_id = serializers.IntegerField(required=True)
    target_session_id = serializers.IntegerField(required=True)


class SessionTagAssignSerializer(serializers.Serializer):
    tag_ids = serializers.ListField(
        child=serializers.IntegerField(),
        required=True,
        allow_empty=True,
    )