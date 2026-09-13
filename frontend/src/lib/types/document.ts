export type DocumentStatus = "uploaded" | "processing" | "processed" | "failed" | "pending" | "indexing" | "indexed";

export interface DocumentListItem {
  id: string;
  name: string;
  type: "PDF" | "DOCX" | "TXT";
  processing: DocumentStatus;
  indexing: DocumentStatus;
  uploadedAt: string;
}
