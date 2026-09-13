"use client";

import { useCallback, useEffect, useState } from "react";
import { useRouter } from "next/navigation";
import Link from "next/link";
import { ArrowLeft, FileText } from "lucide-react";
import { ConfirmDeleteDialog } from "./confirm-delete-dialog";
import { DocumentActions } from "./document-actions";
import { StatusBadge } from "@/components/ui/status-badge";
import { deleteDocument, getDocument, getDocumentChunks, indexDocument, processDocument } from "@/lib/documents/document-api";
import { documentErrorMessage, formatDate, formatFileSize } from "@/lib/documents/document-utils";
import type { DocumentChunk, DocumentRecord } from "@/lib/documents/types";

type Action = "process" | "index" | "delete";

export function DocumentDetailWorkspace({ documentId }: { documentId: string }) {
  const router = useRouter();
  const [document, setDocument] = useState<DocumentRecord | null>(null);
  const [chunks, setChunks] = useState<DocumentChunk[]>([]);
  const [chunkTotal, setChunkTotal] = useState(0);
  const [isLoading, setIsLoading] = useState(true);
  const [chunksLoading, setChunksLoading] = useState(false);
  const [error, setError] = useState<string | null>(null);
  const [feedback, setFeedback] = useState<string | null>(null);
  const [busy, setBusy] = useState<Action | null>(null);
  const [confirmingDelete, setConfirmingDelete] = useState(false);

  const load = useCallback(async () => {
    setIsLoading(true);
    setError(null);
    try {
      const current = await getDocument(documentId);
      setDocument(current);
      if (current.status === "processed") {
        setChunksLoading(true);
        try {
          const response = await getDocumentChunks(documentId);
          setChunks(response.items);
          setChunkTotal(response.total);
        } finally {
          setChunksLoading(false);
        }
      } else {
        setChunks([]);
        setChunkTotal(0);
      }
    } catch (caught) {
      setError(documentErrorMessage(caught, "load"));
    } finally {
      setIsLoading(false);
    }
  }, [documentId]);

  useEffect(() => { queueMicrotask(() => void load()); }, [load]);

  async function runAction(action: "process" | "index") {
    if (!document) return;
    setBusy(action);
    setError(null);
    setFeedback(null);
    try {
      if (action === "process") await processDocument(document.id); else await indexDocument(document.id);
      setFeedback(action === "process" ? "Xử lý tài liệu thành công." : "Lập chỉ mục thành công.");
      await load();
    } catch (caught) {
      const message = documentErrorMessage(caught, action);
      await load();
      setError(message);
    } finally {
      setBusy(null);
    }
  }

  async function remove() {
    if (!document) return;
    setBusy("delete");
    try {
      await deleteDocument(document.id);
      router.replace("/app/documents?deleted=1");
    } catch (caught) {
      setError(documentErrorMessage(caught, "delete"));
      setConfirmingDelete(false);
      setBusy(null);
    }
  }

  if (isLoading) return <div className="page-container detail-skeleton" role="status">Đang tải tài liệu…</div>;
  if (!document) return <div className="page-container"><Link className="back-link" href="/app/documents"><ArrowLeft size={17} /> Quay lại tài liệu</Link><p className="workspace-notice notice-error" role="alert">{error ?? "Không tìm thấy tài liệu."}</p></div>;

  return (
    <div className="page-container document-detail">
      <Link className="back-link" href="/app/documents"><ArrowLeft size={17} /> Quay lại tài liệu</Link>
      {feedback && <p className="workspace-notice notice-success" role="status">{feedback}</p>}
      {error && <p className="workspace-notice notice-error" role="alert">{error}</p>}
      <header className="detail-header">
        <div className="detail-title"><span className="file-icon"><FileText size={24} /></span><div><p className="eyebrow">{document.file_type.toUpperCase()}</p><h1>{document.title}</h1><p>{document.original_filename}</p></div></div>
        <DocumentActions document={document} showView={false} busyAction={busy} onProcess={() => void runAction("process")} onIndex={() => void runAction("index")} onDelete={() => setConfirmingDelete(true)} />
      </header>
      <section className="detail-card" aria-labelledby="metadata-title">
        <h2 id="metadata-title">Thông tin tài liệu</h2>
        <dl className="metadata-grid">
          <div><dt>Tên tệp</dt><dd>{document.original_filename}</dd></div><div><dt>MIME type</dt><dd>{document.mime_type}</dd></div><div><dt>Dung lượng</dt><dd>{formatFileSize(document.file_size)}</dd></div>
          <div><dt>Ngày tải lên</dt><dd>{formatDate(document.created_at)}</dd></div><div><dt>Cập nhật</dt><dd>{formatDate(document.updated_at)}</dd></div><div><dt>Lập chỉ mục lúc</dt><dd>{formatDate(document.embedded_at)}</dd></div>
          <div><dt>Xử lý</dt><dd><StatusBadge status={document.status} kind="processing" /></dd></div><div><dt>Lập chỉ mục</dt><dd><StatusBadge status={document.embedding_status} kind="embedding" /></dd></div>
        </dl>
        {document.description && <div className="document-description"><strong>Mô tả</strong><p>{document.description}</p></div>}
        {document.processing_error && <p className="pipeline-error">Lỗi xử lý: {document.processing_error}</p>}
        {document.embedding_error && <p className="pipeline-error">Lỗi lập chỉ mục: {document.embedding_error}</p>}
      </section>
      <section className="detail-card" aria-labelledby="chunks-title">
        <div className="section-heading"><h2 id="chunks-title">Các đoạn nội dung</h2>{chunkTotal > 0 && <span>{chunkTotal} đoạn</span>}</div>
        {chunksLoading ? <p className="chunks-empty">Đang tải nội dung…</p> : chunks.length === 0 ? <p className="chunks-empty">Chưa có nội dung được trích xuất.</p> : <div className="chunk-list">{chunks.map((chunk) => <article key={chunk.id}><header><strong>Đoạn {chunk.chunk_index + 1}</strong><span>{chunk.char_count} ký tự · khoảng {chunk.token_estimate} token</span></header><p>{chunk.content}</p></article>)}</div>}
        {chunkTotal > chunks.length && <p className="chunks-note">Đang hiển thị {chunks.length} đoạn đầu tiên.</p>}
      </section>
      {confirmingDelete && <ConfirmDeleteDialog documentTitle={document.title} isDeleting={busy === "delete"} onCancel={() => setConfirmingDelete(false)} onConfirm={() => void remove()} />}
    </div>
  );
}
