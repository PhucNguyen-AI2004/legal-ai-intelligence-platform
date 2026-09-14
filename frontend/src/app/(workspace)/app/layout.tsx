import { WorkspaceShell } from "@/components/layout/workspace-shell";
import { ProtectedRoute } from "@/components/auth/auth-guards";
import { ConversationProvider } from "@/components/conversations/conversation-provider";

export default function AppLayout({ children }: Readonly<{ children: React.ReactNode }>) {
  return <ProtectedRoute><ConversationProvider><WorkspaceShell>{children}</WorkspaceShell></ConversationProvider></ProtectedRoute>;
}
