"use client";

import { LogOut, MessageSquareText, Plus, Search, Settings, X, Files } from "lucide-react";
import { usePathname } from "next/navigation";
import { Brand } from "@/components/navigation/brand";
import { SidebarItem } from "@/components/navigation/sidebar-item";
import { IconButton } from "@/components/ui/icon-button";
import { MOCK_CONVERSATIONS, MOCK_PROFILE } from "@/lib/constants/mock-ui";

export function WorkspaceSidebar({ collapsed, mobileOpen, closeMobile }: {
  collapsed: boolean;
  mobileOpen: boolean;
  closeMobile: () => void;
}) {
  const pathname = usePathname();
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
        <div className="profile-summary" title={collapsed ? MOCK_PROFILE.name : undefined}><span>{MOCK_PROFILE.initials}</span>{!collapsed && <div><strong>{MOCK_PROFILE.name}</strong><small>{MOCK_PROFILE.label}</small></div>}</div>
        <div className="footer-actions">
          <IconButton label="Cài đặt (sắp có)"><Settings size={18} /></IconButton>
          <IconButton label="Đăng xuất (sắp có)"><LogOut size={18} /></IconButton>
        </div>
      </div>
    </aside>
  );
}
