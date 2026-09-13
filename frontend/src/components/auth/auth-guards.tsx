"use client";

import { useEffect } from "react";
import { useRouter } from "next/navigation";
import { useAuth } from "./auth-provider";

export function ProtectedRoute({ children }: Readonly<{ children: React.ReactNode }>) {
  const { isAuthenticated, isLoading } = useAuth();
  const router = useRouter();
  useEffect(() => {
    if (!isLoading && !isAuthenticated) router.replace("/login");
  }, [isAuthenticated, isLoading, router]);
  if (isLoading || !isAuthenticated) return <AuthLoading />;
  return children;
}

export function PublicOnlyRoute({ children }: Readonly<{ children: React.ReactNode }>) {
  const { isAuthenticated, isLoading } = useAuth();
  const router = useRouter();
  useEffect(() => {
    if (!isLoading && isAuthenticated) router.replace("/app/chat");
  }, [isAuthenticated, isLoading, router]);
  if (isLoading || isAuthenticated) return <AuthLoading />;
  return children;
}

function AuthLoading() {
  return <main className="auth-loading" role="status" aria-live="polite"><span aria-hidden="true" /><p>Đang kiểm tra phiên đăng nhập…</p></main>;
}
