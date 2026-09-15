"use client";

import { useEffect, useRef, useState } from "react";
import { Button } from "@/components/ui/button";
import { listDocuments } from "@/lib/documents/document-api";
import type { DocumentRecord } from "@/lib/documents/types";

interface Props {
  selected: string[];
  onChange: (ids: string[]) => void;
  disabled: boolean;
}

export function SourcePicker({ selected, onChange, disabled }: Props) {
  const [open, setOpen] = useState(false);
  return <div className="source-control">
    <button type="button" className="source-trigger" disabled={disabled} onClick={() => setOpen(true)} aria-haspopup="dialog">
      Nguồn: {selected.length ? `${selected.length} tài liệu · chỉ tin nhắn này` : "Tất cả tài liệu"}
    </button>
    {open && <DocumentPicker selected={selected} onChange={onChange} disabled={disabled} onClose={() => setOpen(false)} />}
  </div>;
}

// Only one API page is rendered. Default chat does not enumerate the library.
function DocumentPicker({ selected, onChange, onClose }: Props & { onClose: () => void }) {
  const dialog = useRef<HTMLDialogElement>(null);
  const [documents, setDocuments] = useState<DocumentRecord[]>([]);
  const [page, setPage] = useState(0);
  const [total, setTotal] = useState(0);
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState(false);
  const [revision, setRevision] = useState(0);
  const pageSize = 20;

  useEffect(() => { dialog.current?.showModal(); }, []);
  useEffect(() => {
    let active = true;
    listDocuments(page * pageSize, pageSize).then((response) => {
      if (!active) return;
      setDocuments(response.items);
      setTotal(response.total);
      setLoading(false);
    }).catch(() => { if (active) { setError(true); setLoading(false); } });
    return () => { active = false; };
  }, [page, revision]);

  function changePage(next: number) { setLoading(true); setError(false); setPage(next); }
  function refresh() { setLoading(true); setError(false); setRevision((value) => value + 1); }

  return <dialog ref={dialog} className="document-picker" aria-labelledby="source-picker-title" onCancel={onClose} onClose={onClose}>
    <div className="section-heading"><h2 id="source-picker-title">Nguồn cho tin nhắn này</h2><Button variant="secondary" onClick={onClose}>Đóng</Button></div>
    <p>Mặc định tìm trong tất cả tài liệu đủ điều kiện. Lựa chọn riêng chỉ dùng cho một lần gửi và được đặt lại sau khi gửi.</p>
    <Button variant="secondary" onClick={() => onChange([])}>Tất cả tài liệu</Button>
    <p role="status">{selected.length ? `Đã chọn ${selected.length}/100 tài liệu` : "Đang dùng tất cả tài liệu"}</p>
    {loading ? <p role="status">Đang tải tài liệu…</p> : error ? <p role="alert">Không thể tải tài liệu. <button type="button" onClick={refresh}>Thử lại</button></p> : <>
      <div className="source-options">{documents.map((document) => {
        const eligible = document.status === "processed" && document.embedding_status === "indexed";
        const checked = selected.includes(document.id);
        return <label key={document.id}><input type="checkbox" checked={checked} disabled={(!eligible && !checked) || (!checked && selected.length >= 100)} onChange={() => onChange(checked ? selected.filter((id) => id !== document.id) : [...selected, document.id])} /><span>{document.title}{!eligible && " — chưa sẵn sàng"}</span></label>;
      })}</div>
      {!documents.length && <p>Chưa có tài liệu trên trang này. Bạn có thể tải lên và lập chỉ mục trong mục Tài liệu.</p>}
      {documents.length > 0 && !documents.some((document) => document.status === "processed" && document.embedding_status === "indexed") && <p>Trang này chưa có tài liệu đủ điều kiện. Tất cả tài liệu vẫn là phạm vi mặc định.</p>}
    </>}
    <div className="source-pagination">
      <Button variant="secondary" disabled={loading || page === 0} onClick={() => changePage(page - 1)}>Trước</Button>
      <span>Trang {page + 1} · {total} tài liệu</span>
      <Button variant="secondary" disabled={loading || (page + 1) * pageSize >= total} onClick={() => changePage(page + 1)}>Sau</Button>
    </div>
    <div className="dialog-actions"><Button variant="secondary" disabled={loading} onClick={() => { onChange([]); refresh(); }}>Làm mới và bỏ lựa chọn</Button><Button onClick={onClose}>Xong</Button></div>
  </dialog>;
}
