"use client";
import { useEffect, useState, type ReactNode } from "react";
import { Button } from "@/components/ui/button";
import { ApiError } from "@/lib/api/client";
import { getAdminData, type Overview, type Page, type AdminUser, type AdminDocument } from "@/lib/admin/admin-api";
import { adminQuery } from "@/lib/admin/admin-utils";

function DataView<T>({ resource, children }: { resource: string; children: (data: T) => ReactNode }) {
  const [result, setResult] = useState<{ key: string; data?: T; error?: string } | null>(null);
  const [attempt, setAttempt] = useState(0);
  const key = `${resource}:${attempt}`;
  useEffect(() => {
    const controller = new AbortController();
    getAdminData<T>(resource, controller.signal).then(data => {
      if (!controller.signal.aborted) setResult({ key, data });
    }).catch(error => {
      if (!controller.signal.aborted) setResult({ key, error: error instanceof ApiError && error.status === 403 ? "Bạn không có quyền truy cập dữ liệu quản trị." : "Không thể tải dữ liệu. Vui lòng thử lại." });
    });
    return () => controller.abort();
  }, [resource, key]);
  if (!result || result.key !== key) return <p className="admin-state" role="status">Đang tải dữ liệu…</p>;
  if (result.error) return <div className="admin-state" role="alert"><p>{result.error}</p><Button variant="secondary" onClick={() => setAttempt(value => value + 1)}>Thử lại</Button></div>;
  return <>{children(result.data as T)}</>;
}

const processing = { uploaded: "Đã tải lên", processing: "Đang xử lý", processed: "Đã xử lý", failed: "Thất bại" };
const indexing = { pending: "Chờ lập chỉ mục", indexing: "Đang lập chỉ mục", indexed: "Đã lập chỉ mục", failed: "Thất bại" };
const date = (value: string) => new Date(value).toLocaleString("vi-VN");
function Distribution({ title, counts, labels }: { title: string; counts: Record<string, number>; labels: Record<string, string> }) {
  return <section className="admin-distribution"><h2>{title}</h2><dl>{Object.entries(labels).map(([key, label]) => <div key={key}><dt>{label}</dt><dd>{counts[key] ?? 0}</dd></div>)}</dl></section>;
}
export function AdminOverview() {
  return <><h1>Tổng quan quản trị</h1><p className="admin-description">Số lượng tài khoản và tài liệu trong hệ thống tại thời điểm tải.</p><DataView<Overview> resource="overview">{data => <><dl className="admin-metrics">{[["Người dùng", data.total_users], ["Tài liệu", data.total_documents], ["Hội thoại", data.total_conversations], ["Tin nhắn", data.total_messages]].map(([label, count]) => <div key={label}><dt>{label}</dt><dd>{count}</dd></div>)}</dl><div className="admin-distributions"><Distribution title="Xử lý tài liệu" counts={data.processing_counts} labels={processing} /><Distribution title="Lập chỉ mục" counts={data.embedding_counts} labels={indexing} /></div></>}</DataView></>;
}
function Pagination({ page, onPage }: { page: Page<unknown>; onPage: (skip: number) => void }) {
  return <nav className="pagination" aria-label="Phân trang"><span>{page.total} kết quả · Trang {Math.floor(page.skip / page.limit) + 1}</span><div><Button variant="secondary" disabled={page.skip === 0} onClick={() => onPage(Math.max(0, page.skip - page.limit))}>Trước</Button><Button variant="secondary" disabled={page.skip + page.limit >= page.total} onClick={() => onPage(page.skip + page.limit)}>Sau</Button></div></nav>;
}
function Cell({ label, children }: { label: string; children: ReactNode }) { return <td><span className="admin-cell-label" aria-hidden="true">{label}</span><div>{children}</div></td>; }
export function AdminUsers() {
  const [filter, setFilter] = useState({ skip: 0, email: "" });
  const [email, setEmail] = useState("");
  return <><h1>Người dùng</h1><p className="admin-description">Danh sách tài khoản · Chỉ xem</p><form className="admin-filters" onSubmit={event => { event.preventDefault(); setFilter({ skip: 0, email: email.trim() }); }}><label>Email<input value={email} maxLength={254} onChange={event => setEmail(event.target.value)} placeholder="Tìm theo email" /></label><Button type="submit">Tìm kiếm</Button></form><DataView<Page<AdminUser>> resource={`users?${adminQuery(filter.skip, { email: filter.email })}`}>{page => <>{page.items.length ? <table className="admin-table"><caption className="sr-only">Tài khoản người dùng</caption><thead><tr><th scope="col">Email / ID</th><th scope="col">Vai trò</th><th scope="col">Ngày tạo</th></tr></thead><tbody>{page.items.map(user => <tr key={user.id}><Cell label="Email / ID"><strong>{user.email}</strong><small>{user.id}</small></Cell><Cell label="Vai trò">{user.role === "admin" ? "Quản trị viên" : "Người dùng"}</Cell><Cell label="Ngày tạo">{date(user.created_at)}</Cell></tr>)}</tbody></table> : <p className="admin-state">Không có người dùng phù hợp.</p>}<Pagination page={page} onPage={skip => setFilter(current => ({ ...current, skip }))} /></>}</DataView></>;
}
export function AdminDocuments() {
  const [filter, setFilter] = useState({ skip: 0, status: "", embedding_status: "" });
  return <><h1>Tài liệu toàn hệ thống</h1><p className="admin-description">Thông tin tài liệu và chủ sở hữu · Chỉ xem metadata</p><div className="admin-filters">{([['status', 'Xử lý', processing], ['embedding_status', 'Lập chỉ mục', indexing]] as const).map(([key, label, labels]) => <label key={key}>{label}<select value={filter[key]} onChange={event => setFilter(current => ({ ...current, skip: 0, [key]: event.target.value }))}><option value="">Tất cả</option>{Object.entries(labels).map(([value, text]) => <option key={value} value={value}>{text}</option>)}</select></label>)}</div><DataView<Page<AdminDocument>> resource={`documents?${adminQuery(filter.skip, { status: filter.status, embedding_status: filter.embedding_status })}`}>{page => <>{page.items.length ? <table className="admin-table"><caption className="sr-only">Metadata tài liệu toàn hệ thống</caption><thead><tr>{["Tài liệu", "Chủ sở hữu", "Xử lý", "Lập chỉ mục", "Ngày tạo"].map(label => <th scope="col" key={label}>{label}</th>)}</tr></thead><tbody>{page.items.map(doc => <tr key={doc.id}><Cell label="Tài liệu"><strong>{doc.title}</strong><small>{doc.original_filename}</small><small>{doc.id}</small><small>{doc.file_type.toUpperCase()} · {doc.file_size.toLocaleString("vi-VN")} bytes</small></Cell><Cell label="Chủ sở hữu">{doc.owner_email}<small>{doc.owner_id}</small></Cell><Cell label="Xử lý">{processing[doc.status as keyof typeof processing] ?? doc.status}</Cell><Cell label="Lập chỉ mục">{indexing[doc.embedding_status as keyof typeof indexing] ?? doc.embedding_status}</Cell><Cell label="Ngày tạo">{date(doc.created_at)}</Cell></tr>)}</tbody></table> : <p className="admin-state">Không có tài liệu phù hợp.</p>}<Pagination page={page} onPage={skip => setFilter(current => ({ ...current, skip }))} /></>}</DataView></>;
}
