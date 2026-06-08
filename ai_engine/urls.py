from django.urls import path

from .views import (
    AskAIView,
    AIChatHistoryListView,
    AIChatHistoryDetailView,
    ChatSessionListCreateView,
    ChatSessionDetailView,
    SendSessionMessageView,
)

urlpatterns = [
    path("ask/", AskAIView.as_view(), name="ask-ai"),

    path("history/", AIChatHistoryListView.as_view(), name="ai-chat-history"),
    path("history/<int:pk>/", AIChatHistoryDetailView.as_view(), name="ai-chat-detail"),

    path("sessions/", ChatSessionListCreateView.as_view(), name="chat-session-list-create"),
    path("sessions/<int:pk>/", ChatSessionDetailView.as_view(), name="chat-session-detail"),
    path("sessions/<int:pk>/messages/", SendSessionMessageView.as_view(), name="send-session-message"),
]