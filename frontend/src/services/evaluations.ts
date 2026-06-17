import { apiClient } from "../lib/api";

export type Evaluation = {
  id: string;
  interview_id: string;
  application_id: string;
  candidate_id: string;
  evaluator_name: string;
  technical_score: number;
  soft_skills_score: number;
  motivation_score: number;
  communication_score: number;
  culture_fit_score: number;
  global_score: number;
  recommendation: string;
  strengths: string | null;
  weaknesses: string | null;
  comments: string | null;
  submitted_at: string | null;
  created_at: string;
  updated_at: string;
};

export type EvaluationPayload = {
  interview_id: string;
  candidate_id?: string | null;
  evaluator_name: string;
  technical_score: number;
  soft_skills_score: number;
  motivation_score: number;
  communication_score: number;
  culture_fit_score: number;
  recommendation: string;
  strengths?: string | null;
  weaknesses?: string | null;
  comments?: string | null;
};

export async function getEvaluations(): Promise<Evaluation[]> {
  const response = await apiClient.get<Evaluation[]>("/api/evaluations");
  return response.data;
}

export async function getEvaluationById(evaluationId: string): Promise<Evaluation> {
  const response = await apiClient.get<Evaluation>(`/api/evaluations/${evaluationId}`);
  return response.data;
}

export async function getInterviewEvaluations(interviewId: string): Promise<Evaluation[]> {
  const response = await apiClient.get<Evaluation[]>(`/api/evaluations/interview/${interviewId}`);
  return response.data;
}

export async function createEvaluation(payload: EvaluationPayload): Promise<Evaluation> {
  const response = await apiClient.post<Evaluation>("/api/evaluations", payload);
  return response.data;
}

export async function updateEvaluation(evaluationId: string, payload: Partial<EvaluationPayload>): Promise<Evaluation> {
  const response = await apiClient.put<Evaluation>(`/api/evaluations/${evaluationId}`, payload);
  return response.data;
}

export async function deleteEvaluation(evaluationId: string): Promise<void> {
  await apiClient.delete(`/api/evaluations/${evaluationId}`);
}
