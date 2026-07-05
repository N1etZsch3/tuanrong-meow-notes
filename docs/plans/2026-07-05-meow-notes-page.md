# Meow Notes Page Implementation Plan

> **For Claude:** REQUIRED SUB-SKILL: Use superpowers:executing-plans to implement this plan task-by-task.

**Goal:** Rework the third bottom tab from a task list into the Meow Notes bookshelf entry page, while preserving the existing task list and adding supply and landmark list entries.

**Architecture:** Keep the existing task list implementation intact by moving it to `pages/tasks/list`. Make `pages/tasks/index` the Meow Notes bookshelf tab page. Add supply and landmark list pages that reuse task-list visual patterns but load map point data from existing map APIs, avoiding backend schema or API changes.

**Tech Stack:** uni-app, Vue 3, TypeScript, Pinia-compatible user store, existing request service, Vitest raw-source tests.

---

### Task 1: Failing Tests For Tab And Page Registration

**Files:**
- Modify: `frontend/tests/components/app-tab-bar.test.ts`
- Modify: `frontend/tests/pages/tasks-page.test.ts`
- Modify: `frontend/tests/pages/supplies-page.test.ts`
- Create: `frontend/tests/pages/landmarks-page.test.ts`

**Step 1: Write failing tests**

- Expect `APP_TAB_ITEMS` labels to be `["地图", "猫咪库", "喵记", "我的"]`.
- Expect `pages.json` to contain:
  - `pages/tasks/index`
  - `pages/tasks/list`
  - `pages/supplies/index`
  - `pages/landmarks/index`
- Expect `pages/tasks/index.vue` to contain bookshelf classes and four book labels.
- Expect `pages/tasks/list.vue` to contain the existing `getTasks` task list behavior.
- Expect supply and landmark list pages to call existing map APIs and omit `filter-card`.

**Step 2: Run tests to verify failure**

Run from `frontend`:

```bash
npm run test -- --run tests/components/app-tab-bar.test.ts tests/pages/tasks-page.test.ts tests/pages/supplies-page.test.ts tests/pages/landmarks-page.test.ts
```

Expected: FAIL because tab label and new list pages are not implemented.

### Task 2: Preserve Existing Task List

**Files:**
- Create: `frontend/src/pages/tasks/list.vue`
- Modify: `frontend/src/pages/tasks/index.vue`
- Modify: `frontend/src/pages.json`

**Step 1: Copy the current task list**

Copy the current `frontend/src/pages/tasks/index.vue` content into `frontend/src/pages/tasks/list.vue`.

**Step 2: Register the route**

Add `pages/tasks/list` to `pages.json` with custom navigation and title `任务列表`.

**Step 3: Keep task list active tab**

Keep `<AppTabBar active-key="tasks" />` in `tasks/list.vue` so returning from the list still highlights the Meow Notes tab family.

**Step 4: Run targeted tests**

Run the failing tests again and confirm task list expectations now pass.

### Task 3: Build Meow Notes Bookshelf Page

**Files:**
- Modify: `frontend/src/pages/tasks/index.vue`
- Modify: `frontend/src/components/app-tab-bar.ts`
- Modify: `frontend/src/pages.json`

**Step 1: Implement bookshelf entries**

Define four entries:

```ts
const noteBooks = [
  { key: "tasks", label: "任务", tone: "green", action: "navigate", url: "/pages/tasks/list" },
  { key: "supplies", label: "物资", tone: "cream", action: "navigate", url: "/pages/supplies/index" },
  { key: "landmarks", label: "校园地标", tone: "mint", action: "navigate", url: "/pages/landmarks/index" },
  { key: "medicine", label: "药品", tone: "yellow", action: "toast" },
];
```

**Step 2: Convert shelf CSS**

Use the shelf/book structure from `test/组件/书架书本.html`, translated to uni-app `view` and `button`. Keep the page background `frontend/素材/加载页素材/背景.jpg` and Songti font stack.

**Step 3: Wire navigation**

Task, supply, and landmark books call `uni.navigateTo`; medicine calls `uni.showToast({ title: "药品管理暂未开放", icon: "none" })`.

**Step 4: Update bottom tab text**

Change the third tab label to `喵记`, keeping key `tasks` and route `/pages/tasks/index`.

**Step 5: Run tests**

Run:

```bash
npm run test -- --run tests/components/app-tab-bar.test.ts tests/pages/tasks-page.test.ts
```

Expected: PASS for tab and Meow Notes entry tests.

### Task 4: Add Supply And Landmark List Helpers

**Files:**
- Modify: `frontend/src/api/map.ts`
- Create: `frontend/src/pages/tasks/meow-list-page.ts`

**Step 1: Reuse existing map API types**

Use `MapPointMarkerDto` and `MapSearchResultDto` instead of inventing new backend contracts.

**Step 2: Add list item mapping helpers**

Create a helper that maps map markers/search results to a generic card item:

```ts
export interface MeowPointListItem {
  id: string;
  detail_id: string;
  title: string;
  nearby_landmark_name: string;
  cover_photo_url: string | null;
}
```

Rules:

- `detail_id` uses `business_id || point_id || map_point_id`.
- nearby landmark name prefers associated POI name, location detail, subtitle, area name, then fallback.

**Step 3: Add tests through raw page assertions**

The page tests should confirm the helper name is imported by both list pages.

### Task 5: Build Supply List Page

**Files:**
- Create: `frontend/src/pages/supplies/index.vue`
- Modify: `frontend/src/pages.json`
- Test: `frontend/tests/pages/supplies-page.test.ts`

**Step 1: Implement list page**

Use:

- `getMapPoints(token, { point_types: "supply" })` for initial load.
- `searchMap(token, { keyword, point_types: "supply", page: 1, page_size: 50 })` for search.

**Step 2: UI constraints**

Keep only title, subtitle, search box, scroll list, loading/error/empty states, and cards. Do not include `filter-card`.

**Step 3: Card click**

Navigate to `/pages/supplies/detail?supply_point_id=${item.detail_id}`.

**Step 4: Run tests**

Run:

```bash
npm run test -- --run tests/pages/supplies-page.test.ts
```

Expected: PASS.

### Task 6: Build Landmark List Page

**Files:**
- Create: `frontend/src/pages/landmarks/index.vue`
- Modify: `frontend/src/pages.json`
- Test: `frontend/tests/pages/landmarks-page.test.ts`

**Step 1: Implement list page**

Use:

- `getMapPoints(token, { point_types: "landmark" })`.
- `searchMap(token, { keyword, point_types: "landmark", page: 1, page_size: 50 })`.

**Step 2: UI constraints**

Reuse the supply list layout and task-list card style. Keep only search, list, and state blocks.

**Step 3: Card click**

Navigate to `/pages/landmarks/detail?landmark_id=${item.detail_id}`.

**Step 4: Run tests**

Run:

```bash
npm run test -- --run tests/pages/landmarks-page.test.ts
```

Expected: PASS.

### Task 7: Verification And Progress

**Files:**
- Modify: `docs/开发进度.md`

**Step 1: Run targeted frontend tests**

Run:

```bash
npm run test -- --run tests/components/app-tab-bar.test.ts tests/pages/tasks-page.test.ts tests/pages/supplies-page.test.ts tests/pages/landmarks-page.test.ts tests/api/map.test.ts
```

Expected: PASS.

**Step 2: Run type check**

Run:

```bash
npm run type-check
```

Expected: PASS.

**Step 3: Run WeChat Mini Program build**

Run:

```bash
npm run build:mp-weixin
```

Expected: PASS.

**Step 4: Update progress**

Add a 2026-07-05 progress entry with branch, read docs, changed files, no API/table changes, verification, unverified manual checks, and next step.

**Step 5: Commit implementation**

Stage explicit files only:

```bash
git add -- frontend/src/pages.json frontend/src/components/app-tab-bar.ts frontend/src/pages/tasks/index.vue frontend/src/pages/tasks/list.vue frontend/src/pages/tasks/meow-list-page.ts frontend/src/pages/supplies/index.vue frontend/src/pages/landmarks/index.vue frontend/tests/components/app-tab-bar.test.ts frontend/tests/pages/tasks-page.test.ts frontend/tests/pages/supplies-page.test.ts frontend/tests/pages/landmarks-page.test.ts docs/开发进度.md
git commit -m "feat(tasks): add meow notes bookshelf"
```
