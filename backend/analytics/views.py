from __future__ import annotations

from django.contrib.auth.models import User
from django.core.management import call_command
from django.http import HttpResponse
from django.utils import timezone
from rest_framework.decorators import action
from rest_framework import status
from rest_framework.permissions import AllowAny, IsAuthenticated
from rest_framework.response import Response
from rest_framework.views import APIView
from rest_framework.viewsets import ModelViewSet

from analytics.models import Attendance, AuditLog, Employee, Project, UserProfile, WorkLog
from analytics.reporting import html_report
from analytics.serializers import (
    AttendanceSerializer,
    AdminUserSerializer,
    AuditLogSerializer,
    EmployeeSerializer,
    LoginSerializer,
    ProjectSerializer,
    SignupSerializer,
    UserSummarySerializer,
    WorkLogSerializer,
    auth_payload,
)
from analytics.services import AnalyticsService, Filters, accessible_employee_ids, scoped_filters, user_role


def audit(request, action: str, entity: str, entity_id: str, summary: str, metadata: dict | None = None) -> None:
    AuditLog.objects.create(
        actor=request.user if request.user.is_authenticated else None,
        action=action,
        entity=entity,
        entity_id=str(entity_id),
        summary=summary,
        metadata=metadata or {},
    )


def can_manage_system(user) -> bool:
    return user_role(user) == UserProfile.ROLE_ADMIN


def can_view_reports(user) -> bool:
    return user_role(user) in {UserProfile.ROLE_ADMIN, UserProfile.ROLE_MANAGER}


def filters_from_request(request) -> Filters:
    value = lambda key: request.query_params.get(key) or None
    return scoped_filters(
        Filters(
            date_from=value("date_from"),
            date_to=value("date_to"),
            department=value("department"),
            employee_id=value("employee_id"),
            task_type=value("task_type"),
            project=value("project"),
        ),
        request.user,
    )


class LoginView(APIView):
    permission_classes = [AllowAny]

    def post(self, request):
        serializer = LoginSerializer(data=request.data)
        serializer.is_valid(raise_exception=True)
        return Response(auth_payload(serializer.validated_data["user"]))


class DemoLoginView(APIView):
    permission_classes = [AllowAny]

    def post(self, _request):
        if not Employee.objects.exists():
            call_command("seed_demo")
        user = User.objects.filter(username="admin").first()
        if user is None:
            call_command("seed_demo")
            user = User.objects.get(username="admin")
        return Response(auth_payload(user))


class SignupView(APIView):
    permission_classes = [AllowAny]

    def post(self, request):
        serializer = SignupSerializer(data=request.data)
        serializer.is_valid(raise_exception=True)
        user = serializer.save()
        return Response(auth_payload(user), status=status.HTTP_201_CREATED)


class MeView(APIView):
    def get(self, request):
        return Response(auth_payload(request.user)["user"])


class OptionsView(APIView):
    def get(self, request):
        allowed_ids = accessible_employee_ids(request.user)
        employee_qs = Employee.objects.all()
        if allowed_ids is not None:
            employee_qs = employee_qs.filter(employee_id__in=allowed_ids)
        project_names = set(Project.objects.order_by("name").values_list("name", flat=True))
        project_names.update(
            AnalyticsService().work_log_queryset(filters_from_request(request)).order_by("project").values_list("project", flat=True).distinct()
        )

        return Response(
            {
                "departments": ["All", *employee_qs.order_by("department").values_list("department", flat=True).distinct()],
                "employees": [
                    {"id": employee.employee_id, "label": f"{employee.employee_id} - {employee.name}"}
                    for employee in employee_qs.order_by("name")
                ],
                "task_types": ["All", *WorkLog.objects.order_by("task_type").values_list("task_type", flat=True).distinct()],
                "projects": ["All", *sorted(project for project in project_names if project)],
                "statuses": ["Active", "On Leave", "Inactive"],
                "roles": ["employee", "manager", "admin"],
            }
        )


class DashboardView(APIView):
    def get(self, request):
        return Response(AnalyticsService().dashboard(filters_from_request(request)))


class InsightsView(APIView):
    def get(self, request):
        filters = filters_from_request(request)
        service = AnalyticsService()
        return Response(
            {
                "summary": service.executive_summary(filters),
                "insights": [item.__dict__ for item in service.insights(filters)],
            }
        )


class ReportView(APIView):
    def get(self, request):
        if not can_view_reports(request.user):
            return Response({"detail": "Only managers and admins can export reports."}, status=status.HTTP_403_FORBIDDEN)
        return HttpResponse(html_report(filters_from_request(request)), content_type="text/html; charset=utf-8")


class EmployeeViewSet(ModelViewSet):
    serializer_class = EmployeeSerializer
    queryset = Employee.objects.all()

    def get_queryset(self):
        queryset = Employee.objects.all()
        allowed_ids = accessible_employee_ids(self.request.user)
        if allowed_ids is not None:
            return queryset.filter(employee_id__in=allowed_ids)
        department = self.request.query_params.get("department")
        search = self.request.query_params.get("search")
        if department and department != "All":
            queryset = queryset.filter(department=department)
        if search:
            queryset = queryset.filter(name__icontains=search) | queryset.filter(employee_id__icontains=search)
        return queryset.order_by("department", "name")

    def create(self, request, *args, **kwargs):
        if not can_manage_system(request.user):
            return Response({"detail": "Only admins can manage employees."}, status=status.HTTP_403_FORBIDDEN)
        response = super().create(request, *args, **kwargs)
        audit(request, AuditLog.ACTION_CREATE, "employee", response.data["employee_id"], f"Created employee {response.data['name']}")
        return response

    def update(self, request, *args, **kwargs):
        if not can_manage_system(request.user):
            return Response({"detail": "Only admins can manage employees."}, status=status.HTTP_403_FORBIDDEN)
        response = super().update(request, *args, **kwargs)
        audit(request, AuditLog.ACTION_UPDATE, "employee", response.data["employee_id"], f"Updated employee {response.data['name']}")
        return response

    def destroy(self, request, *args, **kwargs):
        if not can_manage_system(request.user):
            return Response({"detail": "Only admins can manage employees."}, status=status.HTTP_403_FORBIDDEN)
        instance = self.get_object()
        audit(request, AuditLog.ACTION_DELETE, "employee", instance.employee_id, f"Deleted employee {instance.name}")
        return super().destroy(request, *args, **kwargs)


class WorkLogViewSet(ModelViewSet):
    serializer_class = WorkLogSerializer
    queryset = WorkLog.objects.select_related("employee")

    def get_queryset(self):
        service = AnalyticsService()
        return service.work_log_queryset(filters_from_request(self.request))

    def perform_create(self, serializer):
        role = user_role(self.request.user)
        if role in {UserProfile.ROLE_ADMIN, UserProfile.ROLE_MANAGER}:
            employee_id = self.request.data.get("employee_id")
            allowed_ids = accessible_employee_ids(self.request.user)
            if allowed_ids is not None and employee_id not in allowed_ids:
                employee_id = self.request.user.profile.employee_id
        else:
            employee_id = self.request.user.profile.employee_id
        log = serializer.save(employee_id=employee_id)
        Project.objects.get_or_create(name=log.project, defaults={"owner": log.employee.name})
        audit(self.request, AuditLog.ACTION_CREATE, "work_log", log.id, f"Created timesheet for {log.employee.name}")

    def perform_update(self, serializer):
        log = serializer.save()
        Project.objects.get_or_create(name=log.project, defaults={"owner": log.employee.name})
        audit(self.request, AuditLog.ACTION_UPDATE, "work_log", log.id, f"Updated timesheet for {log.employee.name}")

    def destroy(self, request, *args, **kwargs):
        instance = self.get_object()
        allowed_ids = accessible_employee_ids(request.user)
        if allowed_ids is not None and instance.employee_id not in allowed_ids:
            return Response({"detail": "You can only delete work logs you are allowed to access."}, status=status.HTTP_403_FORBIDDEN)
        audit(request, AuditLog.ACTION_DELETE, "work_log", instance.id, f"Deleted timesheet for {instance.employee.name}")
        return super().destroy(request, *args, **kwargs)


class AttendanceViewSet(ModelViewSet):
    serializer_class = AttendanceSerializer
    queryset = Attendance.objects.select_related("employee")

    def get_queryset(self):
        service = AnalyticsService()
        return service.attendance_queryset(filters_from_request(self.request))

    def perform_create(self, serializer):
        role = user_role(self.request.user)
        if role in {UserProfile.ROLE_ADMIN, UserProfile.ROLE_MANAGER}:
            employee_id = self.request.data.get("employee_id")
            allowed_ids = accessible_employee_ids(self.request.user)
            if allowed_ids is not None and employee_id not in allowed_ids:
                employee_id = self.request.user.profile.employee_id
        else:
            employee_id = self.request.user.profile.employee_id
        record = serializer.save(employee_id=employee_id)
        audit(self.request, AuditLog.ACTION_CREATE, "attendance", record.id, f"Saved attendance for {record.employee.name}")

    def perform_update(self, serializer):
        record = serializer.save()
        audit(self.request, AuditLog.ACTION_UPDATE, "attendance", record.id, f"Updated attendance for {record.employee.name}")

    @action(detail=False, methods=["post"], url_path="mark-today")
    def mark_today(self, request):
        profile = getattr(request.user, "profile", None)
        if not profile or not profile.employee_id:
            return Response({"detail": "No employee profile is linked to this user."}, status=status.HTTP_400_BAD_REQUEST)
        now = timezone.localtime()
        record, _created = Attendance.objects.update_or_create(
            employee_id=profile.employee_id,
            work_date=now.date(),
            defaults={
                "status": Attendance.STATUS_PRESENT,
                "check_in": now.time().replace(microsecond=0),
                "late_minutes": 0,
            },
        )
        audit(request, AuditLog.ACTION_MARK_ATTENDANCE, "attendance", record.id, f"Marked attendance for {record.employee.name}")
        return Response(AttendanceSerializer(record).data)


class ProjectViewSet(ModelViewSet):
    serializer_class = ProjectSerializer
    queryset = Project.objects.all()

    def get_permissions(self):
        return [IsAuthenticated()]

    def create(self, request, *args, **kwargs):
        if not can_manage_system(request.user):
            return Response({"detail": "Only admins can manage projects."}, status=status.HTTP_403_FORBIDDEN)
        response = super().create(request, *args, **kwargs)
        audit(request, AuditLog.ACTION_CREATE, "project", response.data["id"], f"Created project {response.data['name']}")
        return response

    def update(self, request, *args, **kwargs):
        if not can_manage_system(request.user):
            return Response({"detail": "Only admins can manage projects."}, status=status.HTTP_403_FORBIDDEN)
        response = super().update(request, *args, **kwargs)
        audit(request, AuditLog.ACTION_UPDATE, "project", response.data["id"], f"Updated project {response.data['name']}")
        return response

    def partial_update(self, request, *args, **kwargs):
        return self.update(request, *args, **kwargs)

    def destroy(self, request, *args, **kwargs):
        if not can_manage_system(request.user):
            return Response({"detail": "Only admins can manage projects."}, status=status.HTTP_403_FORBIDDEN)
        instance = self.get_object()
        audit(request, AuditLog.ACTION_DELETE, "project", instance.id, f"Deleted project {instance.name}")
        return super().destroy(request, *args, **kwargs)


class UserAdminViewSet(ModelViewSet):
    queryset = User.objects.select_related("profile", "profile__employee").all()

    def get_serializer_class(self):
        if self.action == "create":
            return AdminUserSerializer
        return UserSummarySerializer

    def get_queryset(self):
        if not can_manage_system(self.request.user):
            return User.objects.none()
        return User.objects.select_related("profile", "profile__employee").filter(profile__isnull=False).order_by("username")

    def list(self, request, *args, **kwargs):
        if not can_manage_system(request.user):
            return Response({"detail": "Only admins can manage users."}, status=status.HTTP_403_FORBIDDEN)
        return super().list(request, *args, **kwargs)

    def create(self, request, *args, **kwargs):
        if not can_manage_system(request.user):
            return Response({"detail": "Only admins can create users."}, status=status.HTTP_403_FORBIDDEN)
        serializer = self.get_serializer(data=request.data)
        serializer.is_valid(raise_exception=True)
        user = serializer.save()
        audit(request, AuditLog.ACTION_CREATE, "user", user.username, f"Created user {user.username}")
        return Response(auth_payload(user)["user"], status=status.HTTP_201_CREATED)


class AuditLogViewSet(ModelViewSet):
    serializer_class = AuditLogSerializer
    queryset = AuditLog.objects.select_related("actor")
    http_method_names = ["get", "head", "options"]

    def get_queryset(self):
        if not can_manage_system(self.request.user):
            return AuditLog.objects.none()
        return AuditLog.objects.select_related("actor")

    def list(self, request, *args, **kwargs):
        if not can_manage_system(request.user):
            return Response({"detail": "Only admins can view audit logs."}, status=status.HTTP_403_FORBIDDEN)
        return super().list(request, *args, **kwargs)
