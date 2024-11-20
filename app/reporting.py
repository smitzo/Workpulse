from __future__ import annotations

from datetime import datetime
from html import escape
from pathlib import Path

from .analytics_service import AnalyticsService
from .data_store import Filters


def write_html_report(service: AnalyticsService, filters: Filters, output_path: Path) -> None:
    data = service.dashboard(filters)
    insights = service.insights(filters)
    summary = data["summary"]

    def rows(items: list[tuple[str, float]], suffix: str = "") -> str:
        return "\n".join(
            f"<tr><td>{escape(str(label))}</td><td>{value:g}{suffix}</td></tr>"
            for label, value in items
        ) or "<tr><td colspan='2'>No data</td></tr>"

    def performance_rows() -> str:
        result = []
        for row in data["employee_performance"][:12]:
            result.append(
                "<tr>"
                f"<td>{escape(row['employee_id'])}</td>"
                f"<td>{escape(row['name'])}</td>"
                f"<td>{escape(row['department'])}</td>"
                f"<td>{row['total_hours']}</td>"
                f"<td>{row['avg_productivity']}%</td>"
                f"<td>{row['overtime_hours']}</td>"
                "</tr>"
            )
        return "\n".join(result)

    insight_html = "\n".join(
        f"<li><strong>{escape(item.title)}:</strong> {escape(item.detail)}</li>"
        for item in insights
    )

    output_path.write_text(
        f"""<!doctype html>
<html lang="en">
<head>
  <meta charset="utf-8">
  <title>Employee Analytics Report</title>
  <style>
    body {{ font-family: Arial, sans-serif; margin: 32px; color: #0f172a; }}
    h1 {{ margin-bottom: 4px; }}
    .muted {{ color: #64748b; }}
    .kpis {{ display: grid; grid-template-columns: repeat(3, 1fr); gap: 12px; margin: 24px 0; }}
    .kpi {{ border: 1px solid #cbd5e1; padding: 14px; border-radius: 6px; }}
    .kpi div:first-child {{ color: #64748b; font-size: 12px; font-weight: bold; }}
    .kpi div:last-child {{ font-size: 24px; font-weight: bold; margin-top: 6px; }}
    section {{ margin-top: 28px; }}
    table {{ border-collapse: collapse; width: 100%; margin-top: 10px; }}
    th, td {{ border: 1px solid #cbd5e1; padding: 8px; text-align: left; }}
    th {{ background: #f1f5f9; }}
    .grid {{ display: grid; grid-template-columns: 1fr 1fr; gap: 24px; }}
  </style>
</head>
<body>
  <h1>Employee Data Analytics Report</h1>
  <div class="muted">Generated {datetime.now().strftime('%Y-%m-%d %H:%M')}</div>
  <p>{escape(service.executive_summary(filters))}</p>

  <div class="kpis">
    <div class="kpi"><div>Employees</div><div>{summary['total_employees']}</div></div>
    <div class="kpi"><div>Total Hours</div><div>{summary['total_hours']}</div></div>
    <div class="kpi"><div>Avg Productivity</div><div>{summary['avg_productivity']}%</div></div>
    <div class="kpi"><div>Attendance</div><div>{summary['attendance_rate']}%</div></div>
    <div class="kpi"><div>Overtime</div><div>{summary['overtime_hours']}</div></div>
    <div class="kpi"><div>Absences</div><div>{summary['absence_count']}</div></div>
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
      <tbody>{performance_rows()}</tbody>
    </table>
  </section>
</body>
</html>
""",
        encoding="utf-8",
    )
