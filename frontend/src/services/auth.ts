import { apiClient } from "../lib/api";
import { clearStoredAuth, getStoredToken, getStoredUser, storeToken, storeUser } from "../lib/authStorage";

export type AuthUser = {
  id: string;
  full_name: string;
  email: string;
  role: string;
  status: string;
  created_at: string;
};

export type AuthResponse = {
  access_token: string;
  token_type: "bearer";
  user: AuthUser;
};

export type RegisterPayload = {
  full_name: string;
  email: string;
  password: string;
};

export type LoginPayload = {
  email: string;
  password: string;
};

export function storeAuth(response: AuthResponse) {
  storeToken(response.access_token);
  storeUser(response.user);
}

export async function loginRecruiter(payload: LoginPayload): Promise<AuthResponse> {
  const response = await apiClient.post<AuthResponse>("/api/auth/login", payload);
  storeAuth(response.data);
  return response.data;
}

export async function registerRecruiter(payload: RegisterPayload): Promise<AuthResponse> {
  const response = await apiClient.post<AuthResponse>("/api/auth/register", payload);
  storeAuth(response.data);
  return response.data;
}

export async function getCurrentRecruiter(): Promise<AuthUser> {
  const response = await apiClient.get<AuthUser>("/api/auth/me");
  storeUser(response.data);
  return response.data;
}

export { clearStoredAuth, getStoredToken, getStoredUser };
