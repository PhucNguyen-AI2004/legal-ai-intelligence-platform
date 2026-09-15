"use client";

import { useState } from "react";
import { useConversations } from "@/components/conversations/conversation-provider";
import { ChatEmptyState } from "./chat-empty-state";
import { ChatComposer } from "./chat-composer";

export function NewChatWorkspace() {
  const { createNew, isCreating, error } = useConversations();
  const [draft, setDraft] = useState("");
  return <div className="chat-page">
    <ChatEmptyState />
    <div className="chat-controls">
      {error && <p className="workspace-notice notice-error" role="alert">{error}</p>}
      {isCreating && <p role="status">Đang mở hội thoại và gửi câu hỏi…</p>}
      <ChatComposer value={draft} onChange={setDraft} busy={isCreating} onSend={createNew} />
    </div>
  </div>;
}
