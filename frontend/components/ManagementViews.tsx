"use client";

import { CalendarCheck, ClipboardList, Clock3, Save, Trash2, Users } from "lucide-react";
import type { FormEvent } from "react";
import { useEffect, useState } from "react";

import {
  deleteEmployee,
  deleteLog,
  getAttendance,
  getEmployees,
  getLogs,
  saveAttendance,
  saveEmployee,
  saveLog
} from "@/lib/api";
import type { Attendance, AuthUser, Employee, Filters, OptionsPayload, WorkLog } from "@/types/api";

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
  return new Date().toISOString().slice(0, 10);
}

export function ManagementViews({ active, filters, options, token, user, setMessage, afterChange }: ManagementProps) {
  if (active === "employees") {
    return <EmployeesPanel token={token} user={user} setMessage={setMessage} afterChange={afterChange} />;
  }
  if (active === "logs") {
    return <LogsPanel filters={filters} options={options} token={token} user={user} setMessage={setMessage} afterChange={afterChange} />;
  }
  return <AttendancePanel filters={filters} options={options} token={token} user={user} setMessage={setMessage} afterChange={afterChange} />;
}

function EmployeesPanel({ token, user, setMessage, afterChange }: Pick<ManagementProps, "token" | "user" | "setMessage" | "afterChange">) {
  const [employees, setEmployees] = useState<Employee[]>([]);

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
      await saveEmployee(token, formValues(event.currentTarget));
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
            <label>Manager<input name="manager" required /></label>
            <label>Hire date<input name="hire_date" type="date" required /></label>
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
            <thead><tr><th>ID</th><th>Name</th><th>Department</th><th>Role</th><th>Status</th><th></th></tr></thead>
            <tbody>
              {employees.map((employee) => (
                <tr key={employee.employee_id}>
                  <td>{employee.employee_id}</td>
                  <td>{employee.name}</td>
                  <td>{employee.department}</td>
                  <td>{employee.role}</td>
                  <td>{employee.status}</td>
                  <td>{user.role === "admin" && <button className="danger-btn" type="button" onClick={() => remove(employee.employee_id)}><Trash2 size={14} />Delete</button>}</td>
                </tr>
              ))}
            </tbody>
          </table>
        </div>
      </article>
    </section>
  );
}

function LogsPanel({ filters, options, token, user, setMessage, afterChange }: Omit<ManagementProps, "active">) {
  const [logs, setLogs] = useState<WorkLog[]>([]);

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
            {user.role === "admin" && (
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
            <thead><tr><th>Date</th><th>Employee</th><th>Department</th><th>Project</th><th>Task</th><th>Hours</th><th>Score</th><th></th></tr></thead>
            <tbody>
              {logs.map((log) => (
                <tr key={log.id}>
                  <td>{log.log_date}</td><td>{log.name}</td><td>{log.department}</td><td>{log.project}</td><td>{log.task_type}</td><td>{log.hours}</td><td>{log.productivity_score}</td>
                  <td><button className="danger-btn" type="button" onClick={() => remove(log.id)}><Trash2 size={14} />Delete</button></td>
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

  return (
    <section className="management-grid">
      <form className="panel form-panel attendance-form" onSubmit={submit}>
        <header>
          <div className="panel-title">
            <CalendarCheck size={18} />
            <h2>{user.role === "admin" ? "Record Attendance" : "My Attendance"}</h2>
          </div>
        </header>
        <div className="form-section">
          <span>Attendance details</span>
          <div className="form-grid">
            {user.role === "admin" && (
              <label className="span-2">Employee<select name="employee_id" required>{(options?.employees || []).map((employee) => <option key={employee.id} value={employee.id}>{employee.label}</option>)}</select></label>
            )}
            <label>Date<input name="work_date" type="date" defaultValue={today()} required /></label>
            <label>Status<select name="status" defaultValue="Present"><option>Present</option><option>Leave</option><option>Absent</option></select></label>
            <label>Check in<input name="check_in" type="time" /></label>
            <label>Check out<input name="check_out" type="time" /></label>
            <label>Late minutes<input name="late_minutes" type="number" min="0" defaultValue="0" /></label>
            <button className="primary-btn form-submit" type="submit"><Save size={16} />Save attendance</button>
          </div>
        </div>
      </form>
      <article className="panel table-panel wide">
        <header>
          <div className="panel-title">
            <CalendarCheck size={18} />
            <h2>Attendance</h2>
          </div>
        </header>
        <div className="table-wrap">
          <table>
            <thead><tr><th>Date</th><th>Employee</th><th>Department</th><th>Status</th><th>Check in</th><th>Check out</th><th>Late</th></tr></thead>
            <tbody>
              {rows.map((row) => (
                <tr key={row.id}>
                  <td>{row.work_date}</td><td>{row.name}</td><td>{row.department}</td><td>{row.status}</td><td>{row.check_in || ""}</td><td>{row.check_out || ""}</td><td>{row.late_minutes}</td>
                </tr>
              ))}
            </tbody>
          </table>
        </div>
      </article>
    </section>
  );
}
