"use client";

import { useRef, useState, type FormEvent } from "react";
import { Upload } from "lucide-react";
import { Button } from "@/components/ui/button";
import { Input } from "@/components/ui/input";
import { Modal } from "@/components/ui/modal";
import { ACCEPTED_DOCUMENTS, MAX_UPLOAD_BYTES, documentErrorMessage } from "@/lib/documents/document-utils";
import { uploadDocument } from "@/lib/documents/document-api";

export function UploadDocumentDialog({ onClose, onUploaded }: { onClose: () => void; onUploaded: () => void }) {
  const fileInput = useRef<HTMLInputElement>(null);
  const [file, setFile] = useState<File | null>(null);
  const [title, setTitle] = useState("");
  const [description, setDescription] = useState("");
  const [error, setError] = useState<string | null>(null);
  const [isUploading, setIsUploading] = useState(false);

  async function submit(event: FormEvent<HTMLFormElement>) {
    event.preventDefault();
    if (!file) return setError("Vui lòng chọn một tệp PDF, DOCX hoặc TXT.");
    const extension = `.${file.name.split(".").pop()?.toLowerCase() ?? ""}`;
    if (![".pdf", ".docx", ".txt"].includes(extension)) return setError("Định dạng tệp không được hỗ trợ.");
    if (file.size > MAX_UPLOAD_BYTES) return setError("Tệp vượt quá dung lượng cho phép.");
    setError(null);
    setIsUploading(true);
    try {
      await uploadDocument({ file, title, description });
      setIsUploading(false);
      onUploaded();
    } catch (caught) {
      setError(documentErrorMessage(caught, "upload"));
      setIsUploading(false);
    }
  }

  return (
      <Modal className="dialog-card upload-dialog" labelledBy="upload-title" busy={isUploading} onClose={onClose}>
        <h2 id="upload-title">Tải tài liệu lên</h2>
        <p>Hỗ trợ PDF, DOCX và TXT. Dung lượng tối đa 20 MB.</p>
        <form className="upload-form" onSubmit={submit}>
          <input ref={fileInput} hidden aria-label="Tệp tài liệu" id="document-file" type="file" accept={ACCEPTED_DOCUMENTS} disabled={isUploading} onChange={(event) => setFile(event.target.files?.[0] ?? null)} />
          <Button autoFocus type="button" variant="secondary" onClick={() => fileInput.current?.click()} disabled={isUploading}><Upload size={17} /> <span>{file ? file.name : "Chọn tệp"}</span></Button>
          <Input label="Tiêu đề (không bắt buộc)" name="title" value={title} maxLength={255} onChange={(event) => setTitle(event.target.value)} disabled={isUploading} />
          <label className="field" htmlFor="document-description"><span className="field-label">Mô tả (không bắt buộc)</span><textarea id="document-description" value={description} maxLength={5000} onChange={(event) => setDescription(event.target.value)} disabled={isUploading} /></label>
          <p className={`form-alert form-error${error ? "" : " form-alert-empty"}`} role={error ? "alert" : "status"} aria-live="polite">{error ?? ""}</p>
          <div className="dialog-actions"><Button type="button" variant="secondary" onClick={onClose} disabled={isUploading}>Hủy</Button><Button type="submit" disabled={isUploading}>{isUploading ? "Đang tải lên..." : "Tải tài liệu lên"}</Button></div>
        </form>
      </Modal>
  );
}
