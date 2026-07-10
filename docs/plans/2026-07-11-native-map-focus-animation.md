# Native Map Focus Animation Implementation Plan

> **For Claude:** REQUIRED SUB-SKILL: Use superpowers:executing-plans to implement this plan task-by-task.

**Goal:** Replace logic-layer map-center tweening with a native map movement so Marker, POI, and “我的位置” focus smoothly without zooming out an already enlarged map.

**Architecture:** Keep `centerMapToPoint` as the shared page entry, but route smooth movements through one `MapContext.moveToLocation` call instead of repeated reactive longitude/latitude writes. Add a pure scale helper in `map-page.ts`, use a latest-request sequence to ignore stale callbacks, and retain a one-write controlled-center fallback.

**Tech Stack:** uni-app, Vue 3 Composition API, TypeScript, WeChat Mini Program `MapContext`, Vitest

---

### Task 1: Define the minimum focus-scale rule

**Files:**
- Modify: `frontend/src/pages/index/map-page.ts`
- Test: `frontend/tests/pages/map-page.test.ts`

**Step 1: Write the failing test**

Import `getMapFocusTargetScale` and add:

```ts
it("only raises the map focus scale when it is below the minimum", () => {
  expect(getMapFocusTargetScale(16, 18)).toBe(18);
  expect(getMapFocusTargetScale(18, 18)).toBe(18);
  expect(getMapFocusTargetScale(19.5, 18)).toBe(19.5);
});
```

**Step 2: Run test to verify it fails**

Run: `npm run test -- --run tests/pages/map-page.test.ts`

Expected: FAIL because `getMapFocusTargetScale` is not exported.

**Step 3: Write minimal implementation**

Add beside the other map-scale helpers:

```ts
export function getMapFocusTargetScale(
  currentScale: number,
  minimumScale: number,
): number {
  if (!Number.isFinite(currentScale)) return minimumScale;
  return Math.max(currentScale, minimumScale);
}
```

**Step 4: Run test to verify it passes**

Run: `npm run test -- --run tests/pages/map-page.test.ts`

Expected: PASS.

**Step 5: Commit**

```powershell
git add -- frontend/src/pages/index/map-page.ts frontend/tests/pages/map-page.test.ts
git commit -m "test: define map focus scale behavior"
```

### Task 2: Replace the JS center tween with native map movement

**Files:**
- Modify: `frontend/src/pages/index/index.vue:540-570`
- Modify: `frontend/src/pages/index/index.vue:1000-1040`
- Modify: `frontend/src/pages/index/index.vue:1690-1785`
- Modify: `frontend/src/pages/index/index.vue:2570-2690`
- Modify: `frontend/src/pages/index/index.vue:2790-2850`
- Modify: `frontend/src/pages/index/index.vue:3025-3055`
- Modify: `frontend/src/pages/index/index.vue:3095-3120`
- Test: `frontend/tests/pages/map-page.test.ts:885-935`

**Step 1: Write the failing page-source test**

Replace the old test that requires `animateMapCenterToPoint` with assertions for the new shared native path:

```ts
it("uses one native movement for marker poi and location focus", () => {
  const nativeMoveSource = extractFunctionSource("moveNativeMapToPoint");
  const focusSource = extractFunctionSource("focusMapToPoint");
  const poiTapSource = extractFunctionSource("handleNativePoiTap");
  const markerTapSource = extractFunctionSource("handleNativeMarkerTap");
  const locateMeSource = extractFunctionSource("locateMe");

  expect(nativeMoveSource).toContain("mapContext.moveToLocation");
  expect(nativeMoveSource).toContain("longitude: nextCenter.lng");
  expect(nativeMoveSource).toContain("latitude: nextCenter.lat");
  expect(nativeMoveSource).toContain("requestId !== mapCenterMoveRequestId");
  expect(focusSource).toContain("getMapFocusTargetScale");
  expect(markerTapSource).toContain("focusMapToPoint");
  expect(poiTapSource).toContain("focusMapToPoint");
  expect(locateMeSource).toContain("focusMapToPoint(point)");
  expect(indexPageSource).not.toContain("MAP_CENTER_ANIMATION_STEPS");
  expect(indexPageSource).not.toContain("animateMapCenterToPoint");
});
```

Update the manual-drag test to require `invalidateMapCenterMovement()` instead of `stopMapCenterAnimation()`.

**Step 2: Run test to verify it fails**

Run: `npm run test -- --run tests/pages/map-page.test.ts`

Expected: FAIL because the page still contains the fixed-step tween and has no native movement helper.

**Step 3: Extend the local map context type**

Add the API used by this page:

```ts
moveToLocation?: (options: {
  longitude: number;
  latitude: number;
  success?: () => void;
  fail?: () => void;
}) => void;
```

**Step 4: Replace timer state with latest-request state**

Remove `MAP_CENTER_ANIMATION_DURATION_MS`, `MAP_CENTER_ANIMATION_STEPS`, and `mapCenterAnimationTimer`. Keep POI tap suppression independent with a descriptive settle constant, and add:

```ts
const MAP_FOCUS_SETTLE_MS = 720;
let mapCenterMoveRequestId = 0;

function invalidateMapCenterMovement() {
  mapCenterMoveRequestId += 1;
}
```

**Step 5: Implement the native movement with a one-write fallback**

Replace `animateMapCenterToPoint` with:

```ts
function moveNativeMapToPoint(nextCenter: LngLat) {
  const requestId = ++mapCenterMoveRequestId;
  const mapContext = getNativeMapContext();
  const syncLatestCenter = () => {
    if (requestId !== mapCenterMoveRequestId) return;
    syncMapCenterFromNative(nextCenter);
  };

  if (!mapContext?.moveToLocation) {
    syncLatestCenter();
    return;
  }

  mapContext.moveToLocation({
    longitude: nextCenter.lng,
    latitude: nextCenter.lat,
    success: syncLatestCenter,
    fail: syncLatestCenter,
  });
}
```

Make smooth `centerMapToPoint` calls use `moveNativeMapToPoint`; non-smooth calls invalidate pending movement and write the controlled center once. If the page currently creates a map context inline, extract or reuse the existing context accessor rather than creating a second abstraction.

**Step 6: Apply the conditional scale and shared focus entry**

Import `getMapFocusTargetScale` and change the focus path to:

```ts
function focusMapToPoint(point: LngLat) {
  const targetScale = getClampedMapScale(
    getMapFocusTargetScale(observedMapScale.value, MAP_POINT_FOCUS_SCALE),
  );
  if (targetScale > observedMapScale.value) {
    setControlledMapScale(targetScale);
  }
  centerMapToPoint(point, { smooth: true });
}
```

Use `focusMapToPoint(point)` in `locateMe`. Keep Marker and resolved POI callers on the same function.

**Step 7: Invalidate stale movement on user interaction and teardown**

On a drag-caused `regionchange` begin, call `invalidateMapCenterMovement()`. On unmount, invalidate the request instead of clearing an animation timer. Do not alter the existing Marker bubble refresh rules.

**Step 8: Run targeted tests**

Run: `npm run test -- --run tests/pages/map-page.test.ts`

Expected: PASS.

**Step 9: Run type checking**

Run: `npm run type-check`

Expected: PASS.

**Step 10: Commit**

```powershell
git add -- frontend/src/pages/index/index.vue frontend/tests/pages/map-page.test.ts
git commit -m "fix: smooth native map focus movement"
```

### Task 3: Record and verify the completed change

**Files:**
- Modify: `docs/开发进度.md`

**Step 1: Add the progress entry**

Record the branch, native movement replacement, conditional zoom rule, files changed, automated verification, and the remaining WeChat DevTools/real-device checks. State explicitly that location permission behavior and map APIs were not changed.

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
git add -- docs/开发进度.md
git commit -m "docs: record native map focus verification"
```

**Step 7: Manual Mini Program verification**

In WeChat DevTools or a real device, verify Marker, POI, and “我的位置” movement at scale below 18 and above 18; rapid repeated taps; dragging during movement; final Marker bubbles. Record this as pending if the environment is unavailable.
