"use client";

import { BarChart3, LogIn, Sparkles, UserPlus } from "lucide-react";
import type { FormEvent } from "react";
import { useState } from "react";

import { demoLogin, login, signup } from "@/lib/api";
import type { AuthPayload } from "@/types/api";

type AuthPanelProps = {
  onAuthenticated: (payload: AuthPayload) => void;
};

export function AuthPanel({ onAuthenticated }: AuthPanelProps) {
  const [mode, setMode] = useState<"login" | "signup">("login");
  const [message, setMessage] = useState("");
  const [loading, setLoading] = useState(false);

  async function submit(event: FormEvent<HTMLFormElement>) {
    event.preventDefault();
    const formData = new FormData(event.currentTarget);
    setLoading(true);
    setMessage("");
    try {
      const payload =
        mode === "login"
          ? await login(String(formData.get("username") || ""), String(formData.get("password") || ""))
          : await signup(Object.fromEntries(formData.entries()) as Record<string, string>);
      onAuthenticated(payload);
    } catch (error) {
      setMessage(error instanceof Error ? error.message : "Something went wrong.");
    } finally {
      setLoading(false);
    }
  }

  async function enterDemo() {
    setLoading(true);
    setMessage("");
    try {
      onAuthenticated(await demoLogin());
    } catch (error) {
      setMessage(error instanceof Error ? error.message : "Could not enter demo mode.");
    } finally {
      setLoading(false);
    }
  }

  return (
    <main className="auth-screen">
      <section className="auth-hero" aria-label="Employee analytics overview">
        <div className="brand-mark">
          <BarChart3 size={28} />
        </div>
        <h1>Employee Analytics</h1>
        <p>
          Monitor performance, attendance, overtime, workload balance, and executive reports from one web dashboard.
        </p>
      </section>

      <section className="auth-card">
        <div className="auth-tabs" role="tablist" aria-label="Authentication mode">
          <button className={mode === "login" ? "active" : ""} onClick={() => setMode("login")} type="button">
            <LogIn size={16} />
            Login
          </button>
          <button className={mode === "signup" ? "active" : ""} onClick={() => setMode("signup")} type="button">
            <UserPlus size={16} />
            Sign up
          </button>
        </div>

        <form onSubmit={submit} className="stack">
          <label>
            Username
            <input name="username" autoComplete="username" required />
          </label>
          <label>
            Password
            <input name="password" type="password" autoComplete={mode === "login" ? "current-password" : "new-password"} required />
          </label>

          {mode === "signup" && (
            <>
              <label>
                Full name
                <input name="name" autoComplete="name" required />
              </label>
              <label>
                Email
                <input name="email" type="email" autoComplete="email" />
              </label>
              <div className="two-col">
                <label>
                  Department
                  <input name="department" defaultValue="General" required />
                </label>
                <label>
                  Role
                  <input name="role" defaultValue="Employee" required />
                </label>
              </div>
              <div className="two-col">
                <label>
                  Location
                  <input name="location" defaultValue="Remote" required />
                </label>
                <label>
                  Hire date
                  <input name="hire_date" type="date" required />
                </label>
              </div>
              <label>
                Manager
                <input name="manager" defaultValue="Unassigned" required />
              </label>
            </>
          )}

          <button className="primary-btn" disabled={loading} type="submit">
            {mode === "login" ? "Sign in" : "Create account"}
          </button>
        </form>

        <div className="demo-entry">
          <button className="demo-btn" disabled={loading} type="button" onClick={enterDemo}>
            <Sparkles size={18} />
            Explore demo dashboard
          </button>
          <p>
            No setup needed. This opens a seeded admin demo with sample employees, attendance, timesheets, charts, and reports.
          </p>
        </div>

        {message && <p className="form-error">{message}</p>}
      </section>
    </main>
  );
}
