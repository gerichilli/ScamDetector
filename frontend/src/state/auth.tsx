import { createContext, useContext, useEffect, useMemo, useState } from "react";
import type React from "react";
import { api } from "../api/client";
import type { User } from "../api/types";

type AuthContextValue = {
  user: User | null;
  loading: boolean;
  login: (email: string, password: string) => Promise<void>;
  register: (email: string, password: string, fullName?: string) => Promise<void>;
  logout: () => void;
};

const AuthContext = createContext<AuthContextValue | null>(null);

export function AuthProvider({ children }: { children: React.ReactNode }) {
  const [user, setUser] = useState<User | null>(null);
  const [loading, setLoading] = useState(true);

  useEffect(() => {
    const token = localStorage.getItem("access_token");
    if (!token) {
      setLoading(false);
      return;
    }
    api.get<User>("/auth/me")
      .then((response) => setUser(response.data))
      .catch(() => localStorage.removeItem("access_token"))
      .finally(() => setLoading(false));
  }, []);

  async function login(email: string, password: string) {
    const response = await api.post("/auth/login", { email, password });
    localStorage.setItem("access_token", response.data.access_token);
    setUser(response.data.user);
  }

  const value = useMemo<AuthContextValue>(() => ({
    user,
    loading,
    login,
    async register(email, password, fullName) {
      await api.post("/auth/register", { email, password, full_name: fullName || null });
      await login(email, password);
    },
    logout() {
      localStorage.removeItem("access_token");
      setUser(null);
    },
  }), [user, loading]);

  return <AuthContext.Provider value={value}>{children}</AuthContext.Provider>;
}

export function useAuth() {
  const context = useContext(AuthContext);
  if (!context) throw new Error("useAuth must be used within AuthProvider");
  return context;
}
