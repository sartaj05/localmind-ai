from django.conf import settings
from rest_framework.views import APIView
from rest_framework.response import Response
from rest_framework import status

from .serializers import AskAIRequestSerializer
from .services import ask_local_model


class AskAIView(APIView):
    """
    POST API to ask local AI model using Ollama.
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

            return Response(
                {
                    "success": True,
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