import type { MessageCitation } from "../conversations/types";
import type { DocumentChunkListResponse, DocumentRecord } from "./types";

export const READER_PAGE_SIZE = 10;
export const citationWindow = (index: number) => Math.max(0, index - 2);
export type ReaderResult =
  | { status: "ready"; document: DocumentRecord; page: DocumentChunkListResponse }
  | { status: "unavailable" | "document-error" | "chunks-error" };
interface ReaderApi {
  document: (id: string) => Promise<DocumentRecord>;
  chunks: (id: string, skip: number, limit: number) => Promise<DocumentChunkListResponse>;
}
const notFound = (error: unknown) => typeof error === "object" && error !== null && "status" in error && error.status === 404;

// Reverify on each page request: a new document version is not old evidence.
export async function loadReaderPage(citation: MessageCitation, skip: number, api: ReaderApi): Promise<ReaderResult> {
  let document: DocumentRecord;
  try { document = await api.document(citation.document_id); }
  catch (error) { return { status: notFound(error) ? "unavailable" : "document-error" }; }
  if (document.id !== citation.document_id) return { status: "unavailable" };
  try {
    const page = await api.chunks(document.id, skip, READER_PAGE_SIZE);
    if (page.document_id !== document.id) return { status: "unavailable" };
    if (!page.items.some((chunk) => chunk.id === citation.chunk_id)) {
      const evidence = await api.chunks(document.id, citation.chunk_index, 1);
      if (evidence.document_id !== document.id || !evidence.items.some((chunk) => chunk.id === citation.chunk_id)) return { status: "unavailable" };
    }
    return { status: "ready", document, page };
  } catch (error) { return { status: notFound(error) ? "unavailable" : "chunks-error" }; }
}
