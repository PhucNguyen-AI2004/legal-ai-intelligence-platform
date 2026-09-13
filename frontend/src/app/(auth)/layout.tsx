import { Brand } from "@/components/navigation/brand";
import { PublicOnlyRoute } from "@/components/auth/auth-guards";

export default function AuthLayout({ children }: Readonly<{ children: React.ReactNode }>) {
  return (
    <PublicOnlyRoute><main className="auth-layout"><section className="auth-panel" aria-labelledby="auth-heading"><Brand />{children}</section></main></PublicOnlyRoute>
  );
}
