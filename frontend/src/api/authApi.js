import apiClient from "./apiClient";

export const loginUser = (data) => {
  return apiClient.post("/auth/login/", data);
};

export const registerUser = (data) => {
  return apiClient.post("/auth/register/", data);
};

export const getProfile = () => {
  return apiClient.get("/auth/me/");
};