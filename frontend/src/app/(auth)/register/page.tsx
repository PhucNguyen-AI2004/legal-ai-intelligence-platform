import Link from "next/link";
import { AuthForm } from "@/components/auth/auth-form";

export default function RegisterPage() {
  return (
    <>
      <header className="auth-heading">
        <h1 id="auth-heading">Tạo tài khoản Legal AI</h1>
        <p>Bắt đầu xây dựng không gian tra cứu tài liệu của bạn.</p>
      </header>
      <AuthForm mode="register" />
      <p className="auth-switch">Đã có tài khoản? <Link href="/login">Đăng nhập</Link></p>
    </>
  );
}
