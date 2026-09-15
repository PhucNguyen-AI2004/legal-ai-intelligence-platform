import type { Metadata } from "next";
import { NewChatWorkspace } from "@/components/chat/new-chat-workspace";

export const metadata: Metadata = { title: "Hội thoại" };

export default function ChatPage() {
  return <NewChatWorkspace />;
}
