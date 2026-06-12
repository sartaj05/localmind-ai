import apiClient from "./apiClient";

export const exportAllChatSessionsTXT = () =>
  apiClient.get("/ai/sessions/export/all/txt/", {
    responseType: "blob",
  });

export const exportAllChatSessionsJSON = () =>
  apiClient.get("/ai/sessions/export/all/json/", {
    responseType: "blob",
  });

export const clearKnowledgeHistory = (password) =>
  apiClient.delete("/ai/knowledge-history/clear/", {
    data: { password },
  });

export const exportAllKnowledgeHistoryTXT = () =>
  apiClient.get("/ai/knowledge-history/export/all/txt/", {
    responseType: "blob",
  });

export const exportAllKnowledgeHistoryJSON = () =>
  apiClient.get("/ai/knowledge-history/export/all/json/", {
    responseType: "blob",
  });