from django.conf import settings
from django.db import migrations, models
import django.core.validators
import django.db.models.deletion
import decimal


class Migration(migrations.Migration):
    initial = True

    dependencies = [
        migrations.swappable_dependency(settings.AUTH_USER_MODEL),
    ]

    operations = [
        migrations.CreateModel(
            name="Employee",
            fields=[
                ("employee_id", models.CharField(max_length=24, primary_key=True, serialize=False)),
                ("name", models.CharField(max_length=120)),
                ("department", models.CharField(db_index=True, max_length=80)),
                ("role", models.CharField(max_length=120)),
                ("location", models.CharField(max_length=120)),
                ("manager", models.CharField(max_length=120)),
                ("hire_date", models.DateField()),
                ("status", models.CharField(db_index=True, max_length=32)),
            ],
            options={"ordering": ["department", "name"]},
        ),
        migrations.CreateModel(
            name="IdealTime",
            fields=[
                ("task_type", models.CharField(max_length=120, primary_key=True, serialize=False)),
                (
                    "ideal_hours",
                    models.DecimalField(
                        decimal_places=2,
                        max_digits=6,
                        validators=[django.core.validators.MinValueValidator(decimal.Decimal("0"))],
                    ),
                ),
            ],
            options={"ordering": ["task_type"]},
        ),
        migrations.CreateModel(
            name="WorkGroup",
            fields=[
                ("id", models.BigAutoField(auto_created=True, primary_key=True, serialize=False, verbose_name="ID")),
                ("group_name", models.CharField(max_length=120, unique=True)),
                ("color_code", models.CharField(default="#64748b", max_length=16)),
            ],
            options={"ordering": ["group_name"]},
        ),
        migrations.CreateModel(
            name="Attendance",
            fields=[
                ("id", models.BigAutoField(auto_created=True, primary_key=True, serialize=False, verbose_name="ID")),
                ("work_date", models.DateField(db_index=True)),
                (
                    "status",
                    models.CharField(
                        choices=[("Present", "Present"), ("Leave", "Leave"), ("Absent", "Absent")],
                        db_index=True,
                        max_length=24,
                    ),
                ),
                ("check_in", models.TimeField(blank=True, null=True)),
                ("check_out", models.TimeField(blank=True, null=True)),
                ("late_minutes", models.PositiveIntegerField(default=0)),
                (
                    "employee",
                    models.ForeignKey(
                        on_delete=django.db.models.deletion.CASCADE,
                        related_name="attendance_records",
                        to="analytics.employee",
                    ),
                ),
            ],
            options={"ordering": ["-work_date", "employee__name"]},
        ),
        migrations.CreateModel(
            name="UserProfile",
            fields=[
                ("id", models.BigAutoField(auto_created=True, primary_key=True, serialize=False, verbose_name="ID")),
                (
                    "role",
                    models.CharField(
                        choices=[("admin", "Admin"), ("employee", "Employee")],
                        db_index=True,
                        max_length=16,
                    ),
                ),
                (
                    "employee",
                    models.ForeignKey(
                        blank=True,
                        null=True,
                        on_delete=django.db.models.deletion.CASCADE,
                        related_name="users",
                        to="analytics.employee",
                    ),
                ),
                (
                    "user",
                    models.OneToOneField(
                        on_delete=django.db.models.deletion.CASCADE,
                        related_name="profile",
                        to=settings.AUTH_USER_MODEL,
                    ),
                ),
            ],
            options={"ordering": ["user__username"]},
        ),
        migrations.CreateModel(
            name="WorkGroupItem",
            fields=[
                ("id", models.BigAutoField(auto_created=True, primary_key=True, serialize=False, verbose_name="ID")),
                ("task_type", models.CharField(max_length=120)),
                (
                    "group",
                    models.ForeignKey(
                        on_delete=django.db.models.deletion.CASCADE,
                        related_name="items",
                        to="analytics.workgroup",
                    ),
                ),
            ],
            options={"ordering": ["group__group_name", "task_type"]},
        ),
        migrations.CreateModel(
            name="WorkLog",
            fields=[
                ("id", models.BigAutoField(auto_created=True, primary_key=True, serialize=False, verbose_name="ID")),
                ("log_date", models.DateField(db_index=True)),
                ("project", models.CharField(db_index=True, max_length=120)),
                ("task_type", models.CharField(db_index=True, max_length=120)),
                (
                    "hours",
                    models.DecimalField(
                        decimal_places=2,
                        max_digits=6,
                        validators=[django.core.validators.MinValueValidator(decimal.Decimal("0"))],
                    ),
                ),
                (
                    "productivity_score",
                    models.PositiveSmallIntegerField(
                        validators=[
                            django.core.validators.MinValueValidator(0),
                            django.core.validators.MaxValueValidator(100),
                        ]
                    ),
                ),
                (
                    "overtime_hours",
                    models.DecimalField(
                        decimal_places=2,
                        default=0,
                        max_digits=6,
                        validators=[django.core.validators.MinValueValidator(decimal.Decimal("0"))],
                    ),
                ),
                ("notes", models.TextField(blank=True)),
                ("created_at", models.DateTimeField(auto_now_add=True)),
                (
                    "employee",
                    models.ForeignKey(
                        on_delete=django.db.models.deletion.CASCADE,
                        related_name="work_logs",
                        to="analytics.employee",
                    ),
                ),
            ],
            options={
                "ordering": ["-log_date", "-id"],
                "indexes": [
                    models.Index(fields=["employee", "log_date"], name="analytics_w_employe_d19759_idx"),
                    models.Index(fields=["project", "log_date"], name="analytics_w_project_6baa14_idx"),
                    models.Index(fields=["task_type", "log_date"], name="analytics_w_task_ty_b03ef2_idx"),
                ],
            },
        ),
        migrations.AddConstraint(
            model_name="attendance",
            constraint=models.UniqueConstraint(fields=("employee", "work_date"), name="unique_employee_attendance_date"),
        ),
        migrations.AddConstraint(
            model_name="workgroupitem",
            constraint=models.UniqueConstraint(fields=("group", "task_type"), name="unique_work_group_task"),
        ),
    ]
