import { clearAccessToken, getAccessToken } from "@/lib/auth/token-storage";

const DEFAULT_API_BASE_URL = "http://localhost:8000";

export interface ApiErrorBody {
  detail?: string | Array<{ loc?: Array<string | number>; msg?: string; type?: string }>;
}

export class ApiError extends Error {
  constructor(public readonly status: number, public readonly body: ApiErrorBody | null) {
    super(typeof body?.detail === "string" ? body.detail : `API request failed with status ${status}`);
    this.name = "ApiError";
  }
}

export interface ApiRequestOptions extends Omit<RequestInit, "body"> {
  body?: unknown;
  auth?: "none" | "optional" | "required";
}

type UnauthorizedHandler = () => void;
let unauthorizedHandler: UnauthorizedHandler | null = null;

export function setUnauthorizedHandler(handler: UnauthorizedHandler | null): void {
  unauthorizedHandler = handler;
}

export function normalizeBaseUrl(value: string): string {
  return value.trim().replace(/\/+$/, "");
}

export const apiBaseUrl = normalizeBaseUrl(process.env.NEXT_PUBLIC_API_BASE_URL ?? DEFAULT_API_BASE_URL);

export async function apiRequest<T>(path: string, options: ApiRequestOptions = {}): Promise<T | null> {
  const { body, auth = "optional", headers: customHeaders, ...requestOptions } = options;
  const headers = new Headers(customHeaders);
  const isFormData = typeof FormData !== "undefined" && body instanceof FormData;
  headers.set("Accept", "application/json");
  if (body !== undefined && !isFormData) headers.set("Content-Type", "application/json");
  const token = auth === "none" ? null : getAccessToken();
  if (token) headers.set("Authorization", `Bearer ${token}`);

  const response = await fetch(`${apiBaseUrl}/${path.replace(/^\/+/, "")}`, {
    ...requestOptions,
    headers,
    body: body === undefined ? undefined : isFormData ? body : JSON.stringify(body),
  });
  if (!response.ok) {
    const errorBody = await readJson<ApiErrorBody>(response);
    if (response.status === 401 && auth !== "none") {
      clearAccessToken();
      unauthorizedHandler?.();
    }
    throw new ApiError(response.status, errorBody);
  }
  if (response.status === 204) return null;
  return readJson<T>(response);
}

async function readJson<T>(response: Response): Promise<T | null> {
  const contentType = response.headers.get("content-type") ?? "";
  if (!contentType.includes("application/json")) return null;
  return response.json() as Promise<T>;
}
