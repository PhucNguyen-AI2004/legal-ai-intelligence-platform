"use client";

import { useEffect, useMemo, useState } from "react";
import Link from "next/link";
import { ChatComposer } from "@/components/chat/chat-composer";
import { ChatEmptyState } from "@/components/chat/chat-empty-state";
import { CitationSource } from "@/components/chat/citation-source";
import { useConversations } from "./conversation-provider";
import { Button } from "@/components/ui/button";
import { ApiError } from "@/lib/api/client";
import { messagePersistence } from "@/lib/conversations/message-flow";

export function ConversationDetailWorkspace({ conversationId }: { conversationId: string }) {
  const { histories, submissions, loadHistory, submitMessage, acknowledge } = useConversations();
  const conversation = histories[conversationId];
  const submission = submissions[conversationId];
  const pending = Boolean(submission && submission.phase !== "settled");
  const recovery = Boolean(submission && !submission.acknowledged && (submission.postError || submission.syncError));
  const [draft, setDraft] = useState("");
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState<string | null>(null);
  const [missing, setMissing] = useState(false);

  useEffect(() => {
    let active = true;
    loadHistory(conversationId).catch((caught) => {
      if (!active) return;
      if (caught instanceof ApiError && caught.status === 404) setMissing(true);
      setError("Không thể tải lịch sử hội thoại.");
    }).finally(() => { if (active) setLoading(false); });
    return () => { active = false; };
  }, [conversationId, loadHistory]);

  async function reload() {
    setLoading(true);
    setError(null);
    try { await loadHistory(conversationId); }
    catch (caught) {
      if (caught instanceof ApiError && caught.status === 404) setMissing(true);
      setError("Không thể tải lịch sử hội thoại.");
    } finally { setLoading(false); }
  }

  const messages = useMemo(() => [...(conversation?.messages ?? [])].sort((a, b) => a.sequence_number - b.sequence_number), [conversation]);
  const showPendingQuestion = pending && submission && conversation && messagePersistence(conversation, submission.previousIds, submission.request.content, false) !== "saved";

  if (missing) return <div className="conversation-detail-state"><h1>Không tìm thấy cuộc trò chuyện</h1><p>Hội thoại không tồn tại hoặc bạn không có quyền truy cập.</p><Link href="/app/chat">Quay lại hội thoại</Link></div>;
  if (loading && !conversation) return <div className="conversation-detail-state" role="status">Đang tải lịch sử hội thoại…</div>;

  return <div className="conversation-page">
    <div className="message-history" aria-label="Lịch sử tin nhắn" aria-busy={pending}>
      {!messages.length && !pending && !error && <ChatEmptyState />}
      {messages.map((message) => <article className={`message message-${message.role}`} key={message.id}>
        <div className="message-role">{message.role === "user" ? "Bạn" : "Legal AI"}</div>
        <div className="message-content">{message.content}</div>
        {message.role === "assistant" && <>
          <span className={`grounding-label${message.grounded === true ? " grounded" : ""}`}>{message.grounded === true ? "Có nguồn trích dẫn" : message.grounded === false ? "Chưa có căn cứ từ nguồn trích dẫn" : "Chưa có thông tin về nguồn"}</span>
          {!message.citations.length && <p className="source-note">Không có nguồn trích dẫn được lưu cho phản hồi này. Hãy kiểm tra tài liệu đã lập chỉ mục hoặc điều chỉnh câu hỏi.</p>}
          <div className="citation-markers">{[...message.citations].sort((a, b) => a.citation_index - b.citation_index).map((citation) => <CitationSource key={`${message.id}-${citation.citation_index}-${citation.chunk_id}`} citation={citation} />)}</div>
        </>}
      </article>)}
      {showPendingQuestion && <article className="message message-user"><div className="message-role">Bạn · Đang gửi</div><div className="message-content">{submission.request.content}</div></article>}
      {pending && <p role="status">{submission?.phase === "reconciling" ? "Đang đồng bộ lịch sử…" : "Đang gửi và tìm nguồn cho câu trả lời…"}</p>}
    </div>
    <div className="chat-controls">
      {error && <p className="workspace-notice notice-error" role="alert">{error}</p>}
      {recovery && submission && <section className="workspace-notice notice-error" role="alert">
        {submission.postError && <p>{submission.postError}</p>}
        {submission.syncError ? <p>Chưa tải được lịch sử để kiểm tra kết quả. Chỉ tải lại lịch sử, không gửi lại câu hỏi.</p>
          : submission.persistence === "saved" ? <p>Câu hỏi đã được lưu trong lịch sử. Ô soạn thảo được giữ trống để tránh gửi trùng.</p>
          : submission.persistence === "not-saved" ? <p>Lịch sử không có câu hỏi vừa gửi. Bạn có thể khôi phục bản nháp; hãy chọn lại nguồn nếu cần.</p>
          : <p>Chưa xác định được câu hỏi đã lưu hay chưa; yêu cầu có thể vẫn đang xử lý. Kiểm tra lại lịch sử trước khi đặt câu hỏi mới.</p>}
        {!pending && !submission.syncError && <div className="recovery-actions">
          {submission.persistence === "not-saved" && <Button variant="secondary" disabled={loading} onClick={() => { setDraft(submission.request.content); acknowledge(conversationId); }}>Khôi phục bản nháp</Button>}
          <Button variant="secondary" disabled={loading} onClick={() => { setDraft(""); acknowledge(conversationId); }}>Đã kiểm tra — soạn câu hỏi mới</Button>
        </div>}
      </section>}
      {(error || recovery) && <Button variant="secondary" disabled={pending || loading} onClick={() => void reload()}>Tải lại lịch sử (không gửi tin nhắn)</Button>}
      <ChatComposer disabled={!conversation || Boolean(error) || recovery || loading} busy={pending} value={draft} onChange={setDraft} onSend={(request) => submitMessage(conversationId, request)} />
    </div>
  </div>;
}
