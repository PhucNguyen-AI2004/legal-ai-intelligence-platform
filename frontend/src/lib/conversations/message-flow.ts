import type { ConversationDetail, CreateMessageRequest } from "./types";

export type Persistence = "saved" | "not-saved" | "unknown";

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
