import { ApiError } from "@/lib/api/client";
import type { ConversationSummary } from "./types";

export function conversationErrorMessage(error: unknown, action: "load" | "create" | "rename" | "delete"): string {
  if (error instanceof ApiError && error.status === 404) return "Cuộc trò chuyện không tồn tại hoặc bạn không có quyền truy cập.";
  if (action === "load") return "Không thể tải danh sách hội thoại.";
  if (action === "create") return "Không thể tạo cuộc trò chuyện. Vui lòng thử lại.";
  if (action === "rename") return "Không thể đổi tên hội thoại.";
  return "Không thể xóa hội thoại. Vui lòng thử lại.";
}

export function groupConversations(items: ConversationSummary[]): Array<{ label: string; items: ConversationSummary[] }> {
  const now = new Date();
  const startToday = new Date(now.getFullYear(), now.getMonth(), now.getDate()).getTime();
  const day = 86_400_000;
  const groups = [
    { label: "Hôm nay", test: (time: number) => time >= startToday, items: [] as ConversationSummary[] },
    { label: "7 ngày qua", test: (time: number) => time >= startToday - 6 * day, items: [] as ConversationSummary[] },
    { label: "30 ngày qua", test: (time: number) => time >= startToday - 29 * day, items: [] as ConversationSummary[] },
    { label: "Cũ hơn", test: () => true, items: [] as ConversationSummary[] },
  ];
  for (const item of items) {
    const time = new Date(item.updated_at).getTime();
    (groups.find((group) => group.test(time)) ?? groups.at(-1))?.items.push(item);
  }
  return groups.filter((group) => group.items.length > 0).map(({ label, items: groupItems }) => ({ label, items: groupItems }));
}
