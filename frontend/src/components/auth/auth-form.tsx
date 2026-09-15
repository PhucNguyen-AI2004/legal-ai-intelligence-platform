"use client";

import { useState, type FormEvent } from "react";
import { useRouter } from "next/navigation";
import { Button } from "@/components/ui/button";
import { Input } from "@/components/ui/input";
import { ApiError } from "@/lib/api/client";
import { useAuth } from "./auth-provider";

export function AuthForm({ mode, registered = false }: { mode: "login" | "register"; registered?: boolean }) {
  const router = useRouter();
  const { login, register } = useAuth();
  const [fullName, setFullName] = useState("");
  const [email, setEmail] = useState("");
  const [password, setPassword] = useState("");
  const [error, setError] = useState<string | null>(null);
  const [isSubmitting, setIsSubmitting] = useState(false);

  async function handleSubmit(event: FormEvent<HTMLFormElement>) {
    event.preventDefault();
    if (isSubmitting) return;
    setError(null);
    const validationError = validateForm(mode, fullName, email, password);
    if (validationError) {
      setError(validationError);
      return;
    }
    setIsSubmitting(true);
    try {
      if (mode === "login") {
        await login(email.trim(), password);
        router.replace("/app/chat");
      } else {
        await register({ full_name: fullName.trim(), email: email.trim(), password });
        router.replace("/login?registered=1");
      }
    } catch (caught) {
      setError(toUserMessage(caught, mode));
    } finally {
      setIsSubmitting(false);
    }
  }

  return (
    <form className="auth-form" onSubmit={handleSubmit} noValidate>
      {registered && mode === "login" && <p className="form-alert form-success" role="status">Tạo tài khoản thành công. Bạn có thể đăng nhập.</p>}
      {mode === "register" && <Input label="Họ và tên" name="fullName" autoComplete="name" value={fullName} onChange={(event) => setFullName(event.target.value)} disabled={isSubmitting} aria-describedby="auth-form-status" />}
      <Input label="Email" name="email" type="email" autoComplete="email" value={email} onChange={(event) => setEmail(event.target.value)} disabled={isSubmitting} placeholder="ban@example.com" aria-describedby="auth-form-status" />
      <Input label="Mật khẩu" name="password" type="password" autoComplete={mode === "login" ? "current-password" : "new-password"} value={password} onChange={(event) => setPassword(event.target.value)} disabled={isSubmitting} aria-describedby="auth-form-status" />
      {mode === "register" && <p className="field-hint">Mật khẩu cần từ 12 đến 128 ký tự.</p>}
      <p id="auth-form-status" className={`form-alert form-error${error ? "" : " form-alert-empty"}`} role={error ? "alert" : "status"} aria-live="polite">{error ?? ""}</p>
      <Button type="submit" className="auth-submit" disabled={isSubmitting}>
        {isSubmitting ? (mode === "login" ? "Đang đăng nhập..." : "Đang tạo tài khoản...") : (mode === "login" ? "Đăng nhập" : "Đăng ký")}
      </Button>
    </form>
  );
}

function validateForm(mode: "login" | "register", fullName: string, email: string, password: string): string | null {
  if (!/^\S+@\S+\.\S+$/.test(email.trim()) || password.length === 0) return "Vui lòng nhập email và mật khẩu hợp lệ.";
  if (password.length > 128) return "Mật khẩu không được vượt quá 128 ký tự.";
  if (mode === "register") {
    if (!fullName.trim() || fullName.trim().length > 200) return "Họ và tên phải có từ 1 đến 200 ký tự.";
    if (password.length < 12 || !password.trim()) return "Mật khẩu phải có từ 12 đến 128 ký tự và không chỉ chứa khoảng trắng.";
  }
  return null;
}

function toUserMessage(error: unknown, mode: "login" | "register"): string {
  if (error instanceof ApiError) {
    if (mode === "login" && error.status === 401) return "Email hoặc mật khẩu không chính xác.";
    if (mode === "register" && error.status === 409) return "Email này đã được sử dụng.";
    if (error.status === 422) return mode === "login" ? "Thông tin đăng nhập chưa hợp lệ." : "Thông tin đăng ký chưa hợp lệ.";
    if (error.status >= 500) return "Máy chủ đang gặp sự cố. Vui lòng thử lại.";
    return "Đã xảy ra lỗi. Vui lòng thử lại.";
  }
  if (error instanceof TypeError) return "Không thể kết nối đến máy chủ. Vui lòng thử lại.";
  return "Đã xảy ra lỗi. Vui lòng thử lại.";
}
