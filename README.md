# WorkPulse

A full-stack work management platform with a Django REST API, Postgres/Neon
support, token authentication, retained demo data, and a polished Next.js
dashboard with light and dark themes.

## What It Includes

- Django backend with modular analytics models, services, serializers, and API views.
- Postgres-ready configuration through `DATABASE_URL`; Neon works with `sslmode=require`.
- Token authentication, login, signup, and three demo POV entries.
- Deterministic demo data for employees, work logs, attendance, projects, task groups, demo users, and ideal task times.
- Next.js frontend with dashboard KPIs, charts, reports, employee management, timesheets, attendance, filters, and theme toggle.
- Admin, manager, and employee scoping. Admins see all data, managers see direct reports, and employees are restricted to their own records.
- Inline editing for employee and project list views.
- HTML report export from the API.

## Demo Access

The login page includes Employee, Manager, and Admin demo buttons. They seed demo
data if needed and sign in with the correct role so reviewers can inspect the app
from three points of view.

Manual credentials are also available after running `seed_demo`:

- Admin: `demoadmin` / `demo`
- Manager: `demomanager` / `demo`
- Employee: `demouser` / `demo`

## Project Structure

```text
backend/
  analytics/        Django app: models, services, API views, serializers, demo seed command
  config/           Django settings, URLs, ASGI/WSGI
  requirements.txt  Backend dependencies
frontend/
  app/              Next.js App Router entry
  features/         Feature modules: auth, dashboard, layout, management, reports
  lib/              API client
  types/            Shared TypeScript API types
docs/
  API.md            REST API reference
  DEPLOYMENT.md     Neon and deployment guide
```

The deployable product is `backend/` plus `frontend/`; the old Tkinter and
standard-library local web prototype has been removed.

## Local Development

Backend:

```bash
cd backend
python3 -m venv .venv
source .venv/bin/activate
pip install -r requirements.txt
cp .env.example .env
python manage.py migrate
python manage.py seed_demo --reset
python manage.py runserver 127.0.0.1:8000
```

Frontend:

```bash
cd frontend
npm install
cp .env.example .env.local
npm run dev
```

Open `http://localhost:3000`. If that port is already busy, Next.js can run on
another port such as `3001`; the backend CORS defaults include both local ports.

## Neon Postgres

Set `DATABASE_URL` in `backend/.env` or your hosting provider:

```bash
DATABASE_URL=postgresql://USER:PASSWORD@HOST.neon.tech/DBNAME?sslmode=require
```

Then run:

```bash
python manage.py migrate
python manage.py seed_demo --reset
```

## Useful Commands

```bash
# Backend checks
cd backend
python manage.py check
python manage.py migrate
python manage.py seed_demo --reset

# Frontend checks
cd frontend
npm run typecheck
npm run build
```

## Deployment Shape

Deploy the backend and frontend as separate services:

- Backend: Django/Gunicorn service with `backend/requirements.txt`, `DATABASE_URL`, and `gunicorn config.wsgi:application`.
- Frontend: Next.js service with `frontend/package.json` and `NEXT_PUBLIC_API_BASE_URL=https://your-api-domain/api`.
- CORS: add the frontend origin to `CORS_ALLOWED_ORIGINS` on the backend.
- Hosts: add the backend domain to `DJANGO_ALLOWED_HOSTS`.

See [docs/DEPLOYMENT.md](docs/DEPLOYMENT.md) for the full checklist.
