# Backend

Backend API service for the Campus Cat Association Map Task System.

## Stack

- FastAPI
- Pydantic v2
- SQLAlchemy 2.0
- Alembic
- PostgreSQL + PostGIS
- JWT authentication

Read `../AGENTS.md` and the relevant documents under `../docs` before adding backend code.

## Python Version

Use Python 3.11 for backend development.

The backend pins this in:

- `.python-version`
- `pyproject.toml` with `requires-python = ">=3.11,<3.12"`

## Local Setup

From the `backend` directory:

```powershell
py -3.11 -m pip install -e ".[dev]"
```

## Environment

Copy the backend environment template before local development:

```powershell
Copy-Item .env.example .env
```

The real `.env` file is ignored by Git and must not be committed. Keep only safe placeholders in `.env.example`.

Current database-related environment keys:

```text
CATMAP_DATABASE_HOST=
CATMAP_DATABASE_PORT=
CATMAP_DATABASE_NAME=
CATMAP_DATABASE_USER=
CATMAP_DATABASE_PASSWORD=
CATMAP_DATABASE_URL=
CATMAP_JWT_SECRET_KEY=
CATMAP_JWT_ALGORITHM=
CATMAP_ACCESS_TOKEN_EXPIRE_SECONDS=
CATMAP_CAPTCHA_SECRET_KEY=
CATMAP_CAPTCHA_EXPIRE_SECONDS=
CATMAP_AUTH_LOCK_FAILED_ATTEMPTS=
CATMAP_AUTH_LOCK_MINUTES=
CATMAP_AMAP_WEB_KEY=
CATMAP_AMAP_SECURITY_JS_CODE=
CATMAP_CORS_ALLOW_ORIGINS=
CATMAP_CORS_ALLOW_ORIGIN_REGEX=
```

## Run The API

From the `backend` directory:

```powershell
py -3.11 -m uvicorn app.main:app --reload
```

The initial V1 health endpoint is:

```text
GET http://127.0.0.1:8000/api/v1/health
```

## Local CORS

Local development allows loopback origins on any port through:

```text
CATMAP_CORS_ALLOW_ORIGIN_REGEX=^https?://(localhost|127\.0\.0\.1|\[::1\])(:[0-9]+)?$
```

This is intentionally permissive for local H5 testing without nginx. Before deployment, clear the
development regex, use exact allowed origins only if cross-origin access is still needed, and prefer
serving frontend and backend under the same origin through nginx proxying.

## Auth Endpoints

Implemented V1 auth endpoints:

```text
GET    /api/v1/auth/captcha
POST   /api/v1/auth/login
GET    /api/v1/auth/me
POST   /api/v1/auth/renew
PATCH  /api/v1/auth/password
POST   /api/v1/auth/logout
GET    /api/v1/admin/users
POST   /api/v1/admin/users
PATCH  /api/v1/admin/users/{user_id}/password
PATCH  /api/v1/admin/users/{user_id}/status
PATCH  /api/v1/admin/users/{user_id}/role
```

Frontend contract checked against `feature/frontend-login:frontend/src/api/auth.ts`.
The frontend default base URL is:

```text
http://localhost:8000/api/v1
```

## Map Endpoints

Implemented first-batch member map endpoints:

```text
GET /api/v1/map/init
GET /api/v1/map/points
GET /api/v1/map/search
GET /api/v1/map/points/{point_id}/summary
GET /api/v1/map/points/{point_id}/navigation
GET /api/v1/map/bottom-content
```

`/api/v1/map/init` returns the Amap web key and security JS code in `amap_config`.
Local defaults match the prototype HTML files; use `CATMAP_AMAP_WEB_KEY` and
`CATMAP_AMAP_SECURITY_JS_CODE` to override them without changing source code.

## Database Environment

Development database settings are loaded from `backend/.env` with the `CATMAP_` prefix.

Use `backend/.env.example` as the template when recreating local settings. The current
development database is expected to be PostgreSQL with PostGIS enabled.

## Database And Migrations

Database sessions are provided by `app.db.session.get_db`. Alembic reads
`CATMAP_DATABASE_URL` from `backend/.env`.

From the `backend` directory:

```powershell
py -3.11 -m alembic current
py -3.11 -m alembic upgrade head
```

The initial migration enables required PostgreSQL extensions:

- `postgis`
- `pgcrypto`

## Test

From the `backend` directory:

```powershell
py -3.11 -m pytest
```

## Code Quality

From the `backend` directory:

```powershell
py -3.11 -m ruff check .
```

## Current Scope

The current skeleton includes:

- FastAPI app factory in `app/main.py`
- `/api/v1` router mounting
- Unified success response envelope
- Unified error response handlers
- Request trace ID middleware using `X-Trace-Id`
- Health check endpoint
- SQLAlchemy engine/session utilities
- Alembic migration wiring
- Auth tables and migrations
- Student number login with captcha and JWT
- Current-user, password-change, logout, and admin member account endpoints
- Map base tables, seed campus/marker data, and first-batch member map endpoints

Batch member import, refresh tokens, public registration, password recovery, and third-party login are intentionally out of scope for V1 auth core.
