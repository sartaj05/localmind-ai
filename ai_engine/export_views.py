import json

from django.http import HttpResponse
from rest_framework import status
from rest_framework.response import Response
from rest_framework.views import APIView
from rest_framework.permissions import IsAuthenticated
from django.contrib.auth import authenticate
from .models import ChatSession, KnowledgeHistory
from .serializers import ChatSessionDetailSerializer, KnowledgeHistorySerializer


class ExportAllChatSessionsTXTView(APIView):
    permission_classes = [IsAuthenticated]

    def get(self, request):
        sessions = ChatSession.objects.filter(
            user=request.user,
            is_deleted=False,
        ).prefetch_related("messages")

        lines = [
            "LocalMind AI - All Chat Sessions Export",
            f"Total Sessions: {sessions.count()}",
            "",
            "=" * 80,
        ]

        for index, session in enumerate(sessions, start=1):
            lines.extend(
                [
                    "",
                    f"SESSION {index}",
                    "-" * 80,
                    f"ID: {session.id}",
                    f"Title: {session.title}",
                    f"Model: {session.model_name}",
                    f"Created At: {session.created_at}",
                    f"Updated At: {session.updated_at}",
                    "",
                    "MESSAGES:",
                    "",
                ]
            )

            for message in session.messages.all():
                role = "User" if message.role == "user" else "Assistant"
                lines.extend(
                    [
                        f"{role}:",
                        message.content,
                        "",
                        "-" * 40,
                        "",
                    ]
                )

            lines.append("=" * 80)

        content = "\n".join(lines)

        response = HttpResponse(content, content_type="text/plain")
        response["Content-Disposition"] = (
            'attachment; filename="all_chat_sessions.txt"'
        )
        return response


class ExportAllChatSessionsJSONView(APIView):
    permission_classes = [IsAuthenticated]

    def get(self, request):
        sessions = ChatSession.objects.filter(
            user=request.user,
            is_deleted=False,
        ).prefetch_related("messages")

        data = {
            "total_sessions": sessions.count(),
            "sessions": ChatSessionDetailSerializer(sessions, many=True).data,
        }

        response = Response(data, status=status.HTTP_200_OK)
        response["Content-Disposition"] = (
            'attachment; filename="all_chat_sessions.json"'
        )
        return response


class ClearKnowledgeHistoryView(APIView):
    permission_classes = [IsAuthenticated]

    def delete(self, request):
        password = request.data.get("password")

        if not password:
            return Response(
                {
                    "success": False,
                    "error": "Password is required",
                },
                status=status.HTTP_400_BAD_REQUEST,
            )

        user = authenticate(
            username=request.user.username,
            password=password,
        )

        if user is None:
            return Response(
                {
                    "success": False,
                    "error": "Invalid password",
                },
                status=status.HTTP_403_FORBIDDEN,
            )

        histories = KnowledgeHistory.objects.filter(user=request.user)
        deleted_count = histories.count()
        histories.delete()

        return Response(
            {
                "success": True,
                "message": "Knowledge history cleared successfully",
                "deleted_count": deleted_count,
            },
            status=status.HTTP_200_OK,
        )