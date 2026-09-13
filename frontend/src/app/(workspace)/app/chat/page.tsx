import type { Metadata } from "next";
import { ChatComposer } from "@/components/chat/chat-composer";
import { ChatEmptyState } from "@/components/chat/chat-empty-state";

export const metadata: Metadata = { title: "Hội thoại" };

export default function ChatPage() {
  return (
    <div className="chat-page">
      <ChatEmptyState />
      <ChatComposer />
    </div>
  );
}
