# Marker Selection Drawer Expansion Implementation Plan

> **For Claude:** REQUIRED SUB-SKILL: Use superpowers:executing-plans to implement this plan task-by-task.

**Goal:** Expand the map content drawer from its collapsed snap point to the detail snap point whenever a valid point detail is selected, without collapsing it when selection is cleared.

**Architecture:** Vue emits a monotonic one-way request token whenever `selectedSummary` receives a valid detail. The WXS module remains the sole owner of actual drawer progress and applies the existing snap animation only when its current progress is exactly the collapsed state.

**Tech Stack:** uni-app, Vue 3 Composition API, WeChat WXS, TypeScript, Vitest

---

### Task 1: Add the one-way drawer expansion request

**Files:**
- Modify: `frontend/src/pages/index/index.vue:1-12`
- Modify: `frontend/src/pages/index/index.vue:500-550`
- Modify: `frontend/src/pages/index/index.vue:3025-3080`
- Modify: `frontend/src/pages/index/drawer.wxs:1-225`
- Test: `frontend/tests/pages/map-page.test.ts:315-470`
- Test: `frontend/tests/pages/map-page.test.ts:600-625`

**Step 1: Write the failing test**

Add a page/WXS regression test:

```ts
it("opens a collapsed drawer to the detail snap point when a point detail is selected", () => {
  const ensureDetailSource = drawerWxsSource.slice(
    drawerWxsSource.indexOf("function ensureDetailVisible"),
    drawerWxsSource.indexOf("function touchstart"),
  );
  const clearSource = extractFunctionSource("clearSelectedMapPointState");

  expect(indexPageSource).toContain(':drawerDetailRequest="drawerDetailRequest"');
  expect(indexPageSource).toContain(
    ':change:drawerDetailRequest="drawer.ensureDetailVisible"',
  );
  expect(indexPageSource).toContain("watch(selectedSummary");
  expect(indexPageSource).toContain("drawerDetailRequest.value += 1");
  expect(drawerWxsSource).toContain("var DETAIL_DRAWER_PROGRESS = 2");
  expect(ensureDetailSource).toContain("currentProgress !== 0");
  expect(ensureDetailSource).toContain("isDragging");
  expect(ensureDetailSource).toContain("currentProgress = DETAIL_DRAWER_PROGRESS");
  expect(ensureDetailSource).toContain("applyFinalProgress(currentProgress, ownerInstance)");
  expect(drawerWxsSource).toContain("ensureDetailVisible: ensureDetailVisible");
  expect(clearSource).not.toContain("drawerDetailRequest");
});
```

**Step 2: Run the test to verify it fails**

Run: `npm run test -- --run tests/pages/map-page.test.ts`

Expected: FAIL because the page has no request binding and WXS has no programmatic detail expansion handler.

**Step 3: Add the Vue request token**

Add to the root map page bindings:

```vue
:drawerDetailRequest="drawerDetailRequest"
:change:drawerDetailRequest="drawer.ensureDetailVisible"
```

Add page state:

```ts
const drawerDetailRequest = ref(0);
```

Add a watcher that only emits on valid details:

```ts
watch(selectedSummary, (summary) => {
  if (summary) {
    drawerDetailRequest.value += 1;
  }
});
```

Do not write the token from `clearSelectedMapPointState`, filter changes, search clearing, or any other path that sets the summary to `null`.

**Step 4: Add the WXS command**

Add the target snap constant and handler:

```js
var DETAIL_DRAWER_PROGRESS = 2;

function ensureDetailVisible(newValue, oldValue, ownerInstance) {
  if (!newValue || newValue === oldValue || isDragging || currentProgress !== 0) return;
  setDrawerResizeInProgress(ownerInstance, true);
  currentProgress = DETAIL_DRAWER_PROGRESS;
  applyFinalProgress(currentProgress, ownerInstance);
  setDrawerResizeInProgress(ownerInstance, false);
}
```

Export `ensureDetailVisible`. Do not add a reverse command when `newValue` is empty or when selection is cleared.

**Step 5: Run targeted tests**

Run: `npm run test -- --run tests/pages/map-page.test.ts`

Expected: PASS.

**Step 6: Run type checking**

Run: `npm run type-check`

Expected: PASS.

**Step 7: Commit**

```powershell
git add -- frontend/src/pages/index/index.vue frontend/src/pages/index/drawer.wxs frontend/tests/pages/map-page.test.ts
git commit -m "fix: expand collapsed drawer for selected points"
```

### Task 2: Record and verify the drawer behavior

**Files:**
- Modify: `docs/开发进度.md`

**Step 1: Update the progress entry**

Record the one-way Vue-to-WXS request, the `0 -> 2` condition, selection-clear behavior, unchanged native map focus animation, automated checks, and remaining WeChat DevTools/real-device checks.

**Step 2: Run the complete frontend test suite**

Run: `npm run test -- --run`

Expected: all test files pass.

**Step 3: Run final type checking**

Run: `npm run type-check`

Expected: PASS.

**Step 4: Build the WeChat Mini Program**

Run: `npm run build:mp-weixin`

Expected: build exits with code 0.

**Step 5: Inspect the final diff and status**

Run: `git diff --check` and `git status --short`

Expected: no whitespace errors; only the intended progress document remains uncommitted.

**Step 6: Commit**

```powershell
git add -- docs/开发进度.md docs/plans/2026-07-11-marker-selection-drawer-expansion-design.md docs/plans/2026-07-11-marker-selection-drawer-expansion.md
git commit -m "docs: record selected-point drawer behavior"
```

**Step 7: Manual Mini Program verification**

Collapse the drawer and select a business Marker and a native POI; verify it snaps to detail progress `2`. Repeat from progress `1`, `2`, and `3`; clear selection by tapping blank map space; manually collapse and select again. Confirm clearing never moves the drawer and native map focus animation is unchanged.
