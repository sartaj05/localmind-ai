from django.conf import settings
from django.http import StreamingHttpResponse, HttpResponse

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
from .rag_service import (
    build_knowledge_base,
    search_knowledge,
    get_user_collection_stats,
    search_knowledge_with_sources,
)
from .serializers import (
    AskAIRequestSerializer,
    AIChatHistorySerializer,
    ChatMessageSerializer,
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
from .rag_service import build_knowledge_base, search_knowledge, get_user_collection_stats
from .services import (
    ask_local_model,
    build_context_prompt,
    build_rag_context_prompt,
    list_local_models,
    check_ollama_health,
    generate_chat_title,
)



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
        show_archived = request.query_params.get("archived", "false").lower() == "true"

        sessions = ChatSession.objects.filter(
            user=request.user,
            is_archived=show_archived,
            is_deleted=False,
        )

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

        session.soft_delete()

        return Response(
            {
                "success": True,
                "message": "Chat session moved to trash successfully",
            },
            status=status.HTTP_200_OK,
        )

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
                session.title = generate_chat_title(
                    user_message=user_message,
                    model=model,
                )

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
            retrieval = search_knowledge_with_sources(
                query=question,
                user=request.user,
            )

            context = retrieval["context"]
            sources = retrieval["sources"]

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
                    "sources": sources,
                    "answer": answer,
                },
                status=status.HTTP_200_OK,
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

        total_chunks = build_knowledge_base(request.user)

        return Response(
            {
                "success": True,
                "message": "Document uploaded successfully and knowledge base rebuilt.",
                "total_chunks": total_chunks,
                "result": KnowledgeDocumentSerializer(document).data,
            },
            status=status.HTTP_201_CREATED,
        )

class KnowledgeDocumentDetailView(APIView):
    def patch(self, request, pk):
        try:
            document = KnowledgeDocument.objects.get(pk=pk, user=request.user)
        except KnowledgeDocument.DoesNotExist:
            return Response(
                {"success": False, "error": "Document not found"},
                status=status.HTTP_404_NOT_FOUND,
            )

        title = request.data.get("title")
        new_file = request.FILES.get("file")

        allowed_extensions = [".txt", ".pdf"]

        if new_file and not any(
            new_file.name.lower().endswith(ext) for ext in allowed_extensions
        ):
            return Response(
                {"success": False, "error": "Only TXT and PDF files are allowed"},
                status=status.HTTP_400_BAD_REQUEST,
            )

        if title:
            document.title = title

        if new_file:
            document.file.delete(save=False)
            document.file = new_file

        if not title and not new_file:
            return Response(
                {"success": False, "error": "Title or file is required"},
                status=status.HTTP_400_BAD_REQUEST,
            )

        document.save()

        total_chunks = build_knowledge_base(request.user)

        return Response(
            {
                "success": True,
                "message": "Document updated successfully and knowledge base rebuilt.",
                "total_chunks": total_chunks,
                "result": KnowledgeDocumentSerializer(document).data,
            },
            status=status.HTTP_200_OK,
        )

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

        total_chunks = build_knowledge_base(request.user)

        return Response(
            {
                "success": True,
                "message": "Document deleted successfully and knowledge base rebuilt.",
                "total_chunks": total_chunks,
            },
            status=status.HTTP_200_OK,
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
            retrieval = search_knowledge_with_sources(
                query=user_message,
                user=request.user,
                top_k=top_k,
            )

            rag_context = retrieval["context"]
            sources = retrieval["sources"]

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
                session.title = generate_chat_title(
                    user_message=user_message,
                    model=model,
                )

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
                    "sources": sources,
                    "user_message": user_message,
                    "assistant_message": {
                        "id": assistant_message.id,
                        "role": assistant_message.role,
                        "content": assistant_message.content,
                        "created_at": assistant_message.created_at,
                    },
                },
                status=status.HTTP_200_OK,
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
            },
            status=status.HTTP_200_OK,
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
            retrieval = search_knowledge_with_sources(
                query=user_message,
                user=request.user,
                top_k=top_k,
            )

            rag_context = retrieval["context"]
            sources = retrieval["sources"]

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
                    yield "Sources used:\n"

                    for source in sources:
                        yield f"- {source['source']} ({source['file_name']})\n"

                    yield "\nAnswer:\n"

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
                        session.title = generate_chat_title(
                            user_message=user_message,
                            model=model,
                        )

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

        total_chunks = build_knowledge_base(request.user)

        return Response(
            {
                "success": True,
                "message": "All knowledge documents deleted successfully and knowledge base rebuilt.",
                "deleted_documents": deleted_count,
                "total_chunks": total_chunks,
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
    def patch(self, request, session_pk, message_pk):
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

        content = request.data.get("content")

        if not content:
            return Response(
                {"success": False, "error": "Content is required"},
                status=status.HTTP_400_BAD_REQUEST,
            )

        message.content = content
        message.save(update_fields=["content"])

        return Response(
            {
                "success": True,
                "message": "Chat message updated successfully",
                "result": {
                    "id": message.id,
                    "role": message.role,
                    "content": message.content,
                    "created_at": message.created_at,
                },
            },
            status=status.HTTP_200_OK,
        )

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
        
class RegenerateChatMessageView(APIView):
    def post(self, request, session_pk, message_pk):
        started_at = now_ms()

        try:
            session = ChatSession.objects.get(pk=session_pk, user=request.user)
        except ChatSession.DoesNotExist:
            return Response(
                {"success": False, "error": "Chat session not found"},
                status=status.HTTP_404_NOT_FOUND,
            )

        try:
            user_message = ChatMessage.objects.get(
                pk=message_pk,
                session=session,
                role="user",
            )
        except ChatMessage.DoesNotExist:
            return Response(
                {"success": False, "error": "User message not found"},
                status=status.HTTP_404_NOT_FOUND,
            )

        model = request.data.get("model") or session.model_name

        try:
            context_prompt = build_context_prompt(
                messages=session.messages.filter(created_at__lt=user_message.created_at),
                new_message=user_message.content,
            )

            ai_answer = ask_local_model(
                prompt=context_prompt,
                model=model,
            )

            assistant_message = ChatMessage.objects.create(
                session=session,
                role="assistant",
                content=ai_answer,
            )

            session.model_name = model
            session.save(update_fields=["model_name", "updated_at"])

            create_usage_log(
                user=request.user,
                endpoint=f"/api/ai/sessions/{session_pk}/messages/{message_pk}/regenerate/",
                model_name=model,
                prompt=user_message.content,
                success=True,
                started_at_ms=started_at,
            )

            return Response(
                {
                    "success": True,
                    "message": "AI answer regenerated successfully",
                    "assistant_message": {
                        "id": assistant_message.id,
                        "role": assistant_message.role,
                        "content": assistant_message.content,
                        "created_at": assistant_message.created_at,
                    },
                },
                status=status.HTTP_200_OK,
            )

        except Exception as error:
            create_usage_log(
                user=request.user,
                endpoint=f"/api/ai/sessions/{session_pk}/messages/{message_pk}/regenerate/",
                model_name=model,
                prompt=user_message.content,
                success=False,
                error_message=str(error),
                started_at_ms=started_at,
            )

            return Response(
                {"success": False, "error": str(error)},
                status=status.HTTP_500_INTERNAL_SERVER_ERROR,
            )
            
class RegenerateRAGChatMessageView(APIView):
    def post(self, request, session_pk, message_pk):
        started_at = now_ms()

        try:
            session = ChatSession.objects.get(pk=session_pk, user=request.user)
        except ChatSession.DoesNotExist:
            return Response(
                {"success": False, "error": "Chat session not found"},
                status=status.HTTP_404_NOT_FOUND,
            )

        try:
            user_message = ChatMessage.objects.get(
                pk=message_pk,
                session=session,
                role="user",
            )
        except ChatMessage.DoesNotExist:
            return Response(
                {"success": False, "error": "User message not found"},
                status=status.HTTP_404_NOT_FOUND,
            )

        model = request.data.get("model") or session.model_name
        top_k = request.data.get("top_k") or 3

        try:
            retrieval = search_knowledge_with_sources(
                query=user_message.content,
                user=request.user,
                top_k=top_k,
            )

            rag_context = retrieval["context"]
            sources = retrieval["sources"]

            context_prompt = build_rag_context_prompt(
                messages=session.messages.filter(created_at__lt=user_message.created_at),
                new_message=user_message.content,
                rag_context=rag_context,
            )

            ai_answer = ask_local_model(
                prompt=context_prompt,
                model=model,
            )

            assistant_message = ChatMessage.objects.create(
                session=session,
                role="assistant",
                content=ai_answer,
            )

            session.model_name = model
            session.save(update_fields=["model_name", "updated_at"])

            create_usage_log(
                user=request.user,
                endpoint=f"/api/ai/sessions/{session_pk}/messages/{message_pk}/regenerate-rag/",
                model_name=model,
                prompt=user_message.content,
                success=True,
                started_at_ms=started_at,
            )

            return Response(
                {
                    "success": True,
                    "message": "RAG AI answer regenerated successfully",
                    "rag_context": rag_context,
                    "sources": sources,
                    "assistant_message": {
                        "id": assistant_message.id,
                        "role": assistant_message.role,
                        "content": assistant_message.content,
                        "created_at": assistant_message.created_at,
                    },
                },
                status=status.HTTP_200_OK,
            )

        except Exception as error:
            create_usage_log(
                user=request.user,
                endpoint=f"/api/ai/sessions/{session_pk}/messages/{message_pk}/regenerate-rag/",
                model_name=model,
                prompt=user_message.content,
                success=False,
                error_message=str(error),
                started_at_ms=started_at,
            )

            return Response(
                {"success": False, "error": str(error)},
                status=status.HTTP_500_INTERNAL_SERVER_ERROR,
            )
            
class ExportChatSessionTXTView(APIView):
    def get(self, request, pk):
        try:
            session = ChatSession.objects.get(pk=pk, user=request.user)
        except ChatSession.DoesNotExist:
            return Response(
                {"success": False, "error": "Chat session not found"},
                status=status.HTTP_404_NOT_FOUND,
            )

        lines = []
        lines.append(f"Chat Title: {session.title}")
        lines.append(f"Model: {session.model_name}")
        lines.append(f"Created At: {session.created_at}")
        lines.append(f"Updated At: {session.updated_at}")
        lines.append("")
        lines.append("=" * 60)
        lines.append("MESSAGES")
        lines.append("=" * 60)
        lines.append("")

        for message in session.messages.all():
            role = "User" if message.role == "user" else "Assistant"
            lines.append(f"{role}:")
            lines.append(message.content)
            lines.append("")
            lines.append("-" * 60)
            lines.append("")

        content = "\n".join(lines)

        response = HttpResponse(content, content_type="text/plain")
        response["Content-Disposition"] = (
            f'attachment; filename="chat_session_{session.id}.txt"'
        )

        return response
    
class ExportChatSessionJSONView(APIView):
    def get(self, request, pk):
        try:
            session = ChatSession.objects.get(pk=pk, user=request.user)
        except ChatSession.DoesNotExist:
            return Response(
                {"success": False, "error": "Chat session not found"},
                status=status.HTTP_404_NOT_FOUND,
            )

        data = {
            "id": session.id,
            "title": session.title,
            "model_name": session.model_name,
            "created_at": session.created_at,
            "updated_at": session.updated_at,
            "messages": ChatMessageSerializer(session.messages.all(), many=True).data,
        }

        response = Response(data, status=status.HTTP_200_OK)
        response["Content-Disposition"] = (
            f'attachment; filename="chat_session_{session.id}.json"'
        )

        return response
    
    
class KnowledgeBaseStatusView(APIView):
    def get(self, request):
        total_documents = KnowledgeDocument.objects.filter(user=request.user).count()
        stats = get_user_collection_stats(request.user)

        return Response(
            {
                "success": True,
                "knowledge_base": {
                    "total_documents": total_documents,
                    "total_chunks": stats["total_chunks"],
                    "is_indexed": stats["is_indexed"],
                },
            },
            status=status.HTTP_200_OK,
        )
        
        
class TogglePinChatSessionView(APIView):
    def patch(self, request, pk):
        try:
            session = ChatSession.objects.get(pk=pk, user=request.user)
        except ChatSession.DoesNotExist:
            return Response(
                {"success": False, "error": "Chat session not found"},
                status=status.HTTP_404_NOT_FOUND,
            )

        session.is_pinned = not session.is_pinned
        session.save(update_fields=["is_pinned", "updated_at"])

        return Response(
            {
                "success": True,
                "message": "Chat session pin status updated successfully",
                "is_pinned": session.is_pinned,
                "result": ChatSessionSerializer(session).data,
            },
            status=status.HTTP_200_OK,
        )
        
        
class ToggleArchiveChatSessionView(APIView):
    def patch(self, request, pk):
        try:
            session = ChatSession.objects.get(pk=pk, user=request.user)
        except ChatSession.DoesNotExist:
            return Response(
                {"success": False, "error": "Chat session not found"},
                status=status.HTTP_404_NOT_FOUND,
            )

        session.is_archived = not session.is_archived
        session.save(update_fields=["is_archived", "updated_at"])

        return Response(
            {
                "success": True,
                "message": "Chat session archive status updated successfully",
                "is_archived": session.is_archived,
                "result": ChatSessionSerializer(session).data,
            },
            status=status.HTTP_200_OK,
        )
        
class TrashChatSessionListView(APIView):
    def get(self, request):
        search = request.query_params.get("search", "")

        sessions = ChatSession.objects.filter(
            user=request.user,
            is_deleted=True,
        )

        if search:
            sessions = sessions.filter(title__icontains=search)

        paginator = StandardResultsSetPagination()
        page = paginator.paginate_queryset(sessions, request)
        serializer = ChatSessionSerializer(page, many=True)

        return paginator.get_paginated_response(
            {"success": True, "results": serializer.data}
        )


class RestoreChatSessionView(APIView):
    def patch(self, request, pk):
        try:
            session = ChatSession.objects.get(
                pk=pk,
                user=request.user,
                is_deleted=True,
            )
        except ChatSession.DoesNotExist:
            return Response(
                {"success": False, "error": "Deleted chat session not found"},
                status=status.HTTP_404_NOT_FOUND,
            )

        session.restore()

        return Response(
            {
                "success": True,
                "message": "Chat session restored successfully",
                "result": ChatSessionSerializer(session).data,
            },
            status=status.HTTP_200_OK,
        )


class PermanentDeleteChatSessionView(APIView):
    def delete(self, request, pk):
        try:
            session = ChatSession.objects.get(
                pk=pk,
                user=request.user,
                is_deleted=True,
            )
        except ChatSession.DoesNotExist:
            return Response(
                {"success": False, "error": "Deleted chat session not found"},
                status=status.HTTP_404_NOT_FOUND,
            )

        session.delete()

        return Response(
            {
                "success": True,
                "message": "Chat session permanently deleted successfully",
            },
            status=status.HTTP_200_OK,
        )
        
class StreamSessionMessageView(APIView):
    def get(self, request, pk):
        return Response(
            {
                "success": True,
                "message": "This endpoint supports POST streaming only.",
                "method": "POST",
                "url": f"/api/ai/sessions/{pk}/stream-message/",
                "example_body": {
                    "message": "Explain Django ORM in simple words",
                    "model": "phi3",
                },
            },
            status=status.HTTP_200_OK,
        )

    def post(self, request, pk):
        started_at = now_ms()

        try:
            session = ChatSession.objects.get(
                pk=pk,
                user=request.user,
                is_deleted=False,
            )
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
                        session.title = generate_chat_title(
                            user_message=user_message,
                            model=model,
                        )

                    session.save(update_fields=["model_name", "title", "updated_at"])

                    create_usage_log(
                        user=request.user,
                        endpoint=f"/api/ai/sessions/{pk}/stream-message/",
                        model_name=model,
                        prompt=user_message,
                        success=True,
                        started_at_ms=started_at,
                    )

                except Exception as error:
                    create_usage_log(
                        user=request.user,
                        endpoint=f"/api/ai/sessions/{pk}/stream-message/",
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
                endpoint=f"/api/ai/sessions/{pk}/stream-message/",
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
            
class ChatSessionStatsView(APIView):
    def get(self, request, pk):
        try:
            session = ChatSession.objects.get(
                pk=pk,
                user=request.user,
                is_deleted=False,
            )
        except ChatSession.DoesNotExist:
            return Response(
                {"success": False, "error": "Chat session not found"},
                status=status.HTTP_404_NOT_FOUND,
            )

        messages = session.messages.all()
        last_message = messages.last()

        return Response(
            {
                "success": True,
                "session": {
                    "id": session.id,
                    "title": session.title,
                    "model_name": session.model_name,
                    "is_pinned": session.is_pinned,
                    "is_archived": session.is_archived,
                    "is_deleted": session.is_deleted,
                    "created_at": session.created_at,
                    "updated_at": session.updated_at,
                },
                "stats": {
                    "total_messages": messages.count(),
                    "user_messages": messages.filter(role="user").count(),
                    "assistant_messages": messages.filter(role="assistant").count(),
                    "last_message": {
                        "id": last_message.id,
                        "role": last_message.role,
                        "content": last_message.content,
                        "created_at": last_message.created_at,
                    } if last_message else None,
                },
            },
            status=status.HTTP_200_OK,
        )
        
class DuplicateChatSessionView(APIView):
    def post(self, request, pk):
        try:
            original_session = ChatSession.objects.get(
                pk=pk,
                user=request.user,
                is_deleted=False,
            )
        except ChatSession.DoesNotExist:
            return Response(
                {"success": False, "error": "Chat session not found"},
                status=status.HTTP_404_NOT_FOUND,
            )

        new_title = request.data.get("title") or f"Copy of {original_session.title}"

        new_session = ChatSession.objects.create(
            user=request.user,
            title=new_title,
            model_name=original_session.model_name,
            is_pinned=False,
            is_archived=False,
        )

        messages_to_create = []

        for message in original_session.messages.all():
            messages_to_create.append(
                ChatMessage(
                    session=new_session,
                    role=message.role,
                    content=message.content,
                )
            )

        ChatMessage.objects.bulk_create(messages_to_create)

        return Response(
            {
                "success": True,
                "message": "Chat session duplicated successfully",
                "result": ChatSessionDetailSerializer(new_session).data,
            },
            status=status.HTTP_201_CREATED,
        )
        
class SearchChatSessionMessagesView(APIView):
    def get(self, request, pk):
        query = request.query_params.get("q", "")

        if not query:
            return Response(
                {
                    "success": False,
                    "error": "Search query is required. Use ?q=your_text",
                },
                status=status.HTTP_400_BAD_REQUEST,
            )

        try:
            session = ChatSession.objects.get(
                pk=pk,
                user=request.user,
                is_deleted=False,
            )
        except ChatSession.DoesNotExist:
            return Response(
                {"success": False, "error": "Chat session not found"},
                status=status.HTTP_404_NOT_FOUND,
            )

        messages = session.messages.filter(content__icontains=query)

        paginator = StandardResultsSetPagination()
        page = paginator.paginate_queryset(messages, request)

        serializer = ChatMessageSerializer(page, many=True)

        return paginator.get_paginated_response(
            {
                "success": True,
                "query": query,
                "session_id": session.id,
                "results": serializer.data,
            }
        )
        
        
class ToggleImportantChatMessageView(APIView):
    def patch(self, request, session_pk, message_pk):
        try:
            session = ChatSession.objects.get(
                pk=session_pk,
                user=request.user,
                is_deleted=False,
            )
        except ChatSession.DoesNotExist:
            return Response(
                {"success": False, "error": "Chat session not found"},
                status=status.HTTP_404_NOT_FOUND,
            )

        try:
            message = ChatMessage.objects.get(
                pk=message_pk,
                session=session,
            )
        except ChatMessage.DoesNotExist:
            return Response(
                {"success": False, "error": "Chat message not found"},
                status=status.HTTP_404_NOT_FOUND,
            )

        message.is_important = not message.is_important
        message.save(update_fields=["is_important"])

        return Response(
            {
                "success": True,
                "message": "Chat message important status updated successfully",
                "is_important": message.is_important,
                "result": ChatMessageSerializer(message).data,
            },
            status=status.HTTP_200_OK,
        )
        
class ImportantChatMessagesListView(APIView):
    def get(self, request):
        search = request.query_params.get("search", "")

        messages = ChatMessage.objects.filter(
            session__user=request.user,
            session__is_deleted=False,
            is_important=True,
        )

        if search:
            messages = messages.filter(content__icontains=search)

        paginator = StandardResultsSetPagination()
        page = paginator.paginate_queryset(messages, request)

        serializer = ChatMessageSerializer(page, many=True)

        return paginator.get_paginated_response(
            {
                "success": True,
                "results": serializer.data,
            }
        )
        
class ChatSessionTimelineView(APIView):
    def get(self, request, pk):
        try:
            session = ChatSession.objects.get(
                pk=pk,
                user=request.user,
                is_deleted=False,
            )
        except ChatSession.DoesNotExist:
            return Response(
                {"success": False, "error": "Chat session not found"},
                status=status.HTTP_404_NOT_FOUND,
            )

        messages = session.messages.all()

        timeline = []

        for index, message in enumerate(messages, start=1):
            timeline.append(
                {
                    "number": index,
                    "id": message.id,
                    "role": message.role,
                    "content": message.content,
                    "is_important": message.is_important,
                    "created_at": message.created_at,
                }
            )

        return Response(
            {
                "success": True,
                "session": {
                    "id": session.id,
                    "title": session.title,
                    "model_name": session.model_name,
                },
                "total_messages": len(timeline),
                "timeline": timeline,
            },
            status=status.HTTP_200_OK,
        )