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
  current_company: string | null;
  sector: string | null;
  gender: "M" | "F" | null;
  source: string;
  status: string;
  is_talent_pool: boolean;
  archived_at: string | null;
  rejected_at: string | null;
  reactivated_at: string | null;
  last_decision_at: string | null;
  consent_given: boolean;
  owner_user_id: string | null;
  created_at: string;
  updated_at: string;
};

export type PaginatedCandidatesResponse = {
  items: Candidate[];
  total: number;
  next_cursor: string | null;
};

export type CandidateHistoryMatchingResult = {
  id: string;
  application_id: string | null;
  job_offer_id: string;
  job_title: string | null;
  score: string | number;
  semantic_score: number | null;
  used_semantic_embedding: boolean;
  recommendation: string | null;
  explanation: string | null;
  matched_skills: unknown;
  missing_skills: unknown;
  detailed_scores: Record<string, unknown> | null;
  created_at: string;
};

export type CandidateHistoryInterview = {
  id: string;
  application_id: string;
  interview_type: string;
  status: string;
  scheduled_start_at: string;
  scheduled_end_at: string | null;
  location: string | null;
  meeting_url: string | null;
  notes: string | null;
};

export type CandidateHistoryEvaluation = {
  id: string;
  application_id: string;
  interview_id: string | null;
  evaluator_name: string | null;
  rating: number | null;
  technical_score: number | null;
  soft_skills_score: number | null;
  motivation_score: number | null;
  communication_score: number | null;
  culture_fit_score: number | null;
  global_score: string | number | null;
  recommendation: string;
  strengths: string | null;
  weaknesses: string | null;
  comments: string | null;
  notes: string | null;
  submitted_at: string | null;
};

export type CandidateHistoryApplication = {
  id: string;
  job_offer_id: string;
  job_title: string;
  company_name: string | null;
  source: string;
  status: string;
  current_stage: string | null;
  applied_at: string;
  cv_file_id: string | null;
  matching_results: CandidateHistoryMatchingResult[];
  interviews: CandidateHistoryInterview[];
  evaluations: CandidateHistoryEvaluation[];
};

export type CandidateHistoryCVFile = {
  id: string;
  original_filename: string;
  mime_type: string | null;
  file_size_bytes: number | null;
  parsing_status: string;
  parser_model: string | null;
  uploaded_at: string;
};

export type CandidateHistoryTimelineEvent = {
  id: string;
  event_type: string;
  title: string;
  description: string | null;
  metadata: Record<string, unknown> | null;
  created_at: string;
};

export type CandidateHistory = {
  candidate: Candidate;
  cv_files: CandidateHistoryCVFile[];
  applications: CandidateHistoryApplication[];
  matching_results: CandidateHistoryMatchingResult[];
  interviews: CandidateHistoryInterview[];
  evaluations: CandidateHistoryEvaluation[];
  timeline_events: CandidateHistoryTimelineEvent[];
};

export type ApplicationDecisionResponse = {
  id: string;
  candidate_id: string;
  job_offer_id: string;
  cv_file_id: string | null;
  source: string;
  status: string;
  current_stage: string | null;
  applied_at: string;
  created_at: string;
  updated_at: string;
};

export type CandidateCreatePayload = {
  first_name: string;
  last_name: string;
  email?: string | null;
  phone?: string | null;
  location?: string | null;
  linkedin_url?: string | null;
  portfolio_url?: string | null;
  current_title?: string | null;
  current_company?: string | null;
  sector?: string | null;
  gender?: "M" | "F" | null;
  source: string;
  status?: string;
};

export type CandidateUpdatePayload = Partial<CandidateCreatePayload>;

export async function getCandidatesPaginated(params?: {
  skip?: number;
  limit?: number;
  after_id?: string | null;
  filter?: "all" | "active" | "rejected" | "archived" | "talent_pool";
  job_offer_id?: string;
  pipeline_stage?: string;
}): Promise<PaginatedCandidatesResponse> {
  const response = await apiClient.get<PaginatedCandidatesResponse>("/api/candidates", {
    params: {
      skip: params?.skip ?? 0,
      limit: params?.limit ?? 100,
      filter: params?.filter ?? "all",
      ...(params?.after_id ? { after_id: params.after_id } : {}),
      ...(params?.job_offer_id ? { job_offer_id: params.job_offer_id } : {}),
      ...(params?.pipeline_stage ? { pipeline_stage: params.pipeline_stage } : {}),
    },
  });
  return response.data;
}

export async function getCandidates(params?: { skip?: number; limit?: number }): Promise<Candidate[]> {
  const response = await getCandidatesPaginated(params);
  return response.items;
}

export async function createCandidate(payload: CandidateCreatePayload): Promise<Candidate> {
  const response = await apiClient.post<Candidate>("/api/candidates", payload);
  return response.data;
}

export async function getCandidateById(candidateId: string): Promise<Candidate> {
  const response = await apiClient.get<Candidate>(`/api/candidates/${candidateId}`);
  return response.data;
}

export async function getCandidateHistory(candidateId: string): Promise<CandidateHistory> {
  const response = await apiClient.get<CandidateHistory>(`/api/candidates/${candidateId}/history`);
  return response.data;
}

export async function updateCandidate(candidateId: string, payload: CandidateUpdatePayload): Promise<Candidate> {
  const response = await apiClient.put<Candidate>(`/api/candidates/${candidateId}`, payload);
  return response.data;
}

export async function deleteCandidate(candidateId: string): Promise<void> {
  await apiClient.delete(`/api/candidates/${candidateId}`);
}

export async function archiveCandidate(candidateId: string): Promise<Candidate> {
  const response = await apiClient.patch<Candidate>(`/api/candidates/${candidateId}/archive`);
  return response.data;
}

export async function reactivateCandidate(candidateId: string, keepInTalentPool = false): Promise<Candidate> {
  const response = await apiClient.patch<Candidate>(`/api/candidates/${candidateId}/reactivate`, null, {
    params: { keep_in_talent_pool: keepInTalentPool },
  });
  return response.data;
}

export async function acceptApplication(applicationId: string): Promise<ApplicationDecisionResponse> {
  const response = await apiClient.patch<ApplicationDecisionResponse>(`/api/applications/${applicationId}/accept`);
  return response.data;
}

export async function rejectApplication(applicationId: string): Promise<ApplicationDecisionResponse> {
  const response = await apiClient.patch<ApplicationDecisionResponse>(`/api/applications/${applicationId}/reject`);
  return response.data;
}

export async function reactivateApplication(applicationId: string): Promise<ApplicationDecisionResponse> {
  const response = await apiClient.patch<ApplicationDecisionResponse>(`/api/applications/${applicationId}/reactivate`);
  return response.data;
}

export type VivierSearchResult = {
  candidate: Candidate;
  score: number;
  has_cv: boolean;
  cv_file_id: string | null;
};

export type VivierSearchParams = {
  poste?: string;
  secteur?: string;
  experience_level?: string;
  education_level?: string;
  contract_type?: string;
  technical_skills?: string;
  soft_skills?: string;
  langues?: string;
};

export async function searchCandidatesVivier(params: VivierSearchParams): Promise<VivierSearchResult[]> {
  const response = await apiClient.get<VivierSearchResult[]>("/api/matching/search", { params });
  return response.data;
}
