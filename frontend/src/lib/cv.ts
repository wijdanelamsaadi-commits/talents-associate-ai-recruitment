import { API_BASE_URL } from "./api";

export function getCvDownloadUrl(cvFileId: string): string {
  return `${API_BASE_URL}/api/cv/${cvFileId}/download`;
}
