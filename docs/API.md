# API Reference

Base URL: `/api`

Authentication uses DRF token auth:

```http
Authorization: Token <token>
```

## Auth

- `POST /auth/login/` with `{ "username": "...", "password": "..." }`
- `POST /auth/signup/` with username, password, name, department, role, location, manager, hire_date
- `POST /auth/demo/` seeds demo data if needed and returns the demo admin token
- `GET /auth/me/` returns the authenticated user profile

## Analytics

- `GET /dashboard/` returns KPIs, chart datasets, performance rows, heatmap, ideal-vs-actual, and sunburst data
- `GET /insights/` returns executive summary text and insight cards
- `GET /report/` returns an HTML report for admins
- `GET /options/` returns filter dropdown values

Common query filters:

- `date_from`
- `date_to`
- `department`
- `employee_id`
- `task_type`
- `project`

## Management

- `GET|POST /employees/`
- `DELETE /employees/{employee_id}/`
- `GET|POST /logs/`
- `DELETE /logs/{id}/`
- `GET|POST /attendance/`

Employees can access their own logs and attendance. Admin users can access and
manage all records.
