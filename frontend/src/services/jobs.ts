import { apiClient } from "../lib/api";

export type JobOffer = {
  id: string;
  title: string;
  company_name: string | null;
  location: string | null;
  contract_type: string | null;
  required_skills: string[];
  preferred_skills: string[];
  required_experience_years: number | null;
  education_level: string | null;
  description: string;
  status: string;
  created_at: string;
  updated_at: string;
};

export type JobOfferPayload = {
  title: string;
  company_name?: string | null;
  location?: string | null;
  contract_type?: string | null;
  required_skills: string[];
  preferred_skills: string[];
  required_experience_years?: number | null;
  education_level?: string | null;
  description: string;
  status: string;
};

export async function getJobOffers(): Promise<JobOffer[]> {
  const response = await apiClient.get<JobOffer[]>("/api/jobs");
  return response.data;
}

export async function createJobOffer(payload: JobOfferPayload): Promise<JobOffer> {
  const response = await apiClient.post<JobOffer>("/api/jobs", payload);
  return response.data;
}

export async function getJobOfferById(jobId: string): Promise<JobOffer> {
  const response = await apiClient.get<JobOffer>(`/api/jobs/${jobId}`);
  return response.data;
}

export async function updateJobOffer(jobId: string, payload: Partial<JobOfferPayload>): Promise<JobOffer> {
  const response = await apiClient.put<JobOffer>(`/api/jobs/${jobId}`, payload);
  return response.data;
}

export async function deleteJobOffer(jobId: string): Promise<void> {
  await apiClient.delete(`/api/jobs/${jobId}`);
}
