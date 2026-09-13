import type { DocumentListItem } from "@/lib/types/document";

// Temporary Phase 8A UI data. Replace with backend responses in later phases.
export const MOCK_CONVERSATIONS = [
  { label: "Hôm nay", items: ["Quyền và nghĩa vụ các bên", "Điều khoản bảo mật"] },
  { label: "7 ngày trước", items: ["Điều kiện chấm dứt hợp đồng"] },
];

export const MOCK_PROFILE = { initials: "NA", name: "Người dùng mẫu", label: "Dữ liệu giao diện tạm" };

export const MOCK_SUGGESTED_PROMPTS = [
  "Tóm tắt quyền và nghĩa vụ của các bên", "Tìm điều khoản về bảo mật",
  "Điều kiện chấm dứt hợp đồng", "So sánh trách nhiệm của các bên",
];

export const MOCK_DOCUMENTS: DocumentListItem[] = [
  { id: "mock-1", name: "Hợp đồng dịch vụ — mẫu giao diện", type: "PDF", processing: "processed", indexing: "indexed", uploadedAt: "12/09/2026" },
  { id: "mock-2", name: "Quy chế nội bộ — mẫu giao diện", type: "DOCX", processing: "processing", indexing: "pending", uploadedAt: "11/09/2026" },
  { id: "mock-3", name: "Ghi chú pháp lý — mẫu giao diện", type: "TXT", processing: "failed", indexing: "pending", uploadedAt: "09/09/2026" },
];
