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

## Database Environment

Development database settings are loaded from `backend/.env` with the `CATMAP_` prefix.

Use `backend/.env.example` as the template when recreating local settings. The current
development database is expected to be PostgreSQL with PostGIS enabled.

## Test

From the `backend` directory:

```powershell
py -3.11 -m pytest
```

## Current Scope

The current skeleton includes:

- FastAPI app factory in `app/main.py`
- `/api/v1` router mounting
- Unified success response envelope
- Request trace ID middleware using `X-Trace-Id`
- Health check endpoint

Database settings, SQLAlchemy models, Alembic migrations, and authentication endpoints are intentionally left for the next backend slices.
