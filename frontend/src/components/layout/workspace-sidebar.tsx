"use client";

import { useMemo, useState } from "react";
import Link from "next/link";
import { Files, LogOut, MessageSquareText, MoreHorizontal, Pencil, Plus, Search, Settings, Trash2, X } from "lucide-react";
import { usePathname } from "next/navigation";
import { useAuth } from "@/components/auth/auth-provider";
import { useConversations } from "@/components/conversations/conversation-provider";
import { Brand } from "@/components/navigation/brand";
import { SidebarItem } from "@/components/navigation/sidebar-item";
import { Button } from "@/components/ui/button";
import { IconButton } from "@/components/ui/icon-button";
import { groupConversations } from "@/lib/conversations/conversation-utils";
import type { ConversationSummary } from "@/lib/conversations/types";

export function WorkspaceSidebar({ collapsed, mobileOpen, closeMobile }: { collapsed: boolean; mobileOpen: boolean; closeMobile: () => void }) {
  const pathname = usePathname();
  const { user, logout } = useAuth();
  const { conversations, total, isLoading, isLoadingMore, isCreating, error, createNew, loadMore, retry, requestRename, requestDelete } = useConversations();
  const [query, setQuery] = useState("");
  const [menuId, setMenuId] = useState<string | null>(null);
  const displayName = user?.full_name || user?.email || "";
  const initial = displayName.charAt(0).toLocaleUpperCase("vi") || "?";
  const activeId = pathname.startsWith("/app/chat/") ? pathname.slice("/app/chat/".length).split("/")[0] : null;
  const visible = useMemo(() => {
    const normalized = query.trim().toLocaleLowerCase("vi");
    return normalized ? conversations.filter((item) => item.title.toLocaleLowerCase("vi").includes(normalized)) : conversations;
  }, [conversations, query]);

  function chooseAction(conversation: ConversationSummary, action: "rename" | "delete") {
    setMenuId(null);
    if (action === "rename") requestRename(conversation); else requestDelete(conversation);
  }

  return <aside className={`workspace-sidebar${mobileOpen ? " mobile-open" : ""}`} aria-label="Điều hướng không gian làm việc">
    <div className="sidebar-top"><Brand compact={collapsed} /><IconButton className="mobile-close" label="Đóng điều hướng" onClick={closeMobile}><X size={19} /></IconButton></div>
    <button className="new-chat" title={collapsed ? "Cuộc trò chuyện mới" : undefined} onClick={() => { closeMobile(); void createNew(); }} disabled={isCreating}><Plus size={18} />{!collapsed && <span>{isCreating ? "Đang tạo..." : "Cuộc trò chuyện mới"}</span>}</button>
    {!collapsed && <>
      <label className="conversation-search"><Search size={16} /><span className="sr-only">Tìm cuộc trò chuyện</span><input value={query} onChange={(event) => setQuery(event.target.value)} placeholder="Tìm cuộc trò chuyện" /></label>
      <div className="conversation-groups">
        {isLoading ? <div className="conversation-skeleton" role="status">Đang tải hội thoại…<i /><i /><i /></div> : error && conversations.length === 0 ? <div className="conversation-state" role="alert"><span>{error}</span><Button variant="secondary" onClick={() => void retry()}>Thử lại</Button></div> : visible.length === 0 ? <p className="conversation-state">{query ? "Không tìm thấy hội thoại." : "Chưa có hội thoại nào."}</p> : groupConversations(visible).map((group) => <section key={group.label}><h2>{group.label}</h2>{group.items.map((item) => <div className={`conversation-row${activeId === item.id ? " active" : ""}`} key={item.id}><Link href={`/app/chat/${item.id}`} onClick={closeMobile} aria-current={activeId === item.id ? "page" : undefined}>{item.title}</Link><IconButton label={`Thao tác với ${item.title}`} onClick={() => setMenuId((current) => current === item.id ? null : item.id)}><MoreHorizontal size={16} /></IconButton>{menuId === item.id && <div className="conversation-menu"><button onClick={() => chooseAction(item, "rename")}><Pencil size={14} /> Đổi tên</button><button className="delete-action" onClick={() => chooseAction(item, "delete")}><Trash2 size={14} /> Xóa</button></div>}</div>)}</section>)}
        {!isLoading && conversations.length < total && !query && <button className="load-more-conversations" onClick={() => void loadMore()} disabled={isLoadingMore}>{isLoadingMore ? "Đang tải..." : "Xem thêm"}</button>}
        {error && conversations.length > 0 && <p className="conversation-inline-error" role="alert">{error}</p>}
      </div>
    </>}
    <nav className="sidebar-navigation"><SidebarItem href="/app/chat" icon={MessageSquareText} label="Hội thoại" active={pathname.startsWith("/app/chat")} collapsed={collapsed} /><SidebarItem href="/app/documents" icon={Files} label="Tài liệu" active={pathname.startsWith("/app/documents")} collapsed={collapsed} /></nav>
    <div className="sidebar-footer"><div className="profile-summary" title={collapsed ? displayName : undefined}><span>{initial}</span>{!collapsed && <div><strong>{user?.full_name}</strong><small>{user?.email}</small></div>}</div><div className="footer-actions"><IconButton label="Cài đặt (sắp có)"><Settings size={18} /></IconButton><IconButton label="Đăng xuất" onClick={logout}><LogOut size={18} /></IconButton></div></div>
  </aside>;
}
