# Profile Center Implementation Plan

> **For Claude:** REQUIRED SUB-SKILL: Use superpowers:executing-plans to implement this plan task-by-task.

**Goal:** Build the mobile WeChat Mini Program「我的」page, profile editing, record entry pages, logout, and admin account creation.

**Architecture:** Add a thin `me` backend module for personal center aggregations and empty paginated record contracts, reuse the existing profile and admin user services for profile editing and account creation, then wire the uni-app pages to these APIs. Keep task/cat/notification data as empty API contracts until their modules land.

**Tech Stack:** FastAPI, Pydantic, SQLAlchemy 2.0, pytest, Vue 3, uni-app, TypeScript, Pinia, Vitest.

---

### Task 1: Backend Me Contracts

**Files:**
- Create: `backend/app/modules/me/schemas.py`
- Create: `backend/app/modules/me/service.py`
- Create: `backend/app/api/v1/me.py`
- Modify: `backend/app/api/v1/router.py`
- Test: `backend/tests/test_me_api.py`

**Step 1: Write failing tests**

Add tests for:
- `GET /api/v1/me/dashboard` returns profile, zero stats, empty recent lists, and `show_admin_entry`.
- `GET /api/v1/me/tasks`, `/checkins`, `/observations`, `/favorite-cats` return empty paginated data.
- endpoints require password changed and profile completed.

**Step 2: Run tests to verify RED**

Run: `pytest backend\tests\test_me_api.py -q`
Expected: FAIL because `/api/v1/me/*` routes do not exist.

**Step 3: Implement minimal backend**

Create schemas and service helpers returning real profile fields and zero/empty aggregation contracts. Register `me_router` at `/api/v1/me`.

**Step 4: Verify GREEN**

Run: `pytest backend\tests\test_me_api.py -q`
Expected: PASS.

### Task 2: Backend Profile Editing

**Files:**
- Modify: `backend/app/modules/profile/schemas.py`
- Modify: `backend/app/modules/profile/service.py`
- Modify: `backend/app/api/v1/profile.py`
- Test: `backend/tests/test_profile_api.py`

**Step 1: Write failing tests**

Add tests for:
- `PATCH /api/v1/profile/me` updates nickname, department, contact info, and avatar URL.
- invalid nickname/phone/department returns validation error.

**Step 2: Run tests to verify RED**

Run: `pytest backend\tests\test_profile_api.py -q`
Expected: FAIL because PATCH route is missing.

**Step 3: Implement minimal backend**

Add `UpdateProfileRequest`, `update_profile`, and route handler.

**Step 4: Verify GREEN**

Run: `pytest backend\tests\test_profile_api.py -q`
Expected: PASS.

### Task 3: Frontend API Contracts

**Files:**
- Create: `frontend/src/api/me.ts`
- Modify: `frontend/src/api/profile.ts`
- Create: `frontend/src/api/admin-users.ts`
- Test: `frontend/tests/api/me.test.ts`
- Test: `frontend/tests/api/profile.test.ts`
- Test: `frontend/tests/api/admin-users.test.ts`

**Step 1: Write failing tests**

Add tests for dashboard/list endpoints, profile update, and admin create user request payload.

**Step 2: Run tests to verify RED**

Run: `npm run test -- tests/api/me.test.ts tests/api/profile.test.ts tests/api/admin-users.test.ts`
Expected: FAIL because new API helpers are missing.

**Step 3: Implement minimal API helpers**

Use existing `request` wrapper and `snake_case` types.

**Step 4: Verify GREEN**

Run target frontend API tests.

### Task 4: Frontend Pages

**Files:**
- Modify: `frontend/src/pages/profile/index.vue`
- Create: `frontend/src/pages/profile/profile-page.ts`
- Create: `frontend/src/pages/profile/detail.vue`
- Create: `frontend/src/pages/profile/records.vue`
- Create: `frontend/src/pages/admin/index.vue`
- Create: `frontend/src/pages/admin/create-user.vue`
- Modify: `frontend/src/pages.json`
- Test: `frontend/tests/pages/profile-page.test.ts`
- Test: `frontend/tests/pages/admin-page.test.ts`

**Step 1: Write failing tests**

Test page source for:
- dashboard API usage and mobile viewport structure.
- logout call and login redirect.
- stats/favorite/admin/profile navigation routes.
- admin create user calls `createAdminUser`.

**Step 2: Run tests to verify RED**

Run: `npm run test -- tests/pages/profile-page.test.ts tests/pages/admin-page.test.ts`
Expected: FAIL because pages/routes do not exist.

**Step 3: Implement pages**

Reproduce the prototype with Songti font, responsive `rpx`, no decorative overflow, loading/error/empty states, and existing local SVG assets.

**Step 4: Verify GREEN**

Run target page tests.

### Task 5: Docs, Verification, Commit

**Files:**
- Modify: `docs/接口文档/用户与个人中心模块_接口文档.md`
- Modify: `docs/开发进度.md`

**Step 1: Update docs**

Record new implemented endpoints, frontend pages, verification commands, and known gaps.

**Step 2: Run full verification**

Run:
- `pytest -q` from `backend`
- `ruff check .` from `backend`
- `npm run test` from `frontend`
- `npm run type-check` from `frontend`
- `npm run build:mp-weixin` from `frontend`
- `npm run build:h5` from `frontend`
- `git diff --check`

**Step 3: Stage only related files**

Avoid staging unrelated map asset deletions or prototype/image changes not touched in this task.

**Step 4: Commit**

Commit message: `feat(profile): build personal center dashboard`
