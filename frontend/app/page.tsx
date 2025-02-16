"use client";

import { useEffect, useState } from "react";

import { AppShell } from "@/components/AppShell";
import { AuthPanel } from "@/components/AuthPanel";
import type { AuthPayload } from "@/types/api";

export default function HomePage() {
  const [auth, setAuth] = useState<AuthPayload | null>(null);

  useEffect(() => {
    const saved = localStorage.getItem("employee-analytics-auth");
    if (saved) {
      setAuth(JSON.parse(saved));
    }
  }, []);

  function handleAuth(payload: AuthPayload) {
    localStorage.setItem("employee-analytics-auth", JSON.stringify(payload));
    setAuth(payload);
  }

  function logout() {
    localStorage.removeItem("employee-analytics-auth");
    setAuth(null);
  }

  return auth ? <AppShell auth={auth} onLogout={logout} /> : <AuthPanel onAuthenticated={handleAuth} />;
}
