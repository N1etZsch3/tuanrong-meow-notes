# Map Navigation And Admin Point Editing Implementation Plan

> **For Claude:** REQUIRED SUB-SKILL: Use superpowers:executing-plans to implement this plan task-by-task.

**Goal:** Keep route planning inside the mini program map page, add simulated navigation, include Amap POI search, and let admins edit or reposition map points.

**Architecture:** Backend proxies external Amap Web Service calls and exposes route geometry plus POI results through existing `/api/v1/map` contracts. Admin map point edits use dedicated `/api/v1/admin/map` endpoints that update only `map_points`. Frontend renders native map polylines and markers, maps external POIs as temporary markers, and gates point editing controls by admin role.

**Tech Stack:** FastAPI, SQLAlchemy 2.0, Pydantic-style dict DTOs, uni-app, Vue 3, TypeScript, Pinia, Vitest, pytest.

---

### Task 1: Backend Route Planning And External POI Search

**Files:**
- Modify: `backend/app/core/config.py`
- Modify: `backend/.env.example`
- Modify: `backend/app/modules/map/service.py`
- Modify: `backend/app/api/v1/map.py`
- Test: `backend/tests/test_map_api.py`

**Steps:**
1. Write failing backend tests for `GET /api/v1/map/search?include_external=true` and `GET /api/v1/map/points/{point_id}/navigation?from_lng=&from_lat=`.
2. Verify they fail because external search and route geometry are missing.
3. Add Amap Web Service helpers with short timeouts and graceful fallback.
4. Extend navigation response with `route`.
5. Extend search response with external POI items when requested.
6. Run targeted backend tests.

### Task 2: Admin Map Point APIs

**Files:**
- Create: `backend/app/api/v1/admin_map.py`
- Modify: `backend/app/api/v1/router.py`
- Modify: `backend/app/modules/map/service.py`
- Test: `backend/tests/test_map_api.py`

**Steps:**
1. Write failing tests for admin point detail, field update, and location update.
2. Verify 404/failure.
3. Implement admin routes using `require_admin`.
4. Add service helpers that validate point existence and update editable fields.
5. Run targeted backend tests.

### Task 3: Frontend API Contracts

**Files:**
- Modify: `frontend/src/api/map.ts`
- Create: `frontend/src/api/admin-map.ts`
- Test: `frontend/tests/api/map.test.ts`

**Steps:**
1. Write failing API tests for route fields, external search query, and admin map endpoints.
2. Verify failures.
3. Update TypeScript interfaces and request functions.
4. Run targeted frontend API tests.

### Task 4: Frontend Map Page Navigation And Search

**Files:**
- Modify: `frontend/src/pages/index/index.vue`
- Modify: `frontend/src/pages/index/map-page.ts`
- Test: `frontend/tests/pages/map-page.test.ts`

**Steps:**
1. Write failing page tests for in-page route rendering, no `uni.openLocation`, simulated navigation state, and external POI temporary markers.
2. Verify failures.
3. Render backend route polyline.
4. Add navigation panel and simulated marker movement.
5. Pass `include_external=true` to search and support `map_point_id = null`.
6. Run targeted page tests.

### Task 5: Frontend Admin Point Editing

**Files:**
- Modify: `frontend/src/pages/index/index.vue`
- Modify: `frontend/src/pages.json`
- Create: `frontend/src/pages/admin/map-point/edit.vue`
- Test: `frontend/tests/pages/map-page.test.ts`

**Steps:**
1. Write failing tests for admin edit action visibility and save-location request trigger.
2. Verify failures.
3. Add admin-only edit action in map summary handling.
4. Add long-press edit-mode state and save/cancel controls.
5. Add edit page for basic map point fields.
6. Run targeted page tests.

### Task 6: Verification And Progress Notes

**Files:**
- Modify: `docs/开发进度.md`

**Steps:**
1. Run backend targeted tests.
2. Run frontend targeted tests.
3. Run frontend type-check and mini program build.
4. Update progress notes with branch, files, verification, risks.
5. Commit scoped changes only.

