import apiClient from "./apiClient";

export const getPrompts = (params = {}) =>
  apiClient.get("/ai/prompts/", { params });

export const createPrompt = (data) =>
  apiClient.post("/ai/prompts/", data);

export const updatePrompt = (id, data) =>
  apiClient.patch(`/ai/prompts/${id}/`, data);

export const deletePrompt = (id) =>
  apiClient.delete(`/ai/prompts/${id}/`);

export const togglePinPrompt = (id) =>
  apiClient.patch(`/ai/prompts/${id}/toggle-pin/`);