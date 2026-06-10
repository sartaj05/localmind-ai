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
export const getArchivedSessions = () => {
  return apiClient.get("/ai/sessions/?archived=true");
};

export const getTrashSessions = () => {
  return apiClient.get("/ai/sessions/trash/");
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