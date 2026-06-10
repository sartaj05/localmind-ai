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

export const sendSessionMessage = (sessionId, data) => {
  return apiClient.post(`/ai/sessions/${sessionId}/messages/`, data);
};