import { apiClient } from "../lib/api";

export type DashboardJobOption = {
  id: string;
  title: string;
  company_name: string | null;
  location: string | null;
  status: string;
  opened_at: string | null;
};

export type PipelineStageCount = {
  stage: string;
  label: string;
  count: number;
};

export type JobPipeline = {
  job_id: string;
  title: string;
  company_name: string | null;
  location: string | null;
  status: string;
  opened_at: string | null;
  stages: PipelineStageCount[];
};

export type DashboardPipelineFilters = {
  job_id?: string;
  job_status?: "all" | "en_cours" | "cloture" | "annule";
  client?: string;
  location?: string;
  opened_from?: string;
  opened_to?: string;
};

export type DashboardPipeline = {
  filter_options: {
    jobs: DashboardJobOption[];
    clients: string[];
    locations: string[];
  };
  pipelines: JobPipeline[];
};

export async function getDashboardPipeline(filters: DashboardPipelineFilters = {}): Promise<DashboardPipeline> {
  const response = await apiClient.get<DashboardPipeline>("/api/dashboard/pipeline", {
    params: {
      ...(filters.job_id ? { job_id: filters.job_id } : {}),
      ...(filters.job_status && filters.job_status !== "all" ? { job_status: filters.job_status } : {}),
      ...(filters.client ? { client: filters.client } : {}),
      ...(filters.location ? { location: filters.location } : {}),
      ...(filters.opened_from ? { opened_from: filters.opened_from } : {}),
      ...(filters.opened_to ? { opened_to: filters.opened_to } : {}),
    },
  });
  return response.data;
}
