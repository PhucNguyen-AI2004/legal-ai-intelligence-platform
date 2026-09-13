import { Brand } from "@/components/navigation/brand";

export default function AuthLayout({ children }: Readonly<{ children: React.ReactNode }>) {
  return (
    <main className="auth-layout">
      <section className="auth-panel" aria-labelledby="auth-heading">
        <Brand />
        {children}
      </section>
    </main>
  );
}
