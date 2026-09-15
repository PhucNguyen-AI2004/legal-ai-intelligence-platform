"use client";

import { Button } from "@/components/ui/button";
import { Modal } from "@/components/ui/modal";

export function ConfirmDeleteDialog({ documentTitle, isDeleting, onCancel, onConfirm, error }: {
  error?: string | null;
  documentTitle: string;
  isDeleting: boolean;
  onCancel: () => void;
  onConfirm: () => void;
}) {
  return (
      <Modal alert labelledBy="delete-title" describedBy="delete-description" busy={isDeleting} onClose={onCancel}>
        <h2 id="delete-title">Xóa tài liệu?</h2>
        <p className="dialog-document-name">{documentTitle}</p>
        <p id="delete-description">Tài liệu và dữ liệu xử lý liên quan sẽ bị xóa. Hành động này không thể hoàn tác.</p>
        {error && <p className="form-alert form-error" role="alert">{error}</p>}
        <div className="dialog-actions">
          <Button autoFocus type="button" variant="secondary" onClick={onCancel} disabled={isDeleting}>Hủy</Button>
          <Button type="button" className="button-danger" onClick={onConfirm} disabled={isDeleting}>{isDeleting ? "Đang xóa..." : "Xóa tài liệu"}</Button>
        </div>
      </Modal>
  );
}
