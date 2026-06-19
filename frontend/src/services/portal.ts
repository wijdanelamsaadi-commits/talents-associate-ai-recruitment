import axios from "axios";

import { apiClient } from "../lib/api";
import {
  clearStoredCandidateAuth,
  getStoredCandidateToken,
  storeCandidateAuth,
  storeCandidateProfile,
} from "../lib/portalAuthStorage";
import { JobOffer } from "./jobs";

const portalApiClient = axios.create({
  baseURL: import.meta.env.VITE_API_BASE_URL ?? "http://localhost:8001",
});

portalApiClient.interceptors.request.use((config) => {
  const token = getStoredCandidateToken();
  if (token) {
    config.headers.Authorization = `Bearer ${token}`;
  }
  return config;
});

export type CandidateProfile = {
  id: string;
  first_name: string;
  last_name: string;
  email: string | null;
  phone: string | null;
  location: string | null;
  linkedin_url: string | null;
  portfolio_url: string | null;
  current_title: string | null;
  source: string;
  status: string;
  account_status: string;
  latest_cv_file_id: string | null;
  latest_cv_filename: string | null;
  latest_cv_uploaded_at: string | null;
};

export type CandidateAuthResponse = {
  access_token: string;
  token_type: "bearer";
  candidate: CandidateProfile;
};

export type CandidateRegisterPayload = {
  first_name: string;
  last_name: string;
  email: string;
  password: string;
  phone?: string;
  location?: string;
  current_title?: string;
};

export type CandidateLoginPayload = {
  email: string;
  password: string;
};

export type CandidateProfileUpdatePayload = {
  first_name?: string;
  last_name?: string;
  phone?: string;
  location?: string;
  linkedin_url?: string;
  portfolio_url?: string;
  current_title?: string;
};

export type PortalApplicationPayload = {
  first_name: string;
  last_name: string;
  email: string;
  phone?: string;
  location?: string;
  file: File;
};

export type PortalApplicationResponse = {
  candidate_id: string;
  application_id: string;
  cv_file_id: string;
  parsing_status: string;
  confidence_score: number | null;
  matching_result_ids: string[];
  message: string;
};

export type PortalApplicationStatusItem = {
  application_id: string;
  job_offer_id: string;
  job_title: string;
  company_name: string | null;
  application_status: string;
  current_stage: string | null;
  applied_at: string;
  cv_file_id: string | null;
  best_matching_score: number | null;
  recommendation: string | null;
  matching_result_ids?: string[];
};

export type PortalApplicationStatusResponse = {
  email: string;
  candidate_id: string | null;
  applications: PortalApplicationStatusItem[];
};

export async function getPublicJobs(): Promise<JobOffer[]> {
  const response = await apiClient.get<JobOffer[]>("/api/portal/jobs");
  return Array.isArray(response.data) ? response.data : [];
}

export async function getPublicJob(jobId: string): Promise<JobOffer> {
  const response = await apiClient.get<JobOffer>(`/api/portal/jobs/${jobId}`);
  return response.data;
}

export async function registerCandidate(payload: CandidateRegisterPayload): Promise<CandidateAuthResponse> {
  const response = await portalApiClient.post<CandidateAuthResponse>("/api/portal/auth/register", payload);
  storeCandidateAuth(response.data.access_token, response.data.candidate);
  return response.data;
}

export async function loginCandidate(payload: CandidateLoginPayload): Promise<CandidateAuthResponse> {
  const response = await portalApiClient.post<CandidateAuthResponse>("/api/portal/auth/login", payload);
  storeCandidateAuth(response.data.access_token, response.data.candidate);
  return response.data;
}

export async function getCandidateProfile(): Promise<CandidateProfile> {
  const response = await portalApiClient.get<CandidateProfile>("/api/portal/profile");
  storeCandidateProfile(response.data);
  return response.data;
}

export async function updateCandidateProfile(payload: CandidateProfileUpdatePayload): Promise<CandidateProfile> {
  const response = await portalApiClient.put<CandidateProfile>("/api/portal/profile", payload);
  storeCandidateProfile(response.data);
  return response.data;
}

export async function replaceCandidateCv(file: File): Promise<CandidateProfile> {
  const formData = new FormData();
  formData.append("file", file);
  const response = await portalApiClient.put<CandidateProfile>("/api/portal/profile/cv", formData, {
    headers: { "Content-Type": "multipart/form-data" },
  });
  storeCandidateProfile(response.data);
  return response.data;
}

export async function submitAuthenticatedApplication(jobId: string): Promise<PortalApplicationResponse> {
  const response = await portalApiClient.post<PortalApplicationResponse>(`/api/portal/jobs/${jobId}/apply-auth`);
  return response.data;
}

export async function getCandidateApplications(): Promise<PortalApplicationStatusItem[]> {
  const response = await portalApiClient.get<PortalApplicationStatusItem[]>("/api/portal/applications");
  return Array.isArray(response.data) ? response.data : [];
}

export function logoutCandidate() {
  clearStoredCandidateAuth();
}

export async function submitPortalApplication(jobId: string, payload: PortalApplicationPayload): Promise<PortalApplicationResponse> {
  const formData = new FormData();
  formData.append("first_name", payload.first_name);
  formData.append("last_name", payload.last_name);
  formData.append("email", payload.email);
  if (payload.phone) {
    formData.append("phone", payload.phone);
  }
  if (payload.location) {
    formData.append("location", payload.location);
  }
  formData.append("file", payload.file);

  const response = await apiClient.post<PortalApplicationResponse>(`/api/portal/jobs/${jobId}/apply`, formData, {
    headers: { "Content-Type": "multipart/form-data" },
  });
  return response.data;
}

export async function getPortalApplicationStatus(email: string): Promise<PortalApplicationStatusResponse> {
  const response = await apiClient.get<PortalApplicationStatusResponse>("/api/portal/status", {
    params: { email },
  });
  return {
    ...response.data,
    applications: Array.isArray(response.data.applications) ? response.data.applications : [],
  };
}
