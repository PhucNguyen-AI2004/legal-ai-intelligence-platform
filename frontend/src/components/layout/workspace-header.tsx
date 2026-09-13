import { FileText, Menu, PanelLeftClose, PanelLeftOpen } from "lucide-react";
import { IconButton } from "@/components/ui/icon-button";

export function WorkspaceHeader({ collapsed, toggleSidebar, openMobile }: {
  collapsed: boolean;
  toggleSidebar: () => void;
  openMobile: () => void;
}) {
  return (
    <header className="workspace-header">
      <IconButton className="mobile-menu" label="Mở điều hướng" onClick={openMobile}><Menu size={20} /></IconButton>
      <IconButton className="desktop-toggle" label={collapsed ? "Mở rộng thanh bên" : "Thu gọn thanh bên"} onClick={toggleSidebar}>
        {collapsed ? <PanelLeftOpen size={20} /> : <PanelLeftClose size={20} />}
      </IconButton>
      <div className="header-title"><strong>Cuộc trò chuyện mới</strong><span><FileText size={14} /> Chưa chọn tài liệu</span></div>
    </header>
  );
}
