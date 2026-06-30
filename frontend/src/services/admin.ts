import { apiClient } from "../lib/api";

export type AdminUser = {
  id: string;
  full_name: string;
  email: string;
  role: string;
  status: string;
  last_login_at: string | null;
  created_at: string;
  updated_at: string;
};

export type AdminDashboardStats = {
  candidates_count: number;
  recruiters_count: number;
  jobs_count: number;
  applications_count: number;
  talent_pool_count: number;
  email_sent_count: number;
  email_skipped_count: number;
  email_failed_count: number;
};

export type CreateUserPayload = {
  full_name: string;
  email: string;
  role: "admin" | "recruiter";
};

export type UpdateUserPayload = Partial<{
  full_name: string;
  email: string;
  role: "admin" | "recruiter";
  status: "active" | "invited" | "suspended" | "deleted";
  password: string;
}>;

export type AdminSettings = {
  settings: Record<string, unknown>;
};

export async function getAdminDashboard(): Promise<AdminDashboardStats> {
  const response = await apiClient.get<AdminDashboardStats>("/api/admin");
  return response.data;
}

export async function getAdminUsers(): Promise<AdminUser[]> {
  const response = await apiClient.get<AdminUser[]>("/api/admin/users");
  return response.data;
}

export async function createUser(payload: CreateUserPayload): Promise<AdminUser> {
  const response = await apiClient.post<AdminUser>("/api/admin/users", payload);
  return response.data;
}

export async function updateAdminUser(userId: string, payload: UpdateUserPayload): Promise<AdminUser> {
  const response = await apiClient.patch<AdminUser>(`/api/admin/users/${userId}`, payload);
  return response.data;
}

export async function disableAdminUser(userId: string): Promise<AdminUser> {
  const response = await apiClient.patch<AdminUser>(`/api/admin/users/${userId}/disable`);
  return response.data;
}

export async function enableAdminUser(userId: string): Promise<AdminUser> {
  const response = await apiClient.patch<AdminUser>(`/api/admin/users/${userId}/enable`);
  return response.data;
}

export async function deleteAdminUser(userId: string): Promise<AdminUser> {
  const response = await apiClient.delete<AdminUser>(`/api/admin/users/${userId}`);
  return response.data;
}

export async function getAdminSettings(): Promise<AdminSettings> {
  const response = await apiClient.get<AdminSettings>("/api/admin/settings");
  return response.data;
}

export async function updateAdminSettings(settings: Record<string, unknown>): Promise<AdminSettings> {
  const response = await apiClient.patch<AdminSettings>("/api/admin/settings", { settings });
  return response.data;
}