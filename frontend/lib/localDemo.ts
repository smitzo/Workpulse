import demoData from "@/data/demo.json";
import type {
  Attendance,
  AuditLog,
  AuthPayload,
  AuthUser,
  Dashboard,
  Employee,
  Filters,
  InsightsPayload,
  OptionsPayload,
  Project,
  UserRole,
  UserSummary,
  WorkLog
} from "@/types/api";

const TOKEN_PREFIX = "local-demo:";
const employees = structuredClone(demoData.employees) as Employee[];
const projects = structuredClone(demoData.projects) as Project[];
const users = structuredClone(demoData.users) as UserSummary[];
const auditLogs = structuredClone(demoData.audit) as AuditLog[];
const rawLogs = structuredClone(demoData.logs) as Array<Omit<WorkLog, "name" | "department" | "employee"> & { employee_id: string }>;
const rawAttendance = structuredClone(demoData.attendance) as Array<Omit<Attendance, "name" | "department" | "employee"> & { employee_id: string }>;

const roleUsers: Record<UserRole, AuthUser> = {
  employee: {
    username: "demouser",
    email: "employee@workpulse.demo",
    role: "employee",
    employee_id: "EMP001",
    name: "Aarav Sharma",
    department: "Engineering"
  },
  manager: {
    username: "demomanager",
    email: "manager@workpulse.demo",
    role: "manager",
    employee_id: "EMP006",
    name: "Priya Menon",
    department: "Engineering"
  },
  admin: {
    username: "demoadmin",
    email: "admin@workpulse.demo",
    role: "admin",
    employee_id: null,
    name: "Demo Admin",
    department: null
  }
};

export function isLocalDemoToken(token?: string | null) {
  return Boolean(token?.startsWith(TOKEN_PREFIX));
}

function roleFromToken(token: string): UserRole {
  const role = token.replace(TOKEN_PREFIX, "") as UserRole;
  return role in roleUsers ? role : "employee";
}

function allowedEmployeeIds(token: string) {
  const role = roleFromToken(token);
  if (role === "admin") {
    return employees.map((employee) => employee.employee_id);
  }
  if (role === "manager") {
    return ["EMP006", ...employees.filter((employee) => employee.manager_employee_id === "EMP006").map((employee) => employee.employee_id)];
  }
  return ["EMP001"];
}

function employeeById(employeeId: string) {
  return employees.find((employee) => employee.employee_id === employeeId);
}

function matchesFilters(
  row: { employee_id: string; log_date?: string; work_date?: string; project?: string; task_type?: string },
  filters: Filters
) {
  const date = row.log_date || row.work_date || "";
  const employee = employeeById(row.employee_id);
  return (
    (!filters.date_from || date >= filters.date_from) &&
    (!filters.date_to || date <= filters.date_to) &&
    (!filters.employee_id || filters.employee_id === "All" || row.employee_id === filters.employee_id) &&
    (!filters.department || filters.department === "All" || employee?.department === filters.department) &&
    (!filters.project || filters.project === "All" || row.project === filters.project) &&
    (!filters.task_type || filters.task_type === "All" || row.task_type === filters.task_type)
  );
}

function enrichLog(row: (typeof rawLogs)[number]): WorkLog {
  const employee = employeeById(row.employee_id)!;
  return { ...row, employee, name: employee.name, department: employee.department };
}

function enrichAttendance(row: (typeof rawAttendance)[number]): Attendance {
  const employee = employeeById(row.employee_id)!;
  return { ...row, employee, name: employee.name, department: employee.department };
}

function groupedTotal(rows: Array<{ key: string; value: number }>): [string, number][] {
  const totals = new Map<string, number>();
  rows.forEach(({ key, value }) => totals.set(key, (totals.get(key) || 0) + value));
  return [...totals.entries()].map(([key, value]) => [key, Number(value.toFixed(2))]);
}

function average(values: number[]) {
  return values.length ? values.reduce((total, value) => total + value, 0) / values.length : 0;
}

export function localDemoLogin(role: UserRole): AuthPayload {
  return { token: `${TOKEN_PREFIX}${role}`, user: roleUsers[role] };
}

export function localOptions(token: string): OptionsPayload {
  const scopedEmployees = employees.filter((employee) => allowedEmployeeIds(token).includes(employee.employee_id));
  return {
    departments: ["All", ...new Set(scopedEmployees.map((employee) => employee.department))],
    employees: scopedEmployees.map((employee) => ({ id: employee.employee_id, label: `${employee.employee_id} - ${employee.name}` })),
    task_types: ["All", ...new Set(rawLogs.map((log) => log.task_type))],
    projects: ["All", ...projects.map((project) => project.name)],
    statuses: ["Active", "On Leave", "Inactive"],
    roles: ["employee", "manager", "admin"]
  };
}

export function localLogs(token: string, filters: Filters): WorkLog[] {
  const allowed = allowedEmployeeIds(token);
  return rawLogs.filter((row) => allowed.includes(row.employee_id) && matchesFilters(row, filters)).map(enrichLog);
}

export function localAttendance(token: string, filters: Filters): Attendance[] {
  const allowed = allowedEmployeeIds(token);
  return rawAttendance.filter((row) => allowed.includes(row.employee_id) && matchesFilters(row, filters)).map(enrichAttendance);
}

export function localDashboard(token: string, filters: Filters): Dashboard {
  const scopedEmployees = employees.filter((employee) => allowedEmployeeIds(token).includes(employee.employee_id));
  const logs = localLogs(token, filters);
  const attendance = localAttendance(token, filters);
  const totalHours = logs.reduce((total, log) => total + Number(log.hours), 0);
  const overtime = logs.reduce((total, log) => total + Number(log.overtime_hours), 0);
  const present = attendance.filter((row) => row.status === "Present").length;

  const performance = scopedEmployees.map((employee) => {
    const employeeLogs = logs.filter((log) => log.employee?.employee_id === employee.employee_id);
    const hours = employeeLogs.reduce((total, log) => total + Number(log.hours), 0);
    return {
      employee_id: employee.employee_id,
      name: employee.name,
      department: employee.department,
      role: employee.role,
      log_count: employeeLogs.length,
      total_hours: Number(hours.toFixed(2)),
      avg_productivity: Math.round(average(employeeLogs.map((log) => log.productivity_score))),
      overtime_hours: Number(employeeLogs.reduce((total, log) => total + Number(log.overtime_hours), 0).toFixed(2)),
      avg_daily_hours: Number((hours / Math.max(1, new Set(employeeLogs.map((log) => log.log_date)).size)).toFixed(2))
    };
  });

  const taskActual = groupedTotal(logs.map((log) => ({ key: log.task_type, value: Number(log.hours) })));
  const ideals: Record<string, number> = {
    "Project Work": 7.2,
    "Client Support": 6.4,
    Training: 4,
    Documentation: 5.5,
    Planning: 3.5,
    Review: 4.2
  };

  return {
    summary: {
      total_employees: scopedEmployees.length,
      active_employees: scopedEmployees.filter((employee) => employee.status === "Active").length,
      total_hours: Number(totalHours.toFixed(2)),
      avg_productivity: Math.round(average(logs.map((log) => log.productivity_score))),
      overtime_hours: Number(overtime.toFixed(2)),
      work_logs: logs.length,
      attendance_rate: Math.round((present / Math.max(1, attendance.length)) * 100),
      late_minutes: attendance.reduce((total, row) => total + row.late_minutes, 0),
      absence_count: attendance.filter((row) => row.status === "Absent").length
    },
    hours_by_department: groupedTotal(logs.map((log) => ({ key: log.department, value: Number(log.hours) }))),
    productivity_by_department: groupedTotal(
      [...new Set(logs.map((log) => log.department))].map((department) => ({
        key: department,
        value: Math.round(average(logs.filter((log) => log.department === department).map((log) => log.productivity_score)))
      }))
    ),
    hours_by_task: taskActual,
    overtime_by_department: groupedTotal(logs.map((log) => ({ key: log.department, value: Number(log.overtime_hours) }))),
    top_projects: groupedTotal(logs.map((log) => ({ key: log.project, value: Number(log.hours) }))),
    employee_performance: performance,
    hours_trend: groupedTotal(logs.map((log) => ({ key: log.log_date, value: Number(log.hours) }))).sort(([a], [b]) => a.localeCompare(b)),
    productivity_trend: [...new Set(logs.map((log) => log.log_date))]
      .sort()
      .map((date) => [date, Math.round(average(logs.filter((log) => log.log_date === date).map((log) => log.productivity_score)))]),
    attendance_breakdown: ["Present", "Leave", "Absent"].map((status) => [
      status,
      attendance.filter((row) => row.status === status).length
    ]),
    late_by_department: groupedTotal(attendance.map((row) => ({ key: row.department, value: row.late_minutes }))),
    workload_heatmap: logs.map((log) => [log.name, log.log_date, Number(log.hours)]),
    ideal_vs_actual: taskActual.map(([task, actual]) => {
      const ideal = ideals[task] || 0;
      return [task, actual, ideal, Number((actual - ideal).toFixed(2))];
    }),
    sunburst: {}
  };
}

export function localInsights(token: string, filters: Filters): InsightsPayload {
  const dashboard = localDashboard(token, filters);
  const summary = dashboard.summary;
  return {
    summary: `${summary.total_hours} hours logged with ${summary.avg_productivity}% average productivity and ${summary.attendance_rate}% attendance.`,
    insights: [
      { title: "Delivery health", detail: `Productivity is tracking at ${summary.avg_productivity}% across the selected workspace.` },
      { title: "Attendance signal", detail: `${summary.attendance_rate}% attendance with ${summary.late_minutes} total late minutes.` },
      { title: "Workload", detail: `${summary.work_logs} timesheet entries include ${summary.overtime_hours} overtime hours.` }
    ]
  };
}

export function localEmployees(token: string) {
  return employees.filter((employee) => allowedEmployeeIds(token).includes(employee.employee_id));
}

export function localSaveEmployee(payload: Record<string, string>) {
  const employee = payload as unknown as Employee;
  employees.push(employee);
  return employee;
}

export function localUpdateEmployee(employeeId: string, payload: Record<string, string>) {
  const index = employees.findIndex((employee) => employee.employee_id === employeeId);
  employees[index] = { ...employees[index], ...payload };
  return employees[index];
}

export function localDeleteEmployee(employeeId: string) {
  const index = employees.findIndex((employee) => employee.employee_id === employeeId);
  if (index >= 0) employees.splice(index, 1);
}

export function localSaveLog(token: string, payload: Record<string, string>) {
  const employeeId = payload.employee_id || roleUsers[roleFromToken(token)].employee_id || "EMP001";
  const row = {
    id: Math.max(0, ...rawLogs.map((log) => log.id)) + 1,
    employee_id: employeeId,
    log_date: payload.log_date,
    project: payload.project,
    task_type: payload.task_type,
    hours: payload.hours,
    productivity_score: Number(payload.productivity_score),
    overtime_hours: payload.overtime_hours || "0",
    notes: payload.notes || ""
  };
  rawLogs.unshift(row);
  return enrichLog(row);
}

export function localDeleteLog(id: number) {
  const index = rawLogs.findIndex((log) => log.id === id);
  if (index >= 0) rawLogs.splice(index, 1);
}

export function localSaveAttendance(token: string, payload: Record<string, string>) {
  const employeeId = payload.employee_id || roleUsers[roleFromToken(token)].employee_id || "EMP001";
  const existing = rawAttendance.find((row) => row.employee_id === employeeId && row.work_date === payload.work_date);
  const values = {
    employee_id: employeeId,
    work_date: payload.work_date,
    status: payload.status as Attendance["status"],
    check_in: payload.check_in || null,
    check_out: payload.check_out || null,
    late_minutes: Number(payload.late_minutes || 0)
  };
  if (existing) {
    Object.assign(existing, values);
    return enrichAttendance(existing);
  }
  const row = { id: Math.max(0, ...rawAttendance.map((item) => item.id)) + 1, ...values };
  rawAttendance.unshift(row);
  return enrichAttendance(row);
}

export function localMarkAttendanceToday(token: string) {
  const date = new Date();
  date.setMinutes(date.getMinutes() - date.getTimezoneOffset());
  return localSaveAttendance(token, {
    work_date: date.toISOString().slice(0, 10),
    status: "Present",
    check_in: new Date().toTimeString().slice(0, 8),
    late_minutes: "0"
  });
}

export function localProjects() {
  return projects;
}

export function localSaveProject(payload: Record<string, string>) {
  const now = new Date().toISOString();
  const project: Project = {
    id: Math.max(0, ...projects.map((item) => item.id)) + 1,
    name: payload.name,
    owner: payload.owner || "",
    status: payload.status as Project["status"],
    description: payload.description || "",
    created_at: now,
    updated_at: now
  };
  projects.push(project);
  return project;
}

export function localUpdateProject(id: number, payload: Record<string, string>) {
  const index = projects.findIndex((project) => project.id === id);
  projects[index] = { ...projects[index], ...payload, status: payload.status as Project["status"], updated_at: new Date().toISOString() };
  return projects[index];
}

export function localDeleteProject(id: number) {
  const index = projects.findIndex((project) => project.id === id);
  if (index >= 0) projects.splice(index, 1);
}

export function localUsers() {
  return users;
}

export function localCreateUser(payload: Record<string, string>): AuthUser {
  const user: UserSummary = {
    id: Math.max(0, ...users.map((item) => item.id)) + 1,
    username: payload.username,
    email: payload.email || "",
    access_role: payload.access_role as UserRole,
    employee_id: payload.employee_id,
    name: payload.name,
    department: payload.department,
    is_active: true
  };
  users.push(user);
  return {
    username: user.username,
    email: user.email,
    role: user.access_role,
    employee_id: user.employee_id || null,
    name: user.name,
    department: user.department
  };
}

export function localAuditLogs() {
  return auditLogs;
}

export function localReportHtml(token: string, filters: Filters) {
  const dashboard = localDashboard(token, filters);
  const insights = localInsights(token, filters);
  return `<!doctype html><html><head><title>WorkPulse Report</title></head><body><h1>WorkPulse Report</h1><p>${insights.summary}</p><h2>Summary</h2><ul><li>Total hours: ${dashboard.summary.total_hours}</li><li>Productivity: ${dashboard.summary.avg_productivity}%</li><li>Attendance: ${dashboard.summary.attendance_rate}%</li><li>Overtime: ${dashboard.summary.overtime_hours}</li></ul></body></html>`;
}
