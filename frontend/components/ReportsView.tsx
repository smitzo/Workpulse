"use client";

import { Download } from "lucide-react";

import { getReportHtml } from "@/lib/api";
import type { Dashboard, Filters, InsightsPayload } from "@/types/api";

type ReportsViewProps = {
  dashboard: Dashboard;
  filters: Filters;
  insights: InsightsPayload | null;
  token: string;
  setMessage: (message: string) => void;
};

export function ReportsView({ dashboard, filters, insights, token, setMessage }: ReportsViewProps) {
  async function exportReport() {
    try {
      const html = await getReportHtml(token, filters);
      const url = URL.createObjectURL(new Blob([html], { type: "text/html" }));
      window.open(url, "_blank", "noopener,noreferrer");
      setMessage("Report opened in a new tab.");
    } catch (error) {
      setMessage(error instanceof Error ? error.message : "Could not export report.");
    }
  }

  return (
    <section className="reports-grid">
      <article className="panel report-summary">
        <header>
          <h2>Executive Summary</h2>
          <button className="secondary-btn" type="button" onClick={exportReport}>
            <Download size={16} />
            HTML report
          </button>
        </header>
        <p>{insights?.summary || "Loading report summary..."}</p>
      </article>

      <article className="panel">
        <header>
          <h2>Key Insights</h2>
        </header>
        <div className="insight-list">
          {(insights?.insights || []).map((insight) => (
            <div key={insight.title} className="insight-item">
              <strong>{insight.title}</strong>
              <span>{insight.detail}</span>
            </div>
          ))}
        </div>
      </article>

      <article className="panel table-panel wide">
        <header>
          <h2>Actual vs Ideal Task Hours</h2>
        </header>
        <div className="table-wrap">
          <table>
            <thead>
              <tr>
                <th>Task</th>
                <th>Actual</th>
                <th>Ideal</th>
                <th>Variance</th>
              </tr>
            </thead>
            <tbody>
              {dashboard.ideal_vs_actual.map(([task, actual, ideal, variance]) => (
                <tr key={task}>
                  <td>{task}</td>
                  <td>{actual}</td>
                  <td>{ideal}</td>
                  <td>{variance}</td>
                </tr>
              ))}
            </tbody>
          </table>
        </div>
      </article>
    </section>
  );
}
