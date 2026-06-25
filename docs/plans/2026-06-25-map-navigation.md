# Map Navigation Implementation Plan

> **For Claude:** REQUIRED SUB-SKILL: Use superpowers:executing-plans to implement this plan task-by-task.

**Goal:** Fix map drawer resize/request races and add on-page marker loading, filtering, search, location, and navigation behavior for the campus map.

**Architecture:** Keep the map module mobile-first and AMap-backed. Frontend owns H5/in-app map rendering and request cancellation handling; backend remains the authenticated source for internal map points and point navigation metadata. External AMap POI/route capabilities are wrapped behind small frontend helpers so Mini Program adapters can use the same data shape later.

**Tech Stack:** uni-app, Vue 3, TypeScript, WXS, AMap JS API, FastAPI, Pydantic, SQLAlchemy.

---

## Module Start Checklist

- Module: 地图模块.
- Docs read: project overview, database design, API conventions, map feature spec, map API spec, map table design.
- APIs affected: `/api/v1/map/points`, `/api/v1/map/search`, `/api/v1/map/points/{point_id}/navigation` consumers; request cancellation handling.
- Tables affected: none.
- Prototypes/assets: `frontend/页面原型/首页-常规状态.png`, `首页-动态内容栏收缩状态.png`, `地图选点.png`, `frontend/素材/svg/地图点/*`.
- Upstream modules: auth/session storage, tab bar.
- Smallest vertical slice: no default marker load, user-selected marker categories, in-app route drawing, drawer resize recovery.
- Out of scope: custom map engine, external App handoff, Redis/WebSocket, complex routing algorithm.
- Verification: unit tests, backend map API regression, type-check, H5 manual/browser smoke where possible.

## Task 1: Request Cancellation And Initial Marker Policy

**Files:**
- Modify: `frontend/src/services/request.ts`
- Modify: `frontend/src/pages/index/map-page.ts`
- Modify: `frontend/src/pages/index/index.vue`
- Test: `frontend/tests/services/request.test.ts`
- Test: `frontend/tests/pages/map-page.test.ts`

**Step 1: Write failing tests**

- Add a request service test proving `NS_BINDING_ABORTED`/`abort` becomes a request-canceled error and does not trigger auth expiry.
- Add map page utility tests proving initial marker filter is empty and no marker query is built until a filter/search is selected.

**Step 2: Run tests to verify RED**

Run:

```bash
npm test -- --run tests/services/request.test.ts tests/pages/map-page.test.ts
```

Expected: new tests fail because cancel detection and empty initial marker policy do not exist yet.

**Step 3: Implement minimal code**

- Introduce `ApiRequestCanceledError` and `isRequestCanceledError`.
- Treat aborted request failures as cancel errors.
- Add nullable active filter state; skip `refreshMapPoints()` when no marker layer is selected.
- Keep search able to render explicit search results.

**Step 4: Verify GREEN**

Run:

```bash
npm test -- --run tests/services/request.test.ts tests/pages/map-page.test.ts
```

Expected: tests pass.

## Task 2: Drawer Resize And Marker Display Modes

**Files:**
- Modify: `frontend/src/pages/index/index.vue`
- Modify: `frontend/src/pages/index/map-page.ts`
- Test: `frontend/tests/pages/map-page.test.ts`

**Step 1: Write failing tests**

- Add tests for marker display mode selection: dense/many points => icon, moderate => label, few/selected/search => preview.
- Add source-level test that drawer progress handler schedules map resize after WXS layout changes.

**Step 2: Run tests to verify RED**

Run:

```bash
npm test -- --run tests/pages/map-page.test.ts
```

Expected: tests fail because display-mode helper and resize scheduler do not exist.

**Step 3: Implement minimal code**

- Add `getMarkerDisplayMode`.
- Re-render H5 markers on zoom/move using icon, label, or preview HTML.
- Import SVG marker assets from `frontend/素材/svg/地图点`.
- In `onDrawerProgressChange`, schedule AMap `resize()` after the WXS transition using `requestAnimationFrame` and a short timeout.

**Step 4: Verify GREEN**

Run:

```bash
npm test -- --run tests/pages/map-page.test.ts
```

Expected: tests pass.

## Task 3: In-App Location, Search, And Navigation

**Files:**
- Modify: `frontend/src/api/map.ts`
- Modify: `frontend/src/pages/index/map-page.ts`
- Modify: `frontend/src/pages/index/index.vue`
- Test: `frontend/tests/api/map.test.ts`
- Test: `frontend/tests/pages/map-page.test.ts`
- Test: `backend/tests/test_map_api.py`

**Step 1: Write failing tests**

- API test for navigation query accepting current location and mode.
- Page utility test for campus-bounds filtering of external POI results.
- Source-level test proving `window.open` is not used for navigation.
- Backend regression test for optional `from_lng/from_lat/mode` navigation query fields if backend contract changes.

**Step 2: Run tests to verify RED**

Run:

```bash
npm test -- --run tests/api/map.test.ts tests/pages/map-page.test.ts
py -3.11 -m pytest tests/test_map_api.py -q
```

Expected: tests fail because current navigation opens external URL and API types do not accept location.

**Step 3: Implement minimal code**

- Add user-location state and AMap geolocation marker.
- Replace external URL handoff with in-page route rendering.
- Add route overlay state using existing map surface.
- Wrap AMap POI search behind helper functions and filter results to campus bounds.
- Keep backend navigation metadata compatible; external URL remains in response but frontend ignores it for normal navigation.

**Step 4: Verify GREEN**

Run:

```bash
npm test -- --run tests/api/map.test.ts tests/pages/map-page.test.ts
py -3.11 -m pytest tests/test_map_api.py -q
```

Expected: tests pass.

## Task 4: Filter Menu Visual Polish And Progress Notes

**Files:**
- Modify: `frontend/src/pages/index/index.vue`
- Modify: `frontend/src/pages/index/map-page.ts`
- Modify: `frontend/tests/pages/map-page.test.ts`
- Modify: `docs/开发进度.md`

**Step 1: Write failing tests**

- Add source-level tests that filter options include marker SVG icon paths and Songti font stack is retained.

**Step 2: Run tests to verify RED**

Run:

```bash
npm test -- --run tests/pages/map-page.test.ts
```

Expected: tests fail because filter option icon mapping is incomplete.

**Step 3: Implement minimal code**

- Render menu rows with the mapped SVG icon, title, subtitle, active state, and redesigned arrow.
- Ensure Chinese UI text keeps the Songti font stack.
- Update progress notes with branch, files, verification, blockers, and next step.

**Step 4: Final verification**

Run:

```bash
npm test -- --run tests/services/request.test.ts tests/pages/map-page.test.ts tests/api/map.test.ts tests/components/app-tab-bar.test.ts
npm run type-check
npm run build:h5
npm run build:mp-weixin
py -3.11 -m pytest tests/test_map_api.py -q
```

Expected: all commands pass, or any blocked verification is recorded with the exact reason.
