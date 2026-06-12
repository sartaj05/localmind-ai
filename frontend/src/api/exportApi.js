import apiClient from "./apiClient";

export const exportAllChatSessionsTXT = () =>
  apiClient.get("/ai/sessions/export/all/txt/", {
    responseType: "blob",
  });

export const exportAllChatSessionsJSON = () =>
  apiClient.get("/ai/sessions/export/all/json/", {
    responseType: "blob",
  });

export const clearKnowledgeHistory = () =>
  apiClient.delete("/ai/knowledge-history/clear/");