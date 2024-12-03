from __future__ import annotations

from datetime import date, datetime, timedelta
import random


DEPARTMENTS = ["Engineering", "Sales", "Operations", "HR", "Finance", "Support"]
TASK_TYPES = ["Project Work", "Client Support", "Training", "Documentation", "Planning", "Review"]
PROJECTS = ["Payroll Revamp", "CRM Rollout", "Hiring Sprint", "Q2 Forecast", "Helpdesk SLA", "Data Quality"]

WORK_GROUPS = {
    "Delivery": {
        "color": "#2563eb",
        "items": ["Project Work", "Client Support"],
    },
    "Enablement": {
        "color": "#059669",
        "items": ["Training", "Documentation"],
    },
    "Governance": {
        "color": "#f97316",
        "items": ["Planning", "Review"],
    },
}

IDEAL_TIMES = [
    ("Project Work", 7.2),
    ("Client Support", 6.4),
    ("Training", 4.0),
    ("Documentation", 5.5),
    ("Planning", 3.5),
    ("Review", 4.2),
]

USERS = [
    ("admin", "admin123", "admin", None),
    ("EMP001", "pass123", "employee", "EMP001"),
    ("EMP002", "pass123", "employee", "EMP002"),
    ("EMP003", "pass123", "employee", "EMP003"),
]

EMPLOYEES = [
    ("EMP001", "Aarav Sharma", "Engineering", "Backend Developer", "Bengaluru", "Priya Menon", "2022-03-14", "Active"),
    ("EMP002", "Meera Iyer", "Engineering", "QA Analyst", "Bengaluru", "Priya Menon", "2021-11-08", "Active"),
    ("EMP003", "Kabir Khan", "Sales", "Account Executive", "Mumbai", "Rohan Das", "2020-07-20", "Active"),
    ("EMP004", "Nisha Patel", "Operations", "Process Lead", "Ahmedabad", "Anita Rao", "2019-05-02", "Active"),
    ("EMP005", "Rohan Das", "Sales", "Sales Manager", "Mumbai", "Anita Rao", "2018-09-17", "Active"),
    ("EMP006", "Priya Menon", "Engineering", "Engineering Manager", "Bengaluru", "Anita Rao", "2017-01-30", "Active"),
    ("EMP007", "Tanvi Shah", "HR", "Talent Partner", "Pune", "Anita Rao", "2022-12-01", "Active"),
    ("EMP008", "Dev Malhotra", "Finance", "Financial Analyst", "Delhi", "Anita Rao", "2021-04-12", "Active"),
    ("EMP009", "Isha Verma", "Support", "Support Specialist", "Hyderabad", "Anita Rao", "2023-06-05", "Active"),
    ("EMP010", "Arjun Nair", "Operations", "Inventory Analyst", "Chennai", "Anita Rao", "2020-02-24", "Active"),
    ("EMP011", "Sara Thomas", "Support", "Customer Success Lead", "Hyderabad", "Anita Rao", "2019-10-10", "Active"),
    ("EMP012", "Vikram Rao", "Finance", "Payroll Specialist", "Delhi", "Anita Rao", "2023-01-16", "On Leave"),
]


def build_sample_dataset(today: date | None = None) -> dict[str, list[tuple]]:
    """Return deterministic employee, activity, and attendance sample rows."""
    today = today or date.today()
    rng = random.Random(42)
    logs: list[tuple] = []
    attendance: list[tuple] = []
    start_day = today - timedelta(days=74)

    department_bias = {
        "Engineering": (7.6, 88),
        "Sales": (7.1, 82),
        "Operations": (7.4, 84),
        "HR": (6.8, 86),
        "Finance": (7.2, 85),
        "Support": (7.5, 80),
    }

    for day_index in range(75):
        work_day = start_day + timedelta(days=day_index)
        if work_day.weekday() >= 5:
            continue

        for employee in EMPLOYEES:
            employee_id, _name, department, *_ = employee
            base_hours, base_score = department_bias[department]
            leave_roll = rng.random()
            if employee_id == "EMP012" and day_index > 45:
                status = "Leave"
            elif leave_roll < 0.045:
                status = "Leave"
            elif leave_roll < 0.065:
                status = "Absent"
            else:
                status = "Present"

            late_minutes = 0
            check_in = None
            check_out = None
            if status == "Present":
                late_minutes = max(0, int(rng.gauss(7, 12)))
                check_in_dt = datetime.combine(work_day, datetime.strptime("09:30", "%H:%M").time())
                check_in_dt += timedelta(minutes=late_minutes)
                check_out_dt = check_in_dt + timedelta(hours=8, minutes=rng.randint(-30, 60))
                check_in = check_in_dt.time()
                check_out = check_out_dt.time()

                task_count = rng.choice([1, 2, 2, 3])
                remaining_hours = max(4.5, rng.gauss(base_hours, 0.9))
                for task_number in range(task_count):
                    task_type = rng.choice(TASK_TYPES)
                    project = rng.choice(PROJECTS)
                    hours = max(0.75, remaining_hours / (task_count - task_number) + rng.uniform(-0.45, 0.45))
                    remaining_hours -= hours
                    productivity = int(max(55, min(99, rng.gauss(base_score, 7))))
                    overtime = round(max(0, hours - 8.0 / task_count), 2)
                    logs.append(
                        (
                            employee_id,
                            work_day,
                            project,
                            task_type,
                            round(hours, 2),
                            productivity,
                            overtime,
                            sample_note(department, productivity, overtime),
                        )
                    )

            attendance.append((employee_id, work_day, status, check_in, check_out, late_minutes))

    return {
        "employees": EMPLOYEES,
        "work_logs": logs,
        "attendance": attendance,
        "work_groups": WORK_GROUPS,
        "ideal_times": IDEAL_TIMES,
        "users": USERS,
    }


def sample_note(department: str, productivity: int, overtime: float) -> str:
    if overtime > 0.8:
        return f"{department} delivery required overtime support"
    if productivity >= 92:
        return "High quality output with low rework"
    if productivity < 70:
        return "Needs follow-up coaching"
    return "Normal delivery"
