"use client";

import { useEffect, useId, useState } from "react";
import Link from "next/link";
import { getDocumentChunks } from "@/lib/documents/document-api";
import type { MessageCitation } from "@/lib/conversations/types";
import { citationExcerpt } from "@/lib/conversations/message-flow";

export function CitationSource({ citation }: { citation: MessageCitation }) {
  const [open, setOpen] = useState(false);
  const [content, setContent] = useState<string | null>(null);
  const [error, setError] = useState(false);
  const [attempt, setAttempt] = useState(0);
  const previewId = useId();
  useEffect(() => {
    if (!open) return;
    let active = true;
    getDocumentChunks(citation.document_id, citation.chunk_index, 1).then((response) => {
      if (!active) return;
      const chunk = response.items.find((item) => item.id === citation.chunk_id);
      if (chunk) setContent(citationExcerpt(chunk.content)); else setError(true);
    }).catch(() => { if (active) setError(true); });
    return () => { active = false; };
  }, [open, citation.document_id, citation.chunk_id, citation.chunk_index, attempt]);
  return <div className="citation-source">
    <button type="button" className="citation-button" aria-expanded={open} aria-controls={previewId} onClick={() => { setContent(null); setError(false); setOpen(!open); }}>[{citation.citation_index}] {citation.document_name} · Đoạn {citation.chunk_index + 1}</button>
    {open && <section id={previewId} className="source-preview" aria-label="Nội dung nguồn trích dẫn">
      <p>Trích đoạn ngắn từ nguồn hiện tại; có thể thay đổi khi xử lý lại.</p>
      {error ? <p role="alert">Không thể tải nguồn. Tài liệu hoặc đoạn có thể đã bị xóa, thay đổi hoặc không còn truy cập được. <button type="button" onClick={() => { setError(false); setAttempt((value) => value + 1); }}>Thử tải lại</button></p> : content === null ? <p role="status">Đang tải nguồn…</p> : content === "" ? <p>Nguồn hiện tại không có nội dung để xem trước.</p> : <div className="message-content">{content}</div>}
      <Link href={`/app/documents/${citation.document_id}`} target="_blank" rel="noopener noreferrer">Mở tài liệu trong thẻ mới</Link>
      <button type="button" className="source-close" onClick={() => setOpen(false)}>Đóng trích đoạn</button>
    </section>}
  </div>;
}
