# Backend Infrastructure Implementation Plan

> **For Claude:** REQUIRED SUB-SKILL: Use superpowers:executing-plans to implement this plan task-by-task.

**Goal:** Add the backend infrastructure needed before business modules: database engine/session setup, Alembic migration wiring, unified error responses, and quality commands.

**Architecture:** Keep database concerns under `app/db`, shared API errors under `app/core`, and Alembic configuration at the backend root. The app continues to expose `/api/v1`; this slice does not create business tables or auth endpoints.

**Tech Stack:** Python 3.11, FastAPI, Pydantic v2, SQLAlchemy 2.0, psycopg 3, Alembic, pytest, ruff.

---

### Task 1: Database Configuration Contract

**Files:**
- Create: `backend/tests/test_database.py`
- Modify: `backend/pyproject.toml`

**Step 1: Write failing tests**

Assert `settings.required_database_url` returns `CATMAP_DATABASE_URL`, raises when absent, and `SessionLocal` can be imported from `app.db.session`.

**Step 2: Run tests to verify failure**

Run: `py -3.11 -m pytest tests/test_database.py -q`
Expected: FAIL because `app.db` and `required_database_url` do not exist.

### Task 2: Unified Error Response Contract

**Files:**
- Create: `backend/tests/test_errors.py`
- Modify: `backend/app/main.py`
- Modify: `backend/app/core/responses.py`

**Step 1: Write failing tests**

Assert custom API errors and request validation errors return `{code, message, data, trace_id}`.

**Step 2: Run tests to verify failure**

Run: `py -3.11 -m pytest tests/test_errors.py -q`
Expected: FAIL because error handlers do not exist.

### Task 3: Implement Infrastructure

**Files:**
- Create: `backend/app/core/errors.py`
- Create: `backend/app/core/exception_handlers.py`
- Create: `backend/app/db/__init__.py`
- Create: `backend/app/db/base.py`
- Create: `backend/app/db/session.py`
- Create: `backend/alembic.ini`
- Create: `backend/alembic/env.py`
- Create: `backend/alembic/script.py.mako`
- Create: `backend/alembic/versions/.gitkeep`
- Modify: `backend/app/main.py`
- Modify: `backend/app/core/config.py`
- Modify: `backend/app/core/responses.py`
- Modify: `backend/pyproject.toml`

**Step 1: Add minimal code**

Add dependencies, database engine/session, declarative base, Alembic env that reads `CATMAP_DATABASE_URL`, and exception handlers.

**Step 2: Run tests**

Run: `py -3.11 -m pytest -q`
Expected: PASS.

### Task 4: Verify And Document

**Files:**
- Modify: `backend/README.md`
- Modify: `docs/开发进度.md`

**Step 1: Document commands**

Add database migration and quality commands.

**Step 2: Verify**

Run:
- `py -3.11 -m pip install -e ".[dev]"`
- `py -3.11 -m pytest -q`
- `py -3.11 -m alembic current`
- `py -3.11 -m ruff check .`

**Step 3: Commit**

Commit with `feat(backend): add database infrastructure`.
