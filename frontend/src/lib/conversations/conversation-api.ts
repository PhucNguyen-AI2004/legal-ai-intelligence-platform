import { apiRequest } from "@/lib/api/client";
import type { ConversationDetail, ConversationListResponse, ConversationSummary, CreateConversationRequest, UpdateConversationRequest } from "./types";

export async function listConversations(limit = 20, offset = 0): Promise<ConversationListResponse> {
  const response = await apiRequest<ConversationListResponse>(`/conversations?limit=${limit}&offset=${offset}`, { auth: "required" });
  if (!response) throw new Error("The conversations response was empty.");
  return response;
}

export async function createConversation(title = "Cuộc trò chuyện mới"): Promise<ConversationSummary> {
  const body: CreateConversationRequest = { title };
  const response = await apiRequest<ConversationSummary>("/conversations", { method: "POST", auth: "required", body });
  if (!response) throw new Error("The create conversation response was empty.");
  return response;
}

export async function getConversation(id: string): Promise<ConversationDetail> {
  const response = await apiRequest<ConversationDetail>(`/conversations/${id}`, { auth: "required" });
  if (!response) throw new Error("The conversation response was empty.");
  return response;
}

export async function updateConversation(id: string, title: string): Promise<ConversationSummary> {
  const body: UpdateConversationRequest = { title };
  const response = await apiRequest<ConversationSummary>(`/conversations/${id}`, { method: "PATCH", auth: "required", body });
  if (!response) throw new Error("The rename conversation response was empty.");
  return response;
}

export async function deleteConversation(id: string): Promise<void> {
  await apiRequest(`/conversations/${id}`, { method: "DELETE", auth: "required" });
}
