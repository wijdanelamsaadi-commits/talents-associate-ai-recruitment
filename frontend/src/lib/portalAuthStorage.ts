import type { CandidateProfile } from "../services/portal";

const CANDIDATE_TOKEN_KEY = "talents_associate_candidate_token";
const CANDIDATE_PROFILE_KEY = "talents_associate_candidate_profile";

export function getStoredCandidateToken(): string | null {
  return window.localStorage.getItem(CANDIDATE_TOKEN_KEY);
}

export function getStoredCandidateProfile(): CandidateProfile | null {
  const storedProfile = window.localStorage.getItem(CANDIDATE_PROFILE_KEY);
  if (!storedProfile) {
    return null;
  }

  try {
    return JSON.parse(storedProfile) as CandidateProfile;
  } catch {
    clearStoredCandidateAuth();
    return null;
  }
}

export function storeCandidateAuth(token: string, candidate: CandidateProfile) {
  window.localStorage.setItem(CANDIDATE_TOKEN_KEY, token);
  window.localStorage.setItem(CANDIDATE_PROFILE_KEY, JSON.stringify(candidate));
}

export function storeCandidateProfile(candidate: CandidateProfile) {
  window.localStorage.setItem(CANDIDATE_PROFILE_KEY, JSON.stringify(candidate));
}

export function clearStoredCandidateAuth() {
  window.localStorage.removeItem(CANDIDATE_TOKEN_KEY);
  window.localStorage.removeItem(CANDIDATE_PROFILE_KEY);
}
