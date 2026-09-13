import type { DocumentStatus } from "@/lib/documents/types";

const labels: Omit<Record<DocumentStatus, string>, "failed"> = {
  uploaded: "Đã tải lên", processing: "Đang xử lý", processed: "Đã xử lý",
  pending: "Chờ lập chỉ mục", indexing: "Đang lập chỉ mục", indexed: "Đã lập chỉ mục",
};

export function StatusBadge({ status, kind = "processing" }: { status: DocumentStatus; kind?: "processing" | "embedding" }) {
  const label = status === "failed" ? (kind === "processing" ? "Xử lý thất bại" : "Lập chỉ mục thất bại") : labels[status];
  return <span className={`status-badge status-${status}`}><i aria-hidden="true" />{label}</span>;
}
