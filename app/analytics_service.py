from __future__ import annotations

from dataclasses import dataclass

from .data_store import EmployeeAnalyticsStore, Filters


@dataclass(frozen=True)
class Insight:
    title: str
    detail: str


class AnalyticsService:
    def __init__(self, store: EmployeeAnalyticsStore):
        self.store = store

    def dashboard(self, filters: Filters) -> dict:
        performance = [dict(row) for row in self.store.employee_performance(filters)]
        return {
            "summary": self.store.summary(filters),
            "hours_by_department": self.store.grouped_metric("department", "hours", filters),
            "productivity_by_department": self.store.grouped_metric("department", "productivity", filters),
            "hours_by_task": self.store.grouped_metric("task_type", "hours", filters),
            "overtime_by_department": self.store.grouped_metric("department", "overtime", filters),
            "top_projects": self.store.grouped_metric("project", "hours", filters, limit=6),
            "employee_performance": performance,
            "hours_trend": self.store.daily_trend("hours", filters),
            "productivity_trend": self.store.daily_trend("productivity", filters),
            "attendance_breakdown": self.store.attendance_breakdown(filters),
            "late_by_department": self.store.late_by_department(filters),
            "workload_heatmap": self.store.workload_heatmap(filters),
            "ideal_vs_actual": self.store.ideal_vs_actual(filters),
            "sunburst": self.store.sunburst_tree(filters),
        }

    def insights(self, filters: Filters) -> list[Insight]:
        data = self.dashboard(filters)
        summary = data["summary"]
        performance = data["employee_performance"]
        insights: list[Insight] = []

        if summary["attendance_rate"] >= 92:
            insights.append(
                Insight(
                    "Attendance is stable",
                    f"{summary['attendance_rate']}% attendance for the selected period keeps delivery capacity predictable.",
                )
            )
        elif summary["attendance_rate"]:
            insights.append(
                Insight(
                    "Attendance needs attention",
                    f"Attendance is {summary['attendance_rate']}%; review leave clusters and backup ownership.",
                )
            )

        if summary["overtime_hours"] > 0:
            overtime_share = (summary["overtime_hours"] / summary["total_hours"] * 100) if summary["total_hours"] else 0
            if overtime_share > 8:
                insights.append(
                    Insight(
                        "Overtime is concentrated",
                        f"Overtime is {overtime_share:.1f}% of logged time; rebalance overloaded projects or staffing.",
                    )
                )
            else:
                insights.append(
                    Insight(
                        "Overtime is controlled",
                        f"Only {overtime_share:.1f}% of logged time is overtime in this view.",
                    )
                )

        if performance:
            top = performance[0]
            overloaded = [
                row for row in performance
                if row["avg_daily_hours"] and row["avg_daily_hours"] > 8.7
            ]
            if overloaded:
                names = ", ".join(row["name"] for row in overloaded[:3])
                insights.append(
                    Insight(
                        "Capacity risk",
                        f"{names} are averaging more than 8.7 hours on working days; check workload balance.",
                    )
                )
            insights.append(
                Insight(
                    "Top performer",
                    f"{top['name']} leads with {top['avg_productivity']} average productivity over {top['total_hours']} hours.",
                )
            )
            coaching = [row for row in performance if row["log_count"] and row["avg_productivity"] < 75]
            if coaching:
                names = ", ".join(row["name"] for row in coaching[:3])
                insights.append(
                    Insight(
                        "Coaching opportunity",
                        f"{names} are below 75 average productivity; review task mix, blockers, or training needs.",
                    )
                )

        departments = data["hours_by_department"]
        if departments:
            top_department, hours = departments[0]
            insights.append(
                Insight(
                    "Largest workload",
                    f"{top_department} logged the most time with {hours} hours in the selected period.",
                )
            )

        attendance = data["attendance_breakdown"]
        absent = next((value for label, value in attendance if label == "Absent"), 0)
        if absent:
            insights.append(
                Insight(
                    "Absence signal",
                    f"There are {absent:g} absences in the selected period; the Attendance tab shows who and when.",
                )
            )

        if not insights:
            insights.append(Insight("Ready for analysis", "Load sample data or add work logs to generate insights."))

        return insights

    def executive_summary(self, filters: Filters) -> str:
        data = self.dashboard(filters)
        summary = data["summary"]
        top_project = data["top_projects"][0] if data["top_projects"] else ("No project", 0)
        top_department = data["hours_by_department"][0] if data["hours_by_department"] else ("No department", 0)
        return (
            f"{summary['active_employees']} active employees logged {summary['total_hours']} hours "
            f"across {summary['work_logs']} work logs. Average productivity is "
            f"{summary['avg_productivity']}%, attendance is {summary['attendance_rate']}%, and "
            f"overtime totals {summary['overtime_hours']} hours. {top_department[0]} has the "
            f"largest workload ({top_department[1]} hours), while {top_project[0]} is the "
            f"largest project ({top_project[1]} hours)."
        )
