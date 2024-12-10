from __future__ import annotations

from django.contrib.auth import authenticate
from django.contrib.auth.models import User
from django.db import transaction
from rest_framework import serializers
from rest_framework.authtoken.models import Token

from analytics.models import Attendance, Employee, UserProfile, WorkLog


class EmployeeSerializer(serializers.ModelSerializer):
    class Meta:
        model = Employee
        fields = ["employee_id", "name", "department", "role", "location", "manager", "hire_date", "status"]


class WorkLogSerializer(serializers.ModelSerializer):
    employee_id = serializers.CharField(write_only=True, required=False)
    employee = EmployeeSerializer(read_only=True)
    department = serializers.CharField(source="employee.department", read_only=True)
    name = serializers.CharField(source="employee.name", read_only=True)

    class Meta:
        model = WorkLog
        fields = [
            "id",
            "employee_id",
            "employee",
            "name",
            "department",
            "log_date",
            "project",
            "task_type",
            "hours",
            "productivity_score",
            "overtime_hours",
            "notes",
        ]

    def create(self, validated_data):
        employee_id = validated_data.pop("employee_id", None)
        if employee_id:
            validated_data["employee"] = Employee.objects.get(employee_id=employee_id)
        return super().create(validated_data)


class AttendanceSerializer(serializers.ModelSerializer):
    employee_id = serializers.CharField(write_only=True, required=False)
    employee = EmployeeSerializer(read_only=True)
    department = serializers.CharField(source="employee.department", read_only=True)
    name = serializers.CharField(source="employee.name", read_only=True)

    class Meta:
        model = Attendance
        fields = [
            "id",
            "employee_id",
            "employee",
            "name",
            "department",
            "work_date",
            "status",
            "check_in",
            "check_out",
            "late_minutes",
        ]

    def create(self, validated_data):
        employee_id = validated_data.pop("employee_id", None)
        if employee_id:
            validated_data["employee"] = Employee.objects.get(employee_id=employee_id)
        record, _created = Attendance.objects.update_or_create(
            employee=validated_data["employee"],
            work_date=validated_data["work_date"],
            defaults=validated_data,
        )
        return record


class LoginSerializer(serializers.Serializer):
    username = serializers.CharField()
    password = serializers.CharField(write_only=True)

    def validate(self, attrs):
        user = authenticate(username=attrs["username"], password=attrs["password"])
        if not user:
            raise serializers.ValidationError("Invalid username or password.")
        attrs["user"] = user
        return attrs


class SignupSerializer(serializers.Serializer):
    username = serializers.CharField(max_length=150)
    password = serializers.CharField(write_only=True, min_length=8)
    name = serializers.CharField(max_length=120)
    email = serializers.EmailField(required=False, allow_blank=True)
    department = serializers.CharField(max_length=80, default="General")
    role = serializers.CharField(max_length=120, default="Employee")
    location = serializers.CharField(max_length=120, default="Remote")
    manager = serializers.CharField(max_length=120, default="Unassigned")
    hire_date = serializers.DateField()

    def validate_username(self, value):
        if User.objects.filter(username=value).exists():
            raise serializers.ValidationError("That username is already taken.")
        return value

    @transaction.atomic
    def create(self, validated_data):
        name = validated_data.pop("name")
        password = validated_data.pop("password")
        email = validated_data.pop("email", "")
        user = User.objects.create_user(
            username=validated_data["username"],
            password=password,
            email=email,
            first_name=name.split(" ", 1)[0],
            last_name=name.split(" ", 1)[1] if " " in name else "",
        )
        employee_id = validated_data["username"].upper()
        employee = Employee.objects.create(
            employee_id=employee_id,
            name=name,
            department=validated_data["department"],
            role=validated_data["role"],
            location=validated_data["location"],
            manager=validated_data["manager"],
            hire_date=validated_data["hire_date"],
            status="Active",
        )
        UserProfile.objects.create(user=user, role=UserProfile.ROLE_EMPLOYEE, employee=employee)
        Token.objects.create(user=user)
        return user


def auth_payload(user: User) -> dict:
    token, _created = Token.objects.get_or_create(user=user)
    profile = getattr(user, "profile", None)
    employee = profile.employee if profile else None
    return {
        "token": token.key,
        "user": {
            "username": user.username,
            "email": user.email,
            "role": profile.role if profile else ("admin" if user.is_staff else "employee"),
            "employee_id": employee.employee_id if employee else None,
            "name": employee.name if employee else (user.get_full_name() or user.username),
            "department": employee.department if employee else None,
        },
    }
