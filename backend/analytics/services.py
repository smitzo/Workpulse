from __future__ import annotations

from dataclasses import dataclass
from decimal import Decimal

from django.contrib.auth.models import AnonymousUser, User
from django.db.models import Avg, Count, DecimalField, FloatField, IntegerField, Q, Sum
from django.db.models.functions import Coalesce

from analytics.models import Attendance, Employee, IdealTime, UserProfile, WorkGroupItem, WorkLog


HOURS_FIELD = DecimalField(max_digits=12, decimal_places=2)


@dataclass(frozen=True)
class Filters:
    date_from: str | None = None
    date_to: str | None = None
    department: str | None = None
    employee_id: str | None = None
    task_type: str | None = None
    project: str | None = None


@dataclass(frozen=True)
class Insight:
    title: str
    detail: str


def number(value, places: int = 2) -> float:
    if value is None:
        return 0
    if isinstance(value, Decimal):
        value = float(value)
    return round(float(value), places)


def user_role(user: User | AnonymousUser) -> str:
    if not getattr(user, "is_authenticated", False):
        return UserProfile.ROLE_EMPLOYEE
    profile = getattr(user, "profile", None)
    if profile:
        return profile.role
    return UserProfile.ROLE_ADMIN if user.is_staff else UserProfile.ROLE_EMPLOYEE


def scoped_filters(filters: Filters, user: User | AnonymousUser) -> Filters:
    profile = getattr(user, "profile", None)
    if user_role(user) == UserProfile.ROLE_ADMIN:
        return filters
    return Filters(
        date_from=filters.date_from,
        date_to=filters.date_to,
        department=filters.department,
        employee_id=profile.employee_id if profile else filters.employee_id,
        task_type=filters.task_type,
        project=filters.project,
    )


class AnalyticsService:
    def dashboard(self, filters: Filters) -> dict:
        performance = self.employee_performance(filters)
        return {
            "summary": self.summary(filters),
            "hours_by_department": self.grouped_metric("department", "hours", filters),
            "productivity_by_department": self.grouped_metric("department", "productivity", filters),
            "hours_by_task": self.grouped_metric("task_type", "hours", filters),
            "overtime_by_department": self.grouped_metric("department", "overtime", filters),
            "top_projects": self.grouped_metric("project", "hours", filters, limit=6),
            "employee_performance": performance,
            "hours_trend": self.daily_trend("hours", filters),
            "productivity_trend": self.daily_trend("productivity", filters),
            "attendance_breakdown": self.attendance_breakdown(filters),
            "late_by_department": self.late_by_department(filters),
            "workload_heatmap": self.workload_heatmap(filters),
            "ideal_vs_actual": self.ideal_vs_actual(filters),
            "sunburst": self.sunburst_tree(filters),
        }

    def summary(self, filters: Filters) -> dict[str, float]:
        employees = self.employee_queryset(filters)
        logs = self.work_log_queryset(filters)
        attendance = self.attendance_queryset(filters)

        log_stats = logs.aggregate(
            logs=Count("id"),
            hours=Coalesce(Sum("hours"), Decimal("0"), output_field=HOURS_FIELD),
            avg_score=Coalesce(Avg("productivity_score"), 0.0, output_field=FloatField()),
            overtime=Coalesce(Sum("overtime_hours"), Decimal("0"), output_field=HOURS_FIELD),
        )
        attendance_stats = attendance.aggregate(
            rows=Count("id"),
            present=Count("id", filter=Q(status=Attendance.STATUS_PRESENT)),
            absent=Count("id", filter=Q(status=Attendance.STATUS_ABSENT)),
            late_minutes=Coalesce(Sum("late_minutes"), 0, output_field=IntegerField()),
        )
        attendance_rate = 0
        if attendance_stats["rows"]:
            attendance_rate = round(attendance_stats["present"] * 100 / attendance_stats["rows"], 1)

        return {
            "total_employees": employees.count(),
            "active_employees": employees.filter(status="Active").count(),
            "total_hours": number(log_stats["hours"], 1),
            "avg_productivity": number(log_stats["avg_score"], 1),
            "overtime_hours": number(log_stats["overtime"], 1),
            "work_logs": log_stats["logs"],
            "attendance_rate": attendance_rate,
            "late_minutes": attendance_stats["late_minutes"] or 0,
            "absence_count": attendance_stats["absent"] or 0,
        }

    def employee_queryset(self, filters: Filters):
        queryset = Employee.objects.all()
        if filters.department and filters.department != "All":
            queryset = queryset.filter(department=filters.department)
        if filters.employee_id and filters.employee_id != "All":
            queryset = queryset.filter(employee_id=filters.employee_id)
        return queryset

    def work_log_queryset(self, filters: Filters):
        queryset = WorkLog.objects.select_related("employee")
        if filters.date_from:
            queryset = queryset.filter(log_date__gte=filters.date_from)
        if filters.date_to:
            queryset = queryset.filter(log_date__lte=filters.date_to)
        if filters.department and filters.department != "All":
            queryset = queryset.filter(employee__department=filters.department)
        if filters.employee_id and filters.employee_id != "All":
            queryset = queryset.filter(employee_id=filters.employee_id)
        if filters.task_type and filters.task_type != "All":
            queryset = queryset.filter(task_type=filters.task_type)
        if filters.project and filters.project != "All":
            queryset = queryset.filter(project=filters.project)
        return queryset

    def attendance_queryset(self, filters: Filters):
        queryset = Attendance.objects.select_related("employee")
        if filters.date_from:
            queryset = queryset.filter(work_date__gte=filters.date_from)
        if filters.date_to:
            queryset = queryset.filter(work_date__lte=filters.date_to)
        if filters.department and filters.department != "All":
            queryset = queryset.filter(employee__department=filters.department)
        if filters.employee_id and filters.employee_id != "All":
            queryset = queryset.filter(employee_id=filters.employee_id)
        return queryset

    def grouped_metric(self, group_by: str, metric: str, filters: Filters, limit: int = 10) -> list[tuple[str, float]]:
        group_fields = {
            "department": "employee__department",
            "employee": "employee__name",
            "task_type": "task_type",
            "project": "project",
        }
        metrics = {
            "hours": Sum("hours"),
            "productivity": Avg("productivity_score"),
            "overtime": Sum("overtime_hours"),
            "logs": Count("id"),
        }
        field = group_fields[group_by]
        rows = (
            self.work_log_queryset(filters)
            .values(field)
            .annotate(value=metrics[metric])
            .order_by("-value")[:limit]
        )
        return [(row[field], number(row["value"], 2)) for row in rows]

    def daily_trend(self, metric: str, filters: Filters, limit: int = 45) -> list[tuple[str, float]]:
        metrics = {
            "hours": Sum("hours"),
            "productivity": Avg("productivity_score"),
            "overtime": Sum("overtime_hours"),
            "logs": Count("id"),
        }
        rows = (
            self.work_log_queryset(filters)
            .values("log_date")
            .annotate(value=metrics[metric])
            .order_by("-log_date")[:limit]
        )
        return [(row["log_date"].isoformat(), number(row["value"], 2)) for row in reversed(rows)]

    def employee_performance(self, filters: Filters) -> list[dict]:
        log_filter = Q()
        if filters.date_from:
            log_filter &= Q(work_logs__log_date__gte=filters.date_from)
        if filters.date_to:
            log_filter &= Q(work_logs__log_date__lte=filters.date_to)
        if filters.task_type and filters.task_type != "All":
            log_filter &= Q(work_logs__task_type=filters.task_type)
        if filters.project and filters.project != "All":
            log_filter &= Q(work_logs__project=filters.project)

        rows = (
            self.employee_queryset(filters)
            .annotate(
                log_count=Count("work_logs", filter=log_filter),
                total_hours=Coalesce(Sum("work_logs__hours", filter=log_filter), Decimal("0"), output_field=HOURS_FIELD),
                avg_productivity=Coalesce(Avg("work_logs__productivity_score", filter=log_filter), 0.0, output_field=FloatField()),
                overtime_hours=Coalesce(Sum("work_logs__overtime_hours", filter=log_filter), Decimal("0"), output_field=HOURS_FIELD),
                worked_days=Count("work_logs__log_date", filter=log_filter, distinct=True),
            )
            .order_by("-avg_productivity", "-total_hours", "name")
        )
        performance = []
        for row in rows:
            total_hours = number(row.total_hours, 2)
            performance.append(
                {
                    "employee_id": row.employee_id,
                    "name": row.name,
                    "department": row.department,
                    "role": row.role,
                    "log_count": row.log_count,
                    "total_hours": total_hours,
                    "avg_productivity": number(row.avg_productivity, 1),
                    "overtime_hours": number(row.overtime_hours, 2),
                    "avg_daily_hours": round(total_hours / row.worked_days, 2) if row.worked_days else 0,
                }
            )
        return performance

    def attendance_breakdown(self, filters: Filters) -> list[tuple[str, float]]:
        rows = (
            self.attendance_queryset(filters)
            .values("status")
            .annotate(value=Count("id"))
            .order_by("-value")
        )
        return [(row["status"], row["value"]) for row in rows]

    def late_by_department(self, filters: Filters) -> list[tuple[str, float]]:
        rows = (
            self.attendance_queryset(filters)
            .values("employee__department")
            .annotate(value=Avg("late_minutes"))
            .filter(value__gt=0)
            .order_by("-value")
        )
        return [(row["employee__department"], number(row["value"], 1)) for row in rows]

    def workload_heatmap(self, filters: Filters) -> list[tuple[str, str, float]]:
        rows = (
            self.work_log_queryset(filters)
            .values("employee__department", "task_type")
            .annotate(hours=Sum("hours"))
            .order_by("employee__department", "task_type")
        )
        return [(row["employee__department"], row["task_type"], number(row["hours"], 2)) for row in rows]

    def ideal_vs_actual(self, filters: Filters) -> list[tuple[str, float, float, float]]:
        ideal_hours = {item.task_type: number(item.ideal_hours, 2) for item in IdealTime.objects.all()}
        rows = (
            self.work_log_queryset(filters)
            .values("task_type")
            .annotate(actual_hours=Sum("hours"))
            .order_by("-actual_hours")
        )
        result = []
        for row in rows:
            actual = number(row["actual_hours"], 2)
            ideal = ideal_hours.get(row["task_type"], 0)
            result.append((row["task_type"], actual, ideal, round(actual - ideal, 2)))
        return result

    def sunburst_tree(self, filters: Filters) -> dict:
        group_map = {
            item.task_type: (item.group.group_name, item.group.color_code)
            for item in WorkGroupItem.objects.select_related("group")
        }
        rows = (
            self.work_log_queryset(filters)
            .values("project", "task_type")
            .annotate(
                standard_hours=Sum("hours", filter=Q(overtime_hours=0)),
                overtime_hours=Sum("hours", filter=Q(overtime_hours__gt=0)),
            )
            .order_by("project", "task_type")
        )
        root = {"name": "Total Work", "children": []}
        projects: dict[str, dict] = {}
        groups: dict[tuple[str, str], dict] = {}
        tasks: dict[tuple[str, str, str], dict] = {}

        for row in rows:
            project = row["project"]
            task_type = row["task_type"]
            group_name, color = group_map.get(task_type, ("Ungrouped", "#64748b"))
            project_node = projects.setdefault(project, {"name": project, "children": []})
            if project_node not in root["children"]:
                root["children"].append(project_node)

            group_key = (project, group_name)
            group_node = groups.setdefault(group_key, {"name": group_name, "color": color, "children": []})
            if group_node not in project_node["children"]:
                project_node["children"].append(group_node)

            task_key = (project, group_name, task_type)
            task_node = tasks.setdefault(task_key, {"name": task_type, "children": []})
            if task_node not in group_node["children"]:
                group_node["children"].append(task_node)

            if row["standard_hours"]:
                task_node["children"].append({"name": "Standard", "value": number(row["standard_hours"], 2)})
            if row["overtime_hours"]:
                task_node["children"].append({"name": "Overtime", "value": number(row["overtime_hours"], 2)})

        return root

    def insights(self, filters: Filters) -> list[Insight]:
        data = self.dashboard(filters)
        summary = data["summary"]
        performance = data["employee_performance"]
        insights: list[Insight] = []

        if summary["attendance_rate"] >= 92:
            insights.append(Insight("Attendance is stable", f"{summary['attendance_rate']}% attendance keeps delivery capacity predictable."))
        elif summary["attendance_rate"]:
            insights.append(Insight("Attendance needs attention", f"Attendance is {summary['attendance_rate']}%; review leave clusters and backup ownership."))

        if summary["overtime_hours"] > 0:
            overtime_share = (summary["overtime_hours"] / summary["total_hours"] * 100) if summary["total_hours"] else 0
            title = "Overtime is concentrated" if overtime_share > 8 else "Overtime is controlled"
            detail = f"Overtime is {overtime_share:.1f}% of logged time in this view."
            insights.append(Insight(title, detail))

        if performance:
            top = performance[0]
            overloaded = [row for row in performance if row["avg_daily_hours"] > 8.7]
            if overloaded:
                names = ", ".join(row["name"] for row in overloaded[:3])
                insights.append(Insight("Capacity risk", f"{names} are averaging more than 8.7 hours on working days."))
            insights.append(Insight("Top performer", f"{top['name']} leads with {top['avg_productivity']} average productivity over {top['total_hours']} hours."))
            coaching = [row for row in performance if row["log_count"] and row["avg_productivity"] < 75]
            if coaching:
                names = ", ".join(row["name"] for row in coaching[:3])
                insights.append(Insight("Coaching opportunity", f"{names} are below 75 average productivity; review task mix and blockers."))

        departments = data["hours_by_department"]
        if departments:
            top_department, hours = departments[0]
            insights.append(Insight("Largest workload", f"{top_department} logged the most time with {hours} hours."))

        absent = next((value for label, value in data["attendance_breakdown"] if label == "Absent"), 0)
        if absent:
            insights.append(Insight("Absence signal", f"There are {absent:g} absences in the selected period."))

        return insights or [Insight("Ready for analysis", "Seed demo data or add work logs to generate insights.")]

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
