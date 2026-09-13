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
  token?: string;
}

export function normalizeBaseUrl(value: string): string {
  return value.trim().replace(/\/+$/, "");
}

export const apiBaseUrl = normalizeBaseUrl(process.env.NEXT_PUBLIC_API_BASE_URL ?? DEFAULT_API_BASE_URL);

export async function apiRequest<T>(path: string, options: ApiRequestOptions = {}): Promise<T | null> {
  const { body, token, headers: customHeaders, ...requestOptions } = options;
  const headers = new Headers(customHeaders);
  headers.set("Accept", "application/json");
  if (body !== undefined) headers.set("Content-Type", "application/json");
  if (token) headers.set("Authorization", `Bearer ${token}`);

  const response = await fetch(`${apiBaseUrl}/${path.replace(/^\/+/, "")}`, {
    ...requestOptions,
    headers,
    body: body === undefined ? undefined : JSON.stringify(body),
  });
  if (!response.ok) {
    const errorBody = await readJson<ApiErrorBody>(response);
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
