const API_BASE_URL = import.meta.env.VITE_API_BASE_URL ?? "http://localhost:8001";

export function getCvDownloadUrl(cvFileId: string): string {
  return `${API_BASE_URL}/api/cv/${cvFileId}/download`;
}
