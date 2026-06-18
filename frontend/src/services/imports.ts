import { apiClient } from "../lib/api";

export type LinkedInImport = {
  id: string;
  filename: string;
  imported_count: number;
  updated_count: number;
  skipped_count: number;
  report: { rows?: Array<Record<string, unknown>> } | null;
  created_at: string;
  updated_at: string;
};

export type LinkedInImportSummary = {
  total_imports: number;
  total_imported: number;
  total_updated: number;
  total_skipped: number;
};

export async function uploadLinkedInCSV(file: File): Promise<LinkedInImport> {
  const formData = new FormData();
  formData.append("file", file);
  const response = await apiClient.post<LinkedInImport>("/api/imports/linkedin-csv", formData, {
    headers: { "Content-Type": "multipart/form-data" },
  });
  return response.data;
}

export async function getLinkedInImports(): Promise<LinkedInImport[]> {
  const response = await apiClient.get<LinkedInImport[]>("/api/imports/linkedin-csv");
  return Array.isArray(response.data) ? response.data : [];
}

export async function getLinkedInImportSummary(): Promise<LinkedInImportSummary> {
  const response = await apiClient.get<LinkedInImportSummary>("/api/imports/linkedin-csv/summary");
  return response.data;
}
