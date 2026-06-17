import { apiClient } from "../lib/api";

export type MatchingResult = {
  id: string;
  candidate_id: string;
  job_offer_id: string;
  score: number;
  detailed_scores: Record<string, number> | null;
  matched_skills: string[] | Record<string, unknown> | null;
  missing_skills: string[] | Record<string, unknown> | null;
  explanation: string | null;
  recommendation: string | null;
  status: string;
  created_at: string;
  updated_at: string;
};

export async function runMatching(candidateId: string, jobId: string): Promise<MatchingResult> {
  const response = await apiClient.post<MatchingResult>(`/api/matching/candidate/${candidateId}/job/${jobId}`);
  return response.data;
}

export async function getMatchingResults(): Promise<MatchingResult[]> {
  const response = await apiClient.get<MatchingResult[]>("/api/matching/results");
  return response.data;
}

export async function getCandidateMatchingResults(candidateId: string): Promise<MatchingResult[]> {
  const response = await apiClient.get<MatchingResult[]>(`/api/matching/candidate/${candidateId}`);
  return response.data;
}
