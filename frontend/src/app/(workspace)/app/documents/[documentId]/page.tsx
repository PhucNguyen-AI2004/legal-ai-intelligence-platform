import type { Metadata } from "next";
import Link from "next/link";
import { ArrowLeft, FileText, MoreHorizontal } from "lucide-react";
import { Button } from "@/components/ui/button";
import { StatusBadge } from "@/components/ui/status-badge";

export const metadata: Metadata = { title: "Chi tiết tài liệu" };

export default async function DocumentDetailPage({ params }: { params: Promise<{ documentId: string }> }) {
  const { documentId } = await params;
  return (
    <div className="page-container document-detail">
      <Link className="back-link" href="/app/documents"><ArrowLeft size={17} /> Quay lại tài liệu</Link>
      <header className="detail-header">
        <div className="detail-title">
          <span className="file-icon"><FileText size={24} /></span>
          <div><p className="eyebrow">Tài liệu mẫu</p><h1>Chi tiết tài liệu</h1><p>ID: {documentId}</p></div>
        </div>
        <Button variant="secondary"><MoreHorizontal size={18} /> Thao tác</Button>
      </header>
      <section className="detail-card" aria-labelledby="metadata-title">
        <h2 id="metadata-title">Thông tin tài liệu</h2>
        <dl className="metadata-grid">
          <div><dt>Tên tệp</dt><dd>Chưa tải dữ liệu</dd></div>
          <div><dt>Loại</dt><dd>—</dd></div>
          <div><dt>Ngày tải lên</dt><dd>—</dd></div>
          <div><dt>Xử lý</dt><dd><StatusBadge status="pending" /></dd></div>
          <div><dt>Lập chỉ mục</dt><dd><StatusBadge status="pending" /></dd></div>
        </dl>
      </section>
      <section className="detail-card" aria-labelledby="chunks-title">
        <h2 id="chunks-title">Các đoạn văn bản đã trích xuất</h2>
        <div className="development-placeholder">Nội dung sẽ hiển thị sau khi kết nối API tài liệu ở phase tiếp theo.</div>
      </section>
    </div>
  );
}
