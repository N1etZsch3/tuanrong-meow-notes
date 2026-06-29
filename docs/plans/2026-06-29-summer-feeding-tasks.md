# Summer Feeding Tasks Implementation Plan

> **For Claude:** REQUIRED SUB-SKILL: Use superpowers:executing-plans to implement this plan task-by-task.

**Goal:** Build the summer feeding task publishing flow and make created feeding task points visible on the map.

**Architecture:** Add a backend task module with SQLAlchemy models, migrations, service-level transactions, and `/api/v1/tasks` plus `/api/v1/admin/tasks` routers. Add frontend task APIs, admin publishing pages, a task list/detail experience, and use existing map APIs for marker visibility.

**Tech Stack:** FastAPI, Pydantic, SQLAlchemy 2.0, Alembic, PostgreSQL/PostGIS, uni-app, Vue 3, TypeScript, Pinia, Vitest.

---

### Task 1: Backend Contract Tests

**Files:**
- Create: `backend/tests/test_tasks_api.py`

**Step 1: Write failing tests**

Cover:
- Admin publishes a summer feeding task with title, description, route instruction, required items, dates, location, and photos.
- Publish creates a visible map point returned by `/api/v1/map/points?point_types=task`.
- Member gets task list and detail with execution dates, photos, map point, materials, route, and activities.
- Member check-in completes one execution date without completing the parent task.
- Non-admin cannot publish.

**Step 2: Run tests to verify RED**

Run: `py -3.11 -m pytest tests/test_tasks_api.py -q`

Expected: failures because `/api/v1/tasks` and `/api/v1/admin/tasks/summer-feeding` do not exist.

### Task 2: Backend Models And Migration

**Files:**
- Create: `backend/app/modules/tasks/models.py`
- Create: `backend/app/modules/tasks/__init__.py`
- Modify: `backend/alembic/env.py`
- Create: `backend/alembic/versions/20260629_0009_create_summer_feeding_task_tables.py`

**Step 1: Implement models**

Add `Task`, `TaskExecutionDate`, `TaskPhoto`, `TaskCheckin`, `TaskCheckinPhoto`, and `TaskActivityLog`.

**Step 2: Implement migration**

Create tables and indexes for:
- `tasks`
- `task_execution_dates`
- `task_photos`
- `task_checkins`
- `task_checkin_photos`
- `task_activity_logs`

Use UUID primary keys and foreign keys to `users`, `map_points`, and `file_assets` where appropriate.

**Step 3: Run tests**

Run: `py -3.11 -m pytest tests/test_tasks_api.py -q`

Expected: still fails at missing routes/service.

### Task 3: Backend Schemas, Service, And Routes

**Files:**
- Create: `backend/app/modules/tasks/schemas.py`
- Create: `backend/app/modules/tasks/service.py`
- Create: `backend/app/api/v1/tasks.py`
- Create: `backend/app/api/v1/admin_tasks.py`
- Modify: `backend/app/api/v1/router.py`
- Modify: `backend/app/core/errors.py`
- Modify: `backend/app/modules/map/service.py`

**Step 1: Implement schemas**

Add request and response schemas matching the summer feeding interface document.

**Step 2: Implement service**

Implement:
- publish summer feeding task
- list member/admin tasks
- get detail by `task_id` or `map_point_id`
- check in one execution date
- update task basics
- update task status

**Step 3: Implement routes**

Mount:
- `/api/v1/tasks`
- `/api/v1/admin/tasks`

**Step 4: Update map summary**

When a task map point is linked to a task, set `business_id` to the task ID and `view_detail` path to `/pages/tasks/detail?task_id=...`.

**Step 5: Run tests to verify GREEN**

Run: `py -3.11 -m pytest tests/test_tasks_api.py tests/test_map_api.py -q`

Expected: pass.

### Task 4: Frontend API And Helper Tests

**Files:**
- Create: `frontend/src/api/tasks.ts`
- Create: `frontend/src/pages/tasks/task-page.ts`
- Create: `frontend/tests/api/tasks.test.ts`
- Create: `frontend/tests/pages/tasks-page.test.ts`

**Step 1: Write failing tests**

Cover:
- API wrapper calls member/admin task endpoints with bearer tokens.
- Helpers format selected dates, build publish payload, choose current/next execution, and normalize empty task responses.
- Page source contains create/detail routes, image upload references, route instruction, materials, and shared title/background conventions.

**Step 2: Run tests to verify RED**

Run: `npm run test -- --run tests/api/tasks.test.ts tests/pages/tasks-page.test.ts`

Expected: failures because files and UI do not exist.

### Task 5: Frontend Publish And Task Pages

**Files:**
- Modify: `frontend/src/pages.json`
- Modify: `frontend/src/pages/admin/index.vue`
- Modify: `frontend/src/pages/tasks/index.vue`
- Create: `frontend/src/pages/tasks/detail.vue`
- Create: `frontend/src/pages/admin/tasks/create.vue`
- Create: `frontend/src/pages/admin/tasks/location.vue`

**Step 1: Implement API wrapper**

Add task list/detail/check-in/admin publish APIs.

**Step 2: Implement pages**

Build:
- task list tab
- task detail page
- admin publish page
- admin location selection page

The publish form includes title, description, dates, location, materials, route instruction, and task point images.

**Step 3: Use existing file upload API**

Use existing file endpoints to upload task point images, then pass returned file references into the publish payload.

**Step 4: Run frontend tests**

Run: `npm run test -- --run tests/api/tasks.test.ts tests/pages/tasks-page.test.ts tests/pages/map-page.test.ts`

Expected: pass.

### Task 6: SVG Marker Color Assets

**Files:**
- Modify: `frontend/素材/svg/地图点/完成任务.svg`
- Modify: `frontend/素材/svg/地图点/失败任务.svg`

**Step 1: Inspect SVG colors**

Use text inspection to identify fill/stroke colors.

**Step 2: Recolor**

Set completed task icon to green and failed task icon to red using existing SVG structure.

**Step 3: Verify references**

Ensure map/task code references existing assets only.

### Task 7: Progress And Full Verification

**Files:**
- Modify: `docs/开发进度.md`

**Step 1: Update progress**

Record docs read, branch, files changed, API/table changes, migration name, verification, blockers, and next step.

**Step 2: Run full verification**

Run:
- `py -3.11 -m pytest -q`
- `py -3.11 -m ruff check .`
- `py -3.11 -m alembic upgrade head`
- `npm run test -- --run`
- `npm run type-check`
- `npm run build:mp-weixin`
- `git diff --check`

**Step 3: Commit**

Commit with a concise conventional message after verification passes.
