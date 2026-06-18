import { apiClient } from "../lib/api";

export type DashboardCount = {
  name: string;
  count: number;
};

export type DashboardActivity = {
  id: string;
  candidate_id: string;
  event_type: string;
  title: string;
  description: string | null;
  metadata: Record<string, unknown> | null;
  created_at: string;
};

export type DashboardStats = {
  total_candidates: number;
  candidate_counts: DashboardCount[];
  total_jobs: number;
  open_jobs: number;
  job_counts: DashboardCount[];
  total_interviews: number;
  upcoming_interviews: number;
  interview_counts: DashboardCount[];
  total_evaluations: number;
  total_outlook_imports: number;
  total_outlook_imported: number;
  average_matching_score: number | null;
  matching_score_buckets: DashboardCount[];
  recent_activities: DashboardActivity[];
};

function toArray<T>(value: T[] | { items?: T[] } | unknown): T[] {
  if (Array.isArray(value)) {
    return value;
  }
  if (value && typeof value === "object" && Array.isArray((value as { items?: T[] }).items)) {
    return (value as { items: T[] }).items;
  }
  return [];
}

export async function getDashboardStats(): Promise<DashboardStats> {
  const response = await apiClient.get<DashboardStats>("/api/dashboard/stats");
  const data = response.data;

  return {
    ...data,
    candidate_counts: toArray<DashboardCount>(data.candidate_counts),
    job_counts: toArray<DashboardCount>(data.job_counts),
    interview_counts: toArray<DashboardCount>(data.interview_counts),
    matching_score_buckets: toArray<DashboardCount>(data.matching_score_buckets),
    recent_activities: toArray<DashboardActivity>(data.recent_activities),
  };
}
