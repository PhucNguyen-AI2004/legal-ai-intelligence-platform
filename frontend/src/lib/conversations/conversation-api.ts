import { apiRequest } from "@/lib/api/client";
import type { ConversationMessage, CreateMessageRequest } from "./types";
import type { ConversationDetail, ConversationListResponse, ConversationSummary, CreateConversationRequest, UpdateConversationRequest } from "./types";

export async function sendMessage(id: string, body: CreateMessageRequest, signal?: AbortSignal): Promise<ConversationMessage> {
  const response = await apiRequest<ConversationMessage>(`/conversations/${id}/messages`, { method: "POST", auth: "required", body, signal });
  if (!response) throw new Error("The message response was empty.");
  return response;
}

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
  const response = await apiRequest<ConversationDetail>(`/conversations/${id}`, { auth: "required", cache: "no-store" });
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
