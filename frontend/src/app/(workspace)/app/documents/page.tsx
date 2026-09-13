import type { Metadata } from "next";
import { Filter, Plus, Search } from "lucide-react";
import { DocumentsTable } from "@/components/documents/documents-table";
import { Button } from "@/components/ui/button";
import { Input } from "@/components/ui/input";
import { PageHeader } from "@/components/ui/page-header";

export const metadata: Metadata = { title: "Tài liệu" };

export default function DocumentsPage() {
  return (
    <div className="page-container">
      <PageHeader title="Tài liệu" description="Quản lý tài liệu dùng cho tra cứu và dẫn nguồn.">
        <Button><Plus size={17} aria-hidden="true" /> Tải tài liệu lên</Button>
      </PageHeader>
      <div className="table-toolbar">
        <Input label="Tìm tài liệu" hideLabel icon={<Search size={17} />} placeholder="Tìm theo tên tài liệu…" />
        <Button variant="secondary"><Filter size={17} aria-hidden="true" /> Bộ lọc</Button>
      </div>
      <DocumentsTable />
    </div>
  );
}
