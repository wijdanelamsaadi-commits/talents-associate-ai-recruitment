import { apiClient } from "../lib/api";

export type TimelineEvent = {
  id: string;
  candidate_id: string;
  event_type: string;
  title: string;
  description: string | null;
  metadata: Record<string, unknown> | null;
  created_at: string;
};

export type TimelineEventPayload = {
  event_type: string;
  title: string;
  description?: string | null;
  metadata?: Record<string, unknown> | null;
};

export async function getCandidateTimeline(candidateId: string): Promise<TimelineEvent[]> {
  const response = await apiClient.get<TimelineEvent[]>(`/api/candidates/${candidateId}/timeline`);
  return response.data;
}

export async function createCandidateTimelineEvent(
  candidateId: string,
  payload: TimelineEventPayload,
): Promise<TimelineEvent> {
  const response = await apiClient.post<TimelineEvent>(`/api/candidates/${candidateId}/timeline`, payload);
  return response.data;
}

export async function deleteTimelineEvent(eventId: string): Promise<void> {
  await apiClient.delete(`/api/timeline/${eventId}`);
}
