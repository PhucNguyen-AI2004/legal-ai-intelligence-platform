"use client";

import { useEffect, useState } from "react";
import { usePathname } from "next/navigation";
import { Modal } from "@/components/ui/modal";
import { WorkspaceHeader } from "./workspace-header";
import { WorkspaceSidebar } from "./workspace-sidebar";

export function WorkspaceShell({ children }: Readonly<{ children: React.ReactNode }>) {
  const [collapsed, setCollapsed] = useState(false);
  const [mobileOpen, setMobileOpen] = useState(false);
  const pathname = usePathname();
  useEffect(() => {
    const desktop = window.matchMedia("(min-width: 901px)");
    const closeOnDesktop = () => { if (desktop.matches) setMobileOpen(false); };
    desktop.addEventListener("change", closeOnDesktop);
    return () => desktop.removeEventListener("change", closeOnDesktop);
  }, []);

  return (
    <div className={`workspace-shell${collapsed ? " is-collapsed" : ""}`}>
      <a className="skip-link" href="#workspace-content">Đến nội dung chính</a>
      <WorkspaceSidebar collapsed={collapsed} mobileOpen={false} closeMobile={() => setMobileOpen(false)} />
      {mobileOpen && <Modal className="mobile-nav-dialog" label="Điều hướng không gian làm việc" onClose={() => setMobileOpen(false)}>
        <WorkspaceSidebar collapsed={false} mobileOpen closeMobile={() => setMobileOpen(false)} />
      </Modal>}
      <div className="workspace-main">
        <WorkspaceHeader key={pathname} collapsed={collapsed} toggleSidebar={() => setCollapsed((value) => !value)} openMobile={() => setMobileOpen(true)} />
        <main id="workspace-content" tabIndex={-1} className="workspace-content">{children}</main>
      </div>
    </div>
  );
}
