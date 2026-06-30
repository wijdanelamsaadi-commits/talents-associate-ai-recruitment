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

export type CVUploadProcessed = CVFile & {
  processing_status: string;
  confidence_score: number | null;
  parser_model: string | null;
  structured_json: ParsedCVJson | null;
  matching_result_ids: string[];
  message: string | null;
  duplicate: boolean;
  updated_existing: boolean;
};

export type CVBatchResultItem = {
  filename: string;
  status: string;
  candidate_id: string | null;
  error_message: string | null;
};

export type CVBatchUploadSummary = {
  total: number;
  success_count: number;
  error_count: number;
  results: CVBatchResultItem[];
};

export type ExtractedCVText = {
  cv_file_id: string;
  candidate_id: string;
  raw_text: string;
  parsing_status: string;
  confidence_score: number | null;
  parser_model: string | null;
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
  parser_model: string | null;
  structured_json: ParsedCVJson | null;
};

export async function uploadCV(
  candidateId: string | undefined,
  file: File,
  onUploadProgress?: (progressEvent: AxiosProgressEvent) => void,
): Promise<CVUploadProcessed> {
  const formData = new FormData();
  if (candidateId) {
    formData.append("candidate_id", candidateId);
  }
  formData.append("file", file);

  const response = await apiClient.post<CVUploadProcessed>("/api/cv/upload", formData, {
    headers: {
      "Content-Type": "multipart/form-data",
    },
    onUploadProgress,
  });
  return response.data;
}

export async function uploadBatchCVs(
  file: File,
  onUploadProgress?: (progressEvent: AxiosProgressEvent) => void,
): Promise<CVBatchUploadSummary> {
  const formData = new FormData();
  formData.append("file", file);

  const response = await apiClient.post<CVBatchUploadSummary>("/api/cv/upload-batch", formData, {
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

function filenameFromContentDisposition(contentDisposition: string | undefined): string | null {
  if (!contentDisposition) {
    return null;
  }
  const utf8Match = contentDisposition.match(/filename\*=UTF-8''([^;]+)/i);
  if (utf8Match?.[1]) {
    return decodeURIComponent(utf8Match[1]);
  }
  const filenameMatch = contentDisposition.match(/filename="?([^";]+)"?/i);
  return filenameMatch?.[1] ?? null;
}

export async function downloadCVFile(cvFileId: string, fallbackFilename: string): Promise<void> {
  const response = await apiClient.get<Blob>(`/api/cv/${cvFileId}/download`, {
    responseType: "blob",
  });
  const contentDisposition = String(response.headers["content-disposition"] ?? "");
  const contentType = String(response.headers["content-type"] ?? "application/octet-stream");
  const filename = filenameFromContentDisposition(contentDisposition) ?? fallbackFilename;
  const blob = new Blob([response.data], { type: contentType });
  const url = window.URL.createObjectURL(blob);
  const link = document.createElement("a");
  link.href = url;
  link.download = filename;
  document.body.appendChild(link);
  link.click();
  link.remove();
  window.URL.revokeObjectURL(url);
}

export async function deleteCVFile(cvFileId: string): Promise<void> {
  await apiClient.delete(`/api/cv/files/${cvFileId}`);
}
