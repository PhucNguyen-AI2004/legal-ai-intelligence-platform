"use client";

import { DatabaseZap, Eye, FileCog, Trash2 } from "lucide-react";
import Link from "next/link";
import { Button } from "@/components/ui/button";
import { canIndex, canProcess } from "@/lib/documents/document-utils";
import type { DocumentRecord } from "@/lib/documents/types";

export function DocumentActions({ document, busyAction, compact = false, showView = true, onProcess, onIndex, onDelete }: {
  document: DocumentRecord;
  busyAction: "process" | "index" | "delete" | null;
  compact?: boolean;
  showView?: boolean;
  onProcess: () => void;
  onIndex: () => void;
  onDelete: () => void;
}) {
  const disabled = busyAction !== null;
  return (
    <div className={`document-actions${compact ? " document-actions-compact" : ""}`}>
      {showView && <Link className="button button-secondary" href={`/app/documents/${document.id}`}><Eye size={16} /> Xem</Link>}
      {canProcess(document) && <Button variant="secondary" onClick={onProcess} disabled={disabled}><FileCog size={16} />{busyAction === "process" ? "Đang xử lý..." : "Xử lý"}</Button>}
      {canIndex(document) && <Button variant="secondary" onClick={onIndex} disabled={disabled}><DatabaseZap size={16} />{busyAction === "index" ? "Đang lập chỉ mục..." : "Lập chỉ mục"}</Button>}
      <Button variant="secondary" className="delete-action" onClick={onDelete} disabled={disabled || document.status === "processing" || document.embedding_status === "indexing"}><Trash2 size={16} /> Xóa</Button>
    </div>
  );
}
