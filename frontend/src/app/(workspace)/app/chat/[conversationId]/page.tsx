import type { Metadata } from "next";
import { ConversationDetailWorkspace } from "@/components/conversations/conversation-detail-workspace";

export const metadata: Metadata = { title: "Hội thoại" };

export default async function ConversationPage({ params }: { params: Promise<{ conversationId: string }> }) {
  const { conversationId } = await params;
  return <ConversationDetailWorkspace key={conversationId} conversationId={conversationId} />;
}
