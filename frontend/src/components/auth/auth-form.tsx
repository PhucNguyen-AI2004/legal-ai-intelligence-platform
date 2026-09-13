import { Button } from "@/components/ui/button";
import { Input } from "@/components/ui/input";

export function AuthForm({ mode }: { mode: "login" | "register" }) {
  return (
    <form className="auth-form">
      {mode === "register" && <Input label="Họ và tên" name="fullName" autoComplete="name" placeholder="Nguyễn An" />}
      <Input label="Email" name="email" type="email" autoComplete="email" placeholder="ban@example.com" />
      <Input label="Mật khẩu" name="password" type="password" autoComplete={mode === "login" ? "current-password" : "new-password"} placeholder="Nhập mật khẩu" />
      <Button type="button" className="auth-submit">{mode === "login" ? "Đăng nhập" : "Đăng ký"}</Button>
      <p className="form-note">Biểu mẫu giao diện — kết nối xác thực sẽ được bổ sung trong Phase 8B.</p>
    </form>
  );
}
