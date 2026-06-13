import apiClient from "./apiClient";

export const getDashboardDailyRequests = () =>
  apiClient.get("/ai/dashboard/daily-requests/");

export const getDashboardModelUsage = () =>
  apiClient.get("/ai/dashboard/model-usage/");

export const getDashboardSuccessRate = () =>
  apiClient.get("/ai/dashboard/success-rate/");