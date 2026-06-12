import apiClient from "./apiClient";

export const getAIHealth = () => apiClient.get("/ai/health/");
export const getModels = () => apiClient.get("/ai/models/");
export const askAI = (data) => apiClient.post("/ai/ask/", data);

export const getSessions = () => apiClient.get("/ai/sessions/");
export const getArchivedSessions = () => apiClient.get("/ai/sessions/?archived=true");
export const getTrashSessions = () => apiClient.get("/ai/sessions/trash/");
export const createSession = (data) => apiClient.post("/ai/sessions/", data);
export const getSessionDetail = (sessionId) => apiClient.get(`/ai/sessions/${sessionId}/`);
export const sendSessionMessage = (sessionId, data) => apiClient.post(`/ai/sessions/${sessionId}/messages/`, data);
export const renameSession = (sessionId, data) => apiClient.patch(`/ai/sessions/${sessionId}/`, data);
export const deleteSession = (sessionId) => apiClient.delete(`/ai/sessions/${sessionId}/`);
export const togglePinSession = (sessionId) => apiClient.patch(`/ai/sessions/${sessionId}/toggle-pin/`);
export const toggleArchiveSession = (sessionId) => apiClient.patch(`/ai/sessions/${sessionId}/toggle-archive/`);
export const restoreSession = (sessionId) => apiClient.patch(`/ai/sessions/${sessionId}/restore/`);
export const permanentDeleteSession = (sessionId) => apiClient.delete(`/ai/sessions/${sessionId}/permanent-delete/`);
export const emptyTrashSessions = () => apiClient.delete("/ai/sessions/trash/empty/");

export const getKnowledgeDocuments = () => apiClient.get("/ai/documents/");
export const uploadKnowledgeDocument = (formData) =>
  apiClient.post("/ai/documents/", formData, {
    headers: { "Content-Type": "multipart/form-data" },
  });
export const deleteKnowledgeDocument = (documentId) => apiClient.delete(`/ai/documents/${documentId}/`);
export const rebuildKnowledgeDocument = (documentId) => apiClient.post(`/ai/documents/${documentId}/rebuild/`);
export const getDocumentChunks = (documentId) => apiClient.get(`/ai/documents/${documentId}/chunks/`);

export const buildKnowledgeBase = () => apiClient.post("/ai/rag/build/");
export const getKnowledgeBaseStatus = () => apiClient.get("/ai/rag/status/");
export const askRAG = (data) => apiClient.post("/ai/rag/ask/", data);
export const sendSessionRAGMessage = (sessionId, data) => apiClient.post(`/ai/sessions/${sessionId}/rag-message/`, data);

export const streamRAGAsk = (sessionId, data) => {
  return fetch(`${import.meta.env.VITE_API_BASE_URL}/ai/sessions/${sessionId}/rag-stream/`, {
    method: "POST",
    headers: {
      Authorization: `Bearer ${localStorage.getItem("access_token")}`,
      "Content-Type": "application/json",
    },
    body: JSON.stringify(data),
  });
};

export const getAIPreferences = () => apiClient.get("/ai/preferences/");
export const updateAIPreferences = (data) => apiClient.patch("/ai/preferences/", data);

export const getDailyUsage = () => apiClient.get("/ai/usage/daily/");
export const getDashboardSummary = () => apiClient.get("/ai/dashboard/summary/");
export const getKnowledgeHistory = () =>
  apiClient.get("/ai/knowledge-history/");

export const getKnowledgeHistoryDetail = (id) =>
  apiClient.get(`/ai/knowledge-history/${id}/`);

export const deleteKnowledgeHistory = (id) =>
  apiClient.delete(`/ai/knowledge-history/${id}/`);
export const exportKnowledgeHistoryTXT = (id) =>
  apiClient.get(`/ai/knowledge-history/${id}/export/txt/`, {
    responseType: "blob",
  });

export const exportKnowledgeHistoryJSON = (id) =>
  apiClient.get(`/ai/knowledge-history/${id}/export/json/`, {
    responseType: "blob",
  });

export const exportChatSessionTXT = (sessionId) =>
  apiClient.get(`/ai/sessions/${sessionId}/export-txt/`, {
    responseType: "blob",
  });

export const exportChatSessionJSON = (sessionId) =>
  apiClient.get(`/ai/sessions/${sessionId}/export-json/`, {
    responseType: "blob",
  });

export const exportAllKnowledgeHistoryTXT = () =>
  apiClient.get("/ai/knowledge-history/export/all/txt/", {
    responseType: "blob",
  });

export const exportAllKnowledgeHistoryJSON = () =>
  apiClient.get("/ai/knowledge-history/export/all/json/", {
    responseType: "blob",
  });