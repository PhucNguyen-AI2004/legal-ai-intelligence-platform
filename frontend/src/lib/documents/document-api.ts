import { apiRequest } from "@/lib/api/client";
import type {
  DocumentChunkListResponse,
  DocumentListResponse,
  DocumentRecord,
  IndexDocumentResponse,
  ProcessDocumentResponse,
  UploadDocumentInput,
} from "./types";

export async function listDocuments(skip = 0, limit = 20): Promise<DocumentListResponse> {
  return requireResponse(apiRequest<DocumentListResponse>(`/documents?skip=${skip}&limit=${limit}`, { auth: "required", cache: "no-store" }));
}

export async function uploadDocument(input: UploadDocumentInput): Promise<DocumentRecord> {
  const form = new FormData();
  form.append("file", input.file);
  if (input.title?.trim()) form.append("title", input.title.trim());
  if (input.description?.trim()) form.append("description", input.description.trim());
  return requireResponse(apiRequest<DocumentRecord>("/documents", { method: "POST", body: form, auth: "required" }));
}

export async function getDocument(documentId: string): Promise<DocumentRecord> {
  return requireResponse(apiRequest<DocumentRecord>(`/documents/${documentId}`, { auth: "required", cache: "no-store" }));
}

export async function deleteDocument(documentId: string): Promise<void> {
  await apiRequest<never>(`/documents/${documentId}`, { method: "DELETE", auth: "required" });
}

export async function processDocument(documentId: string): Promise<ProcessDocumentResponse> {
  return requireResponse(apiRequest<ProcessDocumentResponse>(`/documents/${documentId}/process`, { method: "POST", auth: "required" }));
}

export async function indexDocument(documentId: string): Promise<IndexDocumentResponse> {
  return requireResponse(apiRequest<IndexDocumentResponse>(`/documents/${documentId}/index`, { method: "POST", auth: "required" }));
}

export async function getDocumentChunks(documentId: string, skip = 0, limit = 100): Promise<DocumentChunkListResponse> {
  return requireResponse(apiRequest<DocumentChunkListResponse>(`/documents/${documentId}/chunks?skip=${skip}&limit=${limit}`, { auth: "required", cache: "no-store" }));
}

async function requireResponse<T>(request: Promise<T | null>): Promise<T> {
  const response = await request;
  if (response === null) throw new Error("API response was empty");
  return response;
}
