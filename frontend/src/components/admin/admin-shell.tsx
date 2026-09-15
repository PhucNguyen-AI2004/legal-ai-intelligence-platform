"use client";
import Link from "next/link";
import { usePathname } from "next/navigation";
import { useAuth } from "@/components/auth/auth-provider";
import { adminAccess } from "@/lib/admin/admin-utils";

export function AdminShell({ children }: { children: React.ReactNode }) {
  const { user, isLoading } = useAuth();
  const pathname = usePathname();
  const access = adminAccess(user, isLoading);
  if (access === "loading") return <p role="status">Đang kiểm tra quyền truy cập…</p>;
  if (access === "denied") return <section className="page-container"><h1>Không có quyền truy cập</h1><p>Khu vực này dành cho quản trị viên.</p><Link href="/app/chat">Quay lại hội thoại</Link></section>;
  return <div className="page-container admin-console"><p className="eyebrow">Legal AI · Admin Console</p><nav className="admin-tabs" aria-label="Quản trị">{[["/app/admin", "Tổng quan"], ["/app/admin/users", "Người dùng"], ["/app/admin/documents", "Tài liệu"]].map(([href, label]) => <Link key={href} href={href} aria-current={pathname === href ? "page" : undefined}>{label}</Link>)}</nav>{children}</div>;
}
