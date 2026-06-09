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
    AIUsageLogListView,
    AIDashboardSummaryView,
    AIRecentActivityView,
    ClearAIChatHistoryView,
    ClearKnowledgeDocumentsView,
    ClearAIUsageLogsView,
    ChatMessageDetailView,
    RegenerateChatMessageView,
    RegenerateRAGChatMessageView,
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
    path("usage-logs/", AIUsageLogListView.as_view(), name="ai-usage-logs"),
    path("dashboard/summary/", AIDashboardSummaryView.as_view(), name="ai-dashboard-summary"),
    path("dashboard/recent-activity/", AIRecentActivityView.as_view(), name="ai-recent-activity"),
    path(
        "history/clear/",
        ClearAIChatHistoryView.as_view(),
        name="clear-ai-chat-history",
    ),
    path(
        "documents/clear/",
        ClearKnowledgeDocumentsView.as_view(),
        name="clear-knowledge-documents",
    ),
    path(
        "usage-logs/clear/",
        ClearAIUsageLogsView.as_view(),
        name="clear-ai-usage-logs",
    ),
    path(
        "sessions/<int:session_pk>/messages/<int:message_pk>/",
        ChatMessageDetailView.as_view(),
        name="chat-message-detail",
    ),
    path(
        "sessions/<int:session_pk>/messages/<int:message_pk>/regenerate/",
        RegenerateChatMessageView.as_view(),
        name="regenerate-chat-message",
    ),
    path(
        "sessions/<int:session_pk>/messages/<int:message_pk>/regenerate-rag/",
        RegenerateRAGChatMessageView.as_view(),
        name="regenerate-rag-chat-message",
    ),
]