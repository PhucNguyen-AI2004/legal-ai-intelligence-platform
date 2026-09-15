"use client";

import { useEffect, useRef, useState } from "react";
import { Button } from "@/components/ui/button";
import { getDocument, getDocumentChunks } from "@/lib/documents/document-api";
import { citationWindow, loadReaderPage, READER_PAGE_SIZE, type ReaderResult } from "@/lib/documents/source-reader";
import type { MessageCitation } from "@/lib/conversations/types";

const readerApi = { document: getDocument, chunks: getDocumentChunks };
type ReaderState = ReaderResult | { status: "loading" };

// Keyed by citation. Responses from a closed reader cannot populate another one.
export function CitationSource({ citation }: { citation: MessageCitation }) {
  const [state, setState] = useState<ReaderState>({ status: "loading" });
  const [request, setRequest] = useState({ skip: citationWindow(citation.chunk_index), revision: 0, focusEvidence: true });
  const viewport = useRef<HTMLDivElement>(null);
  const evidence = useRef<HTMLElement>(null);
  const positioned = useRef(-1);

  useEffect(() => {
    let active = true;
    loadReaderPage(citation, request.skip, readerApi).then((result) => { if (active) setState(result); });
    return () => { active = false; };
  }, [citation, request]);

  useEffect(() => {
    if (state.status !== "ready" || positioned.current === request.revision) return;
    const container = viewport.current;
    if (!container) return;
    positioned.current = request.revision;
    const target = request.focusEvidence ? evidence.current : null;
    // Scroll only the reader; scrollIntoView could move the conversation too.
    if (target) {
      container.scrollTop += target.getBoundingClientRect().top - container.getBoundingClientRect().top;
      target.focus({ preventScroll: true });
    } else {
      container.scrollTop = 0;
      container.focus({ preventScroll: true });
    }
  }, [state, request]);

  function load(skip: number, focusEvidence = false) {
    setState({ status: "loading" });
    setRequest((current) => ({ skip, revision: current.revision + 1, focusEvidence }));
  }

  if (state.status === "loading") return <div className="reader-state" role="status">Đang tải nội dung tài liệu…</div>;
  if (state.status !== "ready") return <div className="reader-state" role="alert">
    <p>{state.status === "unavailable" ? "Nguồn này không còn khả dụng ở phiên bản hiện tại của tài liệu." : state.status === "document-error" ? "Không thể tải tài liệu." : "Không thể tải nội dung tài liệu."}</p>
    <Button variant="secondary" onClick={() => load(request.skip, request.focusEvidence)}>Thử lại</Button>
  </div>;

  const { document, page } = state;
  return <section className="document-source-reader" aria-label={`Đọc nguồn: ${document.title}`}>
    <div className="reader-identity"><strong>{document.title}</strong><span>{document.file_type.toUpperCase()} · Nội dung văn bản hiện tại</span></div>
    <div className="reader-viewport" ref={viewport} tabIndex={0} aria-label="Nội dung tài liệu">
      <p className="source-note">Các đoạn được giữ riêng theo tài liệu đã xử lý; có thể có phần văn bản chồng lặp.</p>
      {page.items.map((chunk) => {
        const cited = chunk.id === citation.chunk_id;
        return <article key={chunk.id} ref={cited ? evidence : undefined} tabIndex={cited ? -1 : undefined} className={`reader-chunk${cited ? " reader-evidence" : ""}`} aria-label={cited ? `Nguồn trích dẫn ${citation.citation_index}, đoạn ${chunk.chunk_index + 1}` : `Đoạn ${chunk.chunk_index + 1}`}>
          <h4>Đoạn {chunk.chunk_index + 1}{cited && <span> · Được trích dẫn [{citation.citation_index}]</span>}</h4>
          <div className="reader-text">{chunk.content}</div>
        </article>;
      })}
      {!page.items.length && <p>Không có nội dung ở phần này. Hãy quay về đoạn trích dẫn.</p>}
    </div>
    <nav className="reader-pagination" aria-label="Đọc các phần tài liệu">
      <Button variant="secondary" disabled={page.skip === 0} onClick={() => load(Math.max(0, page.skip - READER_PAGE_SIZE))}>Phần trước</Button>
      <Button variant="secondary" onClick={() => load(citationWindow(citation.chunk_index), true)}>Đoạn trích dẫn [{citation.citation_index}]</Button>
      <Button variant="secondary" disabled={page.skip + page.items.length >= page.total} onClick={() => load(page.skip + page.limit)}>Phần tiếp</Button>
      <span>{page.items.length ? `${page.skip + 1}–${page.skip + page.items.length}` : "0"} / {page.total} đoạn</span>
    </nav>
  </section>;
}
