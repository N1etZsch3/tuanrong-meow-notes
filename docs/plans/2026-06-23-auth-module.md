# Auth Module Implementation Plan

> **For Claude:** REQUIRED SUB-SKILL: Use superpowers:executing-plans to implement this plan task-by-task.

**Goal:** Implement the V1 authentication backend needed by the login frontend: captcha, student-number login, JWT current-user flow, password change, logout, and basic admin member account management.

**Architecture:** Add auth tables and SQLAlchemy models under `app/modules/auth`, shared security helpers under `app/core/security.py`, and auth/admin routes under `/api/v1/auth` and `/api/v1/admin/users`. Keep route handlers thin and put business rules in `app/modules/auth/service.py`.

**Tech Stack:** FastAPI, Pydantic v2, SQLAlchemy 2.0, Alembic, PostgreSQL/PostGIS, PyJWT, passlib bcrypt, pytest.

---

### Task 1: Auth Tables And Models

**Files:**
- Create: `backend/app/modules/auth/models.py`
- Create: `backend/alembic/versions/20260623_0002_create_auth_tables.py`
- Modify: `backend/app/db/base.py`
- Test: `backend/tests/test_auth_models.py`

**Steps:**
1. Write failing tests proving model metadata contains `users`, `auth_captchas`, `user_profiles`, and `admin_operation_logs`.
2. Implement SQLAlchemy models and migration.
3. Run auth model tests.

### Task 2: Security And Captcha

**Files:**
- Create: `backend/app/core/security.py`
- Create: `backend/app/modules/auth/captcha.py`
- Test: `backend/tests/test_auth_security.py`

**Steps:**
1. Write failing tests for password hash/verify, JWT encode/decode, captcha hash/verify, and captcha image data URL.
2. Implement helpers with no plaintext password or captcha storage.
3. Run security tests.

### Task 3: Public Auth Endpoints

**Files:**
- Create: `backend/app/modules/auth/schemas.py`
- Create: `backend/app/modules/auth/service.py`
- Create: `backend/app/api/v1/auth.py`
- Modify: `backend/app/api/v1/router.py`
- Test: `backend/tests/test_auth_api.py`

**Steps:**
1. Write failing API tests for `GET /api/v1/auth/captcha`, `POST /api/v1/auth/login`, `GET /api/v1/auth/me`, `PATCH /api/v1/auth/password`, and `POST /api/v1/auth/logout`.
2. Implement service logic and routes.
3. Run API tests.

### Task 4: Admin Member Account Endpoints

**Files:**
- Create: `backend/app/api/v1/admin_users.py`
- Modify: `backend/app/api/v1/router.py`
- Test: `backend/tests/test_admin_users_api.py`

**Steps:**
1. Write failing tests for admin create/list/reset-password/status/role endpoints.
2. Implement admin role checks and account management service methods.
3. Run admin tests.

### Task 5: Integration And Handoff

**Files:**
- Modify: `backend/README.md`
- Modify: `docs/开发进度.md`

**Steps:**
1. Run `py -3.11 -m alembic upgrade head`.
2. Run backend tests and ruff.
3. Run an HTTP integration script against a live Uvicorn server using the same request shapes as `feature/frontend-login:frontend/src/api/auth.ts`.
4. Document that real frontend source is currently on `feature/frontend-login`; this branch validates backend compatibility against that contract.
5. Commit with `feat(auth): implement student number login`.

**Explicitly Out Of Scope For This Slice:**
- Public registration.
- Refresh tokens.
- Password recovery.
- Third-party login.
- WebSocket/Redis.
- Batch member import endpoint, unless a later frontend/admin slice needs it.
