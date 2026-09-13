"use client";

import { useEffect, useRef } from "react";
import { Button } from "@/components/ui/button";

export function ConfirmDeleteDialog({ documentTitle, isDeleting, onCancel, onConfirm }: {
  documentTitle: string;
  isDeleting: boolean;
  onCancel: () => void;
  onConfirm: () => void;
}) {
  const cancelRef = useRef<HTMLButtonElement>(null);
  useEffect(() => { cancelRef.current?.focus(); }, []);
  return (
    <div className="dialog-backdrop" role="presentation">
      <section className="dialog-card" role="alertdialog" aria-modal="true" aria-labelledby="delete-title" aria-describedby="delete-description">
        <h2 id="delete-title">Xóa tài liệu?</h2>
        <p className="dialog-document-name">{documentTitle}</p>
        <p id="delete-description">Tài liệu và dữ liệu xử lý liên quan sẽ bị xóa. Hành động này không thể hoàn tác.</p>
        <div className="dialog-actions">
          <Button ref={cancelRef} type="button" variant="secondary" onClick={onCancel} disabled={isDeleting}>Hủy</Button>
          <Button type="button" className="button-danger" onClick={onConfirm} disabled={isDeleting}>{isDeleting ? "Đang xóa..." : "Xóa tài liệu"}</Button>
        </div>
      </section>
    </div>
  );
}
