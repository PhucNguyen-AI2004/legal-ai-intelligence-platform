"use client";

import Link from "next/link";
import { DocumentActions } from "./document-actions";
import { StatusBadge } from "@/components/ui/status-badge";
import { formatDate } from "@/lib/documents/document-utils";
import type { DocumentRecord } from "@/lib/documents/types";

export function DocumentsTable({ documents, busy, onProcess, onIndex, onDelete }: {
  documents: DocumentRecord[];
  busy: { id: string; action: "process" | "index" | "delete" } | null;
  onProcess: (document: DocumentRecord) => void;
  onIndex: (document: DocumentRecord) => void;
  onDelete: (document: DocumentRecord) => void;
}) {
  return (
    <div className="table-surface">
      <table>
        <thead><tr><th>Tên tài liệu</th><th>Loại file</th><th>Trạng thái xử lý</th><th>Trạng thái lập chỉ mục</th><th>Ngày tải lên</th><th>Thao tác</th></tr></thead>
        <tbody>{documents.map((document) => (
          <tr key={document.id}>
            <td><Link className="document-link" href={`/app/documents/${document.id}`}>{document.title}</Link><small>{document.original_filename}</small></td>
            <td>{document.file_type.toUpperCase()}</td>
            <td><StatusBadge status={document.status} kind="processing" /></td>
            <td><StatusBadge status={document.embedding_status} kind="embedding" /></td>
            <td>{formatDate(document.created_at)}</td>
            <td><DocumentActions document={document} compact busyAction={busy?.id === document.id ? busy.action : null} onProcess={() => onProcess(document)} onIndex={() => onIndex(document)} onDelete={() => onDelete(document)} /></td>
          </tr>
        ))}</tbody>
      </table>
    </div>
  );
}
