import { apiClient } from "../lib/api";

export type Interview = {
  id: string;
  application_id: string;
  candidate_id: string;
  job_offer_id: string;
  interview_type: string;
  status: string;
  scheduled_start_at: string;
  scheduled_end_at: string | null;
  meeting_url: string | null;
  location: string | null;
  notes: string | null;
  scheduled_by_user_id: string | null;
  interviewer_user_id: string | null;
  created_at: string;
  updated_at: string;
};

export type InterviewPayload = {
  candidate_id: string;
  job_offer_id: string;
  interview_type: string;
  status: string;
  scheduled_start_at: string;
  scheduled_end_at?: string | null;
  meeting_url?: string | null;
  location?: string | null;
  notes?: string | null;
};

export async function getInterviews(): Promise<Interview[]> {
  const response = await apiClient.get<Interview[]>("/api/interviews");
  return response.data;
}

export async function getInterviewById(interviewId: string): Promise<Interview> {
  const response = await apiClient.get<Interview>(`/api/interviews/${interviewId}`);
  return response.data;
}

export async function createInterview(payload: InterviewPayload): Promise<Interview> {
  const response = await apiClient.post<Interview>("/api/interviews", payload);
  return response.data;
}

export async function updateInterview(interviewId: string, payload: Partial<InterviewPayload>): Promise<Interview> {
  const response = await apiClient.put<Interview>(`/api/interviews/${interviewId}`, payload);
  return response.data;
}

export async function updateInterviewStatus(interviewId: string, status: string): Promise<Interview> {
  const response = await apiClient.patch<Interview>(`/api/interviews/${interviewId}/status`, { status });
  return response.data;
}

export async function deleteInterview(interviewId: string): Promise<void> {
  await apiClient.delete(`/api/interviews/${interviewId}`);
}
