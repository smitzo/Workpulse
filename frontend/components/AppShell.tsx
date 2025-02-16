"use client";

import { BarChart3, LogOut, Moon, Sun } from "lucide-react";
import { useEffect, useState } from "react";

import type { AuthPayload } from "@/types/api";

type AppShellProps = {
  auth: AuthPayload;
  onLogout: () => void;
};

export function AppShell({ auth, onLogout }: AppShellProps) {
  const [theme, setTheme] = useState<"light" | "dark">("light");

  useEffect(() => {
    document.documentElement.dataset.theme = theme;
  }, [theme]);

  return (
    <main className="app-shell">
      <aside className="sidebar">
        <div className="sidebar-brand">
          <BarChart3 />
          <span>Employee Analytics</span>
        </div>
        <nav>
          <button className="active">Dashboard</button>
          <button>Reports</button>
          <button>Employees</button>
          <button>Timesheets</button>
          <button>Attendance</button>
        </nav>
      </aside>

      <section className="workspace">
        <header className="topbar">
          <div>
            <span className="eyebrow">Welcome back</span>
            <h1>{auth.user.name}</h1>
          </div>
          <div className="topbar-actions">
            <button className="icon-btn" type="button" onClick={() => setTheme(theme === "light" ? "dark" : "light")} aria-label="Toggle theme">
              {theme === "light" ? <Moon size={18} /> : <Sun size={18} />}
            </button>
            <button className="secondary-btn" type="button" onClick={onLogout}>
              <LogOut size={16} />
              Sign out
            </button>
          </div>
        </header>

        <section className="empty-state">
          <h2>Dashboard is connected next</h2>
          <p>The authenticated shell is ready. The next commit adds live analytics, charts, reports, and tables.</p>
        </section>
      </section>
    </main>
  );
}
