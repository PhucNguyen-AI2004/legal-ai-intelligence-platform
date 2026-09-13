"use client";

import { createContext, useCallback, useContext, useEffect, useMemo, useState } from "react";
import { useRouter } from "next/navigation";
import { setUnauthorizedHandler } from "@/lib/api/client";
import { currentUserRequest, loginRequest, registerRequest } from "@/lib/auth/auth-api";
import { clearAccessToken, getAccessToken, setAccessToken } from "@/lib/auth/token-storage";
import type { AuthState, RegisterRequest, User } from "@/lib/auth/types";

interface AuthContextValue extends AuthState {
  login(email: string, password: string): Promise<void>;
  register(data: RegisterRequest): Promise<void>;
  logout(): void;
  refreshCurrentUser(): Promise<void>;
}

const AuthContext = createContext<AuthContextValue | null>(null);

export function AuthProvider({ children }: Readonly<{ children: React.ReactNode }>) {
  const router = useRouter();
  const [user, setUser] = useState<User | null>(null);
  const [isLoading, setIsLoading] = useState(true);

  const expireSession = useCallback(() => {
    clearAccessToken();
    setUser(null);
    setIsLoading(false);
    router.replace("/login");
  }, [router]);

  const refreshCurrentUser = useCallback(async () => {
    if (!getAccessToken()) {
      setUser(null);
      setIsLoading(false);
      return;
    }
    try {
      setUser(await currentUserRequest());
    } catch {
      clearAccessToken();
      setUser(null);
    } finally {
      setIsLoading(false);
    }
  }, []);

  useEffect(() => {
    setUnauthorizedHandler(expireSession);
    queueMicrotask(() => void refreshCurrentUser());
    return () => setUnauthorizedHandler(null);
  }, [expireSession, refreshCurrentUser]);

  const login = useCallback(async (email: string, password: string) => {
    const response = await loginRequest({ email, password });
    setAccessToken(response.access_token);
    try {
      const currentUser = await currentUserRequest();
      setUser(currentUser);
      setIsLoading(false);
    } catch (error) {
      clearAccessToken();
      setUser(null);
      throw error;
    }
  }, []);

  const register = useCallback(async (data: RegisterRequest) => {
    await registerRequest(data);
  }, []);

  const logout = useCallback(() => {
    clearAccessToken();
    setUser(null);
    setIsLoading(false);
    router.replace("/login");
  }, [router]);

  const value = useMemo<AuthContextValue>(() => ({
    user,
    isAuthenticated: user !== null,
    isLoading,
    login,
    register,
    logout,
    refreshCurrentUser,
  }), [isLoading, login, logout, refreshCurrentUser, register, user]);

  return <AuthContext.Provider value={value}>{children}</AuthContext.Provider>;
}

export function useAuth(): AuthContextValue {
  const context = useContext(AuthContext);
  if (!context) throw new Error("useAuth must be used inside AuthProvider");
  return context;
}
