"use client";

import { useState } from "react";
import { Menu, MoreHorizontal, PanelLeftClose, PanelLeftOpen, Pencil, Trash2 } from "lucide-react";
import { usePathname } from "next/navigation";
import { useConversations } from "@/components/conversations/conversation-provider";
import { IconButton } from "@/components/ui/icon-button";

export function WorkspaceHeader({ collapsed, toggleSidebar, openMobile }: { collapsed: boolean; toggleSidebar: () => void; openMobile: () => void }) {
  const pathname = usePathname();
  const { conversations, feedback, requestRename, requestDelete } = useConversations();
  const [menuOpen, setMenuOpen] = useState(false);
  const id = pathname.startsWith("/app/chat/") ? pathname.slice("/app/chat/".length).split("/")[0] : null;
  const conversation = conversations.find((item) => item.id === id);
  const isChat = pathname.startsWith("/app/chat");
  const title = isChat ? conversation?.title ?? "Cuộc trò chuyện mới" : pathname.startsWith("/app/documents") ? "Tài liệu" : "Legal AI";

  return <header className="workspace-header">
    <IconButton className="mobile-menu" label="Mở điều hướng" onClick={openMobile}><Menu size={20} /></IconButton>
    <IconButton className="desktop-toggle" label={collapsed ? "Mở rộng thanh bên" : "Thu gọn thanh bên"} onClick={toggleSidebar}>{collapsed ? <PanelLeftOpen size={20} /> : <PanelLeftClose size={20} />}</IconButton>
    <div className="header-title"><strong title={title}>{title}</strong>{feedback && <span role="status">{feedback}</span>}</div>
    {conversation && <div className="header-conversation-actions" onBlur={(event) => { if (!event.currentTarget.contains(event.relatedTarget)) setMenuOpen(false); }} onKeyDown={(event) => { if (event.key === "Escape") { setMenuOpen(false); event.currentTarget.querySelector("button")?.focus(); } }}><IconButton label="Thao tác với hội thoại" aria-expanded={menuOpen} onClick={() => setMenuOpen((value) => !value)}><MoreHorizontal size={18} /></IconButton>{menuOpen && <div className="conversation-menu"><button onClick={() => { setMenuOpen(false); requestRename(conversation); }}><Pencil size={14} /> Đổi tên</button><button className="delete-action" onClick={() => { setMenuOpen(false); requestDelete(conversation); }}><Trash2 size={14} /> Xóa</button></div>}</div>}
  </header>;
}
