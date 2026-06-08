from rest_framework import serializers


class AskAIRequestSerializer(serializers.Serializer):
    prompt = serializers.CharField(required=True, allow_blank=False)
    model = serializers.CharField(required=False, allow_blank=True)


class AskAIResponseSerializer(serializers.Serializer):
    prompt = serializers.CharField()
    model = serializers.CharField()
    answer = serializers.CharField()