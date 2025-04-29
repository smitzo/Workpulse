from __future__ import annotations

from django.conf import settings
from decimal import Decimal

from django.core.validators import MaxValueValidator, MinValueValidator
from django.db import models


class Employee(models.Model):
    employee_id = models.CharField(max_length=24, primary_key=True)
    name = models.CharField(max_length=120)
    department = models.CharField(max_length=80, db_index=True)
    role = models.CharField(max_length=120)
    location = models.CharField(max_length=120)
    manager = models.CharField(max_length=120)
    manager_employee = models.ForeignKey(
        "self",
        on_delete=models.SET_NULL,
        null=True,
        blank=True,
        related_name="direct_reports",
    )
    hire_date = models.DateField()
    status = models.CharField(max_length=32, db_index=True)

    class Meta:
        ordering = ["department", "name"]

    def __str__(self) -> str:
        return f"{self.employee_id} - {self.name}"


class UserProfile(models.Model):
    ROLE_ADMIN = "admin"
    ROLE_MANAGER = "manager"
    ROLE_EMPLOYEE = "employee"
    ROLE_CHOICES = (
        (ROLE_ADMIN, "Admin"),
        (ROLE_MANAGER, "Manager"),
        (ROLE_EMPLOYEE, "Employee"),
    )

    user = models.OneToOneField(settings.AUTH_USER_MODEL, on_delete=models.CASCADE, related_name="profile")
    role = models.CharField(max_length=16, choices=ROLE_CHOICES, db_index=True)
    employee = models.ForeignKey(Employee, on_delete=models.CASCADE, null=True, blank=True, related_name="users")

    class Meta:
        ordering = ["user__username"]

    def __str__(self) -> str:
        return f"{self.user.username} ({self.role})"


class WorkLog(models.Model):
    employee = models.ForeignKey(Employee, on_delete=models.CASCADE, related_name="work_logs")
    log_date = models.DateField(db_index=True)
    project = models.CharField(max_length=120, db_index=True)
    task_type = models.CharField(max_length=120, db_index=True)
    hours = models.DecimalField(max_digits=6, decimal_places=2, validators=[MinValueValidator(Decimal("0"))])
    productivity_score = models.PositiveSmallIntegerField(
        validators=[MinValueValidator(0), MaxValueValidator(100)]
    )
    overtime_hours = models.DecimalField(max_digits=6, decimal_places=2, default=0, validators=[MinValueValidator(Decimal("0"))])
    notes = models.TextField(blank=True)
    created_at = models.DateTimeField(auto_now_add=True)

    class Meta:
        ordering = ["-log_date", "-id"]
        indexes = [
            models.Index(fields=["employee", "log_date"], name="analytics_w_employe_d19759_idx"),
            models.Index(fields=["project", "log_date"], name="analytics_w_project_6baa14_idx"),
            models.Index(fields=["task_type", "log_date"], name="analytics_w_task_ty_b03ef2_idx"),
        ]

    def __str__(self) -> str:
        return f"{self.employee_id} {self.log_date} {self.task_type}"


class Project(models.Model):
    STATUS_ACTIVE = "Active"
    STATUS_PAUSED = "Paused"
    STATUS_ARCHIVED = "Archived"
    STATUS_CHOICES = (
        (STATUS_ACTIVE, "Active"),
        (STATUS_PAUSED, "Paused"),
        (STATUS_ARCHIVED, "Archived"),
    )

    name = models.CharField(max_length=120, unique=True)
    owner = models.CharField(max_length=120, blank=True)
    status = models.CharField(max_length=24, choices=STATUS_CHOICES, default=STATUS_ACTIVE, db_index=True)
    description = models.TextField(blank=True)
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    class Meta:
        ordering = ["name"]

    def __str__(self) -> str:
        return self.name


class Attendance(models.Model):
    STATUS_PRESENT = "Present"
    STATUS_LEAVE = "Leave"
    STATUS_ABSENT = "Absent"
    STATUS_CHOICES = (
        (STATUS_PRESENT, "Present"),
        (STATUS_LEAVE, "Leave"),
        (STATUS_ABSENT, "Absent"),
    )

    employee = models.ForeignKey(Employee, on_delete=models.CASCADE, related_name="attendance_records")
    work_date = models.DateField(db_index=True)
    status = models.CharField(max_length=24, choices=STATUS_CHOICES, db_index=True)
    check_in = models.TimeField(null=True, blank=True)
    check_out = models.TimeField(null=True, blank=True)
    late_minutes = models.PositiveIntegerField(default=0)

    class Meta:
        ordering = ["-work_date", "employee__name"]
        constraints = [
            models.UniqueConstraint(fields=["employee", "work_date"], name="unique_employee_attendance_date"),
        ]

    def __str__(self) -> str:
        return f"{self.employee_id} {self.work_date} {self.status}"


class WorkGroup(models.Model):
    group_name = models.CharField(max_length=120, unique=True)
    color_code = models.CharField(max_length=16, default="#64748b")

    class Meta:
        ordering = ["group_name"]

    def __str__(self) -> str:
        return self.group_name


class WorkGroupItem(models.Model):
    group = models.ForeignKey(WorkGroup, on_delete=models.CASCADE, related_name="items")
    task_type = models.CharField(max_length=120)

    class Meta:
        ordering = ["group__group_name", "task_type"]
        constraints = [
            models.UniqueConstraint(fields=["group", "task_type"], name="unique_work_group_task"),
        ]

    def __str__(self) -> str:
        return f"{self.group.group_name}: {self.task_type}"


class IdealTime(models.Model):
    task_type = models.CharField(max_length=120, primary_key=True)
    ideal_hours = models.DecimalField(max_digits=6, decimal_places=2, validators=[MinValueValidator(Decimal("0"))])

    class Meta:
        ordering = ["task_type"]

    def __str__(self) -> str:
        return f"{self.task_type}: {self.ideal_hours}"


class AuditLog(models.Model):
    ACTION_CREATE = "create"
    ACTION_UPDATE = "update"
    ACTION_DELETE = "delete"
    ACTION_MARK_ATTENDANCE = "mark_attendance"
    ACTION_CHOICES = (
        (ACTION_CREATE, "Create"),
        (ACTION_UPDATE, "Update"),
        (ACTION_DELETE, "Delete"),
        (ACTION_MARK_ATTENDANCE, "Mark attendance"),
    )

    actor = models.ForeignKey(settings.AUTH_USER_MODEL, on_delete=models.SET_NULL, null=True, blank=True)
    action = models.CharField(max_length=32, choices=ACTION_CHOICES, db_index=True)
    entity = models.CharField(max_length=80, db_index=True)
    entity_id = models.CharField(max_length=120, blank=True)
    summary = models.CharField(max_length=255)
    metadata = models.JSONField(default=dict, blank=True)
    created_at = models.DateTimeField(auto_now_add=True, db_index=True)

    class Meta:
        ordering = ["-created_at", "-id"]

    def __str__(self) -> str:
        return f"{self.action} {self.entity} {self.entity_id}"
