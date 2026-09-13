"use client";

import { useState } from "react";
import { WorkspaceHeader } from "./workspace-header";
import { WorkspaceSidebar } from "./workspace-sidebar";

export function WorkspaceShell({ children }: Readonly<{ children: React.ReactNode }>) {
  const [collapsed, setCollapsed] = useState(false);
  const [mobileOpen, setMobileOpen] = useState(false);

  return (
    <div className={`workspace-shell${collapsed ? " is-collapsed" : ""}`}>
      <WorkspaceSidebar collapsed={collapsed} mobileOpen={mobileOpen} closeMobile={() => setMobileOpen(false)} />
      {mobileOpen && <button className="sidebar-scrim" aria-label="Đóng thanh điều hướng" onClick={() => setMobileOpen(false)} />}
      <div className="workspace-main">
        <WorkspaceHeader collapsed={collapsed} toggleSidebar={() => setCollapsed((value) => !value)} openMobile={() => setMobileOpen(true)} />
        <main className="workspace-content">{children}</main>
      </div>
    </div>
  );
}
