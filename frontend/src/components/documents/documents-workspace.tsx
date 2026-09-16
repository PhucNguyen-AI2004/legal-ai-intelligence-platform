"use client";

import { useCallback, useEffect, useMemo, useRef, useState } from "react";
import { FilePlus2, Plus, Search } from "lucide-react";
import { Button } from "@/components/ui/button";
import { Input } from "@/components/ui/input";
import { PageHeader } from "@/components/ui/page-header";
import { ConfirmDeleteDialog } from "./confirm-delete-dialog";
import { DocumentsTable } from "./documents-table";
import { UploadDocumentDialog } from "./upload-document-dialog";
import { deleteDocument, indexDocument, listDocuments, processDocument } from "@/lib/documents/document-api";
import { documentErrorMessage, isPipelineActive } from "@/lib/documents/document-utils";
import type { DocumentRecord } from "@/lib/documents/types";

const PAGE_SIZE = 20;
const POLL_INTERVAL_MS = 3000;
const MAX_POLL_ATTEMPTS = 40;
type BusyState = { id: string; action: "process" | "index" | "delete" } | null;

export function DocumentsWorkspace({ initialFeedback }: { initialFeedback?: string }) {
  const [documents, setDocuments] = useState<DocumentRecord[]>([]);
  const [total, setTotal] = useState(0);
  const [skip, setSkip] = useState(0);
  const [query, setQuery] = useState("");
  const [isLoading, setIsLoading] = useState(true);
  const [error, setError] = useState<string | null>(null);
  const [feedback, setFeedback] = useState<string | null>(initialFeedback ?? null);
  const [uploadOpen, setUploadOpen] = useState(false);
  const [deleteTarget, setDeleteTarget] = useState<DocumentRecord | null>(null);
  const [busy, setBusy] = useState<BusyState>(null);
  const pollAttempts = useRef(0);

  const load = useCallback(async (nextSkip: number, background = false) => {
    if (!background) setIsLoading(true);
    setError(null);
    try {
      const response = await listDocuments(nextSkip, PAGE_SIZE);
      setDocuments(response.items);
      setTotal(response.total);
      setSkip(response.skip);
    } catch (caught) {
      setError(documentErrorMessage(caught, "load"));
    } finally {
      if (!background) setIsLoading(false);
    }
  }, []);

  useEffect(() => { queueMicrotask(() => void load(0)); }, [load]);

  useEffect(() => {
    if (!documents.some(isPipelineActive)) {
      pollAttempts.current = 0;
      return;
    }
    if (pollAttempts.current >= MAX_POLL_ATTEMPTS) return;
    const timer = window.setTimeout(() => {
      pollAttempts.current += 1;
      void load(skip, true);
    }, POLL_INTERVAL_MS);
    return () => window.clearTimeout(timer);
  }, [documents, load, skip]);

  const visibleDocuments = useMemo(() => {
    const normalized = query.trim().toLocaleLowerCase("vi");
    return normalized ? documents.filter((document) => `${document.title} ${document.original_filename}`.toLocaleLowerCase("vi").includes(normalized)) : documents;
  }, [documents, query]);

  async function mutate(document: DocumentRecord, action: "process" | "index") {
    setBusy({ id: document.id, action });
    setError(null);
    setFeedback(null);
    try {
      if (action === "process") await processDocument(document.id); else await indexDocument(document.id);
      setFeedback(action === "process" ? "Yêu cầu xử lý đã được xếp hàng." : "Yêu cầu lập chỉ mục đã được xếp hàng.");
      await load(skip);
    } catch (caught) {
      const message = documentErrorMessage(caught, action);
      await load(skip);
      setError(message);
    } finally {
      setBusy(null);
    }
  }

  async function confirmDelete() {
    if (!deleteTarget) return;
    setBusy({ id: deleteTarget.id, action: "delete" });
    setError(null);
    try {
      await deleteDocument(deleteTarget.id);
      setDeleteTarget(null);
      setFeedback("Đã xóa tài liệu.");
      await load(documents.length === 1 && skip > 0 ? Math.max(0, skip - PAGE_SIZE) : skip);
    } catch (caught) {
      const message = documentErrorMessage(caught, "delete");
      await load(skip);
      setError(message);
    } finally {
      setBusy(null);
    }
  }

  function uploaded() {
    setUploadOpen(false);
    setFeedback("Tải tài liệu thành công.");
    void load(0);
  }

  return (
    <div className="page-container">
      <PageHeader title="Tài liệu" description="Quản lý tài liệu dùng cho tra cứu và dẫn nguồn."><Button onClick={() => setUploadOpen(true)}><Plus size={17} /> Tải tài liệu lên</Button></PageHeader>
      {feedback && <p className="workspace-notice notice-success" role="status">{feedback}</p>}
      {error && <div className="workspace-notice notice-error" role="alert"><p>{error}</p><Button variant="secondary" disabled={isLoading || busy !== null} onClick={() => void load(skip)}>Tải lại danh sách</Button></div>}
      <div className="table-toolbar">
        <Input label="Tìm tài liệu trên trang hiện tại" hideLabel icon={<Search size={17} />} value={query} onChange={(event) => setQuery(event.target.value)} placeholder="Tìm trên trang hiện tại…" />
      </div>
      {isLoading ? <DocumentListSkeleton /> : documents.length === 0 ? (error ? null : <DocumentEmptyState onUpload={() => setUploadOpen(true)} />) : <>
        <DocumentsTable documents={visibleDocuments} busy={busy} onProcess={(document) => void mutate(document, "process")} onIndex={(document) => void mutate(document, "index")} onDelete={(document) => { setError(null); setDeleteTarget(document); }} />
        {visibleDocuments.length === 0 && <p className="no-search-results">Không có tài liệu phù hợp với từ khóa.</p>}
        <div className="pagination"><span>Hiển thị {skip + 1}–{Math.min(skip + documents.length, total)} trong {total}</span><div><Button variant="secondary" disabled={skip === 0 || isLoading} onClick={() => void load(Math.max(0, skip - PAGE_SIZE))}>Trước</Button><Button variant="secondary" disabled={skip + PAGE_SIZE >= total || isLoading} onClick={() => void load(skip + PAGE_SIZE)}>Sau</Button></div></div>
      </>}
      {uploadOpen && <UploadDocumentDialog onClose={() => setUploadOpen(false)} onUploaded={uploaded} />}
      {deleteTarget && <ConfirmDeleteDialog error={error} documentTitle={deleteTarget.title} isDeleting={busy?.action === "delete"} onCancel={() => setDeleteTarget(null)} onConfirm={() => void confirmDelete()} />}
    </div>
  );
}

function DocumentEmptyState({ onUpload }: { onUpload: () => void }) {
  return <section className="document-empty"><FilePlus2 size={26} /><h2>Chưa có tài liệu</h2><p>Tải lên tài liệu pháp lý để bắt đầu tra cứu và phân tích với Legal AI.</p><Button onClick={onUpload}>Tải tài liệu lên</Button></section>;
}

function DocumentListSkeleton() {
  return <div className="table-surface document-skeleton" role="status" aria-live="polite"><span>Đang tải danh sách tài liệu…</span>{[1, 2, 3].map((row) => <i key={row} />)}</div>;
}
