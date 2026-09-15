import { apiRequest } from "@/lib/api/client";

export interface Overview {
  total_users: number; total_documents: number; total_conversations: number; total_messages: number;
  processing_counts: Record<string, number>; embedding_counts: Record<string, number>;
}
export interface AdminUser { id: string; email: string; role: "user" | "admin"; created_at: string }
export interface AdminDocument {
  id: string; owner_id: string; owner_email: string; title: string; original_filename: string;
  file_type: string; file_size: number; status: string; embedding_status: string; created_at: string;
}
export interface Page<T> { items: T[]; total: number; skip: number; limit: number }
export async function getAdminData<T>(resource: string, signal: AbortSignal): Promise<T> {
  const data = await apiRequest<T>(`/admin/${resource}`, { auth: "required", cache: "no-store", signal });
  if (!data) throw new Error("Empty admin response");
  return data;
}
