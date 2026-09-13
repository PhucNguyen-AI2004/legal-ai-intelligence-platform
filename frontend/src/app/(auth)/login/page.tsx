import Link from "next/link";
import { AuthForm } from "@/components/auth/auth-form";

export default function LoginPage() {
  return (
    <>
      <header className="auth-heading">
        <h1 id="auth-heading">Đăng nhập vào Legal AI</h1>
        <p>Truy cập không gian làm việc pháp lý của bạn.</p>
      </header>
      <AuthForm mode="login" />
      <p className="auth-switch">Chưa có tài khoản? <Link href="/register">Đăng ký</Link></p>
    </>
  );
}
