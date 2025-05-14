"use client";

import { ActivitySquare, BriefcaseBusiness, Info, LogIn, ShieldCheck, UserPlus, UsersRound } from "lucide-react";
import type { FormEvent } from "react";
import { useState } from "react";

import { demoLogin, login, signup } from "@/lib/api";
import type { AuthPayload } from "@/types/api";

type AuthPanelProps = {
  onAuthenticated: (payload: AuthPayload) => void;
};

type PreviewRole = "employee" | "manager" | "admin";

function localDate() {
  const date = new Date();
  date.setMinutes(date.getMinutes() - date.getTimezoneOffset());
  return date.toISOString().slice(0, 10);
}

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

  async function enterWorkspace(role: PreviewRole) {
    setLoading(true);
    setMessage("");
    try {
      onAuthenticated(await demoLogin(role));
    } catch (error) {
      setMessage(error instanceof Error ? error.message : "Could not open workspace.");
    } finally {
      setLoading(false);
    }
  }

  return (
    <main className="auth-screen">
      <section className="auth-hero" aria-label="WorkPulse overview">
        <div className="brand-mark">
          <ActivitySquare size={30} />
        </div>
        <h1>WorkPulse</h1>
        <p>
          A modern work hub for attendance, timesheets, projects, team visibility, and clean operational reports.
        </p>
      </section>

      <section className="auth-card">
        <div className="role-entry">
          <div className="role-entry-heading">
            <span>Open demo workspace as</span>
            <details className="demo-info">
              <summary aria-label="About demo data" title="About demo data"><Info size={17} /></summary>
              <div>
                This project is deployed on Render&apos;s free tier, so the backend may go to sleep after a period of inactivity.
                These browser-based demo workspaces let you sample the UI and CRUD functionality immediately without backend or database access.
              </div>
            </details>
          </div>
          <div className="role-entry-grid">
            <button disabled={loading} type="button" onClick={() => enterWorkspace("employee")}>
              <BriefcaseBusiness size={18} />
              Demo Employee
            </button>
            <button disabled={loading} type="button" onClick={() => enterWorkspace("manager")}>
              <UsersRound size={18} />
              Demo Manager
            </button>
            <button disabled={loading} type="button" onClick={() => enterWorkspace("admin")}>
              <ShieldCheck size={18} />
              Demo Admin
            </button>
          </div>
          <p>Instant access with editable sample data stored in your browser. No credentials required.</p>
        </div>

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
                  <input name="hire_date" type="date" defaultValue={localDate()} required />
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

        {message && <p className="form-error">{message}</p>}
      </section>
    </main>
  );
}
