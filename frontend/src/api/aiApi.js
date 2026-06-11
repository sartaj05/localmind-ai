import apiClient from "./apiClient";

export const getAIHealth = () => {
  return apiClient.get("/ai/health/");
};

export const getModels = () => {
  return apiClient.get("/ai/models/");
};

export const askAI = (data) => {
  return apiClient.post("/ai/ask/", data);
};

export const getSessions = () => {
  return apiClient.get("/ai/sessions/");
};

export const getArchivedSessions = () => {
  return apiClient.get("/ai/sessions/?archived=true");
};

export const getTrashSessions = () => {
  return apiClient.get("/ai/sessions/trash/");
};

export const createSession = (data) => {
  return apiClient.post("/ai/sessions/", data);
};

export const getSessionDetail = (sessionId) => {
  return apiClient.get(`/ai/sessions/${sessionId}/`);
};

export const sendSessionMessage = (sessionId, data) => {
  return apiClient.post(`/ai/sessions/${sessionId}/messages/`, data);
};

export const renameSession = (sessionId, data) => {
  return apiClient.patch(`/ai/sessions/${sessionId}/`, data);
};

export const deleteSession = (sessionId) => {
  return apiClient.delete(`/ai/sessions/${sessionId}/`);
};

export const togglePinSession = (sessionId) => {
  return apiClient.patch(`/ai/sessions/${sessionId}/toggle-pin/`);
};

export const toggleArchiveSession = (sessionId) => {
  return apiClient.patch(`/ai/sessions/${sessionId}/toggle-archive/`);
};

export const restoreSession = (sessionId) => {
  return apiClient.patch(`/ai/sessions/${sessionId}/restore/`);
};

export const permanentDeleteSession = (sessionId) => {
  return apiClient.delete(`/ai/sessions/${sessionId}/permanent-delete/`);
};

export const emptyTrashSessions = () => {
  return apiClient.delete("/ai/sessions/trash/empty/");
};

export const getKnowledgeDocuments = () => {
  return apiClient.get("/ai/documents/");
};

export const uploadKnowledgeDocument = (formData) => {
  return apiClient.post("/ai/documents/", formData, {
    headers: {
      "Content-Type": "multipart/form-data",
    },
  });
};

export const deleteKnowledgeDocument = (documentId) => {
  return apiClient.delete(`/ai/documents/${documentId}/`);
};

export const rebuildKnowledgeDocument = (documentId) => {
  return apiClient.post(`/ai/documents/${documentId}/rebuild/`);
};

export const getDocumentChunks = (documentId) => {
  return apiClient.get(`/ai/documents/${documentId}/chunks/`);
};

export const buildKnowledgeBase = () => {
  return apiClient.post("/ai/rag/build/");
};

export const getKnowledgeBaseStatus = () => {
  return apiClient.get("/ai/rag/status/");
};

export const askRAG = (data) => {
  return apiClient.post("/ai/rag/ask/", data);
};

export const sendSessionRAGMessage = (sessionId, data) => {
  return apiClient.post(`/ai/sessions/${sessionId}/rag-message/`, data);
};

export const streamRAGAsk = (sessionId, data) => {
  return fetch(
    `${import.meta.env.VITE_API_BASE_URL}/ai/sessions/${sessionId}/rag-stream/`,
    {
      method: "POST",
      headers: {
        Authorization: `Bearer ${localStorage.getItem("access_token")}`,
        "Content-Type": "application/json",
      },
      body: JSON.stringify(data),
    }
  );
};