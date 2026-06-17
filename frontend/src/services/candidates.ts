import { apiClient } from "../lib/api";

export type Candidate = {
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
  consent_given: boolean;
  owner_user_id: string | null;
  created_at: string;
  updated_at: string;
};

export type CandidateCreatePayload = {
  first_name: string;
  last_name: string;
  email?: string | null;
  phone?: string | null;
  location?: string | null;
  source: string;
};

export async function getCandidates(): Promise<Candidate[]> {
  const response = await apiClient.get<Candidate[]>("/api/candidates");
  return response.data;
}

export async function createCandidate(payload: CandidateCreatePayload): Promise<Candidate> {
  const response = await apiClient.post<Candidate>("/api/candidates", payload);
  return response.data;
}

export async function getCandidateById(candidateId: string): Promise<Candidate> {
  const response = await apiClient.get<Candidate>(`/api/candidates/${candidateId}`);
  return response.data;
}
