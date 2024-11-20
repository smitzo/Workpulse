from __future__ import annotations

from datetime import date
from pathlib import Path
import tempfile
import tkinter as tk
from tkinter import filedialog, messagebox, ttk
import webbrowser

from .analytics_service import AnalyticsService
from .data_store import EmployeeAnalyticsStore, EmployeePayload, Filters
from .reporting import write_html_report


PALETTE = ["#2563eb", "#059669", "#f97316", "#7c3aed", "#dc2626", "#0891b2", "#ca8a04", "#4f46e5"]


class ChartCanvas(tk.Canvas):
    def __init__(self, parent, **kwargs):
        super().__init__(
            parent,
            bg="#ffffff",
            highlightthickness=1,
            highlightbackground="#cbd5e1",
            height=260,
            **kwargs,
        )
        self._last_draw = None
        self.bind("<Configure>", self._redraw)

    def _redraw(self, _event=None) -> None:
        if self._last_draw:
            method, args = self._last_draw
            method(*args, remember=False)

    def _title(self, title: str) -> None:
        self.create_text(16, 14, text=title, anchor="nw", font=("Segoe UI", 11, "bold"), fill="#0f172a")

    def _empty(self, title: str) -> None:
        self.delete("all")
        self._title(title)
        self.create_text(
            max(self.winfo_width(), 520) / 2,
            max(self.winfo_height(), 240) / 2,
            text="No data for this filter",
            fill="#64748b",
            font=("Segoe UI", 10),
        )


class BarChart(ChartCanvas):
    def draw(self, title: str, data: list[tuple[str, float]], value_suffix: str = "", remember: bool = True) -> None:
        if remember:
            self._last_draw = (self.draw, (title, data, value_suffix))
        self.delete("all")
        if not data:
            self._empty(title)
            return

        width = max(self.winfo_width(), 520)
        height = max(self.winfo_height(), 240)
        left, right, top, bottom = 58, 20, 44, 58
        chart_width = width - left - right
        chart_height = height - top - bottom
        max_value = max(value for _label, value in data) or 1
        gap = 12
        bar_width = max(20, (chart_width - gap * (len(data) - 1)) / len(data))

        self._title(title)
        self.create_line(left, top, left, top + chart_height, fill="#94a3b8")
        self.create_line(left, top + chart_height, width - right, top + chart_height, fill="#94a3b8")

        for index, (label, value) in enumerate(data):
            x1 = left + index * (bar_width + gap)
            x2 = min(x1 + bar_width, width - right)
            bar_height = (value / max_value) * chart_height
            y1 = top + chart_height - bar_height
            y2 = top + chart_height
            self.create_rectangle(x1, y1, x2, y2, fill=PALETTE[index % len(PALETTE)], outline="")
            self.create_text((x1 + x2) / 2, y1 - 9, text=f"{value:g}{value_suffix}", fill="#0f172a", font=("Segoe UI", 8))
            short = label if len(label) <= 13 else f"{label[:12]}..."
            self.create_text((x1 + x2) / 2, y2 + 20, text=short, fill="#334155", font=("Segoe UI", 8))


class LineChart(ChartCanvas):
    def draw(self, title: str, data: list[tuple[str, float]], value_suffix: str = "", remember: bool = True) -> None:
        if remember:
            self._last_draw = (self.draw, (title, data, value_suffix))
        self.delete("all")
        if not data:
            self._empty(title)
            return

        width = max(self.winfo_width(), 520)
        height = max(self.winfo_height(), 240)
        left, right, top, bottom = 58, 20, 44, 48
        chart_width = width - left - right
        chart_height = height - top - bottom
        values = [value for _label, value in data]
        min_value = min(values)
        max_value = max(values)
        span = max(max_value - min_value, 1)

        self._title(title)
        self.create_line(left, top, left, top + chart_height, fill="#94a3b8")
        self.create_line(left, top + chart_height, width - right, top + chart_height, fill="#94a3b8")

        points = []
        for index, (label, value) in enumerate(data):
            x = left + (index / max(len(data) - 1, 1)) * chart_width
            y = top + chart_height - ((value - min_value) / span) * chart_height
            points.extend([x, y])
            if index in {0, len(data) - 1}:
                self.create_text(x, top + chart_height + 18, text=label[5:], fill="#334155", font=("Segoe UI", 8))

        if len(points) >= 4:
            self.create_line(*points, fill="#2563eb", width=3, smooth=True)
        for x, y in zip(points[0::2], points[1::2]):
            self.create_oval(x - 3, y - 3, x + 3, y + 3, fill="#2563eb", outline="")
        self.create_text(width - right - 4, top + 2, anchor="ne", text=f"Latest {values[-1]:g}{value_suffix}", fill="#0f172a")


class DonutChart(ChartCanvas):
    def draw(self, title: str, data: list[tuple[str, float]], remember: bool = True) -> None:
        if remember:
            self._last_draw = (self.draw, (title, data))
        self.delete("all")
        if not data:
            self._empty(title)
            return

        width = max(self.winfo_width(), 520)
        height = max(self.winfo_height(), 240)
        total = sum(value for _label, value in data) or 1
        size = min(height - 74, 170)
        x1, y1 = 34, 58
        x2, y2 = x1 + size, y1 + size
        start = 90

        self._title(title)
        for index, (label, value) in enumerate(data):
            extent = value / total * 360
            self.create_arc(x1, y1, x2, y2, start=start, extent=-extent, fill=PALETTE[index % len(PALETTE)], outline="white", width=2)
            start -= extent
        inset = size * 0.28
        self.create_oval(x1 + inset, y1 + inset, x2 - inset, y2 - inset, fill="white", outline="white")
        self.create_text((x1 + x2) / 2, (y1 + y2) / 2, text=f"{total:g}", font=("Segoe UI", 15, "bold"), fill="#0f172a")

        legend_x = x2 + 34
        legend_y = y1 + 4
        for index, (label, value) in enumerate(data[:7]):
            y = legend_y + index * 24
            self.create_rectangle(legend_x, y, legend_x + 12, y + 12, fill=PALETTE[index % len(PALETTE)], outline="")
            pct = value / total * 100
            self.create_text(legend_x + 20, y + 6, anchor="w", text=f"{label}: {pct:.1f}%", fill="#334155", font=("Segoe UI", 9))


class HeatmapChart(ChartCanvas):
    def draw(self, title: str, data: list[tuple[str, str, float]], remember: bool = True) -> None:
        if remember:
            self._last_draw = (self.draw, (title, data))
        self.delete("all")
        if not data:
            self._empty(title)
            return

        width = max(self.winfo_width(), 520)
        height = max(self.winfo_height(), 240)
        departments = sorted({row[0] for row in data})
        tasks = sorted({row[1] for row in data})
        values = {(department, task): value for department, task, value in data}
        max_value = max(values.values()) or 1
        left, top, right, bottom = 118, 52, 18, 46
        cell_w = max(46, (width - left - right) / max(len(tasks), 1))
        cell_h = max(28, (height - top - bottom) / max(len(departments), 1))

        self._title(title)
        for col, task in enumerate(tasks):
            x = left + col * cell_w + cell_w / 2
            short = task if len(task) <= 11 else f"{task[:10]}..."
            self.create_text(x, top - 12, text=short, fill="#334155", font=("Segoe UI", 8))
        for row, department in enumerate(departments):
            y = top + row * cell_h + cell_h / 2
            self.create_text(left - 10, y, anchor="e", text=department, fill="#334155", font=("Segoe UI", 8))
            for col, task in enumerate(tasks):
                value = values.get((department, task), 0)
                intensity = int(245 - (value / max_value) * 135)
                color = f"#{intensity:02x}{max(120, intensity - 25):02x}ff"
                x1 = left + col * cell_w
                y1 = top + row * cell_h
                self.create_rectangle(x1, y1, x1 + cell_w - 3, y1 + cell_h - 3, fill=color, outline="white")
                if value:
                    self.create_text(x1 + cell_w / 2, y1 + cell_h / 2, text=f"{value:g}", fill="#0f172a", font=("Segoe UI", 8, "bold"))


class EmployeeAnalyticsApp(tk.Tk):
    def __init__(self, store: EmployeeAnalyticsStore, sample_mode: bool = False):
        super().__init__()
        self.store = store
        self.analytics = AnalyticsService(store)
        self.sample_mode = sample_mode
        self.options: dict[str, list[str]] = {}

        self.title("Employee Data Analytics")
        self.geometry("1360x860")
        self.minsize(1120, 720)
        self.configure(bg="#e2e8f0")

        self.style = ttk.Style(self)
        self.style.theme_use("clam")
        self.style.configure("TNotebook", background="#e2e8f0", borderwidth=0)
        self.style.configure("TNotebook.Tab", padding=(14, 8), font=("Segoe UI", 10, "bold"))
        self.style.configure("Treeview", rowheight=27, font=("Segoe UI", 9))
        self.style.configure("Treeview.Heading", font=("Segoe UI", 9, "bold"))
        self.style.configure("TLabelframe.Label", font=("Segoe UI", 10, "bold"))

        self._build_variables()
        self._build_layout()
        self.refresh_all()

    def _build_variables(self) -> None:
        window = self.store.date_window(30)
        self.date_from_var = tk.StringVar(value=window.date_from or "")
        self.date_to_var = tk.StringVar(value=window.date_to or "")
        self.department_var = tk.StringVar(value="All")
        self.employee_filter_var = tk.StringVar(value="All")
        self.task_filter_var = tk.StringVar(value="All")
        self.project_filter_var = tk.StringVar(value="All")
        self.employee_search_var = tk.StringVar()

        self.log_employee_var = tk.StringVar()
        self.log_date_var = tk.StringVar(value=date.today().isoformat())
        self.log_project_var = tk.StringVar(value="Demo")
        self.log_task_var = tk.StringVar(value="Project Work")
        self.log_hours_var = tk.StringVar(value="7.5")
        self.log_score_var = tk.StringVar(value="88")
        self.log_overtime_var = tk.StringVar(value="0")
        self.log_notes_var = tk.StringVar(value="Added from demo form")

        self.emp_id_var = tk.StringVar()
        self.emp_name_var = tk.StringVar()
        self.emp_dept_var = tk.StringVar(value="Engineering")
        self.emp_role_var = tk.StringVar()
        self.emp_location_var = tk.StringVar()
        self.emp_manager_var = tk.StringVar()
        self.emp_hire_var = tk.StringVar(value=date.today().isoformat())
        self.emp_status_var = tk.StringVar(value="Active")

        self.att_employee_var = tk.StringVar()
        self.att_date_var = tk.StringVar(value=date.today().isoformat())
        self.att_status_var = tk.StringVar(value="Present")
        self.att_check_in_var = tk.StringVar(value="09:30")
        self.att_check_out_var = tk.StringVar(value="18:00")
        self.att_late_var = tk.StringVar(value="0")

    def _build_layout(self) -> None:
        self._build_header()
        self._build_filter_bar()

        self.notebook = ttk.Notebook(self)
        self.notebook.pack(fill="both", expand=True, padx=12, pady=12)

        self.dashboard_tab = tk.Frame(self.notebook, bg="#f8fafc")
        self.graphs_tab = tk.Frame(self.notebook, bg="#f8fafc")
        self.employees_tab = tk.Frame(self.notebook, bg="#f8fafc")
        self.logs_tab = tk.Frame(self.notebook, bg="#f8fafc")
        self.attendance_tab = tk.Frame(self.notebook, bg="#f8fafc")
        self.insights_tab = tk.Frame(self.notebook, bg="#f8fafc")

        self.notebook.add(self.dashboard_tab, text="Dashboard")
        self.notebook.add(self.graphs_tab, text="Graphs")
        self.notebook.add(self.employees_tab, text="Employees")
        self.notebook.add(self.logs_tab, text="Work Logs")
        self.notebook.add(self.attendance_tab, text="Attendance")
        self.notebook.add(self.insights_tab, text="Insights")

        self._build_dashboard_tab()
        self._build_graphs_tab()
        self._build_employees_tab()
        self._build_logs_tab()
        self._build_attendance_tab()
        self._build_insights_tab()

    def _build_header(self) -> None:
        header = tk.Frame(self, bg="#0f172a", height=82)
        header.pack(side="top", fill="x")
        header.pack_propagate(False)

        title_frame = tk.Frame(header, bg="#0f172a")
        title_frame.pack(side="left", padx=20)
        tk.Label(
            title_frame,
            text="Employee Data Analytics",
            bg="#0f172a",
            fg="white",
            font=("Segoe UI", 20, "bold"),
        ).pack(anchor="w", pady=(12, 0))
        mode_text = "Sample data mode enabled" if self.sample_mode else "SQLite local data mode"
        tk.Label(title_frame, text=mode_text, bg="#0f172a", fg="#cbd5e1", font=("Segoe UI", 10)).pack(anchor="w")

        actions = tk.Frame(header, bg="#0f172a")
        actions.pack(side="right", padx=18)
        ttk.Button(actions, text="Load Sample Data", command=self.load_sample_data).pack(side="left", padx=4)
        ttk.Button(actions, text="HTML Report", command=self.open_html_report).pack(side="left", padx=4)
        ttk.Button(actions, text="Export Logs", command=self.export_logs_csv).pack(side="left", padx=4)
        ttk.Button(actions, text="Refresh", command=self.refresh_all).pack(side="left", padx=4)

    def _build_filter_bar(self) -> None:
        filter_bar = tk.Frame(self, bg="#f1f5f9", padx=14, pady=10)
        filter_bar.pack(side="top", fill="x")
        self._filter_entry(filter_bar, "From", self.date_from_var, 11)
        self._filter_entry(filter_bar, "To", self.date_to_var, 11)
        self.department_menu = self._filter_menu(filter_bar, "Department", self.department_var, ["All"], 14)
        self.employee_menu = self._filter_menu(filter_bar, "Employee", self.employee_filter_var, ["All"], 24)
        self.task_menu = self._filter_menu(filter_bar, "Task", self.task_filter_var, ["All"], 17)
        self.project_menu = self._filter_menu(filter_bar, "Project", self.project_filter_var, ["All"], 17)
        ttk.Button(filter_bar, text="Apply", command=self.refresh_all).pack(side="left", padx=(10, 4))
        ttk.Button(filter_bar, text="Last 30 Days", command=self.set_last_30_days).pack(side="left", padx=4)
        ttk.Button(filter_bar, text="Clear", command=self.clear_filters).pack(side="left", padx=4)

    def _build_dashboard_tab(self) -> None:
        self.kpi_frame = tk.Frame(self.dashboard_tab, bg="#f8fafc")
        self.kpi_frame.pack(fill="x", padx=12, pady=12)
        self.kpi_labels: dict[str, tk.Label] = {}
        for key, title in [
            ("total_employees", "Employees"),
            ("total_hours", "Hours"),
            ("avg_productivity", "Productivity"),
            ("attendance_rate", "Attendance"),
            ("overtime_hours", "Overtime"),
            ("absence_count", "Absences"),
            ("late_minutes", "Late Minutes"),
            ("work_logs", "Work Logs"),
        ]:
            frame = tk.Frame(self.kpi_frame, bg="white", highlightbackground="#cbd5e1", highlightthickness=1, width=150, height=78)
            frame.pack(side="left", padx=5, fill="x", expand=True)
            frame.pack_propagate(False)
            tk.Label(frame, text=title, bg="white", fg="#64748b", font=("Segoe UI", 9, "bold")).pack(anchor="w", padx=10, pady=(10, 0))
            value_label = tk.Label(frame, text="0", bg="white", fg="#0f172a", font=("Segoe UI", 17, "bold"))
            value_label.pack(anchor="w", padx=10)
            self.kpi_labels[key] = value_label

        body = tk.Frame(self.dashboard_tab, bg="#f8fafc")
        body.pack(fill="both", expand=True, padx=12, pady=(0, 12))
        body.columnconfigure(0, weight=1)
        body.columnconfigure(1, weight=1)
        body.rowconfigure(0, weight=1)
        body.rowconfigure(1, weight=1)

        self.hours_chart = BarChart(body)
        self.productivity_chart = BarChart(body)
        self.hours_trend_chart = LineChart(body)
        self.attendance_donut = DonutChart(body)
        self.hours_chart.grid(row=0, column=0, sticky="nsew", padx=6, pady=6)
        self.productivity_chart.grid(row=0, column=1, sticky="nsew", padx=6, pady=6)
        self.hours_trend_chart.grid(row=1, column=0, sticky="nsew", padx=6, pady=6)
        self.attendance_donut.grid(row=1, column=1, sticky="nsew", padx=6, pady=6)

    def _build_graphs_tab(self) -> None:
        body = tk.Frame(self.graphs_tab, bg="#f8fafc")
        body.pack(fill="both", expand=True, padx=12, pady=12)
        for index in range(2):
            body.columnconfigure(index, weight=1)
            body.rowconfigure(index, weight=1)

        self.task_chart = BarChart(body)
        self.overtime_chart = BarChart(body)
        self.productivity_trend_chart = LineChart(body)
        self.heatmap_chart = HeatmapChart(body)
        self.task_chart.grid(row=0, column=0, sticky="nsew", padx=6, pady=6)
        self.overtime_chart.grid(row=0, column=1, sticky="nsew", padx=6, pady=6)
        self.productivity_trend_chart.grid(row=1, column=0, sticky="nsew", padx=6, pady=6)
        self.heatmap_chart.grid(row=1, column=1, sticky="nsew", padx=6, pady=6)

    def _build_employees_tab(self) -> None:
        panel = tk.Frame(self.employees_tab, bg="#f8fafc")
        panel.pack(fill="x", padx=12, pady=12)

        search_bar = tk.Frame(panel, bg="#f8fafc")
        search_bar.pack(fill="x", pady=(0, 8))
        tk.Label(search_bar, text="Search", bg="#f8fafc", fg="#334155", font=("Segoe UI", 9, "bold")).pack(side="left")
        search = ttk.Entry(search_bar, textvariable=self.employee_search_var, width=30)
        search.pack(side="left", padx=8)
        search.bind("<Return>", lambda _event: self.refresh_employees())
        ttk.Button(search_bar, text="Search", command=self.refresh_employees).pack(side="left", padx=4)
        ttk.Button(search_bar, text="Export Employees", command=self.export_employees_csv).pack(side="left", padx=4)

        form = ttk.LabelFrame(panel, text="Employee")
        form.pack(fill="x")
        for index in range(8):
            form.columnconfigure(index, weight=1)
        self._grid_entry(form, "ID", self.emp_id_var, 0, 0)
        self._grid_entry(form, "Name", self.emp_name_var, 0, 2)
        self._grid_entry(form, "Department", self.emp_dept_var, 0, 4)
        self._grid_entry(form, "Role", self.emp_role_var, 0, 6)
        self._grid_entry(form, "Location", self.emp_location_var, 1, 0)
        self._grid_entry(form, "Manager", self.emp_manager_var, 1, 2)
        self._grid_entry(form, "Hire Date", self.emp_hire_var, 1, 4)
        self._grid_combo(form, "Status", self.emp_status_var, ["Active", "On Leave", "Inactive"], 1, 6)
        ttk.Button(form, text="New", command=self.clear_employee_form).grid(row=2, column=0, padx=6, pady=8, sticky="ew")
        ttk.Button(form, text="Save", command=self.save_employee).grid(row=2, column=1, padx=6, pady=8, sticky="ew")
        ttk.Button(form, text="Load Selected", command=self.load_selected_employee).grid(row=2, column=2, padx=6, pady=8, sticky="ew")
        ttk.Button(form, text="Delete", command=self.delete_selected_employee).grid(row=2, column=3, padx=6, pady=8, sticky="ew")

        self.employee_tree = self._make_tree(
            self.employees_tab,
            ("ID", "Name", "Department", "Role", "Location", "Manager", "Hire Date", "Status"),
        )
        self.employee_tree.bind("<Double-1>", lambda _event: self.load_selected_employee())

    def _build_logs_tab(self) -> None:
        form = ttk.LabelFrame(self.logs_tab, text="Work Log")
        form.pack(fill="x", padx=12, pady=12)
        self.log_employee_menu = self._grid_combo(form, "Employee", self.log_employee_var, [""], 0, 0, width=26)
        self._grid_entry(form, "Date", self.log_date_var, 0, 2, width=12)
        self._grid_entry(form, "Project", self.log_project_var, 0, 4, width=18)
        self._grid_entry(form, "Task", self.log_task_var, 0, 6, width=16)
        self._grid_entry(form, "Hours", self.log_hours_var, 1, 0, width=8)
        self._grid_entry(form, "Score", self.log_score_var, 1, 2, width=8)
        self._grid_entry(form, "Overtime", self.log_overtime_var, 1, 4, width=8)
        self._grid_entry(form, "Notes", self.log_notes_var, 1, 6, width=28)
        ttk.Button(form, text="Add Log", command=self.add_log).grid(row=2, column=0, padx=6, pady=8, sticky="ew")
        ttk.Button(form, text="Delete Selected", command=self.delete_selected_log).grid(row=2, column=1, padx=6, pady=8, sticky="ew")
        ttk.Button(form, text="Export Logs", command=self.export_logs_csv).grid(row=2, column=2, padx=6, pady=8, sticky="ew")

        self.log_tree = self._make_tree(
            self.logs_tab,
            ("Log ID", "Date", "Emp ID", "Name", "Department", "Project", "Task", "Hours", "Score", "Overtime", "Notes"),
        )

    def _build_attendance_tab(self) -> None:
        form = ttk.LabelFrame(self.attendance_tab, text="Attendance")
        form.pack(fill="x", padx=12, pady=12)
        self.att_employee_menu = self._grid_combo(form, "Employee", self.att_employee_var, [""], 0, 0, width=26)
        self._grid_entry(form, "Date", self.att_date_var, 0, 2, width=12)
        self._grid_combo(form, "Status", self.att_status_var, ["Present", "Leave", "Absent"], 0, 4, width=12)
        self._grid_entry(form, "Check In", self.att_check_in_var, 0, 6, width=10)
        self._grid_entry(form, "Check Out", self.att_check_out_var, 1, 0, width=10)
        self._grid_entry(form, "Late Min", self.att_late_var, 1, 2, width=8)
        ttk.Button(form, text="Save Attendance", command=self.save_attendance).grid(row=2, column=0, padx=6, pady=8, sticky="ew")
        ttk.Button(form, text="Export Attendance", command=self.export_attendance_csv).grid(row=2, column=1, padx=6, pady=8, sticky="ew")

        lower = tk.Frame(self.attendance_tab, bg="#f8fafc")
        lower.pack(fill="both", expand=True, padx=12, pady=(0, 12))
        lower.columnconfigure(0, weight=2)
        lower.columnconfigure(1, weight=1)
        lower.rowconfigure(0, weight=1)

        table_frame = tk.Frame(lower, bg="#f8fafc")
        table_frame.grid(row=0, column=0, sticky="nsew", padx=(0, 8))
        self.attendance_tree = self._make_tree(
            table_frame,
            ("ID", "Date", "Emp ID", "Name", "Department", "Status", "Check In", "Check Out", "Late Min"),
            outer_pack=False,
        )
        chart_frame = tk.Frame(lower, bg="#f8fafc")
        chart_frame.grid(row=0, column=1, sticky="nsew")
        chart_frame.rowconfigure(0, weight=1)
        chart_frame.rowconfigure(1, weight=1)
        chart_frame.columnconfigure(0, weight=1)
        self.attendance_tab_donut = DonutChart(chart_frame)
        self.late_chart = BarChart(chart_frame)
        self.attendance_tab_donut.grid(row=0, column=0, sticky="nsew", pady=(0, 6))
        self.late_chart.grid(row=1, column=0, sticky="nsew", pady=(6, 0))

    def _build_insights_tab(self) -> None:
        top = tk.Frame(self.insights_tab, bg="#f8fafc")
        top.pack(fill="both", expand=True, padx=12, pady=12)
        top.columnconfigure(0, weight=1)
        top.columnconfigure(1, weight=2)
        top.rowconfigure(0, weight=1)

        left = tk.Frame(top, bg="#f8fafc")
        left.grid(row=0, column=0, sticky="nsew", padx=(0, 8))
        left.rowconfigure(1, weight=1)
        ttk.Button(left, text="Open HTML Report", command=self.open_html_report).grid(row=0, column=0, sticky="ew", pady=(0, 8))
        self.insight_text = tk.Text(left, wrap="word", height=16, font=("Segoe UI", 10), bg="white", relief="solid", bd=1)
        self.insight_text.grid(row=1, column=0, sticky="nsew")

        right = tk.Frame(top, bg="#f8fafc")
        right.grid(row=0, column=1, sticky="nsew")
        right.rowconfigure(0, weight=1)
        right.columnconfigure(0, weight=1)
        self.performance_tree = self._make_tree(
            right,
            ("ID", "Name", "Department", "Role", "Logs", "Hours", "Avg Score", "Daily Hrs", "Overtime"),
            outer_pack=False,
        )

    def _filter_entry(self, parent, label: str, variable: tk.StringVar, width: int) -> None:
        tk.Label(parent, text=label, bg="#f1f5f9", fg="#334155", font=("Segoe UI", 9, "bold")).pack(side="left", padx=(8, 4))
        ttk.Entry(parent, textvariable=variable, width=width).pack(side="left")

    def _filter_menu(self, parent, label: str, variable: tk.StringVar, values: list[str], width: int) -> ttk.Combobox:
        tk.Label(parent, text=label, bg="#f1f5f9", fg="#334155", font=("Segoe UI", 9, "bold")).pack(side="left", padx=(10, 4))
        menu = ttk.Combobox(parent, textvariable=variable, values=values, width=width, state="readonly")
        menu.pack(side="left")
        return menu

    def _grid_entry(self, parent, label: str, variable: tk.StringVar, row: int, column: int, width: int = 18) -> ttk.Entry:
        ttk.Label(parent, text=label).grid(row=row, column=column, padx=(8, 4), pady=6, sticky="e")
        entry = ttk.Entry(parent, textvariable=variable, width=width)
        entry.grid(row=row, column=column + 1, padx=(0, 8), pady=6, sticky="ew")
        return entry

    def _grid_combo(
        self,
        parent,
        label: str,
        variable: tk.StringVar,
        values: list[str],
        row: int,
        column: int,
        width: int = 18,
    ) -> ttk.Combobox:
        ttk.Label(parent, text=label).grid(row=row, column=column, padx=(8, 4), pady=6, sticky="e")
        combo = ttk.Combobox(parent, textvariable=variable, values=values, width=width, state="readonly")
        combo.grid(row=row, column=column + 1, padx=(0, 8), pady=6, sticky="ew")
        return combo

    def _make_tree(self, parent, columns: tuple[str, ...], outer_pack: bool = True) -> ttk.Treeview:
        frame = tk.Frame(parent, bg="#f8fafc")
        if outer_pack:
            frame.pack(fill="both", expand=True, padx=12, pady=(0, 12))
        else:
            frame.pack(fill="both", expand=True)

        tree = ttk.Treeview(frame, columns=columns, show="headings")
        for column in columns:
            width = 90
            if column in {"Name", "Project", "Task", "Notes", "Role"}:
                width = 150
            if column in {"Notes"}:
                width = 220
            tree.heading(column, text=column)
            tree.column(column, width=width, anchor="w")

        y_scroll = ttk.Scrollbar(frame, orient="vertical", command=tree.yview)
        x_scroll = ttk.Scrollbar(frame, orient="horizontal", command=tree.xview)
        tree.configure(yscrollcommand=y_scroll.set, xscrollcommand=x_scroll.set)
        y_scroll.pack(side="right", fill="y")
        x_scroll.pack(side="bottom", fill="x")
        tree.pack(side="left", fill="both", expand=True)
        return tree

    def current_filters(self) -> Filters:
        employee = self.employee_filter_var.get()
        employee_id = employee.split(" - ", 1)[0] if employee and employee != "All" else None
        return Filters(
            date_from=self.date_from_var.get().strip() or None,
            date_to=self.date_to_var.get().strip() or None,
            department=self.department_var.get() if self.department_var.get() != "All" else None,
            employee_id=employee_id,
            task_type=self.task_filter_var.get() if self.task_filter_var.get() != "All" else None,
            project=self.project_filter_var.get() if self.project_filter_var.get() != "All" else None,
        )

    def refresh_all(self) -> None:
        try:
            self.options = self.store.filter_options()
            self._refresh_menus()
            self.refresh_dashboard()
            self.refresh_graphs()
            self.refresh_employees()
            self.refresh_logs()
            self.refresh_attendance()
            self.refresh_insights()
        except Exception as exc:
            messagebox.showerror("Refresh failed", str(exc))

    def _refresh_menus(self) -> None:
        departments = self.options.get("departments", ["All"])
        employees = self.options.get("employees", ["All"])
        tasks = self.options.get("task_types", ["All"])
        projects = self.options.get("projects", ["All"])
        self.department_menu.configure(values=departments)
        self.employee_menu.configure(values=employees)
        self.task_menu.configure(values=tasks)
        self.project_menu.configure(values=projects)
        self.log_employee_menu.configure(values=employees[1:] if len(employees) > 1 else [])
        self.att_employee_menu.configure(values=employees[1:] if len(employees) > 1 else [])
        if not self.log_employee_var.get() and len(employees) > 1:
            self.log_employee_var.set(employees[1])
        if not self.att_employee_var.get() and len(employees) > 1:
            self.att_employee_var.set(employees[1])

    def refresh_dashboard(self) -> None:
        data = self.analytics.dashboard(self.current_filters())
        summary = data["summary"]
        value_formats = {
            "total_employees": "{:.0f}",
            "total_hours": "{:.1f}",
            "avg_productivity": "{:.1f}%",
            "attendance_rate": "{:.1f}%",
            "overtime_hours": "{:.1f}",
            "absence_count": "{:.0f}",
            "late_minutes": "{:.0f}",
            "work_logs": "{:.0f}",
        }
        for key, label in self.kpi_labels.items():
            label.configure(text=value_formats[key].format(summary[key]))
        self.after(50, lambda: self.hours_chart.draw("Hours by Department", data["hours_by_department"]))
        self.after(50, lambda: self.productivity_chart.draw("Productivity by Department", data["productivity_by_department"], "%"))
        self.after(50, lambda: self.hours_trend_chart.draw("Daily Hours Trend", data["hours_trend"]))
        self.after(50, lambda: self.attendance_donut.draw("Attendance Mix", data["attendance_breakdown"]))

    def refresh_graphs(self) -> None:
        data = self.analytics.dashboard(self.current_filters())
        self.after(50, lambda: self.task_chart.draw("Hours by Task Type", data["hours_by_task"]))
        self.after(50, lambda: self.overtime_chart.draw("Overtime by Department", data["overtime_by_department"]))
        self.after(50, lambda: self.productivity_trend_chart.draw("Daily Productivity Trend", data["productivity_trend"], "%"))
        self.after(50, lambda: self.heatmap_chart.draw("Workload Heatmap", data["workload_heatmap"]))

    def refresh_employees(self) -> None:
        rows = self.store.list_employees(
            department=self.department_var.get(),
            search=self.employee_search_var.get().strip(),
        )
        self._replace_tree_rows(
            self.employee_tree,
            [
                (
                    row["employee_id"],
                    row["name"],
                    row["department"],
                    row["role"],
                    row["location"],
                    row["manager"],
                    row["hire_date"],
                    row["status"],
                )
                for row in rows
            ],
        )

    def refresh_logs(self) -> None:
        rows = self.store.list_work_logs(self.current_filters(), limit=700)
        self._replace_tree_rows(
            self.log_tree,
            [
                (
                    row["log_id"],
                    row["log_date"],
                    row["employee_id"],
                    row["name"],
                    row["department"],
                    row["project"],
                    row["task_type"],
                    f"{row['hours']:.2f}",
                    row["productivity_score"],
                    f"{row['overtime_hours']:.2f}",
                    row["notes"] or "",
                )
                for row in rows
            ],
        )

    def refresh_attendance(self) -> None:
        rows = self.store.list_attendance(self.current_filters(), limit=700)
        self._replace_tree_rows(
            self.attendance_tree,
            [
                (
                    row["attendance_id"],
                    row["work_date"],
                    row["employee_id"],
                    row["name"],
                    row["department"],
                    row["status"],
                    row["check_in"],
                    row["check_out"],
                    row["late_minutes"],
                )
                for row in rows
            ],
        )
        data = self.analytics.dashboard(self.current_filters())
        self.after(50, lambda: self.attendance_tab_donut.draw("Attendance Mix", data["attendance_breakdown"]))
        self.after(50, lambda: self.late_chart.draw("Average Late Minutes", data["late_by_department"]))

    def refresh_insights(self) -> None:
        filters = self.current_filters()
        insights = self.analytics.insights(filters)
        summary = self.analytics.executive_summary(filters)
        self.insight_text.configure(state="normal")
        self.insight_text.delete("1.0", "end")
        self.insight_text.insert("end", "Executive Summary\n", ("title",))
        self.insight_text.insert("end", f"{summary}\n\n")
        self.insight_text.insert("end", "Generated Insights\n", ("title",))
        for insight in insights:
            self.insight_text.insert("end", f"{insight.title}\n", ("subtitle",))
            self.insight_text.insert("end", f"{insight.detail}\n\n")
        self.insight_text.tag_configure("title", font=("Segoe UI", 12, "bold"), foreground="#0f172a")
        self.insight_text.tag_configure("subtitle", font=("Segoe UI", 10, "bold"), foreground="#1d4ed8")
        self.insight_text.configure(state="disabled")

        rows = self.store.employee_performance(filters)
        self._replace_tree_rows(
            self.performance_tree,
            [
                (
                    row["employee_id"],
                    row["name"],
                    row["department"],
                    row["role"],
                    row["log_count"],
                    row["total_hours"],
                    row["avg_productivity"],
                    row["avg_daily_hours"],
                    row["overtime_hours"],
                )
                for row in rows
            ],
        )

    def _replace_tree_rows(self, tree: ttk.Treeview, rows: list[tuple]) -> None:
        for item in tree.get_children():
            tree.delete(item)
        for row in rows:
            tree.insert("", "end", values=row)

    def set_last_30_days(self) -> None:
        window = self.store.date_window(30)
        self.date_from_var.set(window.date_from or "")
        self.date_to_var.set(window.date_to or "")
        self.refresh_all()

    def clear_filters(self) -> None:
        self.date_from_var.set("")
        self.date_to_var.set("")
        self.department_var.set("All")
        self.employee_filter_var.set("All")
        self.task_filter_var.set("All")
        self.project_filter_var.set("All")
        self.refresh_all()

    def load_sample_data(self) -> None:
        if not messagebox.askyesno("Load sample data", "Replace local data with fresh sample demo data?"):
            return
        self.store.seed_sample_data(reset=True)
        self.sample_mode = True
        self.refresh_all()
        messagebox.showinfo("Sample data loaded", "Demo data is ready.")

    def clear_employee_form(self) -> None:
        self.emp_id_var.set("")
        self.emp_name_var.set("")
        self.emp_dept_var.set("Engineering")
        self.emp_role_var.set("")
        self.emp_location_var.set("")
        self.emp_manager_var.set("")
        self.emp_hire_var.set(date.today().isoformat())
        self.emp_status_var.set("Active")

    def load_selected_employee(self) -> None:
        selected = self.employee_tree.selection()
        if not selected:
            messagebox.showwarning("No row selected", "Select an employee first.")
            return
        values = self.employee_tree.item(selected[0], "values")
        self.emp_id_var.set(values[0])
        self.emp_name_var.set(values[1])
        self.emp_dept_var.set(values[2])
        self.emp_role_var.set(values[3])
        self.emp_location_var.set(values[4])
        self.emp_manager_var.set(values[5])
        self.emp_hire_var.set(values[6])
        self.emp_status_var.set(values[7])

    def save_employee(self) -> None:
        try:
            if not self.emp_id_var.get().strip() or not self.emp_name_var.get().strip():
                raise ValueError("Employee ID and name are required")
            self.store.upsert_employee(
                EmployeePayload(
                    employee_id=self.emp_id_var.get().strip(),
                    name=self.emp_name_var.get().strip(),
                    department=self.emp_dept_var.get().strip() or "General",
                    role=self.emp_role_var.get().strip() or "Employee",
                    location=self.emp_location_var.get().strip() or "Office",
                    manager=self.emp_manager_var.get().strip() or "Unassigned",
                    hire_date=self.emp_hire_var.get().strip(),
                    status=self.emp_status_var.get().strip() or "Active",
                )
            )
            self.refresh_all()
            messagebox.showinfo("Saved", "Employee saved.")
        except Exception as exc:
            messagebox.showerror("Cannot save employee", str(exc))

    def delete_selected_employee(self) -> None:
        selected = self.employee_tree.selection()
        if not selected:
            messagebox.showwarning("No row selected", "Select an employee first.")
            return
        values = self.employee_tree.item(selected[0], "values")
        employee_id = values[0]
        if messagebox.askyesno("Delete employee", f"Delete employee {employee_id} and related records?"):
            self.store.delete_employee(employee_id)
            self.refresh_all()

    def add_log(self) -> None:
        try:
            employee_value = self.log_employee_var.get()
            if not employee_value or " - " not in employee_value:
                raise ValueError("Select an employee")
            employee_id = employee_value.split(" - ", 1)[0]
            hours = float(self.log_hours_var.get())
            score = int(self.log_score_var.get())
            overtime = float(self.log_overtime_var.get())
            if not (0 <= score <= 100):
                raise ValueError("Score must be between 0 and 100")
            if hours < 0 or overtime < 0:
                raise ValueError("Hours cannot be negative")
            self.store.add_work_log(
                employee_id=employee_id,
                log_date=self.log_date_var.get().strip(),
                project=self.log_project_var.get().strip() or "General",
                task_type=self.log_task_var.get().strip() or "Project Work",
                hours=hours,
                productivity_score=score,
                overtime_hours=overtime,
                notes=self.log_notes_var.get().strip(),
            )
            self.refresh_all()
            messagebox.showinfo("Saved", "Work log added.")
        except Exception as exc:
            messagebox.showerror("Cannot add log", str(exc))

    def delete_selected_log(self) -> None:
        selected = self.log_tree.selection()
        if not selected:
            messagebox.showwarning("No row selected", "Select a work log first.")
            return
        values = self.log_tree.item(selected[0], "values")
        log_id = int(values[0])
        if messagebox.askyesno("Delete work log", f"Delete work log #{log_id}?"):
            self.store.delete_work_log(log_id)
            self.refresh_all()

    def save_attendance(self) -> None:
        try:
            employee_value = self.att_employee_var.get()
            if not employee_value or " - " not in employee_value:
                raise ValueError("Select an employee")
            late_minutes = int(self.att_late_var.get() or 0)
            if late_minutes < 0:
                raise ValueError("Late minutes cannot be negative")
            self.store.upsert_attendance(
                employee_id=employee_value.split(" - ", 1)[0],
                work_date=self.att_date_var.get().strip(),
                status=self.att_status_var.get().strip() or "Present",
                check_in=self.att_check_in_var.get().strip(),
                check_out=self.att_check_out_var.get().strip(),
                late_minutes=late_minutes,
            )
            self.refresh_all()
            messagebox.showinfo("Saved", "Attendance saved.")
        except Exception as exc:
            messagebox.showerror("Cannot save attendance", str(exc))

    def export_logs_csv(self) -> None:
        output = filedialog.asksaveasfilename(
            title="Export work logs",
            defaultextension=".csv",
            filetypes=[("CSV files", "*.csv"), ("All files", "*.*")],
        )
        if output:
            self.store.export_work_logs_csv(Path(output), self.current_filters())
            messagebox.showinfo("Export complete", f"Work logs exported to:\n{output}")

    def export_employees_csv(self) -> None:
        output = filedialog.asksaveasfilename(
            title="Export employees",
            defaultextension=".csv",
            filetypes=[("CSV files", "*.csv"), ("All files", "*.*")],
        )
        if output:
            self.store.export_employees_csv(Path(output))
            messagebox.showinfo("Export complete", f"Employees exported to:\n{output}")

    def export_attendance_csv(self) -> None:
        output = filedialog.asksaveasfilename(
            title="Export attendance",
            defaultextension=".csv",
            filetypes=[("CSV files", "*.csv"), ("All files", "*.*")],
        )
        if output:
            self.store.export_attendance_csv(Path(output), self.current_filters())
            messagebox.showinfo("Export complete", f"Attendance exported to:\n{output}")

    def open_html_report(self) -> None:
        output_path = Path(tempfile.gettempdir()) / "employee_analytics_report.html"
        write_html_report(self.analytics, self.current_filters(), output_path)
        webbrowser.open(output_path.as_uri())
