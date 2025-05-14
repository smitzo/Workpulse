import type {
  Attendance,
  AuditLog,
  AuthPayload,
  Dashboard,
  Employee,
  Filters,
  InsightsPayload,
  OptionsPayload,
  Project,
  UserSummary,
  WorkLog
} from "@/types/api";

const API_BASE_URL = process.env.NEXT_PUBLIC_API_BASE_URL || "http://127.0.0.1:8000/api";

type RequestOptions = RequestInit & {
  token?: string | null;
};

export class ApiError extends Error {
  status: number;

  constructor(message: string, status: number) {
    super(message);
    this.status = status;
  }
}

export async function apiFetch<T>(path: string, options: RequestOptions = {}): Promise<T> {
  const headers = new Headers(options.headers);
  headers.set("Accept", "application/json");
  if (!(options.body instanceof FormData)) {
    headers.set("Content-Type", "application/json");
  }
  if (options.token) {
    headers.set("Authorization", `Token ${options.token}`);
  }

  const response = await fetch(`${API_BASE_URL}${path}`, {
    ...options,
    headers,
    cache: "no-store"
  });
  const contentType = response.headers.get("content-type") || "";
  const payload = contentType.includes("application/json") ? await response.json() : await response.text();
  if (!response.ok) {
    const message =
      typeof payload === "string"
        ? payload.includes("<!doctype html>")
          ? `Backend rejected the request (${response.status}). Check Render host and environment settings.`
          : payload
        : payload.detail || payload.non_field_errors?.[0] || "Request failed";
    throw new ApiError(message, response.status);
  }
  return payload as T;
}

export function login(username: string, password: string) {
  return apiFetch<AuthPayload>("/auth/login/", {
    method: "POST",
    body: JSON.stringify({ username, password })
  });
}

export function demoLogin(role: "employee" | "manager" | "admin" = "admin") {
  return apiFetch<AuthPayload>("/auth/demo/", {
    method: "POST",
    body: JSON.stringify({ role })
  });
}

export function signup(payload: Record<string, string>) {
  return apiFetch<AuthPayload>("/auth/signup/", {
    method: "POST",
    body: JSON.stringify(payload)
  });
}

export function reportUrl(token: string, query = "") {
  const params = new URLSearchParams(query);
  params.set("token", token);
  return `${API_BASE_URL}/report/?${params.toString()}`;
}

export function queryString(filters: Filters) {
  const params = new URLSearchParams();
  Object.entries(filters).forEach(([key, value]) => {
    if (value && value !== "All") {
      params.set(key, value);
    }
  });
  return params.toString();
}

export function getOptions(token: string) {
  return apiFetch<OptionsPayload>("/options/", { token });
}

export function getDashboard(token: string, filters: Filters) {
  const query = queryString(filters);
  return apiFetch<Dashboard>(`/dashboard/${query ? `?${query}` : ""}`, { token });
}

export function getInsights(token: string, filters: Filters) {
  const query = queryString(filters);
  return apiFetch<InsightsPayload>(`/insights/${query ? `?${query}` : ""}`, { token });
}

export async function getReportHtml(token: string, filters: Filters) {
  const query = queryString(filters);
  const response = await fetch(`${API_BASE_URL}/report/${query ? `?${query}` : ""}`, {
    headers: { Authorization: `Token ${token}` },
    cache: "no-store"
  });
  if (!response.ok) {
    throw new ApiError(await response.text(), response.status);
  }
  return response.text();
}

export function getEmployees(token: string) {
  return apiFetch<Employee[]>("/employees/", { token });
}

export function saveEmployee(token: string, payload: Record<string, string>) {
  return apiFetch<Employee>("/employees/", {
    method: "POST",
    token,
    body: JSON.stringify(payload)
  });
}

export function updateEmployee(token: string, employeeId: string, payload: Record<string, string>) {
  return apiFetch<Employee>(`/employees/${employeeId}/`, {
    method: "PATCH",
    token,
    body: JSON.stringify(payload)
  });
}

export function deleteEmployee(token: string, employeeId: string) {
  return apiFetch<void>(`/employees/${employeeId}/`, { method: "DELETE", token });
}

export function getLogs(token: string, filters: Filters) {
  const query = queryString(filters);
  return apiFetch<WorkLog[]>(`/logs/${query ? `?${query}` : ""}`, { token });
}

export function saveLog(token: string, payload: Record<string, string>) {
  return apiFetch<WorkLog>("/logs/", {
    method: "POST",
    token,
    body: JSON.stringify(payload)
  });
}

export function deleteLog(token: string, id: number) {
  return apiFetch<void>(`/logs/${id}/`, { method: "DELETE", token });
}

export function getAttendance(token: string, filters: Filters) {
  const query = queryString(filters);
  return apiFetch<Attendance[]>(`/attendance/${query ? `?${query}` : ""}`, { token });
}

export function saveAttendance(token: string, payload: Record<string, string>) {
  return apiFetch<Attendance>("/attendance/", {
    method: "POST",
    token,
    body: JSON.stringify(payload)
  });
}

export function markAttendanceToday(token: string) {
  return apiFetch<Attendance>("/attendance/mark-today/", { method: "POST", token });
}

export function getProjects(token: string) {
  return apiFetch<Project[]>("/projects/", { token });
}

export function saveProject(token: string, payload: Record<string, string>) {
  return apiFetch<Project>("/projects/", {
    method: "POST",
    token,
    body: JSON.stringify(payload)
  });
}

export function updateProject(token: string, id: number, payload: Record<string, string>) {
  return apiFetch<Project>(`/projects/${id}/`, {
    method: "PATCH",
    token,
    body: JSON.stringify(payload)
  });
}

export function deleteProject(token: string, id: number) {
  return apiFetch<void>(`/projects/${id}/`, { method: "DELETE", token });
}

export function getUsers(token: string) {
  return apiFetch<UserSummary[]>("/users/", { token });
}

export function createUser(token: string, payload: Record<string, string>) {
  return apiFetch<AuthPayload["user"]>("/users/", {
    method: "POST",
    token,
    body: JSON.stringify(payload)
  });
}

export function getAuditLogs(token: string) {
  return apiFetch<AuditLog[]>("/audit-logs/", { token });
}
