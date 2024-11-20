# Employee Data Analytics App

Analytics app for employee performance, attendance, workload,
overtime, productivity, project/task mix, ideal-vs-actual comparison, and
sunburst work distribution.

The main app is a responsive browser UI backed by Python's standard-library HTTP
server and SQLite. A Tkinter desktop UI is still available as a fallback.

## Run

```bash
python3 main.py --reset-sample
```

This starts a local web app and opens it in your browser. The app stores local
data in `data/employee_analytics.sqlite3`, creating the database automatically.

Run without opening a browser:

```bash
python3 main.py --reset-sample --no-browser
```

Run the desktop fallback:

```bash
python3 main.py --reset-sample --desktop
```

## Demo Login

Admin:

- Username: `admin`
- Password: `admin123`

Employee:

- Username: `EMP001`
- Password: `pass123`

Admins can see all employee analytics, reports, employee management, attendance,
timesheets, and the analytics builder. Normal employees only see their own
attendance and timesheet/work-hour screens.

## Demo Features

- Dashboard KPIs for employees, hours, productivity, attendance, overtime,
  absences, late minutes, and work-log count.
- Admin analytics builder with dropdowns for graph type, metric, grouping, and
  employee selection.
- Responsive browser graphs with scrollable chart containers, including bar,
  trend, donut, heatmap, actual-vs-ideal, and sunburst views.
- Filterable analytics by date range, department, employee, task, and project.
- Employee maintenance screen with add/update/delete and searchable table.
- Work-log screen with add/delete.
- Attendance screen with add/update, table view, attendance mix, and late-minute
  analysis.
- Insights section with executive summary and performance table.
- HTML report export for Demo presentation.
- Deterministic sample data with employees, attendance, work logs, projects,
  task types, work groups, ideal times, productivity scores, overtime, leave,
  and absences.

## Structure

- `main.py` - application entrypoint.
- `activity_log.py` - compatibility launcher.
- `app/data_store.py` - SQLite schema, queries, sample-data
  seeding, exports, sunburst data, work groups, and ideal times.
- `app/sample_data.py` - deterministic demo dataset.
- `app/analytics_service.py` - dashboard and insight logic.
- `app/reporting.py` - HTML report generator.
- `app/web.py` - local HTTP API and web launcher.
- `app/web_assets/index.html` - responsive web dashboard.
- `app/ui.py` - Tkinter desktop fallback UI.
- `app/settings.py` - local non-secret app settings.

The previous CustomTkinter/MySQL prototype files were removed after their useful
features were migrated into this modular SQLite architecture.
