import type { DocumentStatus } from "@/lib/types/document";

const labels: Record<DocumentStatus, string> = {
  uploaded: "Uploaded", processing: "Processing", processed: "Processed", failed: "Failed",
  pending: "Pending", indexing: "Indexing", indexed: "Indexed",
};

export function StatusBadge({ status }: { status: DocumentStatus }) {
  return <span className={`status-badge status-${status}`}><i aria-hidden="true" />{labels[status]}</span>;
}
