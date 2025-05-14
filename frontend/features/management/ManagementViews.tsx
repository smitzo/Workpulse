"use client";

import { CalendarCheck, CheckCircle2, ClipboardList, Clock3, FolderKanban, Pencil, Save, ShieldCheck, Trash2, UserPlus, Users, X } from "lucide-react";
import type { FormEvent } from "react";
import { useEffect, useState } from "react";

import {
  deleteAttendance,
  deleteEmployee,
  deleteLog,
  deleteProject,
  deleteUser,
  getAttendance,
  getAuditLogs,
  getEmployees,
  getLogs,
  getProjects,
  getUsers,
  markAttendanceToday,
  createUser,
  saveAttendance,
  saveEmployee,
  saveLog,
  saveProject,
  updateAttendance,
  updateEmployee,
  updateLog,
  updateProject,
  updateUser
} from "@/lib/api";
import type { Attendance, AuditLog, AuthUser, Employee, Filters, OptionsPayload, Project, UserSummary, WorkLog } from "@/types/api";

type ManagementProps = {
  active: string;
  filters: Filters;
  options: OptionsPayload | null;
  token: string;
  user: AuthUser;
  setMessage: (message: string) => void;
  afterChange: () => void;
};

function formValues(form: HTMLFormElement) {
  return Object.fromEntries(new FormData(form).entries()) as Record<string, string>;
}

function today() {
  const date = new Date();
  date.setMinutes(date.getMinutes() - date.getTimezoneOffset());
  return date.toISOString().slice(0, 10);
}

function currentTime() {
  const date = new Date();
  return `${String(date.getHours()).padStart(2, "0")}:${String(date.getMinutes()).padStart(2, "0")}`;
}

export function ManagementViews({ active, filters, options, token, user, setMessage, afterChange }: ManagementProps) {
  if (active === "employees") {
    return <EmployeesPanel token={token} user={user} setMessage={setMessage} afterChange={afterChange} />;
  }
  if (active === "projects") {
    return <ProjectsPanel token={token} setMessage={setMessage} afterChange={afterChange} />;
  }
  if (active === "users") {
    return <UsersPanel token={token} options={options} setMessage={setMessage} afterChange={afterChange} />;
  }
  if (active === "audit") {
    return <AuditPanel token={token} setMessage={setMessage} />;
  }
  if (active === "logs") {
    return <LogsPanel filters={filters} options={options} token={token} user={user} setMessage={setMessage} afterChange={afterChange} />;
  }
  return <AttendancePanel filters={filters} options={options} token={token} user={user} setMessage={setMessage} afterChange={afterChange} />;
}

function EmployeesPanel({ token, user, setMessage, afterChange }: Pick<ManagementProps, "token" | "user" | "setMessage" | "afterChange">) {
  const [employees, setEmployees] = useState<Employee[]>([]);
  const [editingId, setEditingId] = useState<string | null>(null);
  const [draftEmployee, setDraftEmployee] = useState<Employee | null>(null);

  async function load() {
    setEmployees(await getEmployees(token));
  }

  useEffect(() => {
    load().catch((error) => setMessage(error instanceof Error ? error.message : "Could not load employees."));
    // eslint-disable-next-line react-hooks/exhaustive-deps
  }, []);

  async function submit(event: FormEvent<HTMLFormElement>) {
    event.preventDefault();
    if (user.role !== "admin") {
      setMessage("Only admins can manage employees.");
      return;
    }
    try {
      const payload = formValues(event.currentTarget);
      await saveEmployee(token, payload);
      event.currentTarget.reset();
      await load();
      afterChange();
      setMessage("Employee saved.");
    } catch (error) {
      setMessage(error instanceof Error ? error.message : "Could not save employee.");
    }
  }

  async function remove(employeeId: string) {
    try {
      await deleteEmployee(token, employeeId);
      await load();
      afterChange();
      setMessage("Employee deleted.");
    } catch (error) {
      setMessage(error instanceof Error ? error.message : "Could not delete employee.");
    }
  }

  function startEditing(employee: Employee) {
    setEditingId(employee.employee_id);
    setDraftEmployee({ ...employee });
  }

  function updateDraft(key: keyof Employee, value: string) {
    setDraftEmployee((current) => (current ? { ...current, [key]: value } : current));
  }

  async function saveInlineEmployee() {
    if (!draftEmployee) {
      return;
    }
    try {
      await updateEmployee(token, draftEmployee.employee_id, draftEmployee as unknown as Record<string, string>);
      setEditingId(null);
      setDraftEmployee(null);
      await load();
      afterChange();
      setMessage("Employee updated inline.");
    } catch (error) {
      setMessage(error instanceof Error ? error.message : "Could not update employee.");
    }
  }

  return (
    <section className="management-grid">
      {user.role === "admin" && (
        <form className="panel form-panel" onSubmit={submit}>
          <header>
            <div className="panel-title">
              <Users size={18} />
              <h2>Add Employee</h2>
            </div>
          </header>
          <div className="form-grid">
            <label>ID<input name="employee_id" required /></label>
            <label>Name<input name="name" required /></label>
            <label>Department<input name="department" required /></label>
            <label>Role<input name="role" required /></label>
            <label>Location<input name="location" required /></label>
            <label>Manager<input name="manager" defaultValue="Unassigned" required /></label>
            <label>Hire date<input name="hire_date" type="date" defaultValue={today()} required /></label>
            <label>Status<select name="status" defaultValue="Active"><option>Active</option><option>On Leave</option><option>Inactive</option></select></label>
            <button className="primary-btn form-submit" type="submit"><Save size={16} />Save employee</button>
          </div>
        </form>
      )}
      <article className="panel table-panel wide">
        <header>
          <h2>Employees</h2>
        </header>
        <div className="table-wrap">
          <table>
            <thead><tr><th>ID</th><th>Name</th><th>Department</th><th>Role</th><th>Location</th><th>Manager</th><th>Hire Date</th><th>Status</th><th></th></tr></thead>
            <tbody>
              {employees.map((employee) => (
                <tr key={employee.employee_id}>
                  <td>{employee.employee_id}</td>
                  {editingId === employee.employee_id && draftEmployee ? (
                    <>
                      <td><input aria-label="Name" value={draftEmployee.name} onChange={(event) => updateDraft("name", event.target.value)} /></td>
                      <td><input aria-label="Department" value={draftEmployee.department} onChange={(event) => updateDraft("department", event.target.value)} /></td>
                      <td><input aria-label="Role" value={draftEmployee.role} onChange={(event) => updateDraft("role", event.target.value)} /></td>
                      <td><input aria-label="Location" value={draftEmployee.location} onChange={(event) => updateDraft("location", event.target.value)} /></td>
                      <td><input aria-label="Manager" value={draftEmployee.manager} onChange={(event) => updateDraft("manager", event.target.value)} /></td>
                      <td><input aria-label="Hire date" type="date" value={draftEmployee.hire_date} onChange={(event) => updateDraft("hire_date", event.target.value)} /></td>
                      <td><select aria-label="Status" value={draftEmployee.status} onChange={(event) => updateDraft("status", event.target.value)}><option>Active</option><option>On Leave</option><option>Inactive</option></select></td>
                    </>
                  ) : (
                    <>
                      <td>{employee.name}</td>
                      <td>{employee.department}</td>
                      <td>{employee.role}</td>
                      <td>{employee.location}</td>
                      <td>{employee.manager}</td>
                      <td>{employee.hire_date}</td>
                      <td>{employee.status}</td>
                    </>
                  )}
                  <td className="row-actions">
                    {user.role === "admin" && editingId === employee.employee_id && (
                      <>
                        <button className="secondary-btn compact" type="button" onClick={saveInlineEmployee}><Save size={14} />Save</button>
                        <button className="secondary-btn compact" type="button" onClick={() => { setEditingId(null); setDraftEmployee(null); }}><X size={14} />Cancel</button>
                      </>
                    )}
                    {user.role === "admin" && editingId !== employee.employee_id && <button className="secondary-btn compact" type="button" onClick={() => startEditing(employee)}><Pencil size={14} />Edit</button>}
                    {user.role === "admin" && editingId !== employee.employee_id && <button className="danger-btn" type="button" onClick={() => remove(employee.employee_id)}><Trash2 size={14} />Delete</button>}
                  </td>
                </tr>
              ))}
            </tbody>
          </table>
        </div>
      </article>
    </section>
  );
}

function ProjectsPanel({ token, setMessage, afterChange }: Pick<ManagementProps, "token" | "setMessage" | "afterChange">) {
  const [projects, setProjects] = useState<Project[]>([]);
  const [editingId, setEditingId] = useState<number | null>(null);
  const [draftProject, setDraftProject] = useState<Project | null>(null);

  async function load() {
    setProjects(await getProjects(token));
  }

  useEffect(() => {
    load().catch((error) => setMessage(error instanceof Error ? error.message : "Could not load projects."));
    // eslint-disable-next-line react-hooks/exhaustive-deps
  }, []);

  async function submit(event: FormEvent<HTMLFormElement>) {
    event.preventDefault();
    try {
      const payload = formValues(event.currentTarget);
      await saveProject(token, payload);
      event.currentTarget.reset();
      await load();
      afterChange();
      setMessage("Project created.");
    } catch (error) {
      setMessage(error instanceof Error ? error.message : "Could not save project.");
    }
  }

  async function remove(project: Project) {
    try {
      await deleteProject(token, project.id);
      await load();
      afterChange();
      setMessage("Project deleted.");
    } catch (error) {
      setMessage(error instanceof Error ? error.message : "Could not delete project.");
    }
  }

  function startEditing(project: Project) {
    setEditingId(project.id);
    setDraftProject({ ...project });
  }

  function updateDraft(key: keyof Project, value: string) {
    setDraftProject((current) => (current ? { ...current, [key]: value } : current));
  }

  async function saveInlineProject() {
    if (!draftProject) {
      return;
    }
    try {
      await updateProject(token, draftProject.id, {
        name: draftProject.name,
        owner: draftProject.owner,
        status: draftProject.status,
        description: draftProject.description
      });
      setEditingId(null);
      setDraftProject(null);
      await load();
      afterChange();
      setMessage("Project updated inline.");
    } catch (error) {
      setMessage(error instanceof Error ? error.message : "Could not update project.");
    }
  }

  return (
    <section className="management-grid">
      <form className="panel form-panel" onSubmit={submit}>
        <header><div className="panel-title"><FolderKanban size={18} /><h2>Create Project</h2></div></header>
        <div className="form-grid">
          <label>Project name<input name="name" required /></label>
          <label>Owner<input name="owner" /></label>
          <label>Status<select name="status" defaultValue="Active"><option>Active</option><option>Paused</option><option>Archived</option></select></label>
          <label className="span-2">Description<input name="description" /></label>
          <button className="primary-btn form-submit" type="submit"><Save size={16} />Save project</button>
        </div>
      </form>
      <article className="panel table-panel wide">
        <header><div className="panel-title"><FolderKanban size={18} /><h2>Projects</h2></div></header>
        <div className="table-wrap">
          <table>
            <thead><tr><th>Name</th><th>Owner</th><th>Status</th><th>Description</th><th></th></tr></thead>
            <tbody>{projects.map((project) => (
              <tr key={project.id}>
                {editingId === project.id && draftProject ? (
                  <>
                    <td><input aria-label="Project name" value={draftProject.name} onChange={(event) => updateDraft("name", event.target.value)} /></td>
                    <td><input aria-label="Owner" value={draftProject.owner} onChange={(event) => updateDraft("owner", event.target.value)} /></td>
                    <td><select aria-label="Status" value={draftProject.status} onChange={(event) => updateDraft("status", event.target.value)}><option>Active</option><option>Paused</option><option>Archived</option></select></td>
                    <td><input aria-label="Description" value={draftProject.description} onChange={(event) => updateDraft("description", event.target.value)} /></td>
                  </>
                ) : (
                  <>
                    <td>{project.name}</td><td>{project.owner}</td><td>{project.status}</td><td>{project.description}</td>
                  </>
                )}
                <td className="row-actions">
                  {editingId === project.id ? (
                    <>
                      <button className="secondary-btn compact" type="button" onClick={saveInlineProject}><Save size={14} />Save</button>
                      <button className="secondary-btn compact" type="button" onClick={() => { setEditingId(null); setDraftProject(null); }}><X size={14} />Cancel</button>
                    </>
                  ) : (
                    <>
                      <button className="secondary-btn compact" type="button" onClick={() => startEditing(project)}><Pencil size={14} />Edit</button>
                      <button className="danger-btn" type="button" onClick={() => remove(project)}><Trash2 size={14} />Delete</button>
                    </>
                  )}
                </td>
              </tr>
            ))}</tbody>
          </table>
        </div>
      </article>
    </section>
  );
}

function UsersPanel({ token, options, setMessage, afterChange }: Pick<ManagementProps, "token" | "options" | "setMessage" | "afterChange">) {
  const [users, setUsers] = useState<UserSummary[]>([]);
  const [editingId, setEditingId] = useState<number | null>(null);
  const [draftUser, setDraftUser] = useState<UserSummary | null>(null);

  async function load() {
    setUsers(await getUsers(token));
  }

  useEffect(() => {
    load().catch((error) => setMessage(error instanceof Error ? error.message : "Could not load users."));
    // eslint-disable-next-line react-hooks/exhaustive-deps
  }, []);

  async function submit(event: FormEvent<HTMLFormElement>) {
    event.preventDefault();
    try {
      await createUser(token, formValues(event.currentTarget));
      event.currentTarget.reset();
      await load();
      afterChange();
      setMessage("User created.");
    } catch (error) {
      setMessage(error instanceof Error ? error.message : "Could not create user.");
    }
  }

  function startEditing(user: UserSummary) {
    setEditingId(user.id);
    setDraftUser({ ...user });
  }

  function updateDraft(key: keyof UserSummary, value: string | boolean) {
    setDraftUser((current) => (current ? { ...current, [key]: value } : current));
  }

  async function saveInlineUser() {
    if (!draftUser) return;
    try {
      await updateUser(token, draftUser.id, {
        username: draftUser.username,
        email: draftUser.email,
        access_role: draftUser.access_role,
        employee_id: draftUser.employee_id,
        name: draftUser.name,
        department: draftUser.department,
        is_active: String(draftUser.is_active)
      });
      setEditingId(null);
      setDraftUser(null);
      await load();
      afterChange();
      setMessage("User updated.");
    } catch (error) {
      setMessage(error instanceof Error ? error.message : "Could not update user.");
    }
  }

  async function remove(id: number) {
    try {
      await deleteUser(token, id);
      await load();
      afterChange();
      setMessage("User deleted.");
    } catch (error) {
      setMessage(error instanceof Error ? error.message : "Could not delete user.");
    }
  }

  return (
    <section className="management-grid">
      <form className="panel form-panel" onSubmit={submit}>
        <header><div className="panel-title"><UserPlus size={18} /><h2>Create User</h2></div></header>
        <div className="form-grid">
          <label>Username<input name="username" required /></label>
          <label>Password<input name="password" type="password" required /></label>
          <label>Access role<select name="access_role" defaultValue="employee"><option value="employee">Employee</option><option value="manager">Manager</option><option value="admin">Admin</option></select></label>
          <label>Email<input name="email" type="email" /></label>
          <label>Employee ID<input name="employee_id" required /></label>
          <label>Name<input name="name" required /></label>
          <label>Department<input name="department" required /></label>
          <label>Job role<input name="role" required /></label>
          <label>Location<input name="location" defaultValue="Remote" required /></label>
          <label>Manager<select name="manager_employee_id"><option value="">Unassigned</option>{(options?.employees || []).map((employee) => <option key={employee.id} value={employee.id}>{employee.label}</option>)}</select></label>
          <label>Manager name<input name="manager" defaultValue="Unassigned" required /></label>
          <label>Hire date<input name="hire_date" type="date" defaultValue={today()} required /></label>
          <label>Status<select name="status" defaultValue="Active"><option>Active</option><option>On Leave</option><option>Inactive</option></select></label>
          <button className="primary-btn form-submit" type="submit"><Save size={16} />Create user</button>
        </div>
      </form>
      <article className="panel table-panel wide">
        <header><div className="panel-title"><Users size={18} /><h2>Users</h2></div></header>
        <div className="table-wrap">
          <table>
            <thead><tr><th>Username</th><th>Name</th><th>Email</th><th>Access</th><th>Employee</th><th>Department</th><th>Status</th><th></th></tr></thead>
            <tbody>{users.map((row) => (
              <tr key={row.id}>
                {editingId === row.id && draftUser ? (
                  <>
                    <td><input aria-label="Username" value={draftUser.username} onChange={(event) => updateDraft("username", event.target.value)} /></td>
                    <td><input aria-label="Name" value={draftUser.name} onChange={(event) => updateDraft("name", event.target.value)} /></td>
                    <td><input aria-label="Email" type="email" value={draftUser.email} onChange={(event) => updateDraft("email", event.target.value)} /></td>
                    <td><select aria-label="Access role" value={draftUser.access_role} onChange={(event) => updateDraft("access_role", event.target.value)}><option value="employee">Employee</option><option value="manager">Manager</option><option value="admin">Admin</option></select></td>
                    <td><input aria-label="Employee ID" value={draftUser.employee_id} onChange={(event) => updateDraft("employee_id", event.target.value)} /></td>
                    <td><input aria-label="Department" value={draftUser.department} onChange={(event) => updateDraft("department", event.target.value)} /></td>
                    <td><select aria-label="User status" value={String(draftUser.is_active)} onChange={(event) => updateDraft("is_active", event.target.value === "true")}><option value="true">Active</option><option value="false">Disabled</option></select></td>
                  </>
                ) : (
                  <>
                    <td>{row.username}</td><td>{row.name}</td><td>{row.email}</td><td>{row.access_role}</td><td>{row.employee_id}</td><td>{row.department}</td><td>{row.is_active ? "Active" : "Disabled"}</td>
                  </>
                )}
                <td className="row-actions">
                  {editingId === row.id ? (
                    <>
                      <button className="secondary-btn compact" type="button" onClick={saveInlineUser}><Save size={14} />Save</button>
                      <button className="secondary-btn compact" type="button" onClick={() => { setEditingId(null); setDraftUser(null); }}><X size={14} />Cancel</button>
                    </>
                  ) : (
                    <>
                      <button className="secondary-btn compact" type="button" onClick={() => startEditing(row)}><Pencil size={14} />Edit</button>
                      <button className="danger-btn" type="button" onClick={() => remove(row.id)}><Trash2 size={14} />Delete</button>
                    </>
                  )}
                </td>
              </tr>
            ))}</tbody>
          </table>
        </div>
      </article>
    </section>
  );
}

function AuditPanel({ token, setMessage }: Pick<ManagementProps, "token" | "setMessage">) {
  const [logs, setLogs] = useState<AuditLog[]>([]);

  useEffect(() => {
    getAuditLogs(token).then(setLogs).catch((error) => setMessage(error instanceof Error ? error.message : "Could not load audit logs."));
    // eslint-disable-next-line react-hooks/exhaustive-deps
  }, []);

  return (
    <article className="panel table-panel wide">
      <header><div className="panel-title"><ShieldCheck size={18} /><h2>CRUD Audit Logs</h2></div></header>
      <div className="table-wrap">
        <table>
          <thead><tr><th>Time</th><th>Actor</th><th>Action</th><th>Entity</th><th>Summary</th></tr></thead>
          <tbody>{logs.map((log) => <tr key={log.id}><td>{new Date(log.created_at).toLocaleString()}</td><td>{log.actor || "System"}</td><td>{log.action}</td><td>{log.entity}</td><td>{log.summary}</td></tr>)}</tbody>
        </table>
      </div>
    </article>
  );
}

function LogsPanel({ filters, options, token, user, setMessage, afterChange }: Omit<ManagementProps, "active">) {
  const [logs, setLogs] = useState<WorkLog[]>([]);
  const [editingId, setEditingId] = useState<number | null>(null);
  const [draftLog, setDraftLog] = useState<WorkLog | null>(null);

  async function load() {
    setLogs(await getLogs(token, filters));
  }

  useEffect(() => {
    load().catch((error) => setMessage(error instanceof Error ? error.message : "Could not load timesheets."));
    // eslint-disable-next-line react-hooks/exhaustive-deps
  }, [JSON.stringify(filters)]);

  async function submit(event: FormEvent<HTMLFormElement>) {
    event.preventDefault();
    try {
      const payload = formValues(event.currentTarget);
      if (!payload.notes) {
        delete payload.notes;
      }
      await saveLog(token, payload);
      event.currentTarget.reset();
      await load();
      afterChange();
      setMessage("Timesheet saved.");
    } catch (error) {
      setMessage(error instanceof Error ? error.message : "Could not save timesheet.");
    }
  }

  async function remove(id: number) {
    try {
      await deleteLog(token, id);
      await load();
      afterChange();
      setMessage("Timesheet deleted.");
    } catch (error) {
      setMessage(error instanceof Error ? error.message : "Could not delete timesheet.");
    }
  }

  function startEditing(log: WorkLog) {
    setEditingId(log.id);
    setDraftLog({ ...log });
  }

  function updateDraft(key: keyof WorkLog, value: string | number) {
    setDraftLog((current) => (current ? { ...current, [key]: value } : current));
  }

  async function saveInlineLog() {
    if (!draftLog) return;
    try {
      await updateLog(token, draftLog.id, {
        employee_id: draftLog.employee?.employee_id || user.employee_id || "",
        log_date: draftLog.log_date,
        project: draftLog.project,
        task_type: draftLog.task_type,
        hours: draftLog.hours,
        productivity_score: String(draftLog.productivity_score),
        overtime_hours: draftLog.overtime_hours,
        notes: draftLog.notes
      });
      setEditingId(null);
      setDraftLog(null);
      await load();
      afterChange();
      setMessage("Timesheet updated.");
    } catch (error) {
      setMessage(error instanceof Error ? error.message : "Could not update timesheet.");
    }
  }

  return (
    <section className="management-grid">
      <form className="panel form-panel task-form" onSubmit={submit}>
        <header>
          <div className="panel-title">
            <ClipboardList size={18} />
            <h2>{user.role === "admin" ? "Add Timesheet" : "My Timesheet"}</h2>
          </div>
        </header>
        <div className="form-section">
          <span>Work details</span>
          <div className="form-grid">
            {user.role !== "employee" && (
              <label className="span-2">Employee<select name="employee_id" required>{(options?.employees || []).map((employee) => <option key={employee.id} value={employee.id}>{employee.label}</option>)}</select></label>
            )}
            <label>Date<input name="log_date" type="date" defaultValue={today()} required /></label>
            <label>Project<input name="project" list="project-options" placeholder="Project name" required /></label>
            <label>Task<input name="task_type" list="task-options" placeholder="Task type" required /></label>
            <label>Hours<input name="hours" type="number" step="0.25" min="0" max="24" placeholder="7.5" required /></label>
          </div>
        </div>
        <div className="form-section">
          <span>Quality and notes</span>
          <div className="form-grid">
            <label>Productivity<input name="productivity_score" type="number" min="0" max="100" placeholder="88" required /></label>
            <label>Overtime<input name="overtime_hours" type="number" step="0.25" min="0" max="24" defaultValue="0" /></label>
            <label className="span-2">Notes<input name="notes" placeholder="Blockers, wins, or handoff notes" /></label>
            <button className="primary-btn form-submit" type="submit"><Save size={16} />Save timesheet</button>
          </div>
        </div>
        <datalist id="project-options">
          {(options?.projects || []).filter((item) => item !== "All").map((item) => <option key={item} value={item} />)}
        </datalist>
        <datalist id="task-options">
          {(options?.task_types || []).filter((item) => item !== "All").map((item) => <option key={item} value={item} />)}
        </datalist>
      </form>
      <article className="panel table-panel wide">
        <header>
          <div className="panel-title">
            <Clock3 size={18} />
            <h2>Timesheets</h2>
          </div>
        </header>
        <div className="table-wrap">
          <table>
            <thead><tr><th>Date</th><th>Employee</th><th>Department</th><th>Project</th><th>Task</th><th>Hours</th><th>Score</th><th>Overtime</th><th>Notes</th><th></th></tr></thead>
            <tbody>
              {logs.map((log) => (
                <tr key={log.id}>
                  {editingId === log.id && draftLog ? (
                    <>
                      <td><input aria-label="Log date" type="date" value={draftLog.log_date} onChange={(event) => updateDraft("log_date", event.target.value)} /></td>
                      <td>{log.name}</td>
                      <td>{log.department}</td>
                      <td><input aria-label="Project" value={draftLog.project} onChange={(event) => updateDraft("project", event.target.value)} /></td>
                      <td><input aria-label="Task" value={draftLog.task_type} onChange={(event) => updateDraft("task_type", event.target.value)} /></td>
                      <td><input aria-label="Hours" type="number" step="0.25" min="0" max="24" value={draftLog.hours} onChange={(event) => updateDraft("hours", event.target.value)} /></td>
                      <td><input aria-label="Productivity" type="number" min="0" max="100" value={draftLog.productivity_score} onChange={(event) => updateDraft("productivity_score", Number(event.target.value))} /></td>
                      <td><input aria-label="Overtime" type="number" step="0.25" min="0" max="24" value={draftLog.overtime_hours} onChange={(event) => updateDraft("overtime_hours", event.target.value)} /></td>
                      <td><input aria-label="Notes" value={draftLog.notes} onChange={(event) => updateDraft("notes", event.target.value)} /></td>
                    </>
                  ) : (
                    <>
                      <td>{log.log_date}</td><td>{log.name}</td><td>{log.department}</td><td>{log.project}</td><td>{log.task_type}</td><td>{log.hours}</td><td>{log.productivity_score}</td><td>{log.overtime_hours}</td><td>{log.notes}</td>
                    </>
                  )}
                  <td className="row-actions">
                    {editingId === log.id ? (
                      <>
                        <button className="secondary-btn compact" type="button" onClick={saveInlineLog}><Save size={14} />Save</button>
                        <button className="secondary-btn compact" type="button" onClick={() => { setEditingId(null); setDraftLog(null); }}><X size={14} />Cancel</button>
                      </>
                    ) : (
                      <>
                        <button className="secondary-btn compact" type="button" onClick={() => startEditing(log)}><Pencil size={14} />Edit</button>
                        <button className="danger-btn" type="button" onClick={() => remove(log.id)}><Trash2 size={14} />Delete</button>
                      </>
                    )}
                  </td>
                </tr>
              ))}
            </tbody>
          </table>
        </div>
      </article>
    </section>
  );
}

function AttendancePanel({ filters, options, token, user, setMessage, afterChange }: Omit<ManagementProps, "active">) {
  const [rows, setRows] = useState<Attendance[]>([]);
  const [editingId, setEditingId] = useState<number | null>(null);
  const [draftAttendance, setDraftAttendance] = useState<Attendance | null>(null);

  async function load() {
    setRows(await getAttendance(token, filters));
  }

  useEffect(() => {
    load().catch((error) => setMessage(error instanceof Error ? error.message : "Could not load attendance."));
    // eslint-disable-next-line react-hooks/exhaustive-deps
  }, [JSON.stringify(filters)]);

  async function submit(event: FormEvent<HTMLFormElement>) {
    event.preventDefault();
    try {
      const payload = formValues(event.currentTarget);
      if (!payload.check_in) {
        delete payload.check_in;
      }
      if (!payload.check_out) {
        delete payload.check_out;
      }
      await saveAttendance(token, payload);
      event.currentTarget.reset();
      await load();
      afterChange();
      setMessage("Attendance saved.");
    } catch (error) {
      setMessage(error instanceof Error ? error.message : "Could not save attendance.");
    }
  }

  async function markToday() {
    try {
      await markAttendanceToday(token);
      await load();
      afterChange();
      setMessage("Attendance marked for today.");
    } catch (error) {
      setMessage(error instanceof Error ? error.message : "Could not mark attendance.");
    }
  }

  function startEditing(row: Attendance) {
    setEditingId(row.id);
    setDraftAttendance({ ...row });
  }

  function updateDraft(key: keyof Attendance, value: string | number | null) {
    setDraftAttendance((current) => (current ? { ...current, [key]: value } : current));
  }

  async function saveInlineAttendance() {
    if (!draftAttendance) return;
    try {
      await updateAttendance(token, draftAttendance.id, {
        employee_id: draftAttendance.employee?.employee_id || user.employee_id || "",
        work_date: draftAttendance.work_date,
        status: draftAttendance.status,
        check_in: draftAttendance.check_in || "",
        check_out: draftAttendance.check_out || "",
        late_minutes: String(draftAttendance.late_minutes)
      });
      setEditingId(null);
      setDraftAttendance(null);
      await load();
      afterChange();
      setMessage("Attendance updated.");
    } catch (error) {
      setMessage(error instanceof Error ? error.message : "Could not update attendance.");
    }
  }

  async function remove(id: number) {
    try {
      await deleteAttendance(token, id);
      await load();
      afterChange();
      setMessage("Attendance deleted.");
    } catch (error) {
      setMessage(error instanceof Error ? error.message : "Could not delete attendance.");
    }
  }

  return (
    <section className="management-grid">
      {user.role === "employee" && (
        <section className="quick-attendance">
          <div>
            <span>Today</span>
            <strong>Mark your attendance</strong>
          </div>
          <button className="success-btn" type="button" onClick={markToday}><CheckCircle2 size={18} />Mark Present</button>
        </section>
      )}
      <article className="panel table-panel wide">
        <header>
          <div className="panel-title">
            <CalendarCheck size={18} />
            <h2>Attendance</h2>
          </div>
        </header>
        <div className="table-wrap">
          <table>
            <thead><tr><th>Date</th><th>Employee</th><th>Department</th><th>Status</th><th>Check in</th><th>Check out</th><th>Late</th><th></th></tr></thead>
            <tbody>
              {rows.map((row) => (
                <tr key={row.id}>
                  {editingId === row.id && draftAttendance ? (
                    <>
                      <td><input aria-label="Work date" type="date" value={draftAttendance.work_date} onChange={(event) => updateDraft("work_date", event.target.value)} /></td>
                      <td>{row.name}</td>
                      <td>{row.department}</td>
                      <td><select aria-label="Attendance status" value={draftAttendance.status} onChange={(event) => updateDraft("status", event.target.value)}><option>Present</option><option>Leave</option><option>Absent</option></select></td>
                      <td><input aria-label="Check in" type="time" value={draftAttendance.check_in?.slice(0, 5) || ""} onChange={(event) => updateDraft("check_in", event.target.value || null)} /></td>
                      <td><input aria-label="Check out" type="time" value={draftAttendance.check_out?.slice(0, 5) || ""} onChange={(event) => updateDraft("check_out", event.target.value || null)} /></td>
                      <td><input aria-label="Late minutes" type="number" min="0" value={draftAttendance.late_minutes} onChange={(event) => updateDraft("late_minutes", Number(event.target.value))} /></td>
                    </>
                  ) : (
                    <>
                      <td>{row.work_date}</td><td>{row.name}</td><td>{row.department}</td><td>{row.status}</td><td>{row.check_in || ""}</td><td>{row.check_out || ""}</td><td>{row.late_minutes}</td>
                    </>
                  )}
                  <td className="row-actions">
                    {editingId === row.id ? (
                      <>
                        <button className="secondary-btn compact" type="button" onClick={saveInlineAttendance}><Save size={14} />Save</button>
                        <button className="secondary-btn compact" type="button" onClick={() => { setEditingId(null); setDraftAttendance(null); }}><X size={14} />Cancel</button>
                      </>
                    ) : (
                      <>
                        <button className="secondary-btn compact" type="button" onClick={() => startEditing(row)}><Pencil size={14} />Edit</button>
                        <button className="danger-btn" type="button" onClick={() => remove(row.id)}><Trash2 size={14} />Delete</button>
                      </>
                    )}
                  </td>
                </tr>
              ))}
            </tbody>
          </table>
        </div>
      </article>
      {user.role !== "employee" && (
        <form className="panel form-panel attendance-form lower-admin-form" onSubmit={submit}>
          <header>
            <div className="panel-title">
              <CalendarCheck size={18} />
              <h2>Attendance Correction</h2>
            </div>
          </header>
          <div className="form-section">
            <span>Attendance details</span>
            <div className="form-grid">
              <label className="span-2">Employee<select name="employee_id" required>{(options?.employees || []).map((employee) => <option key={employee.id} value={employee.id}>{employee.label}</option>)}</select></label>
              <label>Date<input name="work_date" type="date" defaultValue={today()} required /></label>
              <label>Status<select name="status" defaultValue="Present"><option>Present</option><option>Leave</option><option>Absent</option></select></label>
              <label>Check in<input name="check_in" type="time" defaultValue={currentTime()} /></label>
              <label>Check out<input name="check_out" type="time" defaultValue={currentTime()} /></label>
              <label>Late minutes<input name="late_minutes" type="number" min="0" defaultValue="0" /></label>
              <button className="primary-btn form-submit" type="submit"><Save size={16} />Save attendance</button>
            </div>
          </div>
        </form>
      )}
    </section>
  );
}
