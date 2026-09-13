import { apiRequest } from "@/lib/api/client";
import type { LoginRequest, LoginResponse, RegisterRequest, User } from "./types";

export async function loginRequest(data: LoginRequest): Promise<LoginResponse> {
  const response = await apiRequest<LoginResponse>("/auth/login", { method: "POST", body: data, auth: "none" });
  if (!response) throw new Error("Login response was empty");
  return response;
}

export async function registerRequest(data: RegisterRequest): Promise<User> {
  const response = await apiRequest<User>("/auth/register", { method: "POST", body: data, auth: "none" });
  if (!response) throw new Error("Registration response was empty");
  return response;
}

export async function currentUserRequest(): Promise<User> {
  const response = await apiRequest<User>("/auth/me", { auth: "required", cache: "no-store" });
  if (!response) throw new Error("Current user response was empty");
  return response;
}
