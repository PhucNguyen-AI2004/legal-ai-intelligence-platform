import Link from "next/link";
import type { LucideIcon } from "lucide-react";

export function SidebarItem({ href, icon: Icon, label, active, collapsed }: {
  href: string;
  icon: LucideIcon;
  label: string;
  active?: boolean;
  collapsed: boolean;
}) {
  return (
    <Link className={`sidebar-item${active ? " sidebar-item-active" : ""}`} href={href} title={collapsed ? label : undefined} aria-current={active ? "page" : undefined}>
      <Icon size={19} aria-hidden="true" />
      {!collapsed && <span>{label}</span>}
    </Link>
  );
}
