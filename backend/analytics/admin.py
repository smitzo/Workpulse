from django.contrib import admin

from analytics.models import Attendance, AuditLog, Employee, IdealTime, Project, UserProfile, WorkGroup, WorkGroupItem, WorkLog


@admin.register(Employee)
class EmployeeAdmin(admin.ModelAdmin):
    list_display = ("employee_id", "name", "department", "role", "status")
    list_filter = ("department", "status", "location")
    search_fields = ("employee_id", "name", "role", "manager")


@admin.register(WorkLog)
class WorkLogAdmin(admin.ModelAdmin):
    list_display = ("employee", "log_date", "project", "task_type", "hours", "productivity_score")
    list_filter = ("project", "task_type", "log_date")
    search_fields = ("employee__employee_id", "employee__name", "notes")


@admin.register(Attendance)
class AttendanceAdmin(admin.ModelAdmin):
    list_display = ("employee", "work_date", "status", "check_in", "check_out", "late_minutes")
    list_filter = ("status", "work_date")
    search_fields = ("employee__employee_id", "employee__name")


admin.site.register(UserProfile)
admin.site.register(Project)
admin.site.register(WorkGroup)
admin.site.register(WorkGroupItem)
admin.site.register(IdealTime)
admin.site.register(AuditLog)
