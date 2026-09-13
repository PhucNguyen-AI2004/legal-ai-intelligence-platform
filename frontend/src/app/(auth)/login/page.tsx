import Link from "next/link";
import { AuthForm } from "@/components/auth/auth-form";

export default async function LoginPage({ searchParams }: { searchParams: Promise<{ registered?: string }> }) {
  const { registered } = await searchParams;
  return (
    <>
      <header className="auth-heading">
        <h1 id="auth-heading">Đăng nhập vào Legal AI</h1>
        <p>Truy cập không gian làm việc pháp lý của bạn.</p>
      </header>
      <AuthForm mode="login" registered={registered === "1"} />
      <p className="auth-switch">Chưa có tài khoản? <Link href="/register">Đăng ký</Link></p>
    </>
  );
}
