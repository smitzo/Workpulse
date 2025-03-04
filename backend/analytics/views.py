from __future__ import annotations

from django.contrib.auth.models import User
from django.core.management import call_command
from django.http import HttpResponse
from rest_framework import status
from rest_framework.permissions import AllowAny, IsAuthenticated
from rest_framework.response import Response
from rest_framework.views import APIView
from rest_framework.viewsets import ModelViewSet

from analytics.models import Attendance, Employee, UserProfile, WorkLog
from analytics.reporting import html_report
from analytics.serializers import (
    AttendanceSerializer,
    EmployeeSerializer,
    LoginSerializer,
    SignupSerializer,
    WorkLogSerializer,
    auth_payload,
)
from analytics.services import AnalyticsService, Filters, scoped_filters, user_role


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
        role = user_role(request.user)
        employee_qs = Employee.objects.all()
        if role != UserProfile.ROLE_ADMIN:
            employee_id = request.user.profile.employee_id
            employee_qs = employee_qs.filter(employee_id=employee_id)

        return Response(
            {
                "departments": ["All", *Employee.objects.order_by("department").values_list("department", flat=True).distinct()],
                "employees": [
                    {"id": employee.employee_id, "label": f"{employee.employee_id} - {employee.name}"}
                    for employee in employee_qs.order_by("name")
                ],
                "task_types": ["All", *WorkLog.objects.order_by("task_type").values_list("task_type", flat=True).distinct()],
                "projects": ["All", *WorkLog.objects.order_by("project").values_list("project", flat=True).distinct()],
                "statuses": ["Active", "On Leave", "Inactive"],
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
        if user_role(request.user) != UserProfile.ROLE_ADMIN:
            return Response({"detail": "Only admins can export reports."}, status=status.HTTP_403_FORBIDDEN)
        return HttpResponse(html_report(filters_from_request(request)), content_type="text/html; charset=utf-8")


class EmployeeViewSet(ModelViewSet):
    serializer_class = EmployeeSerializer
    queryset = Employee.objects.all()

    def get_queryset(self):
        queryset = Employee.objects.all()
        if user_role(self.request.user) != UserProfile.ROLE_ADMIN:
            return queryset.filter(employee_id=self.request.user.profile.employee_id)
        department = self.request.query_params.get("department")
        search = self.request.query_params.get("search")
        if department and department != "All":
            queryset = queryset.filter(department=department)
        if search:
            queryset = queryset.filter(name__icontains=search) | queryset.filter(employee_id__icontains=search)
        return queryset.order_by("department", "name")

    def create(self, request, *args, **kwargs):
        if user_role(request.user) != UserProfile.ROLE_ADMIN:
            return Response({"detail": "Only admins can manage employees."}, status=status.HTTP_403_FORBIDDEN)
        return super().create(request, *args, **kwargs)

    def update(self, request, *args, **kwargs):
        if user_role(request.user) != UserProfile.ROLE_ADMIN:
            return Response({"detail": "Only admins can manage employees."}, status=status.HTTP_403_FORBIDDEN)
        return super().update(request, *args, **kwargs)

    def destroy(self, request, *args, **kwargs):
        if user_role(request.user) != UserProfile.ROLE_ADMIN:
            return Response({"detail": "Only admins can manage employees."}, status=status.HTTP_403_FORBIDDEN)
        return super().destroy(request, *args, **kwargs)


class WorkLogViewSet(ModelViewSet):
    serializer_class = WorkLogSerializer
    queryset = WorkLog.objects.select_related("employee")

    def get_queryset(self):
        service = AnalyticsService()
        return service.work_log_queryset(filters_from_request(self.request))

    def perform_create(self, serializer):
        if user_role(self.request.user) == UserProfile.ROLE_ADMIN:
            employee_id = self.request.data.get("employee_id")
        else:
            employee_id = self.request.user.profile.employee_id
        serializer.save(employee_id=employee_id)

    def destroy(self, request, *args, **kwargs):
        instance = self.get_object()
        if user_role(request.user) != UserProfile.ROLE_ADMIN and instance.employee_id != request.user.profile.employee_id:
            return Response({"detail": "You can only delete your own work logs."}, status=status.HTTP_403_FORBIDDEN)
        return super().destroy(request, *args, **kwargs)


class AttendanceViewSet(ModelViewSet):
    serializer_class = AttendanceSerializer
    queryset = Attendance.objects.select_related("employee")

    def get_queryset(self):
        service = AnalyticsService()
        return service.attendance_queryset(filters_from_request(self.request))

    def perform_create(self, serializer):
        if user_role(self.request.user) == UserProfile.ROLE_ADMIN:
            employee_id = self.request.data.get("employee_id")
        else:
            employee_id = self.request.user.profile.employee_id
        serializer.save(employee_id=employee_id)
