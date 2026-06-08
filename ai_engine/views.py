from django.conf import settings
from rest_framework.views import APIView
from rest_framework.response import Response
from rest_framework import status

from .models import AIChatHistory
from .serializers import AskAIRequestSerializer, AIChatHistorySerializer
from .services import ask_local_model


class AskAIView(APIView):
    """
    POST API to ask local AI model using Ollama and save chat history.
    """

    def post(self, request):
        serializer = AskAIRequestSerializer(data=request.data)

        if not serializer.is_valid():
            return Response(
                {
                    "success": False,
                    "errors": serializer.errors,
                },
                status=status.HTTP_400_BAD_REQUEST,
            )

        prompt = serializer.validated_data["prompt"]
        model = serializer.validated_data.get("model") or settings.DEFAULT_AI_MODEL

        try:
            answer = ask_local_model(prompt=prompt, model=model)

            chat = AIChatHistory.objects.create(
                model_name=model,
                prompt=prompt,
                response=answer,
            )

            return Response(
                {
                    "success": True,
                    "chat_id": chat.id,
                    "prompt": prompt,
                    "model": model,
                    "answer": answer,
                },
                status=status.HTTP_200_OK,
            )

        except Exception as error:
            return Response(
                {
                    "success": False,
                    "error": str(error),
                },
                status=status.HTTP_500_INTERNAL_SERVER_ERROR,
            )


class AIChatHistoryListView(APIView):
    """
    GET API to list all AI chat history.
    """

    def get(self, request):
        chats = AIChatHistory.objects.all()
        serializer = AIChatHistorySerializer(chats, many=True)

        return Response(
            {
                "success": True,
                "count": chats.count(),
                "results": serializer.data,
            },
            status=status.HTTP_200_OK,
        )


class AIChatHistoryDetailView(APIView):
    """
    GET and DELETE single chat history.
    """

    def get_object(self, pk):
        try:
            return AIChatHistory.objects.get(pk=pk)
        except AIChatHistory.DoesNotExist:
            return None

    def get(self, request, pk):
        chat = self.get_object(pk)

        if chat is None:
            return Response(
                {
                    "success": False,
                    "error": "Chat history not found",
                },
                status=status.HTTP_404_NOT_FOUND,
            )

        serializer = AIChatHistorySerializer(chat)

        return Response(
            {
                "success": True,
                "result": serializer.data,
            },
            status=status.HTTP_200_OK,
        )

    def delete(self, request, pk):
        chat = self.get_object(pk)

        if chat is None:
            return Response(
                {
                    "success": False,
                    "error": "Chat history not found",
                },
                status=status.HTTP_404_NOT_FOUND,
            )

        chat.delete()

        return Response(
            {
                "success": True,
                "message": "Chat history deleted successfully",
            },
            status=status.HTTP_200_OK,
        )