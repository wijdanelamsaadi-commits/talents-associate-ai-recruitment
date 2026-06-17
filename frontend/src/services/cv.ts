import { AxiosProgressEvent } from "axios";

import { apiClient } from "../lib/api";

export type CVFile = {
  id: string;
  candidate_id: string;
  original_filename: string;
  storage_path: string;
  mime_type: string | null;
  file_size_bytes: number | null;
  checksum_sha256: string | null;
  parsing_status: string;
  uploaded_at: string;
  created_at: string;
  updated_at: string;
};

export type ExtractedCVText = {
  cv_file_id: string;
  candidate_id: string;
  raw_text: string;
  parsing_status: string;
  confidence_score: number | null;
  ai_output: ParsedCVJson | null;
};

export type ParsedCVJson = {
  first_name?: string;
  last_name?: string;
  email?: string;
  phone?: string;
  skills?: unknown[];
  languages?: unknown[];
  education?: unknown[];
  experience?: unknown[];
  certifications?: unknown[];
};

export type ParsedCV = {
  cv_file_id: string;
  parsing_status: string;
  confidence_score: number | null;
  structured_json: ParsedCVJson | null;
};

export async function uploadCV(
  candidateId: string,
  file: File,
  onUploadProgress?: (progressEvent: AxiosProgressEvent) => void,
): Promise<CVFile> {
  const formData = new FormData();
  formData.append("candidate_id", candidateId);
  formData.append("file", file);

  const response = await apiClient.post<CVFile>("/api/cv/upload", formData, {
    headers: {
      "Content-Type": "multipart/form-data",
    },
    onUploadProgress,
  });
  return response.data;
}

export async function getCVFiles(): Promise<CVFile[]> {
  const response = await apiClient.get<CVFile[]>("/api/cv/files");
  return response.data;
}

export async function getCVFileById(cvFileId: string): Promise<CVFile> {
  const response = await apiClient.get<CVFile>(`/api/cv/files/${cvFileId}`);
  return response.data;
}

export async function getCVText(cvFileId: string): Promise<ExtractedCVText> {
  const response = await apiClient.get<ExtractedCVText>(`/api/cv/files/${cvFileId}/text`);
  return response.data;
}

export async function parseCV(cvFileId: string): Promise<ParsedCV> {
  const response = await apiClient.post<ParsedCV>(`/api/cv/${cvFileId}/parse`);
  return response.data;
}

export async function getParsedCV(cvFileId: string): Promise<ParsedCV> {
  const response = await apiClient.get<ParsedCV>(`/api/cv/${cvFileId}/parsed`);
  return response.data;
}

export async function deleteCVFile(cvFileId: string): Promise<void> {
  await apiClient.delete(`/api/cv/files/${cvFileId}`);
}
