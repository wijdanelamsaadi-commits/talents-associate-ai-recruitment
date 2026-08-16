import axios from "axios";

import { apiClient } from "../lib/api";
import { getStoredToken } from "../lib/authStorage";

const FALLBACK_API_BASE_URL = "https://api.talentsag.ma";

function assertJobTitleList(value: unknown): string[] {
  if (!Array.isArray(value) || !value.every((item) => typeof item === "string")) {
    throw new Error("La liste des postes de référence est indisponible.");
  }
  return value;
}

export async function getJobReferenceTitles(): Promise<string[]> {
  try {
    const response = await apiClient.get<unknown>("/api/references/job-titles");
    return assertJobTitleList(response.data);
  } catch (error) {
    const token = getStoredToken();
    const response = await axios.get<unknown>(`${FALLBACK_API_BASE_URL}/api/references/job-titles`, {
      headers: token ? { Authorization: `Bearer ${token}` } : undefined,
    });
    return assertJobTitleList(response.data);
  }
}
