from __future__ import annotations

from django.contrib.auth.models import User
from django.core.management.base import BaseCommand
from django.db import transaction
from rest_framework.authtoken.models import Token

from analytics.models import Attendance, AuditLog, Employee, IdealTime, Project, UserProfile, WorkGroup, WorkGroupItem, WorkLog
from analytics.sample_data import build_sample_dataset


class Command(BaseCommand):
    help = "Seed deterministic demo data for dashboards, reports, and demo login."

    def add_arguments(self, parser):
        parser.add_argument(
            "--reset",
            action="store_true",
            help="Delete existing analytics data and demo users before seeding.",
        )

    @transaction.atomic
    def handle(self, *args, **options):
        if options["reset"]:
            profile_user_ids = list(UserProfile.objects.values_list("user_id", flat=True))
            AuditLog.objects.all().delete()
            Token.objects.all().delete()
            UserProfile.objects.all().delete()
            User.objects.filter(id__in=profile_user_ids).delete()
            User.objects.filter(
                username__in=[
                    "admin",
                    "EMP001",
                    "EMP002",
                    "EMP003",
                    "EMP005",
                    "EMP006",
                    "demoadmin",
                    "demomanager",
                    "demouser",
                ]
            ).delete()
            Attendance.objects.all().delete()
            WorkLog.objects.all().delete()
            Project.objects.all().delete()
            WorkGroupItem.objects.all().delete()
            WorkGroup.objects.all().delete()
            IdealTime.objects.all().delete()
            Employee.objects.all().delete()

        dataset = build_sample_dataset()

        employees = [
            Employee(
                employee_id=employee_id,
                name=name,
                department=department,
                role=role,
                location=location,
                manager=manager,
                hire_date=hire_date,
                status=status,
            )
            for employee_id, name, department, role, location, manager, hire_date, status in dataset["employees"]
        ]
        Employee.objects.bulk_create(employees, update_conflicts=True, update_fields=[
            "name",
            "department",
            "role",
            "location",
            "manager",
            "hire_date",
            "status",
        ], unique_fields=["employee_id"])

        employees_by_name = {employee.name: employee for employee in Employee.objects.all()}
        for employee in Employee.objects.all():
            manager = employees_by_name.get(employee.manager)
            if manager:
                employee.manager_employee = manager
                employee.save(update_fields=["manager_employee"])

        Project.objects.bulk_create(
            [
                Project(name=name, owner=owner, status=status, description=description)
                for name, owner, status, description in dataset["projects"]
            ],
            update_conflicts=True,
            update_fields=["owner", "status", "description"],
            unique_fields=["name"],
        )

        WorkLog.objects.bulk_create(
            [
                WorkLog(
                    employee_id=employee_id,
                    log_date=log_date,
                    project=project,
                    task_type=task_type,
                    hours=hours,
                    productivity_score=productivity,
                    overtime_hours=overtime,
                    notes=notes,
                )
                for employee_id, log_date, project, task_type, hours, productivity, overtime, notes in dataset["work_logs"]
            ]
        )

        Attendance.objects.bulk_create(
            [
                Attendance(
                    employee_id=employee_id,
                    work_date=work_date,
                    status=status,
                    check_in=check_in,
                    check_out=check_out,
                    late_minutes=late_minutes,
                )
                for employee_id, work_date, status, check_in, check_out, late_minutes in dataset["attendance"]
            ],
            update_conflicts=True,
            update_fields=["status", "check_in", "check_out", "late_minutes"],
            unique_fields=["employee", "work_date"],
        )

        IdealTime.objects.bulk_create(
            [IdealTime(task_type=task_type, ideal_hours=ideal_hours) for task_type, ideal_hours in dataset["ideal_times"]],
            update_conflicts=True,
            update_fields=["ideal_hours"],
            unique_fields=["task_type"],
        )

        for group_name, group_data in dataset["work_groups"].items():
            group, _created = WorkGroup.objects.update_or_create(
                group_name=group_name,
                defaults={"color_code": group_data["color"]},
            )
            for task_type in group_data["items"]:
                WorkGroupItem.objects.get_or_create(group=group, task_type=task_type)

        for username, password, role, employee_id in dataset["users"]:
            user, _created = User.objects.update_or_create(
                username=username,
                defaults={
                    "is_staff": role == UserProfile.ROLE_ADMIN,
                    "is_superuser": role == UserProfile.ROLE_ADMIN,
                    "first_name": "Demo",
                    "last_name": role.title(),
                },
            )
            user.set_password(password)
            user.save(update_fields=["password", "is_staff", "is_superuser", "first_name", "last_name"])
            UserProfile.objects.update_or_create(
                user=user,
                defaults={"role": role, "employee_id": employee_id},
            )
            Token.objects.get_or_create(user=user)

        self.stdout.write(self.style.SUCCESS("Demo analytics data seeded."))
