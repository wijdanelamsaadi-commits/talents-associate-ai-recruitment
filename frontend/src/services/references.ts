import { apiClient } from "../lib/api";

export async function getJobReferenceTitles(): Promise<string[]> {
  const response = await apiClient.get<string[]>("/api/references/job-titles");
  return response.data;
}
