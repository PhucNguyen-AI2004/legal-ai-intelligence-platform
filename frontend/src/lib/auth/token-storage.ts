const ACCESS_TOKEN_KEY = "legal_ai_access_token";

export function getAccessToken(): string | null {
  return typeof window === "undefined" ? null : window.localStorage.getItem(ACCESS_TOKEN_KEY);
}

export function setAccessToken(token: string): void {
  if (typeof window !== "undefined") window.localStorage.setItem(ACCESS_TOKEN_KEY, token);
}

export function clearAccessToken(): void {
  if (typeof window !== "undefined") window.localStorage.removeItem(ACCESS_TOKEN_KEY);
}
