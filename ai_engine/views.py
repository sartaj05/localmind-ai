from django.conf import settings
from rest_framework.views import APIView
from rest_framework.response import Response
from rest_framework import status
from django.http import StreamingHttpResponse
from .streaming import stream_ollama_response
from .models import AIChatHistory, ChatSession, ChatMessage
from .serializers import (
    AskAIRequestSerializer,
    AIChatHistorySerializer,
    ChatSessionSerializer,
    ChatSessionDetailSerializer,
    CreateChatSessionSerializer,
    KnowledgeDocumentSerializer,
    RenameChatSessionSerializer,
    SendSessionMessageSerializer,
)
from .services import ask_local_model, build_context_prompt
from .rag_service import build_knowledge_base, search_knowledge
from .models import AIChatHistory, ChatSession, ChatMessage, KnowledgeDocument
class AskAIView(APIView):
    def post(self, request):
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
                {"success": False, "error": str(error)},
                status=status.HTTP_500_INTERNAL_SERVER_ERROR,
            )


class AIChatHistoryListView(APIView):
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
    def get_object(self, pk):
        try:
            return AIChatHistory.objects.get(pk=pk)
        except AIChatHistory.DoesNotExist:
            return None

    def get(self, request, pk):
        chat = self.get_object(pk)

        if chat is None:
            return Response(
                {"success": False, "error": "Chat history not found"},
                status=status.HTTP_404_NOT_FOUND,
            )

        serializer = AIChatHistorySerializer(chat)

        return Response(
            {"success": True, "result": serializer.data},
            status=status.HTTP_200_OK,
        )

    def delete(self, request, pk):
        chat = self.get_object(pk)

        if chat is None:
            return Response(
                {"success": False, "error": "Chat history not found"},
                status=status.HTTP_404_NOT_FOUND,
            )

        chat.delete()

        return Response(
            {"success": True, "message": "Chat history deleted successfully"},
            status=status.HTTP_200_OK,
        )


class ChatSessionListCreateView(APIView):
    def get(self, request):
        sessions = ChatSession.objects.all()
        serializer = ChatSessionSerializer(sessions, many=True)

        return Response(
            {
                "success": True,
                "count": sessions.count(),
                "results": serializer.data,
            },
            status=status.HTTP_200_OK,
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
            title=title,
            model_name=model,
        )

        response_serializer = ChatSessionSerializer(session)

        return Response(
            {
                "success": True,
                "message": "Chat session created successfully",
                "result": response_serializer.data,
            },
            status=status.HTTP_201_CREATED,
        )


class ChatSessionDetailView(APIView):
    def get_object(self, pk):
        try:
            return ChatSession.objects.get(pk=pk)
        except ChatSession.DoesNotExist:
            return None

    def get(self, request, pk):
        session = self.get_object(pk)

        if session is None:
            return Response(
                {"success": False, "error": "Chat session not found"},
                status=status.HTTP_404_NOT_FOUND,
            )

        serializer = ChatSessionDetailSerializer(session)

        return Response(
            {"success": True, "result": serializer.data},
            status=status.HTTP_200_OK,
        )

    def patch(self, request, pk):
        session = self.get_object(pk)

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

        response_serializer = ChatSessionSerializer(session)

        return Response(
            {
                "success": True,
                "message": "Chat session renamed successfully",
                "result": response_serializer.data,
            },
            status=status.HTTP_200_OK,
        )

    def delete(self, request, pk):
        session = self.get_object(pk)

        if session is None:
            return Response(
                {"success": False, "error": "Chat session not found"},
                status=status.HTTP_404_NOT_FOUND,
            )

        session.delete()

        return Response(
            {"success": True, "message": "Chat session deleted successfully"},
            status=status.HTTP_200_OK,
        )


class SendSessionMessageView(APIView):
    def post(self, request, pk):
        try:
            session = ChatSession.objects.get(pk=pk)
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

            ai_answer = ask_local_model(
                prompt=context_prompt,
                model=model,
            )

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
                },
                status=status.HTTP_200_OK,
            )

        except Exception as error:
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
            },
            status=status.HTTP_200_OK,
        )

    def post(self, request):
        prompt = request.data.get("prompt")

        if not prompt:
            return Response(
                {"success": False, "error": "Prompt required"},
                status=status.HTTP_400_BAD_REQUEST,
            )

        model = request.data.get("model")

        generator = stream_ollama_response(
            prompt=prompt,
            model=model,
        )

        return StreamingHttpResponse(
            generator,
            content_type="text/plain",
        )
        
class BuildKnowledgeBaseView(APIView):
    def post(self, request):
        try:
            total_chunks = build_knowledge_base()

            return Response(
                {
                    "success": True,
                    "message": "Knowledge base built successfully",
                    "total_chunks": total_chunks,
                },
                status=status.HTTP_200_OK,
            )

        except Exception as error:
            return Response(
                {"success": False, "error": str(error)},
                status=status.HTTP_500_INTERNAL_SERVER_ERROR,
            )


class AskRAGView(APIView):
    def post(self, request):
        question = request.data.get("question")
        model = request.data.get("model") or settings.DEFAULT_AI_MODEL

        if not question:
            return Response(
                {"success": False, "error": "Question is required"},
                status=status.HTTP_400_BAD_REQUEST,
            )

        try:
            context = search_knowledge(question)

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

            return Response(
                {
                    "success": True,
                    "question": question,
                    "model": model,
                    "context": context,
                    "answer": answer,
                },
                status=status.HTTP_200_OK,
            )

        except Exception as error:
            return Response(
                {"success": False, "error": str(error)},
                status=status.HTTP_500_INTERNAL_SERVER_ERROR,
            )
            
            
class KnowledgeDocumentListCreateView(APIView):
    def get(self, request):
        documents = KnowledgeDocument.objects.all()
        serializer = KnowledgeDocumentSerializer(documents, many=True)

        return Response(
            {
                "success": True,
                "count": documents.count(),
                "results": serializer.data,
            },
            status=status.HTTP_200_OK,
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
            title=title or file.name,
            file=file,
        )

        serializer = KnowledgeDocumentSerializer(document)

        return Response(
            {
                "success": True,
                "message": "Document uploaded successfully",
                "result": serializer.data,
            },
            status=status.HTTP_201_CREATED,
        )


class KnowledgeDocumentDetailView(APIView):
    def delete(self, request, pk):
        try:
            document = KnowledgeDocument.objects.get(pk=pk)
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
            },
            status=status.HTTP_200_OK,
        )