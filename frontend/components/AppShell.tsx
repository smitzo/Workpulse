"use client";

import { BarChart3, LogOut, Moon, RefreshCw, Sun } from "lucide-react";
import { useEffect, useState } from "react";

import { DashboardView } from "@/components/DashboardView";
import { ReportsView } from "@/components/ReportsView";
import { getDashboard, getInsights, getOptions } from "@/lib/api";
import type { AuthPayload, Dashboard, Filters, InsightsPayload, OptionsPayload } from "@/types/api";

type AppShellProps = {
  auth: AuthPayload;
  onLogout: () => void;
};

export function AppShell({ auth, onLogout }: AppShellProps) {
  const [theme, setTheme] = useState<"light" | "dark">("light");
  const [active, setActive] = useState("dashboard");
  const [filters, setFilters] = useState<Filters>({});
  const [options, setOptions] = useState<OptionsPayload | null>(null);
  const [dashboard, setDashboard] = useState<Dashboard | null>(null);
  const [insights, setInsights] = useState<InsightsPayload | null>(null);
  const [message, setMessage] = useState("");

  useEffect(() => {
    document.documentElement.dataset.theme = theme;
  }, [theme]);

  useEffect(() => {
    refresh();
    // eslint-disable-next-line react-hooks/exhaustive-deps
  }, []);

  async function refresh(nextFilters = filters) {
    setMessage("Loading analytics...");
    try {
      const [optionsPayload, dashboardPayload, insightPayload] = await Promise.all([
        getOptions(auth.token),
        getDashboard(auth.token, nextFilters),
        getInsights(auth.token, nextFilters)
      ]);
      setOptions(optionsPayload);
      setDashboard(dashboardPayload);
      setInsights(insightPayload);
      setMessage("");
    } catch (error) {
      setMessage(error instanceof Error ? error.message : "Could not load analytics.");
    }
  }

  function updateFilter(key: keyof Filters, value: string) {
    const next = { ...filters, [key]: value || undefined };
    setFilters(next);
  }

  function applyFilters() {
    refresh(filters);
  }

  function clearFilters() {
    const next = {};
    setFilters(next);
    refresh(next);
  }

  return (
    <main className="app-shell">
      <aside className="sidebar">
        <div className="sidebar-brand">
          <BarChart3 />
          <span>Employee Analytics</span>
        </div>
        <nav>
          {[
            ["dashboard", "Dashboard"],
            ["reports", "Reports"],
            ["employees", "Employees"],
            ["logs", "Timesheets"],
            ["attendance", "Attendance"]
          ].map(([key, label]) => (
            <button key={key} className={active === key ? "active" : ""} type="button" onClick={() => setActive(key)}>
              {label}
            </button>
          ))}
        </nav>
      </aside>

      <section className="workspace">
        <header className="topbar">
          <div>
            <span className="eyebrow">Welcome back</span>
            <h1>{auth.user.name}</h1>
          </div>
          <div className="topbar-actions">
            <button className="secondary-btn" type="button" onClick={() => refresh()}>
              <RefreshCw size={16} />
              Refresh
            </button>
            <button className="icon-btn" type="button" onClick={() => setTheme(theme === "light" ? "dark" : "light")} aria-label="Toggle theme">
              {theme === "light" ? <Moon size={18} /> : <Sun size={18} />}
            </button>
            <button className="secondary-btn" type="button" onClick={onLogout}>
              <LogOut size={16} />
              Sign out
            </button>
          </div>
        </header>

        <section className="filters-panel">
          <label>
            From
            <input type="date" value={filters.date_from || ""} onChange={(event) => updateFilter("date_from", event.target.value)} />
          </label>
          <label>
            To
            <input type="date" value={filters.date_to || ""} onChange={(event) => updateFilter("date_to", event.target.value)} />
          </label>
          {auth.user.role === "admin" && (
            <>
              <label>
                Department
                <select value={filters.department || "All"} onChange={(event) => updateFilter("department", event.target.value)}>
                  {(options?.departments || ["All"]).map((item) => (
                    <option key={item}>{item}</option>
                  ))}
                </select>
              </label>
              <label>
                Employee
                <select value={filters.employee_id || "All"} onChange={(event) => updateFilter("employee_id", event.target.value)}>
                  <option>All</option>
                  {(options?.employees || []).map((employee) => (
                    <option key={employee.id} value={employee.id}>
                      {employee.label}
                    </option>
                  ))}
                </select>
              </label>
            </>
          )}
          <label>
            Task
            <select value={filters.task_type || "All"} onChange={(event) => updateFilter("task_type", event.target.value)}>
              {(options?.task_types || ["All"]).map((item) => (
                <option key={item}>{item}</option>
              ))}
            </select>
          </label>
          <label>
            Project
            <select value={filters.project || "All"} onChange={(event) => updateFilter("project", event.target.value)}>
              {(options?.projects || ["All"]).map((item) => (
                <option key={item}>{item}</option>
              ))}
            </select>
          </label>
          <button className="primary-btn" type="button" onClick={applyFilters}>
            Apply
          </button>
          <button className="secondary-btn" type="button" onClick={clearFilters}>
            Clear
          </button>
        </section>

        {message && <p className="status-line">{message}</p>}

        {!dashboard ? (
          <section className="empty-state">
            <h2>Loading dashboard</h2>
            <p>Fetching analytics from the Django API.</p>
          </section>
        ) : active === "reports" ? (
          <ReportsView dashboard={dashboard} filters={filters} insights={insights} token={auth.token} setMessage={setMessage} />
        ) : active === "dashboard" ? (
          <DashboardView dashboard={dashboard} />
        ) : (
          <section className="empty-state">
            <h2>{active[0].toUpperCase() + active.slice(1)} module</h2>
            <p>This management workspace is added in the next commit.</p>
          </section>
        )}
      </section>
    </main>
  );
}
