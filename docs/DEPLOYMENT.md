# Deployment Guide

This project is designed for two deployable services:

- Django API in `backend/`
- Next.js frontend in `frontend/`

## 1. Create Neon Database

Create a Neon Postgres project and copy the pooled or direct connection string.
Keep `sslmode=require` in the URL.

```bash
DATABASE_URL=postgresql://USER:PASSWORD@HOST.neon.tech/DBNAME?sslmode=require
```

## 2. Backend Environment

Set these variables in your backend host:

```bash
DJANGO_DEBUG=False
DJANGO_SECRET_KEY=<long-random-secret>
DJANGO_ALLOWED_HOSTS=your-api-domain.com
CORS_ALLOWED_ORIGINS=https://your-frontend-domain.com
CSRF_TRUSTED_ORIGINS=https://your-frontend-domain.com
DATABASE_URL=postgresql://USER:PASSWORD@HOST.neon.tech/DBNAME?sslmode=require
```

Install and release:

```bash
pip install -r requirements.txt
python manage.py migrate
python manage.py seed_demo
python manage.py collectstatic --noinput
gunicorn config.wsgi:application
```

## 3. Frontend Environment

Set this variable in the frontend host:

```bash
NEXT_PUBLIC_API_BASE_URL=https://your-api-domain.com/api
```

Build command:

```bash
npm install
npm run build
```

Start command:

```bash
npm run start
```

## 4. Demo Data

The Demo Employee, Demo Manager, and Demo Admin preview buttons use bundled
frontend JSON and work without the backend. Create, update, and delete actions in
these workspaces persist to browser `localStorage`, not the database. This keeps
the UI usable while a free-tier Render backend is sleeping after inactivity.
Normal login, signup, and production records still use the Django API. Run
`seed_demo` only when you intentionally want sample records inside the database.

## 5. Production Checklist

- Use a unique `DJANGO_SECRET_KEY`.
- Set `DJANGO_DEBUG=False`.
- Set explicit `DJANGO_ALLOWED_HOSTS`.
- Set frontend origin in `CORS_ALLOWED_ORIGINS`.
- Run migrations before opening the frontend.
- Create a real admin user or disable demo access before sharing the system beyond demos.
