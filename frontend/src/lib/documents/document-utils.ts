import { ApiError } from "@/lib/api/client";
import type { DocumentRecord } from "./types";

export const MAX_UPLOAD_BYTES = 20 * 1024 * 1024;
export const ACCEPTED_DOCUMENTS = ".pdf,.docx,.txt";

export function canProcess(document: DocumentRecord): boolean {
  return ["uploaded", "failed"].includes(document.status) && document.embedding_status !== "indexing";
}

export function canIndex(document: DocumentRecord): boolean {
  return document.status === "processed" && ["pending", "failed"].includes(document.embedding_status);
}

export function isPipelineActive(document: DocumentRecord): boolean {
  return document.status === "processing" || document.embedding_status === "indexing";
}

export function formatDate(value: string | null): string {
  return value ? new Intl.DateTimeFormat("vi-VN", { dateStyle: "medium", timeStyle: "short" }).format(new Date(value)) : "—";
}

export function formatFileSize(bytes: number): string {
  if (bytes < 1024) return `${bytes} B`;
  if (bytes < 1024 ** 2) return `${(bytes / 1024).toFixed(1)} KB`;
  return `${(bytes / 1024 ** 2).toFixed(1)} MB`;
}

export function documentErrorMessage(error: unknown, operation: "load" | "upload" | "process" | "index" | "delete"): string {
  if (error instanceof ApiError) {
    if (error.status === 404) return "Không tìm thấy tài liệu.";
    if (error.status === 413) return "Tệp vượt quá dung lượng cho phép.";
    if (error.status === 415) return "Định dạng tệp không được hỗ trợ.";
    if (error.status === 409) {
      if (operation === "process") return "Tài liệu đang được xử lý hoặc chưa thể xử lý lại.";
      if (operation === "index") return "Tài liệu chưa sẵn sàng để lập chỉ mục.";
      if (operation === "delete") return "Không thể xóa tài liệu khi đang xử lý hoặc lập chỉ mục.";
    }
    if (error.status === 422) return "Dữ liệu yêu cầu chưa hợp lệ.";
    if (error.status >= 500) return "Đã xảy ra lỗi khi xử lý yêu cầu. Vui lòng thử lại.";
  }
  if (error instanceof TypeError) return "Không thể kết nối đến máy chủ. Vui lòng thử lại.";
  return operation === "load" ? "Không thể tải dữ liệu tài liệu." : "Đã xảy ra lỗi khi xử lý yêu cầu. Vui lòng thử lại.";
}
