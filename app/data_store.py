from __future__ import annotations

from contextlib import contextmanager
from dataclasses import dataclass
from datetime import date, datetime, timedelta
from pathlib import Path
import csv
import hashlib
import sqlite3

from .sample_data import build_sample_dataset


APP_DIR = Path(__file__).resolve().parent.parent
DATA_DIR = APP_DIR / "data"
DEFAULT_DB_PATH = DATA_DIR / "employee_analytics.sqlite3"


@dataclass(frozen=True)
class Filters:
    date_from: str | None = None
    date_to: str | None = None
    department: str | None = None
    employee_id: str | None = None
    task_type: str | None = None
    project: str | None = None


@dataclass(frozen=True)
class EmployeePayload:
    employee_id: str
    name: str
    department: str
    role: str
    location: str
    manager: str
    hire_date: str
    status: str


def hash_password(password: str) -> str:
    return hashlib.sha256(password.encode("utf-8")).hexdigest()


class EmployeeAnalyticsStore:
    def __init__(self, db_path: Path | str = DEFAULT_DB_PATH):
        self.db_path = Path(db_path)
        self.db_path.parent.mkdir(parents=True, exist_ok=True)

    @contextmanager
    def connect(self):
        connection = sqlite3.connect(self.db_path)
        connection.row_factory = sqlite3.Row
        connection.execute("PRAGMA foreign_keys = ON")
        try:
            yield connection
            connection.commit()
        finally:
            connection.close()

    def initialize(self, seed_sample: bool = False, reset_sample: bool = False) -> None:
        with self.connect() as connection:
            self._create_schema(connection)
            has_employees = connection.execute("SELECT COUNT(*) FROM employees").fetchone()[0] > 0
            if reset_sample:
                self.clear_all(connection)
                self._insert_sample_data(connection)
            elif seed_sample and not has_employees:
                self._insert_sample_data(connection)

    def _create_schema(self, connection: sqlite3.Connection) -> None:
        connection.executescript(
            """
            CREATE TABLE IF NOT EXISTS employees (
                employee_id TEXT PRIMARY KEY,
                name TEXT NOT NULL,
                department TEXT NOT NULL,
                role TEXT NOT NULL,
                location TEXT NOT NULL,
                manager TEXT NOT NULL,
                hire_date TEXT NOT NULL,
                status TEXT NOT NULL
            );

            CREATE TABLE IF NOT EXISTS work_logs (
                log_id INTEGER PRIMARY KEY AUTOINCREMENT,
                employee_id TEXT NOT NULL,
                log_date TEXT NOT NULL,
                project TEXT NOT NULL,
                task_type TEXT NOT NULL,
                hours REAL NOT NULL CHECK(hours >= 0),
                productivity_score INTEGER NOT NULL CHECK(productivity_score BETWEEN 0 AND 100),
                overtime_hours REAL NOT NULL DEFAULT 0,
                notes TEXT,
                FOREIGN KEY (employee_id) REFERENCES employees(employee_id) ON DELETE CASCADE
            );

            CREATE TABLE IF NOT EXISTS attendance (
                attendance_id INTEGER PRIMARY KEY AUTOINCREMENT,
                employee_id TEXT NOT NULL,
                work_date TEXT NOT NULL,
                status TEXT NOT NULL,
                check_in TEXT,
                check_out TEXT,
                late_minutes INTEGER NOT NULL DEFAULT 0,
                FOREIGN KEY (employee_id) REFERENCES employees(employee_id) ON DELETE CASCADE,
                UNIQUE (employee_id, work_date)
            );

            CREATE INDEX IF NOT EXISTS idx_work_logs_date ON work_logs(log_date);
            CREATE INDEX IF NOT EXISTS idx_work_logs_employee ON work_logs(employee_id);
            CREATE INDEX IF NOT EXISTS idx_attendance_date ON attendance(work_date);

            CREATE TABLE IF NOT EXISTS work_groups (
                group_id INTEGER PRIMARY KEY AUTOINCREMENT,
                group_name TEXT UNIQUE NOT NULL,
                color_code TEXT NOT NULL DEFAULT '#64748b'
            );

            CREATE TABLE IF NOT EXISTS work_group_items (
                item_id INTEGER PRIMARY KEY AUTOINCREMENT,
                group_id INTEGER NOT NULL,
                task_type TEXT NOT NULL,
                FOREIGN KEY (group_id) REFERENCES work_groups(group_id) ON DELETE CASCADE,
                UNIQUE(group_id, task_type)
            );

            CREATE TABLE IF NOT EXISTS ideal_times (
                task_type TEXT PRIMARY KEY,
                ideal_hours REAL NOT NULL CHECK(ideal_hours >= 0)
            );

            CREATE TABLE IF NOT EXISTS auth_users (
                username TEXT PRIMARY KEY,
                password_hash TEXT NOT NULL,
                role TEXT NOT NULL CHECK(role IN ('admin', 'employee')),
                employee_id TEXT,
                FOREIGN KEY (employee_id) REFERENCES employees(employee_id) ON DELETE CASCADE
            );
            """
        )

    def clear_all(self, connection: sqlite3.Connection | None = None) -> None:
        if connection is None:
            with self.connect() as own_connection:
                self.clear_all(own_connection)
            return
        connection.execute("DELETE FROM attendance")
        connection.execute("DELETE FROM work_logs")
        connection.execute("DELETE FROM work_group_items")
        connection.execute("DELETE FROM work_groups")
        connection.execute("DELETE FROM ideal_times")
        connection.execute("DELETE FROM auth_users")
        connection.execute("DELETE FROM employees")
        connection.execute("DELETE FROM sqlite_sequence WHERE name IN ('attendance', 'work_logs', 'work_groups', 'work_group_items')")

    def seed_sample_data(self, reset: bool = True) -> None:
        with self.connect() as connection:
            self._create_schema(connection)
            if reset:
                self.clear_all(connection)
            self._insert_sample_data(connection)

    def _insert_sample_data(self, connection: sqlite3.Connection) -> None:
        dataset = build_sample_dataset()
        connection.executemany(
            """
            INSERT OR REPLACE INTO employees
            (employee_id, name, department, role, location, manager, hire_date, status)
            VALUES (?, ?, ?, ?, ?, ?, ?, ?)
            """,
            dataset["employees"],
        )
        connection.executemany(
            """
            INSERT INTO work_logs
            (employee_id, log_date, project, task_type, hours, productivity_score, overtime_hours, notes)
            VALUES (?, ?, ?, ?, ?, ?, ?, ?)
            """,
            dataset["work_logs"],
        )
        connection.executemany(
            """
            INSERT OR REPLACE INTO attendance
            (employee_id, work_date, status, check_in, check_out, late_minutes)
            VALUES (?, ?, ?, ?, ?, ?)
            """,
            dataset["attendance"],
        )
        connection.executemany(
            """
            INSERT OR REPLACE INTO ideal_times (task_type, ideal_hours)
            VALUES (?, ?)
            """,
            dataset["ideal_times"],
        )
        for group_name, group_data in dataset["work_groups"].items():
            cursor = connection.execute(
                """
                INSERT OR REPLACE INTO work_groups (group_name, color_code)
                VALUES (?, ?)
                """,
                (group_name, group_data["color"]),
            )
            group_id = cursor.lastrowid
            if not group_id:
                group_id = connection.execute(
                    "SELECT group_id FROM work_groups WHERE group_name = ?",
                    (group_name,),
                ).fetchone()[0]
            for task_type in group_data["items"]:
                connection.execute(
                    """
                    INSERT OR IGNORE INTO work_group_items (group_id, task_type)
                    VALUES (?, ?)
                    """,
                    (group_id, task_type),
                )
        connection.executemany(
            """
            INSERT OR REPLACE INTO auth_users (username, password_hash, role, employee_id)
            VALUES (?, ?, ?, ?)
            """,
            [
                (username, hash_password(password), role, employee_id)
                for username, password, role, employee_id in dataset["users"]
            ],
        )

    def authenticate(self, username: str, password: str) -> dict | None:
        with self.connect() as connection:
            row = connection.execute(
                """
                SELECT au.username, au.role, au.employee_id, e.name, e.department
                FROM auth_users au
                LEFT JOIN employees e ON e.employee_id = au.employee_id
                WHERE au.username = ? AND au.password_hash = ?
                """,
                (username, hash_password(password)),
            ).fetchone()
        return dict(row) if row else None

    def auth_user(self, username: str) -> dict | None:
        with self.connect() as connection:
            row = connection.execute(
                """
                SELECT au.username, au.role, au.employee_id, e.name, e.department
                FROM auth_users au
                LEFT JOIN employees e ON e.employee_id = au.employee_id
                WHERE au.username = ?
                """,
                (username,),
            ).fetchone()
        return dict(row) if row else None

    def list_employees(self, department: str | None = None, search: str | None = None) -> list[sqlite3.Row]:
        clauses: list[str] = []
        params: list[str] = []
        if department and department != "All":
            clauses.append("department = ?")
            params.append(department)
        if search:
            clauses.append("(LOWER(name) LIKE ? OR LOWER(employee_id) LIKE ? OR LOWER(role) LIKE ?)")
            pattern = f"%{search.lower()}%"
            params.extend([pattern, pattern, pattern])
        where = f"WHERE {' AND '.join(clauses)}" if clauses else ""
        query = f"""
            SELECT employee_id, name, department, role, location, manager, hire_date, status
            FROM employees
            {where}
            ORDER BY department, name
        """
        with self.connect() as connection:
            return connection.execute(query, params).fetchall()

    def get_employee(self, employee_id: str) -> sqlite3.Row | None:
        with self.connect() as connection:
            return connection.execute(
                """
                SELECT employee_id, name, department, role, location, manager, hire_date, status
                FROM employees
                WHERE employee_id = ?
                """,
                (employee_id,),
            ).fetchone()

    def upsert_employee(self, employee: EmployeePayload) -> None:
        self._validate_date(employee.hire_date, "Hire date")
        with self.connect() as connection:
            connection.execute(
                """
                INSERT INTO employees
                (employee_id, name, department, role, location, manager, hire_date, status)
                VALUES (?, ?, ?, ?, ?, ?, ?, ?)
                ON CONFLICT(employee_id) DO UPDATE SET
                    name = excluded.name,
                    department = excluded.department,
                    role = excluded.role,
                    location = excluded.location,
                    manager = excluded.manager,
                    hire_date = excluded.hire_date,
                    status = excluded.status
                """,
                (
                    employee.employee_id,
                    employee.name,
                    employee.department,
                    employee.role,
                    employee.location,
                    employee.manager,
                    employee.hire_date,
                    employee.status,
                ),
            )

    def delete_employee(self, employee_id: str) -> None:
        with self.connect() as connection:
            connection.execute("DELETE FROM employees WHERE employee_id = ?", (employee_id,))

    def list_work_logs(self, filters: Filters | None = None, limit: int | None = None) -> list[sqlite3.Row]:
        filters = filters or Filters()
        where, params = self._build_work_log_where(filters)
        limit_sql = " LIMIT ?" if limit else ""
        if limit:
            params.append(limit)
        query = f"""
            SELECT wl.log_id, wl.log_date, e.employee_id, e.name, e.department, wl.project,
                   wl.task_type, wl.hours, wl.productivity_score, wl.overtime_hours, wl.notes
            FROM work_logs wl
            JOIN employees e ON e.employee_id = wl.employee_id
            {where}
            ORDER BY wl.log_date DESC, wl.log_id DESC
            {limit_sql}
        """
        with self.connect() as connection:
            return connection.execute(query, params).fetchall()

    def add_work_log(
        self,
        employee_id: str,
        log_date: str,
        project: str,
        task_type: str,
        hours: float,
        productivity_score: int,
        overtime_hours: float,
        notes: str = "",
    ) -> None:
        self._validate_date(log_date, "Log date")
        with self.connect() as connection:
            connection.execute(
                """
                INSERT INTO work_logs
                (employee_id, log_date, project, task_type, hours, productivity_score, overtime_hours, notes)
                VALUES (?, ?, ?, ?, ?, ?, ?, ?)
                """,
                (employee_id, log_date, project, task_type, hours, productivity_score, overtime_hours, notes),
            )

    def delete_work_log(self, log_id: int) -> None:
        with self.connect() as connection:
            connection.execute("DELETE FROM work_logs WHERE log_id = ?", (log_id,))

    def upsert_attendance(
        self,
        employee_id: str,
        work_date: str,
        status: str,
        check_in: str = "",
        check_out: str = "",
        late_minutes: int = 0,
    ) -> None:
        self._validate_date(work_date, "Attendance date")
        with self.connect() as connection:
            connection.execute(
                """
                INSERT INTO attendance (employee_id, work_date, status, check_in, check_out, late_minutes)
                VALUES (?, ?, ?, ?, ?, ?)
                ON CONFLICT(employee_id, work_date) DO UPDATE SET
                    status = excluded.status,
                    check_in = excluded.check_in,
                    check_out = excluded.check_out,
                    late_minutes = excluded.late_minutes
                """,
                (employee_id, work_date, status, check_in, check_out, late_minutes),
            )

    def list_attendance(self, filters: Filters | None = None, limit: int | None = None) -> list[sqlite3.Row]:
        filters = filters or Filters()
        where, params = self._build_attendance_where(filters)
        limit_sql = " LIMIT ?" if limit else ""
        if limit:
            params.append(limit)
        with self.connect() as connection:
            return connection.execute(
                f"""
                SELECT a.attendance_id, a.work_date, e.employee_id, e.name, e.department,
                       a.status, a.check_in, a.check_out, a.late_minutes
                FROM attendance a
                JOIN employees e ON e.employee_id = a.employee_id
                {where}
                ORDER BY a.work_date DESC, e.name
                {limit_sql}
                """,
                params,
            ).fetchall()

    def filter_options(self) -> dict[str, list[str]]:
        with self.connect() as connection:
            departments = [row[0] for row in connection.execute("SELECT DISTINCT department FROM employees ORDER BY department")]
            employees = [
                f"{row['employee_id']} - {row['name']}"
                for row in connection.execute("SELECT employee_id, name FROM employees ORDER BY name")
            ]
            task_types = [row[0] for row in connection.execute("SELECT DISTINCT task_type FROM work_logs ORDER BY task_type")]
            projects = [row[0] for row in connection.execute("SELECT DISTINCT project FROM work_logs ORDER BY project")]
            statuses = [row[0] for row in connection.execute("SELECT DISTINCT status FROM employees ORDER BY status")]
        return {
            "departments": ["All", *departments],
            "employees": ["All", *employees],
            "task_types": ["All", *task_types],
            "projects": ["All", *projects],
            "statuses": ["All", *statuses],
        }

    def summary(self, filters: Filters | None = None) -> dict[str, float]:
        filters = filters or Filters()
        where, params = self._build_work_log_where(filters)
        with self.connect() as connection:
            employee_where = ""
            employee_params: list[str] = []
            if filters.department and filters.department != "All":
                employee_where = "WHERE department = ?"
                employee_params.append(filters.department)
            employee_stats = connection.execute(
                f"""
                SELECT COUNT(*) AS total,
                       SUM(CASE WHEN status = 'Active' THEN 1 ELSE 0 END) AS active
                FROM employees
                {employee_where}
                """,
                employee_params,
            ).fetchone()
            log_stats = connection.execute(
                f"""
                SELECT COUNT(*) AS logs,
                       COALESCE(SUM(hours), 0) AS hours,
                       COALESCE(AVG(productivity_score), 0) AS avg_score,
                       COALESCE(SUM(overtime_hours), 0) AS overtime
                FROM work_logs wl
                JOIN employees e ON e.employee_id = wl.employee_id
                {where}
                """,
                params,
            ).fetchone()
            attendance_stats = self.attendance_summary(connection, filters)
        return {
            "total_employees": employee_stats["total"] or 0,
            "active_employees": employee_stats["active"] or 0,
            "total_hours": round(log_stats["hours"] or 0, 1),
            "avg_productivity": round(log_stats["avg_score"] or 0, 1),
            "overtime_hours": round(log_stats["overtime"] or 0, 1),
            "work_logs": log_stats["logs"] or 0,
            "attendance_rate": attendance_stats["attendance_rate"],
            "late_minutes": attendance_stats["late_minutes"],
            "absence_count": attendance_stats["absence_count"],
        }

    def attendance_summary(self, connection: sqlite3.Connection, filters: Filters) -> dict[str, float]:
        where, params = self._build_attendance_where(filters)
        row = connection.execute(
            f"""
            SELECT COUNT(*) AS rows,
                   SUM(CASE WHEN a.status = 'Present' THEN 1 ELSE 0 END) AS present,
                   SUM(CASE WHEN a.status = 'Absent' THEN 1 ELSE 0 END) AS absent,
                   COALESCE(SUM(a.late_minutes), 0) AS late_minutes
            FROM attendance a
            JOIN employees e ON e.employee_id = a.employee_id
            {where}
            """,
            params,
        ).fetchone()
        if not row["rows"]:
            return {"attendance_rate": 0, "late_minutes": 0, "absence_count": 0}
        return {
            "attendance_rate": round((row["present"] or 0) * 100 / row["rows"], 1),
            "late_minutes": row["late_minutes"] or 0,
            "absence_count": row["absent"] or 0,
        }

    def grouped_metric(self, group_by: str, metric: str, filters: Filters | None = None, limit: int = 10) -> list[tuple[str, float]]:
        filters = filters or Filters()
        allowed_groups = {
            "department": "e.department",
            "employee": "e.name",
            "task_type": "wl.task_type",
            "project": "wl.project",
        }
        allowed_metrics = {
            "hours": "SUM(wl.hours)",
            "productivity": "AVG(wl.productivity_score)",
            "overtime": "SUM(wl.overtime_hours)",
            "logs": "COUNT(*)",
        }
        group_sql = allowed_groups[group_by]
        metric_sql = allowed_metrics[metric]
        where, params = self._build_work_log_where(filters)
        params.append(limit)
        with self.connect() as connection:
            rows = connection.execute(
                f"""
                SELECT {group_sql} AS label, {metric_sql} AS value
                FROM work_logs wl
                JOIN employees e ON e.employee_id = wl.employee_id
                {where}
                GROUP BY {group_sql}
                ORDER BY value DESC
                LIMIT ?
                """,
                params,
            ).fetchall()
        return [(row["label"], round(row["value"] or 0, 2)) for row in rows]

    def employee_performance(self, filters: Filters | None = None) -> list[sqlite3.Row]:
        filters = filters or Filters()
        join_clauses: list[str] = []
        params: list = []
        employee_clauses: list[str] = []
        if filters.date_from:
            join_clauses.append("wl.log_date >= ?")
            params.append(filters.date_from)
        if filters.date_to:
            join_clauses.append("wl.log_date <= ?")
            params.append(filters.date_to)
        if filters.task_type and filters.task_type != "All":
            join_clauses.append("wl.task_type = ?")
            params.append(filters.task_type)
        if filters.project and filters.project != "All":
            join_clauses.append("wl.project = ?")
            params.append(filters.project)
        if filters.department and filters.department != "All":
            employee_clauses.append("e.department = ?")
            params.append(filters.department)
        if filters.employee_id and filters.employee_id != "All":
            employee_clauses.append("e.employee_id = ?")
            params.append(filters.employee_id)
        join_extra = f" AND {' AND '.join(join_clauses)}" if join_clauses else ""
        where = f"WHERE {' AND '.join(employee_clauses)}" if employee_clauses else ""
        with self.connect() as connection:
            return connection.execute(
                f"""
                SELECT e.employee_id, e.name, e.department, e.role,
                       COUNT(wl.log_id) AS log_count,
                       ROUND(COALESCE(SUM(wl.hours), 0), 2) AS total_hours,
                       ROUND(COALESCE(AVG(wl.productivity_score), 0), 1) AS avg_productivity,
                       ROUND(COALESCE(SUM(wl.overtime_hours), 0), 2) AS overtime_hours,
                       ROUND(COALESCE(SUM(wl.hours) / NULLIF(COUNT(DISTINCT wl.log_date), 0), 0), 2) AS avg_daily_hours
                FROM employees e
                LEFT JOIN work_logs wl ON wl.employee_id = e.employee_id {join_extra}
                {where}
                GROUP BY e.employee_id
                ORDER BY avg_productivity DESC, total_hours DESC
                """,
                params,
            ).fetchall()

    def daily_trend(self, metric: str, filters: Filters | None = None, limit: int = 45) -> list[tuple[str, float]]:
        filters = filters or Filters()
        allowed_metrics = {
            "hours": "SUM(wl.hours)",
            "productivity": "AVG(wl.productivity_score)",
            "overtime": "SUM(wl.overtime_hours)",
            "logs": "COUNT(*)",
        }
        where, params = self._build_work_log_where(filters)
        params.append(limit)
        with self.connect() as connection:
            rows = connection.execute(
                f"""
                SELECT wl.log_date AS label, {allowed_metrics[metric]} AS value
                FROM work_logs wl
                JOIN employees e ON e.employee_id = wl.employee_id
                {where}
                GROUP BY wl.log_date
                ORDER BY wl.log_date DESC
                LIMIT ?
                """,
                params,
            ).fetchall()
        return [(row["label"], round(row["value"] or 0, 2)) for row in reversed(rows)]

    def attendance_breakdown(self, filters: Filters | None = None) -> list[tuple[str, float]]:
        filters = filters or Filters()
        where, params = self._build_attendance_where(filters)
        with self.connect() as connection:
            rows = connection.execute(
                f"""
                SELECT a.status AS label, COUNT(*) AS value
                FROM attendance a
                JOIN employees e ON e.employee_id = a.employee_id
                {where}
                GROUP BY a.status
                ORDER BY value DESC
                """,
                params,
            ).fetchall()
        return [(row["label"], row["value"]) for row in rows]

    def late_by_department(self, filters: Filters | None = None) -> list[tuple[str, float]]:
        filters = filters or Filters()
        where, params = self._build_attendance_where(filters)
        with self.connect() as connection:
            rows = connection.execute(
                f"""
                SELECT e.department AS label, ROUND(AVG(a.late_minutes), 1) AS value
                FROM attendance a
                JOIN employees e ON e.employee_id = a.employee_id
                {where}
                GROUP BY e.department
                HAVING value > 0
                ORDER BY value DESC
                """,
                params,
            ).fetchall()
        return [(row["label"], row["value"]) for row in rows]

    def workload_heatmap(self, filters: Filters | None = None) -> list[tuple[str, str, float]]:
        filters = filters or Filters()
        where, params = self._build_work_log_where(filters)
        with self.connect() as connection:
            rows = connection.execute(
                f"""
                SELECT e.department, wl.task_type, ROUND(SUM(wl.hours), 2) AS hours
                FROM work_logs wl
                JOIN employees e ON e.employee_id = wl.employee_id
                {where}
                GROUP BY e.department, wl.task_type
                ORDER BY e.department, wl.task_type
                """,
                params,
            ).fetchall()
        return [(row["department"], row["task_type"], row["hours"]) for row in rows]

    def ideal_vs_actual(self, filters: Filters | None = None) -> list[tuple[str, float, float, float]]:
        filters = filters or Filters()
        where, params = self._build_work_log_where(filters)
        with self.connect() as connection:
            rows = connection.execute(
                f"""
                SELECT wl.task_type,
                       ROUND(SUM(wl.hours), 2) AS actual_hours,
                       COALESCE(it.ideal_hours, 0) AS ideal_hours,
                       ROUND(SUM(wl.hours) - COALESCE(it.ideal_hours, 0), 2) AS variance
                FROM work_logs wl
                JOIN employees e ON e.employee_id = wl.employee_id
                LEFT JOIN ideal_times it ON it.task_type = wl.task_type
                {where}
                GROUP BY wl.task_type
                ORDER BY actual_hours DESC
                """,
                params,
            ).fetchall()
        return [(row["task_type"], row["actual_hours"], row["ideal_hours"], row["variance"]) for row in rows]

    def work_groups(self) -> dict[str, dict]:
        with self.connect() as connection:
            rows = connection.execute(
                """
                SELECT wg.group_name, wg.color_code, wgi.task_type
                FROM work_groups wg
                LEFT JOIN work_group_items wgi ON wgi.group_id = wg.group_id
                ORDER BY wg.group_name, wgi.task_type
                """
            ).fetchall()
        groups: dict[str, dict] = {}
        for row in rows:
            groups.setdefault(row["group_name"], {"color": row["color_code"], "items": []})
            if row["task_type"]:
                groups[row["group_name"]]["items"].append(row["task_type"])
        return groups

    def sunburst_tree(self, filters: Filters | None = None) -> dict:
        filters = filters or Filters()
        where, params = self._build_work_log_where(filters)
        with self.connect() as connection:
            rows = connection.execute(
                f"""
                SELECT wl.project,
                       COALESCE(wg.group_name, 'Ungrouped') AS group_name,
                       COALESCE(wg.color_code, '#64748b') AS color_code,
                       wl.task_type,
                       CASE WHEN wl.overtime_hours > 0 THEN 'Overtime' ELSE 'Standard' END AS time_type,
                       ROUND(SUM(wl.hours), 2) AS hours
                FROM work_logs wl
                JOIN employees e ON e.employee_id = wl.employee_id
                LEFT JOIN work_group_items wgi ON wgi.task_type = wl.task_type
                LEFT JOIN work_groups wg ON wg.group_id = wgi.group_id
                {where}
                GROUP BY wl.project, group_name, color_code, wl.task_type, time_type
                ORDER BY wl.project, group_name, wl.task_type, time_type
                """,
                params,
            ).fetchall()

        root = {"name": "Total Work", "children": []}
        project_nodes: dict[str, dict] = {}
        group_nodes: dict[tuple[str, str], dict] = {}
        task_nodes: dict[tuple[str, str, str], dict] = {}

        for row in rows:
            project = row["project"]
            group = row["group_name"]
            task = row["task_type"]
            project_node = project_nodes.setdefault(project, {"name": project, "children": []})
            if project_node not in root["children"]:
                root["children"].append(project_node)

            group_key = (project, group)
            group_node = group_nodes.setdefault(
                group_key,
                {"name": group, "color": row["color_code"], "children": []},
            )
            if group_node not in project_node["children"]:
                project_node["children"].append(group_node)

            task_key = (project, group, task)
            task_node = task_nodes.setdefault(task_key, {"name": task, "children": []})
            if task_node not in group_node["children"]:
                group_node["children"].append(task_node)

            task_node["children"].append({"name": row["time_type"], "value": row["hours"]})

        return root

    def date_window(self, days: int = 30) -> Filters:
        today = date.today()
        return Filters(date_from=(today - timedelta(days=days)).isoformat(), date_to=today.isoformat())

    def export_work_logs_csv(self, output_path: Path, filters: Filters | None = None) -> None:
        rows = self.list_work_logs(filters)
        headers = [
            "log_id",
            "log_date",
            "employee_id",
            "name",
            "department",
            "project",
            "task_type",
            "hours",
            "productivity_score",
            "overtime_hours",
            "notes",
        ]
        with output_path.open("w", newline="", encoding="utf-8") as file:
            writer = csv.writer(file)
            writer.writerow(headers)
            for row in rows:
                writer.writerow([row[key] for key in headers])

    def export_employees_csv(self, output_path: Path) -> None:
        rows = self.list_employees()
        headers = ["employee_id", "name", "department", "role", "location", "manager", "hire_date", "status"]
        with output_path.open("w", newline="", encoding="utf-8") as file:
            writer = csv.writer(file)
            writer.writerow(headers)
            for row in rows:
                writer.writerow([row[key] for key in headers])

    def export_attendance_csv(self, output_path: Path, filters: Filters | None = None) -> None:
        rows = self.list_attendance(filters)
        headers = ["attendance_id", "work_date", "employee_id", "name", "department", "status", "check_in", "check_out", "late_minutes"]
        with output_path.open("w", newline="", encoding="utf-8") as file:
            writer = csv.writer(file)
            writer.writerow(headers)
            for row in rows:
                writer.writerow([row[key] for key in headers])

    def _build_work_log_where(self, filters: Filters) -> tuple[str, list]:
        clauses: list[str] = []
        params: list = []
        if filters.date_from:
            clauses.append("wl.log_date >= ?")
            params.append(filters.date_from)
        if filters.date_to:
            clauses.append("wl.log_date <= ?")
            params.append(filters.date_to)
        if filters.department and filters.department != "All":
            clauses.append("e.department = ?")
            params.append(filters.department)
        if filters.employee_id and filters.employee_id != "All":
            clauses.append("e.employee_id = ?")
            params.append(filters.employee_id)
        if filters.task_type and filters.task_type != "All":
            clauses.append("wl.task_type = ?")
            params.append(filters.task_type)
        if filters.project and filters.project != "All":
            clauses.append("wl.project = ?")
            params.append(filters.project)
        return (f"WHERE {' AND '.join(clauses)}" if clauses else "", params)

    def _build_attendance_where(self, filters: Filters) -> tuple[str, list]:
        clauses: list[str] = []
        params: list = []
        if filters.date_from:
            clauses.append("a.work_date >= ?")
            params.append(filters.date_from)
        if filters.date_to:
            clauses.append("a.work_date <= ?")
            params.append(filters.date_to)
        if filters.department and filters.department != "All":
            clauses.append("e.department = ?")
            params.append(filters.department)
        if filters.employee_id and filters.employee_id != "All":
            clauses.append("e.employee_id = ?")
            params.append(filters.employee_id)
        return (f"WHERE {' AND '.join(clauses)}" if clauses else "", params)

    def _validate_date(self, value: str, label: str) -> None:
        try:
            datetime.strptime(value, "%Y-%m-%d")
        except ValueError as exc:
            raise ValueError(f"{label} must use YYYY-MM-DD format") from exc
