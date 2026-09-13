"use client";

import { LogOut, MessageSquareText, Plus, Search, Settings, X, Files } from "lucide-react";
import { usePathname } from "next/navigation";
import { Brand } from "@/components/navigation/brand";
import { SidebarItem } from "@/components/navigation/sidebar-item";
import { IconButton } from "@/components/ui/icon-button";
import { MOCK_CONVERSATIONS } from "@/lib/constants/mock-ui";
import { useAuth } from "@/components/auth/auth-provider";

export function WorkspaceSidebar({ collapsed, mobileOpen, closeMobile }: {
  collapsed: boolean;
  mobileOpen: boolean;
  closeMobile: () => void;
}) {
  const pathname = usePathname();
  const { user, logout } = useAuth();
  const displayName = user?.full_name || user?.email || "";
  const initial = displayName.charAt(0).toLocaleUpperCase("vi") || "?";
  return (
    <aside className={`workspace-sidebar${mobileOpen ? " mobile-open" : ""}`} aria-label="Điều hướng không gian làm việc">
      <div className="sidebar-top">
        <Brand compact={collapsed} />
        <IconButton className="mobile-close" label="Đóng điều hướng" onClick={closeMobile}><X size={19} /></IconButton>
      </div>
      <button className="new-chat" title={collapsed ? "Cuộc trò chuyện mới" : undefined}><Plus size={18} />{!collapsed && <span>Cuộc trò chuyện mới</span>}</button>
      {!collapsed && (
        <>
          <label className="conversation-search"><Search size={16} /><span className="sr-only">Tìm cuộc trò chuyện</span><input placeholder="Tìm cuộc trò chuyện" /></label>
          <div className="conversation-groups">
            {MOCK_CONVERSATIONS.map((group) => (
              <section key={group.label}><h2>{group.label}</h2>{group.items.map((item) => <button key={item}>{item}</button>)}</section>
            ))}
          </div>
        </>
      )}
      <nav className="sidebar-navigation">
        <SidebarItem href="/app/chat" icon={MessageSquareText} label="Hội thoại" active={pathname.startsWith("/app/chat")} collapsed={collapsed} />
        <SidebarItem href="/app/documents" icon={Files} label="Tài liệu" active={pathname.startsWith("/app/documents")} collapsed={collapsed} />
      </nav>
      <div className="sidebar-footer">
        <div className="profile-summary" title={collapsed ? displayName : undefined}><span>{initial}</span>{!collapsed && <div><strong>{user?.full_name}</strong><small>{user?.email}</small></div>}</div>
        <div className="footer-actions">
          <IconButton label="Cài đặt (sắp có)"><Settings size={18} /></IconButton>
          <IconButton label="Đăng xuất" onClick={logout}><LogOut size={18} /></IconButton>
        </div>
      </div>
    </aside>
  );
}
