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
const STORAGE_KEY = "workpulse-demo-data-v2";
type DemoWorkLog = Omit<WorkLog, "name" | "department" | "employee"> & { employee_id: string };
type DemoAttendance = Omit<Attendance, "name" | "department" | "employee"> & { employee_id: string };

let employees = structuredClone(demoData.employees) as Employee[];
let projects = structuredClone(demoData.projects) as Project[];
let users = structuredClone(demoData.users) as UserSummary[];
let auditLogs = structuredClone(demoData.audit) as AuditLog[];
let rawLogs = structuredClone(demoData.logs) as DemoWorkLog[];
let rawAttendance = structuredClone(demoData.attendance) as DemoAttendance[];
let hydrated = false;

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

function hydrateDemoData() {
  if (hydrated) return;
  hydrated = true;
  if (typeof window === "undefined") return;

  try {
    const saved = window.localStorage.getItem(STORAGE_KEY);
    if (!saved) return;
    const state = JSON.parse(saved) as {
      employees: Employee[];
      projects: Project[];
      users: UserSummary[];
      auditLogs: AuditLog[];
      rawLogs: DemoWorkLog[];
      rawAttendance: DemoAttendance[];
    };
    employees = state.employees;
    projects = state.projects;
    users = state.users;
    auditLogs = state.auditLogs;
    rawLogs = state.rawLogs;
    rawAttendance = state.rawAttendance;
  } catch {
    window.localStorage.removeItem(STORAGE_KEY);
  }
}

function persistDemoData() {
  if (typeof window === "undefined") return;
  window.localStorage.setItem(
    STORAGE_KEY,
    JSON.stringify({ employees, projects, users, auditLogs, rawLogs, rawAttendance })
  );
}

export function isLocalDemoToken(token?: string | null) {
  return Boolean(token?.startsWith(TOKEN_PREFIX));
}

function roleFromToken(token: string): UserRole {
  const role = token.replace(TOKEN_PREFIX, "") as UserRole;
  return role in roleUsers ? role : "employee";
}

function allowedEmployeeIds(token: string) {
  hydrateDemoData();
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
  hydrateDemoData();
  return employees.find((employee) => employee.employee_id === employeeId);
}

function recordAudit(token: string, action: string, entity: string, entityId: string | number, summary: string) {
  auditLogs.unshift({
    id: Math.max(0, ...auditLogs.map((log) => log.id)) + 1,
    actor: roleUsers[roleFromToken(token)].username,
    action,
    entity,
    entity_id: String(entityId),
    summary,
    metadata: { source: "browser-demo" },
    created_at: new Date().toISOString()
  });
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
  hydrateDemoData();
  return { token: `${TOKEN_PREFIX}${role}`, user: roleUsers[role] };
}

export function localOptions(token: string): OptionsPayload {
  hydrateDemoData();
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
  hydrateDemoData();
  const allowed = allowedEmployeeIds(token);
  return rawLogs.filter((row) => allowed.includes(row.employee_id) && matchesFilters(row, filters)).map(enrichLog);
}

export function localAttendance(token: string, filters: Filters): Attendance[] {
  hydrateDemoData();
  const allowed = allowedEmployeeIds(token);
  return rawAttendance.filter((row) => allowed.includes(row.employee_id) && matchesFilters(row, filters)).map(enrichAttendance);
}

export function localDashboard(token: string, filters: Filters): Dashboard {
  hydrateDemoData();
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
  hydrateDemoData();
  return employees.filter((employee) => allowedEmployeeIds(token).includes(employee.employee_id));
}

export function localSaveEmployee(token: string, payload: Record<string, string>) {
  hydrateDemoData();
  if (employees.some((employee) => employee.employee_id === payload.employee_id)) {
    throw new Error(`Employee ${payload.employee_id} already exists.`);
  }
  const employee = { ...payload, manager_employee_id: payload.manager_employee_id || null } as unknown as Employee;
  employees.push(employee);
  recordAudit(token, "create", "employee", employee.employee_id, `Created employee ${employee.name}`);
  persistDemoData();
  return employee;
}

export function localUpdateEmployee(token: string, employeeId: string, payload: Record<string, string>) {
  hydrateDemoData();
  const index = employees.findIndex((employee) => employee.employee_id === employeeId);
  if (index < 0) throw new Error("Employee not found.");
  employees[index] = { ...employees[index], ...payload };
  recordAudit(token, "update", "employee", employeeId, `Updated employee ${employees[index].name}`);
  persistDemoData();
  return employees[index];
}

export function localDeleteEmployee(token: string, employeeId: string) {
  hydrateDemoData();
  const index = employees.findIndex((employee) => employee.employee_id === employeeId);
  if (index < 0) throw new Error("Employee not found.");
  const [employee] = employees.splice(index, 1);
  rawLogs = rawLogs.filter((log) => log.employee_id !== employeeId);
  rawAttendance = rawAttendance.filter((row) => row.employee_id !== employeeId);
  users = users.filter((user) => user.employee_id !== employeeId);
  recordAudit(token, "delete", "employee", employeeId, `Deleted employee ${employee.name}`);
  persistDemoData();
}

export function localSaveLog(token: string, payload: Record<string, string>) {
  hydrateDemoData();
  const employeeId = payload.employee_id || roleUsers[roleFromToken(token)].employee_id || "EMP001";
  if (!employeeById(employeeId)) throw new Error("Employee not found.");
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
  recordAudit(token, "create", "work_log", row.id, `Created timesheet for ${employeeById(employeeId)?.name}`);
  persistDemoData();
  return enrichLog(row);
}

export function localUpdateLog(token: string, id: number, payload: Record<string, string>) {
  hydrateDemoData();
  const index = rawLogs.findIndex((log) => log.id === id);
  if (index < 0) throw new Error("Timesheet not found.");
  rawLogs[index] = {
    ...rawLogs[index],
    ...payload,
    employee_id: payload.employee_id || rawLogs[index].employee_id,
    productivity_score: Number(payload.productivity_score ?? rawLogs[index].productivity_score)
  };
  recordAudit(token, "update", "work_log", id, `Updated timesheet for ${employeeById(rawLogs[index].employee_id)?.name}`);
  persistDemoData();
  return enrichLog(rawLogs[index]);
}

export function localDeleteLog(token: string, id: number) {
  hydrateDemoData();
  const index = rawLogs.findIndex((log) => log.id === id);
  if (index < 0) throw new Error("Timesheet not found.");
  const [row] = rawLogs.splice(index, 1);
  recordAudit(token, "delete", "work_log", id, `Deleted timesheet for ${employeeById(row.employee_id)?.name}`);
  persistDemoData();
}

export function localSaveAttendance(token: string, payload: Record<string, string>) {
  hydrateDemoData();
  const employeeId = payload.employee_id || roleUsers[roleFromToken(token)].employee_id || "EMP001";
  if (!employeeById(employeeId)) throw new Error("Employee not found.");
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
    recordAudit(token, "update", "attendance", existing.id, `Updated attendance for ${employeeById(employeeId)?.name}`);
    persistDemoData();
    return enrichAttendance(existing);
  }
  const row = { id: Math.max(0, ...rawAttendance.map((item) => item.id)) + 1, ...values };
  rawAttendance.unshift(row);
  recordAudit(token, "create", "attendance", row.id, `Saved attendance for ${employeeById(employeeId)?.name}`);
  persistDemoData();
  return enrichAttendance(row);
}

export function localUpdateAttendance(token: string, id: number, payload: Record<string, string>) {
  hydrateDemoData();
  const index = rawAttendance.findIndex((row) => row.id === id);
  if (index < 0) throw new Error("Attendance record not found.");
  rawAttendance[index] = {
    ...rawAttendance[index],
    ...payload,
    employee_id: payload.employee_id || rawAttendance[index].employee_id,
    status: (payload.status || rawAttendance[index].status) as Attendance["status"],
    check_in: payload.check_in || null,
    check_out: payload.check_out || null,
    late_minutes: Number(payload.late_minutes ?? rawAttendance[index].late_minutes)
  };
  recordAudit(token, "update", "attendance", id, `Updated attendance for ${employeeById(rawAttendance[index].employee_id)?.name}`);
  persistDemoData();
  return enrichAttendance(rawAttendance[index]);
}

export function localDeleteAttendance(token: string, id: number) {
  hydrateDemoData();
  const index = rawAttendance.findIndex((row) => row.id === id);
  if (index < 0) throw new Error("Attendance record not found.");
  const [row] = rawAttendance.splice(index, 1);
  recordAudit(token, "delete", "attendance", id, `Deleted attendance for ${employeeById(row.employee_id)?.name}`);
  persistDemoData();
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
  hydrateDemoData();
  return projects;
}

export function localSaveProject(token: string, payload: Record<string, string>) {
  hydrateDemoData();
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
  recordAudit(token, "create", "project", project.id, `Created project ${project.name}`);
  persistDemoData();
  return project;
}

export function localUpdateProject(token: string, id: number, payload: Record<string, string>) {
  hydrateDemoData();
  const index = projects.findIndex((project) => project.id === id);
  if (index < 0) throw new Error("Project not found.");
  projects[index] = { ...projects[index], ...payload, status: payload.status as Project["status"], updated_at: new Date().toISOString() };
  recordAudit(token, "update", "project", id, `Updated project ${projects[index].name}`);
  persistDemoData();
  return projects[index];
}

export function localDeleteProject(token: string, id: number) {
  hydrateDemoData();
  const index = projects.findIndex((project) => project.id === id);
  if (index < 0) throw new Error("Project not found.");
  const [project] = projects.splice(index, 1);
  recordAudit(token, "delete", "project", id, `Deleted project ${project.name}`);
  persistDemoData();
}

export function localUsers() {
  hydrateDemoData();
  return users;
}

export function localCreateUser(token: string, payload: Record<string, string>): AuthUser {
  hydrateDemoData();
  if (users.some((user) => user.username === payload.username)) {
    throw new Error(`Username ${payload.username} already exists.`);
  }
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
  recordAudit(token, "create", "user", user.id, `Created user ${user.username}`);
  persistDemoData();
  return {
    username: user.username,
    email: user.email,
    role: user.access_role,
    employee_id: user.employee_id || null,
    name: user.name,
    department: user.department
  };
}

export function localUpdateUser(token: string, id: number, payload: Record<string, string>) {
  hydrateDemoData();
  const index = users.findIndex((user) => user.id === id);
  if (index < 0) throw new Error("User not found.");
  users[index] = {
    ...users[index],
    ...payload,
    access_role: (payload.access_role || users[index].access_role) as UserRole,
    is_active: payload.is_active === undefined ? users[index].is_active : payload.is_active === "true"
  };
  recordAudit(token, "update", "user", id, `Updated user ${users[index].username}`);
  persistDemoData();
  return users[index];
}

export function localDeleteUser(token: string, id: number) {
  hydrateDemoData();
  const index = users.findIndex((user) => user.id === id);
  if (index < 0) throw new Error("User not found.");
  const [user] = users.splice(index, 1);
  recordAudit(token, "delete", "user", id, `Deleted user ${user.username}`);
  persistDemoData();
}

export function localAuditLogs() {
  hydrateDemoData();
  return auditLogs;
}

export function localReportHtml(token: string, filters: Filters) {
  const dashboard = localDashboard(token, filters);
  const insights = localInsights(token, filters);
  return `<!doctype html><html><head><title>WorkPulse Report</title></head><body><h1>WorkPulse Report</h1><p>${insights.summary}</p><h2>Summary</h2><ul><li>Total hours: ${dashboard.summary.total_hours}</li><li>Productivity: ${dashboard.summary.avg_productivity}%</li><li>Attendance: ${dashboard.summary.attendance_rate}%</li><li>Overtime: ${dashboard.summary.overtime_hours}</li></ul></body></html>`;
}
