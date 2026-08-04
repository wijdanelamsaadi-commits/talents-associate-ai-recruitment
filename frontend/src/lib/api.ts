import axios from "axios";

import { getStoredToken } from "./authStorage";

const getDefaultApiBaseUrl = () => {
  if (typeof window === "undefined") {
    return "";
  }
  return `${window.location.protocol}//${window.location.hostname}:8001`;
};

export const API_BASE_URL = import.meta.env.VITE_API_BASE_URL ?? getDefaultApiBaseUrl();

export const apiClient = axios.create({
  baseURL: API_BASE_URL,
  headers: {
    "Content-Type": "application/json",
  },
});

apiClient.interceptors.request.use((config) => {
  const token = getStoredToken();
  if (token) {
    config.headers.Authorization = `Bearer ${token}`;
  }
  return config;
});
