import type { AuthPayload, Dashboard, Filters, InsightsPayload, OptionsPayload } from "@/types/api";

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
    const message = typeof payload === "string" ? payload : payload.detail || payload.non_field_errors?.[0] || "Request failed";
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

export function demoLogin() {
  return apiFetch<AuthPayload>("/auth/demo/", { method: "POST" });
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
