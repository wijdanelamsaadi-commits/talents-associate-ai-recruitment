import { apiClient } from "../lib/api";
import { JobOffer } from "./jobs";

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
