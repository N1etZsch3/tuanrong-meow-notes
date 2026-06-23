# Backend Foundation Implementation Plan

> **For Claude:** REQUIRED SUB-SKILL: Use superpowers:executing-plans to implement this plan task-by-task.

**Goal:** Build the initial FastAPI backend skeleton with Python 3.11 metadata, unified API response shape, request trace IDs, and a verified health endpoint.

**Architecture:** Keep the backend as a small Python package under `backend/app`. Route handlers stay thin, shared response helpers live under `backend/app/core`, and V1 APIs are mounted below `/api/v1`. Database configuration is intentionally excluded until connection details are provided.

**Tech Stack:** Python 3.11, FastAPI, Pydantic v2, Uvicorn, pytest, HTTPX.

---

### Task 1: Backend Metadata And Test Contract

**Files:**
- Create: `backend/.python-version`
- Create: `backend/pyproject.toml`
- Create: `backend/tests/test_health.py`

**Step 1: Write the failing test**

Create a test that imports `backend.app.main.app` and asserts `GET /api/v1/health` returns the unified response envelope with `code`, `message`, `data`, and `trace_id`.

**Step 2: Run test to verify it fails**

Run: `py -3.11 -m pytest backend/tests/test_health.py -q`
Expected: FAIL because FastAPI app files do not exist yet.

### Task 2: FastAPI App Skeleton

**Files:**
- Create: `backend/app/__init__.py`
- Create: `backend/app/main.py`
- Create: `backend/app/api/__init__.py`
- Create: `backend/app/api/v1/__init__.py`
- Create: `backend/app/api/v1/router.py`
- Create: `backend/app/api/v1/health.py`
- Create: `backend/app/core/__init__.py`
- Create: `backend/app/core/config.py`
- Create: `backend/app/core/responses.py`
- Create: `backend/app/core/trace.py`

**Step 1: Implement minimal code**

Create the FastAPI app, mount `/api/v1`, add trace ID middleware, and return health data through the shared response helper.

**Step 2: Run tests**

Run: `py -3.11 -m pytest backend/tests/test_health.py -q`
Expected: PASS.

### Task 3: Documentation And Progress

**Files:**
- Modify: `backend/README.md`
- Modify: `docs/开发进度.md`

**Step 1: Document local startup**

Add Python 3.11 setup commands and the app startup command.

**Step 2: Update progress**

Record changed files, no database work, and verification commands.

**Step 3: Run full verification**

Run: `py -3.11 -m pytest backend/tests -q`
Expected: all tests pass.
