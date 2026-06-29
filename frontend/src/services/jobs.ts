import { apiClient } from "../lib/api";

export type JobLanguage = {
  language: string;
  level: string;
};

export type JobOffer = {
  id: string;
  title: string;
  company_name: string | null;
  location: string | null;
  sector: string | null;
  contract_type: string | null;
  required_skills: string[];
  preferred_skills: string[];
  soft_skills: string[];
  languages: JobLanguage[];
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
  sector?: string | null;
  contract_type?: string | null;
  required_skills: string[];
  preferred_skills?: string[];
  soft_skills?: string[];
  languages?: JobLanguage[];
  required_experience_years?: number | null;
  education_level?: string | null;
  description: string;
  status: string;
};

export async function getJobOffers(): Promise<JobOffer[]> {
  const response = await apiClient.get<JobOffer[]>("/api/jobs");
  return response.data.map(normalizeJobOffer);
}

export async function createJobOffer(payload: JobOfferPayload): Promise<JobOffer> {
  const response = await apiClient.post<JobOffer>("/api/jobs", payload);
  return normalizeJobOffer(response.data);
}

export async function getJobOfferById(jobId: string): Promise<JobOffer> {
  const response = await apiClient.get<JobOffer>(`/api/jobs/${jobId}`);
  return normalizeJobOffer(response.data);
}

export async function updateJobOffer(jobId: string, payload: Partial<JobOfferPayload>): Promise<JobOffer> {
  const response = await apiClient.put<JobOffer>(`/api/jobs/${jobId}`, payload);
  return normalizeJobOffer(response.data);
}

export async function deleteJobOffer(jobId: string): Promise<void> {
  await apiClient.delete(`/api/jobs/${jobId}`);
}

function normalizeJobOffer(job: JobOffer): JobOffer {
  return {
    ...job,
    required_skills: job.required_skills ?? [],
    preferred_skills: job.preferred_skills ?? [],
    soft_skills: job.soft_skills ?? [],
    languages: job.languages ?? [],
  };
}
