"use client";

import { useCallback, useEffect, useMemo, useState } from "react";
import Link from "next/link";
import { AlertCircle, RefreshCw } from "lucide-react";
import { ChatComposer } from "@/components/chat/chat-composer";
import { ChatEmptyState } from "@/components/chat/chat-empty-state";
import { useConversations } from "./conversation-provider";
import { Button } from "@/components/ui/button";
import { ApiError } from "@/lib/api/client";
import { getConversation } from "@/lib/conversations/conversation-api";
import { conversationErrorMessage } from "@/lib/conversations/conversation-utils";
import type { ConversationDetail } from "@/lib/conversations/types";

export function ConversationDetailWorkspace({ conversationId }: { conversationId: string }) {
  const { upsert } = useConversations();
  const [conversation, setConversation] = useState<ConversationDetail | null>(null);
  const [isLoading, setIsLoading] = useState(true);
  const [error, setError] = useState<string | null>(null);
  const [missing, setMissing] = useState(false);

  const load = useCallback(async () => {
    setIsLoading(true);
    setError(null);
    setMissing(false);
    try {
      const response = await getConversation(conversationId);
      setConversation(response);
      upsert(response);
    } catch (caught) {
      setConversation(null);
      if (caught instanceof ApiError && caught.status === 404) setMissing(true);
      else setError(conversationErrorMessage(caught, "load"));
    } finally {
      setIsLoading(false);
    }
  }, [conversationId, upsert]);

  useEffect(() => { queueMicrotask(() => void load()); }, [load]);
  const messages = useMemo(() => [...(conversation?.messages ?? [])].sort((a, b) => a.sequence_number - b.sequence_number), [conversation]);

  if (isLoading) return <div className="conversation-detail-state" role="status"><span className="conversation-loading-spinner" />Đang tải lịch sử hội thoại…</div>;
  if (missing) return <div className="conversation-detail-state"><AlertCircle size={30} /><h1>Không tìm thấy cuộc trò chuyện</h1><p>Hội thoại không tồn tại hoặc bạn không có quyền truy cập.</p><Link className="button button-secondary" href="/app/chat">Quay lại hội thoại</Link></div>;
  if (error) return <div className="conversation-detail-state" role="alert"><AlertCircle size={30} /><h1>Không thể tải hội thoại</h1><p>{error}</p><Button variant="secondary" onClick={() => void load()}><RefreshCw size={16} /> Thử lại</Button></div>;
  if (!conversation || messages.length === 0) return <div className="chat-page"><ChatEmptyState /><ChatComposer disabled /></div>;

  return <div className="conversation-page"><div className="message-history" aria-label="Lịch sử tin nhắn">{messages.map((message) => <article className={`message message-${message.role}`} key={message.id}><div className="message-role">{message.role === "user" ? "Bạn" : "Legal AI"}</div><div className="message-content">{message.content}</div>{message.role === "assistant" && message.grounded !== null && <span className={`grounding-label${message.grounded ? " grounded" : ""}`}>{message.grounded ? "Đã đối chiếu nguồn" : "Chưa có nguồn phù hợp"}</span>}{message.role === "assistant" && message.citations.length > 0 && <div className="citation-markers" aria-label="Nguồn trích dẫn">{[...message.citations].sort((a, b) => a.citation_index - b.citation_index).map((citation) => <span key={`${message.id}-${citation.citation_index}`} title={`${citation.document_name} · đoạn ${citation.chunk_index}`}>[{citation.citation_index}]</span>)}</div>}</article>)}</div><ChatComposer disabled /></div>;
}
