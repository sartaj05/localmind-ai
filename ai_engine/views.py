from django.conf import settings
from django.http import StreamingHttpResponse

from rest_framework.views import APIView
from rest_framework.response import Response
from rest_framework import status
from django.db.models import Avg
from .models import (
    AIChatHistory,
    ChatSession,
    ChatMessage,
    KnowledgeDocument,
    AIUsageLog,
)
from .serializers import (
    AskAIRequestSerializer,
    AIChatHistorySerializer,
    ChatSessionSerializer,
    ChatSessionDetailSerializer,
    CreateChatSessionSerializer,
    KnowledgeDocumentSerializer,
    RenameChatSessionSerializer,
    SendSessionMessageSerializer,
    SendSessionRAGMessageSerializer,
    AIUsageLogSerializer,
)
from .pagination import StandardResultsSetPagination
from .services import (
    ask_local_model,
    build_context_prompt,
    build_rag_context_prompt,
    list_local_models,
    check_ollama_health,
)
from .rag_service import build_knowledge_base, search_knowledge
from .streaming import stream_ollama_response
from .logging_service import create_usage_log, now_ms


class AskAIView(APIView):
    def post(self, request):
        started_at = now_ms()
        serializer = AskAIRequestSerializer(data=request.data)

        if not serializer.is_valid():
            return Response(
                {"success": False, "errors": serializer.errors},
                status=status.HTTP_400_BAD_REQUEST,
            )

        prompt = serializer.validated_data["prompt"]
        model = serializer.validated_data.get("model") or settings.DEFAULT_AI_MODEL

        try:
            answer = ask_local_model(prompt=prompt, model=model)

            chat = AIChatHistory.objects.create(
                user=request.user,
                model_name=model,
                prompt=prompt,
                response=answer,
            )

            create_usage_log(
                user=request.user,
                endpoint="/api/ai/ask/",
                model_name=model,
                prompt=prompt,
                success=True,
                started_at_ms=started_at,
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
            create_usage_log(
                user=request.user,
                endpoint="/api/ai/ask/",
                model_name=model,
                prompt=prompt,
                success=False,
                error_message=str(error),
                started_at_ms=started_at,
            )

            return Response(
                {"success": False, "error": str(error)},
                status=status.HTTP_500_INTERNAL_SERVER_ERROR,
            )


class AIChatHistoryListView(APIView):
    def get(self, request):
        search = request.query_params.get("search", "")
        chats = AIChatHistory.objects.filter(user=request.user)

        if search:
            chats = chats.filter(prompt__icontains=search)

        paginator = StandardResultsSetPagination()
        page = paginator.paginate_queryset(chats, request)
        serializer = AIChatHistorySerializer(page, many=True)

        return paginator.get_paginated_response(
            {"success": True, "results": serializer.data}
        )


class AIChatHistoryDetailView(APIView):
    def get_object(self, request, pk):
        try:
            return AIChatHistory.objects.get(pk=pk, user=request.user)
        except AIChatHistory.DoesNotExist:
            return None

    def get(self, request, pk):
        chat = self.get_object(request, pk)

        if chat is None:
            return Response(
                {"success": False, "error": "Chat history not found"},
                status=status.HTTP_404_NOT_FOUND,
            )

        serializer = AIChatHistorySerializer(chat)
        return Response({"success": True, "result": serializer.data})

    def delete(self, request, pk):
        chat = self.get_object(request, pk)

        if chat is None:
            return Response(
                {"success": False, "error": "Chat history not found"},
                status=status.HTTP_404_NOT_FOUND,
            )

        chat.delete()
        return Response({"success": True, "message": "Chat history deleted successfully"})


class ChatSessionListCreateView(APIView):
    def get(self, request):
        search = request.query_params.get("search", "")
        sessions = ChatSession.objects.filter(user=request.user)

        if search:
            sessions = sessions.filter(title__icontains=search)

        paginator = StandardResultsSetPagination()
        page = paginator.paginate_queryset(sessions, request)
        serializer = ChatSessionSerializer(page, many=True)

        return paginator.get_paginated_response(
            {"success": True, "results": serializer.data}
        )

    def post(self, request):
        serializer = CreateChatSessionSerializer(data=request.data)

        if not serializer.is_valid():
            return Response(
                {"success": False, "errors": serializer.errors},
                status=status.HTTP_400_BAD_REQUEST,
            )

        title = serializer.validated_data.get("title") or "New Chat"
        model = serializer.validated_data.get("model") or settings.DEFAULT_AI_MODEL

        session = ChatSession.objects.create(
            user=request.user,
            title=title,
            model_name=model,
        )

        return Response(
            {
                "success": True,
                "message": "Chat session created successfully",
                "result": ChatSessionSerializer(session).data,
            },
            status=status.HTTP_201_CREATED,
        )


class ChatSessionDetailView(APIView):
    def get_object(self, request, pk):
        try:
            return ChatSession.objects.get(pk=pk, user=request.user)
        except ChatSession.DoesNotExist:
            return None

    def get(self, request, pk):
        session = self.get_object(request, pk)

        if session is None:
            return Response(
                {"success": False, "error": "Chat session not found"},
                status=status.HTTP_404_NOT_FOUND,
            )

        return Response(
            {"success": True, "result": ChatSessionDetailSerializer(session).data}
        )

    def patch(self, request, pk):
        session = self.get_object(request, pk)

        if session is None:
            return Response(
                {"success": False, "error": "Chat session not found"},
                status=status.HTTP_404_NOT_FOUND,
            )

        serializer = RenameChatSessionSerializer(data=request.data)

        if not serializer.is_valid():
            return Response(
                {"success": False, "errors": serializer.errors},
                status=status.HTTP_400_BAD_REQUEST,
            )

        session.title = serializer.validated_data["title"]
        session.save(update_fields=["title", "updated_at"])

        return Response(
            {
                "success": True,
                "message": "Chat session renamed successfully",
                "result": ChatSessionSerializer(session).data,
            }
        )

    def delete(self, request, pk):
        session = self.get_object(request, pk)

        if session is None:
            return Response(
                {"success": False, "error": "Chat session not found"},
                status=status.HTTP_404_NOT_FOUND,
            )

        session.delete()
        return Response({"success": True, "message": "Chat session deleted successfully"})


class SendSessionMessageView(APIView):
    def post(self, request, pk):
        started_at = now_ms()

        try:
            session = ChatSession.objects.get(pk=pk, user=request.user)
        except ChatSession.DoesNotExist:
            return Response(
                {"success": False, "error": "Chat session not found"},
                status=status.HTTP_404_NOT_FOUND,
            )

        serializer = SendSessionMessageSerializer(data=request.data)

        if not serializer.is_valid():
            return Response(
                {"success": False, "errors": serializer.errors},
                status=status.HTTP_400_BAD_REQUEST,
            )

        user_message = serializer.validated_data["message"]
        model = serializer.validated_data.get("model") or session.model_name

        try:
            context_prompt = build_context_prompt(
                messages=session.messages,
                new_message=user_message,
            )

            ai_answer = ask_local_model(prompt=context_prompt, model=model)

            ChatMessage.objects.create(
                session=session,
                role="user",
                content=user_message,
            )

            assistant_message = ChatMessage.objects.create(
                session=session,
                role="assistant",
                content=ai_answer,
            )

            session.model_name = model

            if session.title == "New Chat":
                session.title = user_message[:50]

            session.save(update_fields=["model_name", "title", "updated_at"])

            create_usage_log(
                user=request.user,
                endpoint=f"/api/ai/sessions/{pk}/messages/",
                model_name=model,
                prompt=user_message,
                success=True,
                started_at_ms=started_at,
            )

            return Response(
                {
                    "success": True,
                    "session_id": session.id,
                    "model": model,
                    "user_message": user_message,
                    "assistant_message": {
                        "id": assistant_message.id,
                        "role": assistant_message.role,
                        "content": assistant_message.content,
                        "created_at": assistant_message.created_at,
                    },
                }
            )

        except Exception as error:
            create_usage_log(
                user=request.user,
                endpoint=f"/api/ai/sessions/{pk}/messages/",
                model_name=model,
                prompt=user_message,
                success=False,
                error_message=str(error),
                started_at_ms=started_at,
            )

            return Response(
                {"success": False, "error": str(error)},
                status=status.HTTP_500_INTERNAL_SERVER_ERROR,
            )


class StreamAIView(APIView):
    authentication_classes = []
    permission_classes = []

    def get(self, request):
        return Response(
            {
                "success": True,
                "message": "This endpoint supports POST streaming only.",
                "method": "POST",
                "url": "/api/ai/stream/",
                "example_body": {
                    "prompt": "Explain Django ORM in simple words",
                    "model": "phi3",
                },
            }
        )

    def post(self, request):
        prompt = request.data.get("prompt")

        if not prompt:
            return Response(
                {"success": False, "error": "Prompt required"},
                status=status.HTTP_400_BAD_REQUEST,
            )

        model = request.data.get("model") or settings.DEFAULT_AI_MODEL

        generator = stream_ollama_response(prompt=prompt, model=model)

        return StreamingHttpResponse(generator, content_type="text/plain")


class BuildKnowledgeBaseView(APIView):
    def post(self, request):
        try:
            total_chunks = build_knowledge_base(request.user)

            return Response(
                {
                    "success": True,
                    "message": "Knowledge base built successfully",
                    "total_chunks": total_chunks,
                }
            )

        except Exception as error:
            return Response(
                {"success": False, "error": str(error)},
                status=status.HTTP_500_INTERNAL_SERVER_ERROR,
            )


class AskRAGView(APIView):
    def post(self, request):
        started_at = now_ms()

        question = request.data.get("question")
        model = request.data.get("model") or settings.DEFAULT_AI_MODEL

        if not question:
            return Response(
                {"success": False, "error": "Question is required"},
                status=status.HTTP_400_BAD_REQUEST,
            )

        try:
            context = search_knowledge(query=question, user=request.user)

            prompt = f"""
You are a helpful AI assistant. Answer the question only using the provided context.

If the answer is not available in the context, say:
"I do not have enough information in the uploaded knowledge base."

Context:
{context}

Question:
{question}

Answer:
"""

            answer = ask_local_model(prompt=prompt, model=model)

            create_usage_log(
                user=request.user,
                endpoint="/api/ai/rag/ask/",
                model_name=model,
                prompt=question,
                success=True,
                started_at_ms=started_at,
            )

            return Response(
                {
                    "success": True,
                    "question": question,
                    "model": model,
                    "context": context,
                    "answer": answer,
                }
            )

        except Exception as error:
            create_usage_log(
                user=request.user,
                endpoint="/api/ai/rag/ask/",
                model_name=model,
                prompt=question,
                success=False,
                error_message=str(error),
                started_at_ms=started_at,
            )

            return Response(
                {"success": False, "error": str(error)},
                status=status.HTTP_500_INTERNAL_SERVER_ERROR,
            )


class KnowledgeDocumentListCreateView(APIView):
    def get(self, request):
        search = request.query_params.get("search", "")
        documents = KnowledgeDocument.objects.filter(user=request.user)

        if search:
            documents = documents.filter(title__icontains=search)

        paginator = StandardResultsSetPagination()
        page = paginator.paginate_queryset(documents, request)
        serializer = KnowledgeDocumentSerializer(page, many=True)

        return paginator.get_paginated_response(
            {"success": True, "results": serializer.data}
        )

    def post(self, request):
        file = request.FILES.get("file")
        title = request.data.get("title")

        if not file:
            return Response(
                {"success": False, "error": "File is required"},
                status=status.HTTP_400_BAD_REQUEST,
            )

        allowed_extensions = [".txt", ".pdf"]

        if not any(file.name.lower().endswith(ext) for ext in allowed_extensions):
            return Response(
                {"success": False, "error": "Only TXT and PDF files are allowed"},
                status=status.HTTP_400_BAD_REQUEST,
            )

        document = KnowledgeDocument.objects.create(
            user=request.user,
            title=title or file.name,
            file=file,
        )

        return Response(
            {
                "success": True,
                "message": "Document uploaded successfully",
                "result": KnowledgeDocumentSerializer(document).data,
            },
            status=status.HTTP_201_CREATED,
        )


class KnowledgeDocumentDetailView(APIView):
    def delete(self, request, pk):
        try:
            document = KnowledgeDocument.objects.get(pk=pk, user=request.user)
        except KnowledgeDocument.DoesNotExist:
            return Response(
                {"success": False, "error": "Document not found"},
                status=status.HTTP_404_NOT_FOUND,
            )

        document.file.delete(save=False)
        document.delete()

        return Response(
            {
                "success": True,
                "message": "Document deleted successfully. Rebuild knowledge base after deleting.",
            }
        )


class SendSessionRAGMessageView(APIView):
    def post(self, request, pk):
        started_at = now_ms()

        try:
            session = ChatSession.objects.get(pk=pk, user=request.user)
        except ChatSession.DoesNotExist:
            return Response(
                {"success": False, "error": "Chat session not found"},
                status=status.HTTP_404_NOT_FOUND,
            )

        serializer = SendSessionRAGMessageSerializer(data=request.data)

        if not serializer.is_valid():
            return Response(
                {"success": False, "errors": serializer.errors},
                status=status.HTTP_400_BAD_REQUEST,
            )

        user_message = serializer.validated_data["message"]
        model = serializer.validated_data.get("model") or session.model_name
        top_k = serializer.validated_data.get("top_k") or 3

        try:
            rag_context = search_knowledge(
                query=user_message,
                user=request.user,
                top_k=top_k,
            )

            context_prompt = build_rag_context_prompt(
                messages=session.messages,
                new_message=user_message,
                rag_context=rag_context,
            )

            ai_answer = ask_local_model(prompt=context_prompt, model=model)

            ChatMessage.objects.create(
                session=session,
                role="user",
                content=user_message,
            )

            assistant_message = ChatMessage.objects.create(
                session=session,
                role="assistant",
                content=ai_answer,
            )

            session.model_name = model

            if session.title == "New Chat":
                session.title = user_message[:50]

            session.save(update_fields=["model_name", "title", "updated_at"])

            create_usage_log(
                user=request.user,
                endpoint=f"/api/ai/sessions/{pk}/rag-message/",
                model_name=model,
                prompt=user_message,
                success=True,
                started_at_ms=started_at,
            )

            return Response(
                {
                    "success": True,
                    "session_id": session.id,
                    "model": model,
                    "rag_context": rag_context,
                    "user_message": user_message,
                    "assistant_message": {
                        "id": assistant_message.id,
                        "role": assistant_message.role,
                        "content": assistant_message.content,
                        "created_at": assistant_message.created_at,
                    },
                }
            )

        except Exception as error:
            create_usage_log(
                user=request.user,
                endpoint=f"/api/ai/sessions/{pk}/rag-message/",
                model_name=model,
                prompt=user_message,
                success=False,
                error_message=str(error),
                started_at_ms=started_at,
            )

            return Response(
                {"success": False, "error": str(error)},
                status=status.HTTP_500_INTERNAL_SERVER_ERROR,
            )


class StreamSessionRAGMessageView(APIView):
    def get(self, request, pk):
        return Response(
            {
                "success": True,
                "message": "This endpoint supports POST streaming only.",
                "method": "POST",
                "url": f"/api/ai/sessions/{pk}/rag-stream/",
                "example_body": {
                    "message": "What is this document about?",
                    "model": "phi3",
                    "top_k": 3,
                },
            }
        )

    def post(self, request, pk):
        started_at = now_ms()

        try:
            session = ChatSession.objects.get(pk=pk, user=request.user)
        except ChatSession.DoesNotExist:
            return Response(
                {"success": False, "error": "Chat session not found"},
                status=status.HTTP_404_NOT_FOUND,
            )

        serializer = SendSessionRAGMessageSerializer(data=request.data)

        if not serializer.is_valid():
            return Response(
                {"success": False, "errors": serializer.errors},
                status=status.HTTP_400_BAD_REQUEST,
            )

        user_message = serializer.validated_data["message"]
        model = serializer.validated_data.get("model") or session.model_name
        top_k = serializer.validated_data.get("top_k") or 3

        try:
            rag_context = search_knowledge(
                query=user_message,
                user=request.user,
                top_k=top_k,
            )

            context_prompt = build_rag_context_prompt(
                messages=session.messages,
                new_message=user_message,
                rag_context=rag_context,
            )

            ChatMessage.objects.create(
                session=session,
                role="user",
                content=user_message,
            )

            def response_generator():
                full_answer = ""

                try:
                    for token in stream_ollama_response(
                        prompt=context_prompt,
                        model=model,
                    ):
                        full_answer += token
                        yield token

                    ChatMessage.objects.create(
                        session=session,
                        role="assistant",
                        content=full_answer,
                    )

                    session.model_name = model

                    if session.title == "New Chat":
                        session.title = user_message[:50]

                    session.save(update_fields=["model_name", "title", "updated_at"])

                    create_usage_log(
                        user=request.user,
                        endpoint=f"/api/ai/sessions/{pk}/rag-stream/",
                        model_name=model,
                        prompt=user_message,
                        success=True,
                        started_at_ms=started_at,
                    )

                except Exception as error:
                    create_usage_log(
                        user=request.user,
                        endpoint=f"/api/ai/sessions/{pk}/rag-stream/",
                        model_name=model,
                        prompt=user_message,
                        success=False,
                        error_message=str(error),
                        started_at_ms=started_at,
                    )
                    yield f"\n[ERROR] {str(error)}"

            return StreamingHttpResponse(
                response_generator(),
                content_type="text/plain",
            )

        except Exception as error:
            create_usage_log(
                user=request.user,
                endpoint=f"/api/ai/sessions/{pk}/rag-stream/",
                model_name=model,
                prompt=user_message,
                success=False,
                error_message=str(error),
                started_at_ms=started_at,
            )

            return Response(
                {"success": False, "error": str(error)},
                status=status.HTTP_500_INTERNAL_SERVER_ERROR,
            )


class LocalModelListView(APIView):
    def get(self, request):
        try:
            models = list_local_models()

            return Response(
                {
                    "success": True,
                    "default_model": settings.DEFAULT_AI_MODEL,
                    "count": len(models),
                    "results": models,
                }
            )

        except Exception as error:
            return Response(
                {"success": False, "error": str(error)},
                status=status.HTTP_500_INTERNAL_SERVER_ERROR,
            )


class AIHealthCheckView(APIView):
    authentication_classes = []
    permission_classes = []

    def get(self, request):
        ollama = check_ollama_health()

        return Response(
            {
                "success": True,
                "django": {"available": True},
                "ollama": ollama,
                "default_model": settings.DEFAULT_AI_MODEL,
            }
        )


class AIUsageLogListView(APIView):
    def get(self, request):
        search = request.query_params.get("search", "")

        logs = AIUsageLog.objects.filter(user=request.user)

        if search:
            logs = logs.filter(prompt__icontains=search)

        paginator = StandardResultsSetPagination()
        page = paginator.paginate_queryset(logs, request)

        serializer = AIUsageLogSerializer(page, many=True)

        return paginator.get_paginated_response(
            {"success": True, "results": serializer.data}
        )
        
class AIDashboardSummaryView(APIView):
    def get(self, request):
        total_sessions = ChatSession.objects.filter(user=request.user).count()
        total_documents = KnowledgeDocument.objects.filter(user=request.user).count()
        total_history = AIChatHistory.objects.filter(user=request.user).count()

        logs = AIUsageLog.objects.filter(user=request.user)

        total_requests = logs.count()
        successful_requests = logs.filter(success=True).count()
        failed_requests = logs.filter(success=False).count()

        avg_response_time = logs.aggregate(
            avg_time=Avg("response_time_ms")
        )["avg_time"]

        return Response(
            {
                "success": True,
                "summary": {
                    "total_sessions": total_sessions,
                    "total_documents": total_documents,
                    "total_history": total_history,
                    "total_ai_requests": total_requests,
                    "successful_requests": successful_requests,
                    "failed_requests": failed_requests,
                    "average_response_time_ms": round(avg_response_time or 0, 2),
                },
            },
            status=status.HTTP_200_OK,
        )
        
class AIRecentActivityView(APIView):
    def get(self, request):
        recent_sessions = ChatSession.objects.filter(user=request.user)[:5]
        recent_documents = KnowledgeDocument.objects.filter(user=request.user)[:5]
        recent_logs = AIUsageLog.objects.filter(user=request.user)[:5]

        return Response(
            {
                "success": True,
                "recent_activity": {
                    "sessions": ChatSessionSerializer(recent_sessions, many=True).data,
                    "documents": KnowledgeDocumentSerializer(recent_documents, many=True).data,
                    "usage_logs": AIUsageLogSerializer(recent_logs, many=True).data,
                },
            },
            status=status.HTTP_200_OK,
        )
        
        
class ClearAIChatHistoryView(APIView):
    def delete(self, request):
        chats = AIChatHistory.objects.filter(user=request.user)
        deleted_count = chats.count()
        chats.delete()

        return Response(
            {
                "success": True,
                "message": "AI chat history cleared successfully",
                "deleted_history": deleted_count,
            },
            status=status.HTTP_200_OK,
        )
        
class ClearKnowledgeDocumentsView(APIView):
    def delete(self, request):
        documents = KnowledgeDocument.objects.filter(user=request.user)
        deleted_count = documents.count()

        for document in documents:
            document.file.delete(save=False)

        documents.delete()

        return Response(
            {
                "success": True,
                "message": "All knowledge documents deleted successfully. Rebuild knowledge base after deleting.",
                "deleted_documents": deleted_count,
            },
            status=status.HTTP_200_OK,
        )
        
class ClearAIUsageLogsView(APIView):
    def delete(self, request):
        logs = AIUsageLog.objects.filter(user=request.user)
        deleted_count = logs.count()
        logs.delete()

        return Response(
            {
                "success": True,
                "message": "AI usage logs cleared successfully",
                "deleted_logs": deleted_count,
            },
            status=status.HTTP_200_OK,
        )
        
class ChatMessageDetailView(APIView):
    def delete(self, request, session_pk, message_pk):
        try:
            session = ChatSession.objects.get(pk=session_pk, user=request.user)
        except ChatSession.DoesNotExist:
            return Response(
                {"success": False, "error": "Chat session not found"},
                status=status.HTTP_404_NOT_FOUND,
            )

        try:
            message = ChatMessage.objects.get(pk=message_pk, session=session)
        except ChatMessage.DoesNotExist:
            return Response(
                {"success": False, "error": "Chat message not found"},
                status=status.HTTP_404_NOT_FOUND,
            )

        message.delete()

        return Response(
            {
                "success": True,
                "message": "Chat message deleted successfully",
            },
            status=status.HTTP_200_OK,
        )