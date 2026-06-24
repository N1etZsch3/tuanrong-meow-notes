# Backend Map Support Implementation Plan

> **For Claude:** REQUIRED SUB-SKILL: Use superpowers:executing-plans to implement this plan task-by-task.

**Goal:** Build the smallest backend map module that supports the current frontend map shell and the documented first batch member map APIs.

**Architecture:** Add a `modules.map` package with SQLAlchemy models, Pydantic schemas, and services for campus config, marker query, search, point summary, navigation, and bottom content. Persist core map tables through Alembic and seed one active HBNU campus, marker configs, campus areas, and demo map points that mirror the current frontend shell items. Keep task/cat/supply full business models out of this slice; encode only map-layer metadata and action links.

**Tech Stack:** FastAPI, Pydantic, SQLAlchemy 2.0, Alembic, PostgreSQL/PostGIS, pytest, Ruff.

---

### Task 1: Map API Contract Tests

**Files:**
- Create: `backend/tests/test_map_api.py`
- Modify only after RED: `backend/app/api/v1/router.py`, `backend/app/api/v1/map.py`, `backend/app/modules/map/*`

**Steps:**
1. Write failing tests for `GET /api/v1/map/init`, `/map/points`, `/map/search`, `/map/points/{point_id}/summary`, `/map/points/{point_id}/navigation`, `/map/bottom-content` using authenticated member tokens.
2. Verify tests fail because routes do not exist.
3. Implement minimal routes/services to satisfy response shape.
4. Run targeted map tests.

### Task 2: Map Tables And Migration

**Files:**
- Create: `backend/app/modules/map/models.py`
- Create: `backend/alembic/versions/20260624_0003_create_map_tables.py`
- Modify: `backend/alembic/env.py`

**Steps:**
1. Add failing model tests for table metadata and relationships.
2. Implement `campuses`, `campus_areas`, `map_marker_configs`, `map_points`, `map_point_photos`.
3. Add migration with PostGIS geography columns and seed baseline HBNU/demo marker data.
4. Verify Alembic upgrade/current.

### Task 3: Map Query Behavior

**Files:**
- Create: `backend/app/modules/map/schemas.py`
- Create: `backend/app/modules/map/service.py`
- Test: `backend/tests/test_map_api.py`

**Steps:**
1. Add tests for filters, keyword search, distance calculation, not-found summary, and must-change-password restriction.
2. Implement service queries with thin route handlers.
3. Return unified response envelope through existing helpers.
4. Run full backend test suite and Ruff.

### Task 4: Progress And Merge Flow

**Files:**
- Modify: `docs/开发进度.md`

**Steps:**
1. Record docs read, APIs/tables added, migration name, verification commands, and frontend support scope.
2. Commit feature branch.
3. Merge `codex/feature/backend-map-support` into `dev`, verify.
4. Merge `dev` into `main`, verify.
