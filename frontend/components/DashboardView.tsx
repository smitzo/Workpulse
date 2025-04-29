"use client";

import {
  Bar,
  BarChart,
  CartesianGrid,
  Cell,
  Line,
  LineChart,
  Pie,
  PieChart,
  ResponsiveContainer,
  Tooltip,
  XAxis,
  YAxis
} from "recharts";

import type { Dashboard } from "@/types/api";

const palette = ["#2563eb", "#0f9f6e", "#f97316", "#7c3aed", "#dc2626", "#0891b2", "#b7791f", "#4f46e5"];

type DashboardViewProps = {
  dashboard: Dashboard;
  role?: "admin" | "manager" | "employee";
};

function tupleData(rows: [string, number][]) {
  return rows.map(([name, value]) => ({ name, value }));
}

function Kpi({ label, value, accent }: { label: string; value: string | number; accent?: string }) {
  return (
    <article className="kpi-card">
      <span>{label}</span>
      <strong style={{ color: accent }}>{value}</strong>
    </article>
  );
}

export function DashboardView({ dashboard, role = "admin" }: DashboardViewProps) {
  const summary = dashboard.summary;
  return (
    <section className="dashboard-grid">
      <div className="kpi-grid">
        <Kpi label="Hours" value={summary.total_hours} />
        <Kpi label="Productivity" value={`${summary.avg_productivity}%`} accent="var(--primary)" />
        <Kpi label="Attendance" value={`${summary.attendance_rate}%`} accent="var(--green)" />
        <Kpi label="Overtime" value={summary.overtime_hours} accent="var(--amber)" />
      </div>

      <div className="metric-strip">
        {role === "admin" && <span><strong>{summary.total_employees}</strong> employees</span>}
        {role === "admin" && <span><strong>{summary.active_employees}</strong> active</span>}
        <span><strong>{summary.work_logs}</strong> work logs</span>
        <span><strong>{summary.absence_count}</strong> absences</span>
        <span><strong>{summary.late_minutes}</strong> late minutes</span>
      </div>

      <article className="panel chart-panel wide">
        <header>
          <h2>Hours Trend</h2>
        </header>
        <ResponsiveContainer width="100%" height={310}>
          <LineChart data={tupleData(dashboard.hours_trend)}>
            <CartesianGrid strokeDasharray="3 3" stroke="var(--line)" />
            <XAxis dataKey="name" tick={{ fill: "var(--muted)", fontSize: 12 }} minTickGap={24} />
            <YAxis tick={{ fill: "var(--muted)", fontSize: 12 }} />
            <Tooltip />
            <Line type="monotone" dataKey="value" stroke="#2563eb" strokeWidth={3} dot={false} />
          </LineChart>
        </ResponsiveContainer>
      </article>

      <article className="panel chart-panel">
        <header>
          <h2>Hours by Department</h2>
        </header>
        <ResponsiveContainer width="100%" height={300}>
          <BarChart data={tupleData(dashboard.hours_by_department)}>
            <CartesianGrid strokeDasharray="3 3" stroke="var(--line)" />
            <XAxis dataKey="name" tick={{ fill: "var(--muted)", fontSize: 12 }} />
            <YAxis tick={{ fill: "var(--muted)", fontSize: 12 }} />
            <Tooltip />
            <Bar dataKey="value" radius={[6, 6, 0, 0]}>
              {dashboard.hours_by_department.map((_, index) => (
                <Cell key={index} fill={palette[index % palette.length]} />
              ))}
            </Bar>
          </BarChart>
        </ResponsiveContainer>
      </article>

      <article className="panel chart-panel">
        <header>
          <h2>Attendance Mix</h2>
        </header>
        <ResponsiveContainer width="100%" height={300}>
          <PieChart>
            <Pie data={tupleData(dashboard.attendance_breakdown)} dataKey="value" nameKey="name" innerRadius={64} outerRadius={104} paddingAngle={3}>
              {dashboard.attendance_breakdown.map((_, index) => (
                <Cell key={index} fill={palette[index % palette.length]} />
              ))}
            </Pie>
            <Tooltip />
          </PieChart>
        </ResponsiveContainer>
      </article>

      <article className="panel table-panel wide">
        <header>
          <h2>Employee Performance</h2>
        </header>
        <div className="table-wrap">
          <table>
            <thead>
              <tr>
                <th>Employee</th>
                <th>Department</th>
                <th>Role</th>
                <th>Hours</th>
                <th>Productivity</th>
                <th>Overtime</th>
              </tr>
            </thead>
            <tbody>
              {dashboard.employee_performance.slice(0, 12).map((row) => (
                <tr key={row.employee_id}>
                  <td>{row.name}</td>
                  <td>{row.department}</td>
                  <td>{row.role}</td>
                  <td>{row.total_hours}</td>
                  <td>{row.avg_productivity}%</td>
                  <td>{row.overtime_hours}</td>
                </tr>
              ))}
            </tbody>
          </table>
        </div>
      </article>
    </section>
  );
}
