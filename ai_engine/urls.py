from django.urls import path

from .views import (
    AskAIView,
    AIChatHistoryListView,
    AIChatHistoryDetailView,
    ChatSessionListCreateView,
    ChatSessionDetailView,
    SendSessionMessageView,
    BuildKnowledgeBaseView,
    AskRAGView,
    KnowledgeDocumentListCreateView,
    KnowledgeDocumentDetailView,
    SendSessionRAGMessageView,
    StreamSessionRAGMessageView,
    LocalModelListView,
    AIHealthCheckView,
)
from .views import StreamAIView
urlpatterns = [
    path("ask/", AskAIView.as_view(), name="ask-ai"),

    path("history/", AIChatHistoryListView.as_view(), name="ai-chat-history"),
    path("history/<int:pk>/", AIChatHistoryDetailView.as_view(), name="ai-chat-detail"),

    path("sessions/", ChatSessionListCreateView.as_view(), name="chat-session-list-create"),
    path("sessions/<int:pk>/", ChatSessionDetailView.as_view(), name="chat-session-detail"),
    path("sessions/<int:pk>/messages/", SendSessionMessageView.as_view(), name="send-session-message"),
    path(
        "stream/",
        StreamAIView.as_view(),
        name="stream-ai",
    ),
    path("rag/build/", BuildKnowledgeBaseView.as_view(), name="rag-build"),
    path("rag/ask/", AskRAGView.as_view(), name="rag-ask"),
    path("documents/", KnowledgeDocumentListCreateView.as_view(), name="knowledge-documents"),
    path("documents/<int:pk>/", KnowledgeDocumentDetailView.as_view(), name="knowledge-document-detail"),
    path(
        "sessions/<int:pk>/rag-message/",
        SendSessionRAGMessageView.as_view(),
        name="send-session-rag-message",
    ),
    path(
        "sessions/<int:pk>/rag-stream/",
        StreamSessionRAGMessageView.as_view(),
        name="stream-session-rag-message",
    ),
    path("models/", LocalModelListView.as_view(), name="local-model-list"),
    path("health/", AIHealthCheckView.as_view(), name="ai-health-check"),
]