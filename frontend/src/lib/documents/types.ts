export type ProcessingStatus = "uploaded" | "processing" | "processed" | "failed";
export type EmbeddingStatus = "pending" | "indexing" | "indexed" | "failed";
export type DocumentStatus = ProcessingStatus | EmbeddingStatus;

export interface DocumentRecord {
  id: string;
  owner_id: string;
  original_filename: string;
  file_type: string;
  mime_type: string;
  file_size: number;
  title: string;
  description: string | null;
  status: ProcessingStatus;
  processing_error: string | null;
  embedding_status: EmbeddingStatus;
  embedding_error: string | null;
  embedded_at: string | null;
  created_at: string;
  updated_at: string;
}

export interface DocumentListResponse {
  items: DocumentRecord[];
  total: number;
  skip: number;
  limit: number;
}

export interface DocumentChunk {
  id: string;
  chunk_index: number;
  content: string;
  char_count: number;
  token_estimate: number;
  created_at: string;
}

export interface DocumentChunkListResponse {
  document_id: string;
  status: ProcessingStatus;
  items: DocumentChunk[];
  total: number;
  skip: number;
  limit: number;
}

export interface ProcessDocumentResponse {
  document_id: string;
  job_id: string;
  job_type: "process";
  status: "queued";
}

export interface IndexDocumentResponse {
  document_id: string;
  job_id: string;
  job_type: "index";
  status: "queued";
}

export interface UploadDocumentInput {
  file: File;
  title?: string;
  description?: string;
}
