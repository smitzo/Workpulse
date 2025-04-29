export type UserRole = "admin" | "manager" | "employee";

export type AuthUser = {
  username: string;
  email?: string;
  role: UserRole;
  employee_id: string | null;
  name: string;
  department: string | null;
};

export type AuthPayload = {
  token: string;
  user: AuthUser;
};

export type Employee = {
  employee_id: string;
  name: string;
  department: string;
  role: string;
  location: string;
  manager: string;
  manager_employee_id?: string | null;
  hire_date: string;
  status: string;
};

export type Project = {
  id: number;
  name: string;
  owner: string;
  status: "Active" | "Paused" | "Archived";
  description: string;
  created_at: string;
  updated_at: string;
};

export type UserSummary = {
  id: number;
  username: string;
  email: string;
  access_role: UserRole;
  employee_id: string;
  name: string;
  department: string;
  is_active: boolean;
};

export type AuditLog = {
  id: number;
  actor: string | null;
  action: string;
  entity: string;
  entity_id: string;
  summary: string;
  metadata: Record<string, unknown>;
  created_at: string;
};

export type WorkLog = {
  id: number;
  employee?: Employee;
  name: string;
  department: string;
  log_date: string;
  project: string;
  task_type: string;
  hours: string;
  productivity_score: number;
  overtime_hours: string;
  notes: string;
};

export type Attendance = {
  id: number;
  employee?: Employee;
  name: string;
  department: string;
  work_date: string;
  status: "Present" | "Leave" | "Absent";
  check_in: string | null;
  check_out: string | null;
  late_minutes: number;
};

export type Summary = {
  total_employees: number;
  active_employees: number;
  total_hours: number;
  avg_productivity: number;
  overtime_hours: number;
  work_logs: number;
  attendance_rate: number;
  late_minutes: number;
  absence_count: number;
};

export type Insight = {
  title: string;
  detail: string;
};

export type Dashboard = {
  summary: Summary;
  hours_by_department: [string, number][];
  productivity_by_department: [string, number][];
  hours_by_task: [string, number][];
  overtime_by_department: [string, number][];
  top_projects: [string, number][];
  employee_performance: Array<{
    employee_id: string;
    name: string;
    department: string;
    role: string;
    log_count: number;
    total_hours: number;
    avg_productivity: number;
    overtime_hours: number;
    avg_daily_hours: number;
  }>;
  hours_trend: [string, number][];
  productivity_trend: [string, number][];
  attendance_breakdown: [string, number][];
  late_by_department: [string, number][];
  workload_heatmap: [string, string, number][];
  ideal_vs_actual: [string, number, number, number][];
  sunburst: unknown;
};

export type OptionsPayload = {
  departments: string[];
  employees: Array<{ id: string; label: string }>;
  task_types: string[];
  projects: string[];
  statuses: string[];
  roles: UserRole[];
};

export type Filters = {
  date_from?: string;
  date_to?: string;
  department?: string;
  employee_id?: string;
  task_type?: string;
  project?: string;
};

export type InsightsPayload = {
  summary: string;
  insights: Insight[];
};
