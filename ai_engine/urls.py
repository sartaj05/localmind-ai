from django.urls import path

from .views import (
    AskAIView,
    AIChatHistoryListView,
    AIChatHistoryDetailView,
)

urlpatterns = [
    path("ask/", AskAIView.as_view(), name="ask-ai"),
    path("history/", AIChatHistoryListView.as_view(), name="ai-chat-history"),
    path("history/<int:pk>/", AIChatHistoryDetailView.as_view(), name="ai-chat-detail"),
]