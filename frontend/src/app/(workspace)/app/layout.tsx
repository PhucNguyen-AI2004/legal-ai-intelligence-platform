import { WorkspaceShell } from "@/components/layout/workspace-shell";
import { ProtectedRoute } from "@/components/auth/auth-guards";

export default function AppLayout({ children }: Readonly<{ children: React.ReactNode }>) {
  return <ProtectedRoute><WorkspaceShell>{children}</WorkspaceShell></ProtectedRoute>;
}
