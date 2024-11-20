from __future__ import annotations

from http.server import BaseHTTPRequestHandler, ThreadingHTTPServer
import json
from pathlib import Path
from urllib.parse import parse_qs, urlparse
import webbrowser

from .analytics_service import AnalyticsService
from .data_store import EmployeeAnalyticsStore, EmployeePayload, Filters
from .reporting import write_html_report


ASSET_DIR = Path(__file__).resolve().parent / "web_assets"


def row_to_dict(row) -> dict:
    return dict(row)


def filters_from_query(query: dict[str, list[str]]) -> Filters:
    def value(name: str) -> str | None:
        raw = query.get(name, [""])[0].strip()
        return raw if raw and raw != "All" else None

    return Filters(
        date_from=value("date_from"),
        date_to=value("date_to"),
        department=value("department"),
        employee_id=value("employee_id"),
        task_type=value("task_type"),
        project=value("project"),
    )


def scoped_filters(filters: Filters, user: dict) -> Filters:
    if user["role"] == "admin":
        return filters
    return Filters(
        date_from=filters.date_from,
        date_to=filters.date_to,
        department=filters.department,
        employee_id=user["employee_id"],
        task_type=filters.task_type,
        project=filters.project,
    )


class EmployeeAnalyticsWebApp:
    def __init__(self, store: EmployeeAnalyticsStore):
        self.store = store
        self.analytics = AnalyticsService(store)

    def chart_payload(self, chart_type: str, metric: str, group_by: str, filters: Filters) -> dict:
        if chart_type == "bar":
            return {
                "chart_type": chart_type,
                "title": f"{metric.replace('_', ' ').title()} by {group_by.replace('_', ' ').title()}",
                "data": self.store.grouped_metric(group_by, metric, filters, limit=40),
            }
        if chart_type == "trend":
            return {
                "chart_type": chart_type,
                "title": f"Daily {metric.replace('_', ' ').title()} Trend",
                "data": self.store.daily_trend(metric, filters, limit=90),
            }
        if chart_type == "donut":
            return {
                "chart_type": chart_type,
                "title": "Attendance Mix",
                "data": self.store.attendance_breakdown(filters),
            }
        if chart_type == "heatmap":
            return {
                "chart_type": chart_type,
                "title": "Department and Task Workload",
                "data": self.store.workload_heatmap(filters),
            }
        if chart_type == "ideal_actual":
            return {
                "chart_type": chart_type,
                "title": "Actual vs Ideal Task Hours",
                "data": self.store.ideal_vs_actual(filters),
            }
        if chart_type == "sunburst":
            return {
                "chart_type": chart_type,
                "title": "Project, Group, Task, Time Sunburst",
                "data": self.store.sunburst_tree(filters),
            }
        raise ValueError("Unsupported chart type")

    def make_handler(self):
        app = self

        class Handler(BaseHTTPRequestHandler):
            def log_message(self, format, *args):  # noqa: A002
                return

            def do_GET(self):
                parsed = urlparse(self.path)
                query = parse_qs(parsed.query)
                try:
                    if parsed.path == "/":
                        self.send_file(ASSET_DIR / "index.html", "text/html; charset=utf-8")
                    elif parsed.path == "/api/me":
                        self.send_json(self.require_user())
                    elif parsed.path == "/api/options":
                        user = self.require_user()
                        options = app.store.filter_options()
                        if user["role"] != "admin":
                            options["employees"] = [f"{user['employee_id']} - {user['name']}"]
                            if user.get("department"):
                                options["departments"] = [user["department"]]
                        self.send_json(options)
                    elif parsed.path == "/api/dashboard":
                        user = self.require_user()
                        filters = scoped_filters(filters_from_query(query), user)
                        self.send_json(app.analytics.dashboard(filters))
                    elif parsed.path == "/api/chart":
                        user = self.require_user()
                        filters = scoped_filters(filters_from_query(query), user)
                        chart_type = query.get("chart_type", ["bar"])[0]
                        metric = query.get("metric", ["hours"])[0]
                        group_by = query.get("group_by", ["department"])[0]
                        self.send_json(app.chart_payload(chart_type, metric, group_by, filters))
                    elif parsed.path == "/api/summary":
                        user = self.require_user()
                        filters = scoped_filters(filters_from_query(query), user)
                        self.send_json({"summary": app.analytics.executive_summary(filters)})
                    elif parsed.path == "/api/employees":
                        user = self.require_user()
                        if user["role"] != "admin":
                            self.send_json([
                                row_to_dict(row)
                                for row in app.store.list_employees(search=user["employee_id"])
                            ])
                            return
                        self.send_json([
                            row_to_dict(row)
                            for row in app.store.list_employees(
                                department=query.get("department", ["All"])[0],
                                search=query.get("search", [""])[0],
                            )
                        ])
                    elif parsed.path == "/api/logs":
                        user = self.require_user()
                        filters = scoped_filters(filters_from_query(query), user)
                        self.send_json([row_to_dict(row) for row in app.store.list_work_logs(filters, limit=1200)])
                    elif parsed.path == "/api/attendance":
                        user = self.require_user()
                        filters = scoped_filters(filters_from_query(query), user)
                        self.send_json([row_to_dict(row) for row in app.store.list_attendance(filters, limit=1200)])
                    elif parsed.path == "/api/report":
                        user = self.require_user()
                        if user["role"] != "admin":
                            raise PermissionError("Only admins can open the full analytics report")
                        filters = scoped_filters(filters_from_query(query), user)
                        report_path = Path("/tmp/employee_analytics_report.html")
                        write_html_report(app.analytics, filters, report_path)
                        self.send_file(report_path, "text/html; charset=utf-8")
                    else:
                        self.send_error(404, "Not found")
                except PermissionError as exc:
                    self.send_json({"error": str(exc)}, status=403)
                except Exception as exc:
                    status = 401 if str(exc) == "Sign in required" else 500
                    self.send_json({"error": str(exc)}, status=status)

            def do_POST(self):
                parsed = urlparse(self.path)
                try:
                    payload = self.read_json()
                    if parsed.path == "/api/login":
                        user = app.store.authenticate(
                            payload.get("username", "").strip(),
                            payload.get("password", ""),
                        )
                        if not user:
                            self.send_json({"error": "Invalid username or password"}, status=401)
                            return
                        self.send_json(user)
                    elif parsed.path == "/api/reset-sample":
                        user = self.require_user()
                        if user["role"] != "admin":
                            raise PermissionError("Only admins can reset sample data")
                        app.store.seed_sample_data(reset=True)
                        self.send_json({"ok": True})
                    elif parsed.path == "/api/employees":
                        user = self.require_user()
                        if user["role"] != "admin":
                            raise PermissionError("Only admins can manage employees")
                        app.store.upsert_employee(
                            EmployeePayload(
                                employee_id=payload["employee_id"].strip(),
                                name=payload["name"].strip(),
                                department=payload.get("department", "General").strip() or "General",
                                role=payload.get("role", "Employee").strip() or "Employee",
                                location=payload.get("location", "Office").strip() or "Office",
                                manager=payload.get("manager", "Unassigned").strip() or "Unassigned",
                                hire_date=payload["hire_date"].strip(),
                                status=payload.get("status", "Active").strip() or "Active",
                            )
                        )
                        self.send_json({"ok": True})
                    elif parsed.path == "/api/logs":
                        user = self.require_user()
                        employee_id = payload.get("employee_id", "").strip()
                        if user["role"] != "admin":
                            employee_id = user["employee_id"]
                        app.store.add_work_log(
                            employee_id=employee_id,
                            log_date=payload["log_date"].strip(),
                            project=payload.get("project", "General").strip() or "General",
                            task_type=payload.get("task_type", "Project Work").strip() or "Project Work",
                            hours=float(payload["hours"]),
                            productivity_score=int(payload["productivity_score"]),
                            overtime_hours=float(payload.get("overtime_hours", 0)),
                            notes=payload.get("notes", "").strip(),
                        )
                        self.send_json({"ok": True})
                    elif parsed.path == "/api/attendance":
                        user = self.require_user()
                        employee_id = payload.get("employee_id", "").strip()
                        if user["role"] != "admin":
                            employee_id = user["employee_id"]
                        app.store.upsert_attendance(
                            employee_id=employee_id,
                            work_date=payload["work_date"].strip(),
                            status=payload.get("status", "Present").strip() or "Present",
                            check_in=payload.get("check_in", "").strip(),
                            check_out=payload.get("check_out", "").strip(),
                            late_minutes=int(payload.get("late_minutes", 0) or 0),
                        )
                        self.send_json({"ok": True})
                    else:
                        self.send_error(404, "Not found")
                except PermissionError as exc:
                    self.send_json({"error": str(exc)}, status=403)
                except Exception as exc:
                    status = 401 if str(exc) == "Sign in required" else 400
                    self.send_json({"error": str(exc)}, status=status)

            def do_DELETE(self):
                parsed = urlparse(self.path)
                try:
                    user = self.require_user()
                    parts = [part for part in parsed.path.split("/") if part]
                    if len(parts) == 3 and parts[:2] == ["api", "logs"]:
                        if user["role"] != "admin":
                            row = app.store.list_work_logs(Filters(employee_id=user["employee_id"]))
                            allowed_ids = {str(item["log_id"]) for item in row}
                            if parts[2] not in allowed_ids:
                                raise PermissionError("You can only delete your own work logs")
                        app.store.delete_work_log(int(parts[2]))
                        self.send_json({"ok": True})
                    elif len(parts) == 3 and parts[:2] == ["api", "employees"]:
                        if user["role"] != "admin":
                            raise PermissionError("Only admins can delete employees")
                        app.store.delete_employee(parts[2])
                        self.send_json({"ok": True})
                    else:
                        self.send_error(404, "Not found")
                except PermissionError as exc:
                    self.send_json({"error": str(exc)}, status=403)
                except Exception as exc:
                    status = 401 if str(exc) == "Sign in required" else 400
                    self.send_json({"error": str(exc)}, status=status)

            def require_user(self) -> dict:
                username = self.headers.get("X-Auth-User", "").strip()
                if not username:
                    raise RuntimeError("Sign in required")
                user = app.store.auth_user(username)
                if not user:
                    raise RuntimeError("Sign in required")
                return user

            def read_json(self) -> dict:
                length = int(self.headers.get("Content-Length", "0"))
                if not length:
                    return {}
                return json.loads(self.rfile.read(length).decode("utf-8"))

            def send_json(self, data, status: int = 200) -> None:
                body = json.dumps(data, default=str).encode("utf-8")
                self.send_response(status)
                self.send_header("Content-Type", "application/json; charset=utf-8")
                self.send_header("Content-Length", str(len(body)))
                self.end_headers()
                self.wfile.write(body)

            def send_file(self, path: Path, content_type: str) -> None:
                body = path.read_bytes()
                self.send_response(200)
                self.send_header("Content-Type", content_type)
                self.send_header("Content-Length", str(len(body)))
                self.end_headers()
                self.wfile.write(body)

        return Handler


def run_web_app(store: EmployeeAnalyticsStore, host: str, port: int, open_browser: bool = True) -> None:
    app = EmployeeAnalyticsWebApp(store)
    server = ThreadingHTTPServer((host, port), app.make_handler())
    url = f"http://{host}:{server.server_port}"
    print(f"Employee Data Analytics web app running at {url}")
    if open_browser:
        webbrowser.open(url)
    try:
        server.serve_forever()
    except KeyboardInterrupt:
        print("\nStopping server...")
    finally:
        server.server_close()
