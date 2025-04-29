from django.urls import include, path
from rest_framework.routers import DefaultRouter

from analytics.views import (
    AttendanceViewSet,
    AuditLogViewSet,
    DashboardView,
    DemoLoginView,
    EmployeeViewSet,
    InsightsView,
    LoginView,
    MeView,
    OptionsView,
    ProjectViewSet,
    ReportView,
    SignupView,
    UserAdminViewSet,
    WorkLogViewSet,
)


router = DefaultRouter()
router.register("employees", EmployeeViewSet, basename="employees")
router.register("logs", WorkLogViewSet, basename="logs")
router.register("attendance", AttendanceViewSet, basename="attendance")
router.register("projects", ProjectViewSet, basename="projects")
router.register("users", UserAdminViewSet, basename="users")
router.register("audit-logs", AuditLogViewSet, basename="audit-logs")

urlpatterns = [
    path("auth/login/", LoginView.as_view(), name="login"),
    path("auth/demo/", DemoLoginView.as_view(), name="demo-login"),
    path("auth/signup/", SignupView.as_view(), name="signup"),
    path("auth/me/", MeView.as_view(), name="me"),
    path("options/", OptionsView.as_view(), name="options"),
    path("dashboard/", DashboardView.as_view(), name="dashboard"),
    path("insights/", InsightsView.as_view(), name="insights"),
    path("report/", ReportView.as_view(), name="report"),
    path("", include(router.urls)),
]
