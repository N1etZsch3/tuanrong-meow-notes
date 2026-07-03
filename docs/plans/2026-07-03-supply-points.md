# Supply Points Implementation Plan

> **For Claude:** REQUIRED SUB-SKILL: Use superpowers:executing-plans to implement this plan task-by-task.

**Goal:** Build the V1 supply point module: admin creates/edits long-term supply points, members record supply snapshots, and map users enter supply details from supply markers.

**Architecture:** Supply points are a business module separate from tasks. They reuse the existing `map_points` marker pipeline and frontend task page patterns, but persist supply configuration and member snapshot records in dedicated tables.

**Tech Stack:** FastAPI, Pydantic, SQLAlchemy 2.0, Alembic, PostgreSQL/PostGIS, uni-app, Vue 3, TypeScript, Pinia-compatible APIs.

---

### Task 1: Backend Data Model And API

**Files:**
- Create: `backend/app/modules/supplies/models.py`
- Create: `backend/app/modules/supplies/schemas.py`
- Create: `backend/app/modules/supplies/service.py`
- Create: `backend/app/api/v1/admin_supplies.py`
- Create: `backend/app/api/v1/supplies.py`
- Create: `backend/alembic/versions/20260703_0011_create_supply_point_tables.py`
- Modify: `backend/app/api/v1/router.py`
- Modify: `backend/tests/conftest.py`
- Test: `backend/tests/test_supplies_api.py`

**Steps:**
1. Write failing API tests for admin create/detail/edit/delete, member detail, and member record snapshot.
2. Add SQLAlchemy supply models and relationships.
3. Add Pydantic request schemas with item and photo validation.
4. Implement service functions that create `map_points` with `point_type="supply"`, maintain initial items, and create record snapshots.
5. Register admin and member routers.
6. Add Alembic migration with downgrade.
7. Run targeted tests until green.

### Task 2: Map Integration

**Files:**
- Modify: `backend/app/modules/map/service.py`
- Test: `backend/tests/test_map_api.py`

**Steps:**
1. Write a failing test that a supply `map_point` summary links to a real supply point detail and exposes current supply tags.
2. Update map summary lookups to join supply business data for `point_type="supply"`.
3. Keep task marker logic unchanged.
4. Run map and supply tests.

### Task 3: Frontend Supply APIs And Pages

**Files:**
- Create: `frontend/src/api/supplies.ts`
- Create: `frontend/src/pages/admin/supplies/create.vue`
- Create: `frontend/src/pages/admin/supplies/location.vue`
- Create: `frontend/src/pages/admin/supplies/supply-page.ts`
- Create: `frontend/src/pages/supplies/detail.vue`
- Modify: `frontend/src/pages.json`
- Modify: `frontend/src/pages/admin/index.vue`

**Steps:**
1. Add typed supply point API client methods.
2. Add admin entrance for creating supply points.
3. Build create/edit page by reusing the feeding task publish page structure.
4. Build supply location page by reusing task map selection behavior, with read-only point name.
5. Build supply detail page by reusing task detail patterns, replacing dates/requirements with current supply status and snapshot records.
6. Add record modal with required item tags and required photo upload.
7. Wire delete/edit actions for admins.

### Task 4: Frontend Detail Scroll Optimizations

**Files:**
- Modify: `frontend/src/pages/tasks/detail.vue`
- Modify: `frontend/src/pages/supplies/detail.vue`

**Steps:**
1. Add bounded scroll regions for task activity and task check-in photos.
2. Add bounded scroll regions and date filter controls for supply records.
3. Run frontend type check and WeChat Mini Program build.

### Task 5: Progress And Verification

**Files:**
- Modify: `docs/开发进度.md`

**Steps:**
1. Run backend targeted tests and broader backend tests where practical.
2. Run frontend type check and relevant build.
3. Update progress with changed files, APIs, tables, verification, risks, and next steps.
4. Review `git diff` and commit with a conventional message.
