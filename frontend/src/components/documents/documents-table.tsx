import { MoreHorizontal } from "lucide-react";
import { IconButton } from "@/components/ui/icon-button";
import { StatusBadge } from "@/components/ui/status-badge";
import { MOCK_DOCUMENTS } from "@/lib/constants/mock-ui";

export function DocumentsTable() {
  return (
    <div className="table-surface">
      <table>
        <thead><tr><th>Tên tài liệu</th><th>Loại</th><th>Trạng thái xử lý</th><th>Trạng thái lập chỉ mục</th><th>Ngày tải lên</th><th><span className="sr-only">Thao tác</span></th></tr></thead>
        <tbody>{MOCK_DOCUMENTS.map((document) => (
          <tr key={document.id}>
            <td><strong>{document.name}</strong><small>Dữ liệu minh họa giao diện</small></td>
            <td>{document.type}</td><td><StatusBadge status={document.processing} /></td><td><StatusBadge status={document.indexing} /></td><td>{document.uploadedAt}</td>
            <td><IconButton label={`Thao tác với ${document.name}`}><MoreHorizontal size={18} /></IconButton></td>
          </tr>
        ))}</tbody>
      </table>
    </div>
  );
}
