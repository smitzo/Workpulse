from __future__ import annotations

from html import escape

from analytics.services import AnalyticsService, Filters


def html_report(filters: Filters) -> str:
    service = AnalyticsService()
    data = service.dashboard(filters)
    insights = service.insights(filters)
    summary = data["summary"]

    def rows(items: list[tuple[str, float]], suffix: str = "") -> str:
        return "\n".join(
            f"<tr><td>{escape(str(label))}</td><td>{value:g}{suffix}</td></tr>"
            for label, value in items
        ) or "<tr><td colspan='2'>No data</td></tr>"

    performance = "\n".join(
        "<tr>"
        f"<td>{escape(row['employee_id'])}</td>"
        f"<td>{escape(row['name'])}</td>"
        f"<td>{escape(row['department'])}</td>"
        f"<td>{row['total_hours']}</td>"
        f"<td>{row['avg_productivity']}%</td>"
        f"<td>{row['overtime_hours']}</td>"
        "</tr>"
        for row in data["employee_performance"][:20]
    )
    insight_html = "\n".join(
        f"<li><strong>{escape(item.title)}:</strong> {escape(item.detail)}</li>"
        for item in insights
    )

    return f"""<!doctype html>
<html lang="en">
<head>
  <meta charset="utf-8">
  <title>Employee Analytics Report</title>
  <style>
    body {{ font-family: Inter, Arial, sans-serif; margin: 32px; color: #111827; }}
    h1 {{ margin-bottom: 4px; }}
    .muted {{ color: #64748b; }}
    .kpis {{ display: grid; grid-template-columns: repeat(3, 1fr); gap: 12px; margin: 24px 0; }}
    .kpi {{ border: 1px solid #cbd5e1; padding: 14px; border-radius: 8px; }}
    .kpi span {{ color: #64748b; font-size: 12px; font-weight: 700; }}
    .kpi strong {{ display: block; font-size: 24px; margin-top: 6px; }}
    section {{ margin-top: 28px; }}
    table {{ border-collapse: collapse; width: 100%; margin-top: 10px; }}
    th, td {{ border: 1px solid #cbd5e1; padding: 8px; text-align: left; }}
    th {{ background: #f8fafc; }}
    .grid {{ display: grid; grid-template-columns: 1fr 1fr; gap: 24px; }}
  </style>
</head>
<body>
  <h1>Employee Data Analytics Report</h1>
  <p class="muted">Generated from the Django analytics API.</p>
  <p>{escape(service.executive_summary(filters))}</p>
  <div class="kpis">
    <div class="kpi"><span>Employees</span><strong>{summary['total_employees']}</strong></div>
    <div class="kpi"><span>Total Hours</span><strong>{summary['total_hours']}</strong></div>
    <div class="kpi"><span>Avg Productivity</span><strong>{summary['avg_productivity']}%</strong></div>
    <div class="kpi"><span>Attendance</span><strong>{summary['attendance_rate']}%</strong></div>
    <div class="kpi"><span>Overtime</span><strong>{summary['overtime_hours']}</strong></div>
    <div class="kpi"><span>Absences</span><strong>{summary['absence_count']}</strong></div>
  </div>
  <section>
    <h2>Key Insights</h2>
    <ul>{insight_html}</ul>
  </section>
  <section class="grid">
    <div>
      <h2>Hours by Department</h2>
      <table><tbody>{rows(data['hours_by_department'])}</tbody></table>
    </div>
    <div>
      <h2>Top Projects</h2>
      <table><tbody>{rows(data['top_projects'])}</tbody></table>
    </div>
  </section>
  <section>
    <h2>Employee Performance</h2>
    <table>
      <thead><tr><th>ID</th><th>Name</th><th>Department</th><th>Hours</th><th>Productivity</th><th>Overtime</th></tr></thead>
      <tbody>{performance}</tbody>
    </table>
  </section>
</body>
</html>"""
