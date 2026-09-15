"use client";

import { useEffect, useId, useRef, useState } from "react";
import { ArrowLeft, BookOpen, ChevronRight, X } from "lucide-react";
import { Modal } from "@/components/ui/modal";
import { IconButton } from "@/components/ui/icon-button";
import type { MessageCitation } from "@/lib/conversations/types";
import { CitationSource } from "./citation-source";
import { citationKey, selectedCitation } from "@/lib/conversations/message-flow";

// Each control owns evidence for exactly one answer, independent of send scope.
export function MessageSources({ citations }: { citations: MessageCitation[] }) {
  const [open, setOpen] = useState(false);
  const titleId = useId();
  if (!citations.length) return null;
  return <>
    <button type="button" className="answer-sources-button" aria-haspopup="dialog" aria-expanded={open} onClick={() => setOpen(true)}>
      <BookOpen size={16} aria-hidden="true" /> Nguồn · {citations.length}
    </button>
    {open && <Modal className="answer-sources-panel" labelledBy={titleId} onClose={() => setOpen(false)}>
      <header className="sources-panel-heading"><h2 id={titleId}>Nguồn của câu trả lời</h2><IconButton autoFocus label="Đóng bảng nguồn" onClick={() => setOpen(false)}><X size={20} aria-hidden="true" /></IconButton></header>
      <SourcesBrowser citations={citations} />
    </Modal>}
  </>;
}

// Unmount on close: reopening always starts at this answer's source list.
function SourcesBrowser({ citations }: { citations: MessageCitation[] }) {
  const [selected, setSelected] = useState<string | null>(null);
  const previous = useRef<string | null>(null);
  const entries = useRef(new Map<string, HTMLButtonElement>());
  const detailHeading = useRef<HTMLHeadingElement>(null);
  const citation = selectedCitation(citations, selected);

  useEffect(() => {
    if (selected !== null) detailHeading.current?.focus();
    else if (previous.current !== null) entries.current.get(previous.current)?.focus();
    previous.current = selected;
  }, [selected]);

  if (selected !== null) return <div className="source-detail-view">
    <button type="button" className="sources-back" onClick={() => setSelected(null)}><ArrowLeft size={16} aria-hidden="true" /> Tất cả nguồn</button>
    <h3 ref={detailHeading} tabIndex={-1}>{citation ? `[${citation.citation_index}] ${citation.document_name}` : "Nguồn không còn khả dụng"}</h3>
    {citation ? <CitationSource key={citationKey(citation)} citation={citation} /> : <p>Nguồn này không còn trong câu trả lời hiện tại. Quay lại danh sách để xem các nguồn còn lại.</p>}
  </div>;

  return <>
    <p className="source-note">Chọn một nguồn để đọc tài liệu tại đoạn được trích dẫn. Số [n] tương ứng với trích dẫn trong câu trả lời.</p>
    <div className="sources-panel-list">{[...citations].sort((a, b) => a.citation_index - b.citation_index).map((item) => {
      const key = citationKey(item);
      return <button key={key} ref={(node) => { if (node) entries.current.set(key, node); else entries.current.delete(key); }} type="button" className="citation-button source-list-entry" onClick={() => setSelected(key)}>
        <span><strong>[{item.citation_index}] {item.document_name}</strong><small>Đoạn {item.chunk_index + 1}</small></span><ChevronRight size={18} aria-hidden="true" />
      </button>;
    })}</div>
  </>;
}
