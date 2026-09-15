export function isAdmin(user: { role?: string } | null | undefined): boolean {
  return user?.role === "admin";
}
export function adminAccess(user: { role?: string } | null, loading: boolean): "loading" | "allowed" | "denied" {
  return loading ? "loading" : isAdmin(user) ? "allowed" : "denied";
}
export function adminQuery(skip: number, filters: Record<string, string> = {}): string {
  const query = new URLSearchParams({ skip: String(Math.max(0, skip)), limit: "20" });
  for (const [key, value] of Object.entries(filters)) if (value.trim()) query.set(key, value.trim());
  return query.toString();
}
