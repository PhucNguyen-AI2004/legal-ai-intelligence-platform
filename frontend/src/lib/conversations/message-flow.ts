import type { ConversationDetail, CreateMessageRequest, MessageCitation } from "./types";

export function citationKey(citation: MessageCitation): string {
  return `${citation.citation_index}:${citation.document_id}:${citation.chunk_id}`;
}

// Resolve only against the citations of the answer whose drawer is mounted.
export function selectedCitation(citations: MessageCitation[], key: string | null): MessageCitation | undefined {
  return key === null ? undefined : citations.find((citation) => citationKey(citation) === key);
}

export function verifiedCitationExcerpt(items: Array<{ id: string; content: string }>, chunkId: string): string | null {
  const chunk = items.find((item) => item.id === chunkId);
  return chunk ? citationExcerpt(chunk.content) : null;
}

export type Persistence = "saved" | "not-saved" | "unknown";
export type SubmissionPhase = "queued" | "sending" | "stopping" | "reconciling" | "settled";

export function isClientAbort(error: unknown): boolean {
  return error instanceof Error && error.name === "AbortError";
}

export function canStartSubmission(phase?: SubmissionPhase): boolean {
  return phase === undefined || phase === "settled";
}

export function messageRequest(content: string, documentIds: string[]): CreateMessageRequest {
  return { content: content.trim(), top_k: 5, ...(documentIds.length ? { document_ids: [...documentIds] } : {}) };
}

// A repeated question from an earlier turn is not evidence that this send saved.
// A lost connection can leave the server running even after a history GET returns.
export function messagePersistence(history: ConversationDetail, previousIds: string[], content: string, definitiveFailure: boolean): Persistence {
  const previous = new Set(previousIds);
  if (history.messages.some((message) => message.role === "user" && !previous.has(message.id) && message.content === content)) return "saved";
  return definitiveFailure ? "not-saved" : "unknown";
}

export function citationExcerpt(content: string): string {
  const limit = 280;
  const source = content.normalize("NFC").replace(/\r\n?/g, "\n").trim();
  if (!source) return "";
  // Blank lines delimit paragraphs; single line breaks may be wrapped prose.
  // This is a source preview, not an inferred answer-support span.
  const paragraph = source.split(/\n\s*\n/u, 1)[0].replace(/\s+/gu, " ");
  const characters = Array.from(paragraph);
  const hasMore = characters.length > limit || paragraph !== source.replace(/\s+/gu, " ");
  if (!hasMore) return paragraph;
  return `${characters.slice(0, limit - 1).join("").trimEnd()}…`;
}
