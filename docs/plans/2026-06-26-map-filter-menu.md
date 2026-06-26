# Map Filter Menu Implementation Plan

> **For Claude:** REQUIRED SUB-SKILL: Use superpowers:executing-plans to implement this plan task-by-task.

**Goal:** Optimize the map page filter dropdown so it uses the new map point SVG assets, animates the arrow/menu through WXS, and remains tappable after native map zoom gestures.

**Architecture:** Keep the change scoped to the frontend map page. The filter control will move into a stable overlay layer above the map viewport instead of living inside the native map area, and WXS will own the high-frequency style updates for the dropdown and arrow. Vue remains responsible for filter state and data loading.

**Tech Stack:** uni-app, Vue 3, TypeScript, WXS, Vitest, WeChat Mini Program native `map`.

---

## Task 1: Add Regression Coverage

**Files:**
- Modify: `frontend/tests/pages/map-page.test.ts`

**Steps:**
1. Add tests asserting the map filter uses the new named SVG assets: `全部.svg`, `紧急任务.svg`, `日常任务.svg`, `猫咪点.svg`, `物资点.svg`, `地标.svg`, `筛选.svg`, `箭头.svg`.
2. Add tests asserting the filter overlay is outside the map viewport and has a native-map-safe wrapper.
3. Add tests asserting a WXS filter animation module exists and the old CSS-only `.filter-chevron-mark` arrow is gone.
4. Run `npm test -- --run tests/pages/map-page.test.ts`.
5. Expected first run: fail because implementation still uses the old icon mapping, old arrow, and no filter WXS module.

## Task 2: Update Assets and Template Structure

**Files:**
- Modify: `frontend/src/pages/index/index.vue`
- Add/use: `frontend/素材/svg/地图点/*.svg`

**Steps:**
1. Replace old icon imports with the named SVG assets.
2. Move the filter overlay out of `.map-viewport` so the native `map` does not capture its tap area after zoom gestures.
3. Use `cover-view` / `cover-image` for the menu layer where uni-app supports it, while preserving H5-compatible classes.
4. Replace the CSS arrow with the `箭头.svg` image.
5. Keep the public Vue methods `toggleFilterMenu`, `selectFilter`, and `getFilterOptionIcon`.

## Task 3: Add WXS Animation

**Files:**
- Add: `frontend/src/pages/index/filter-menu.wxs`
- Modify: `frontend/src/pages/index/index.vue`

**Steps:**
1. Create `filter-menu.wxs` with `init`, `toggle`, and `sync` functions.
2. Animate the menu panel via opacity, translateY, and scaleY using `setStyle`.
3. Animate the arrow image by translating from the chip’s left side to the right side when open, and back when closed.
4. Call back to Vue only when the logical open/closed state changes.
5. Keep state idempotent so repeated toggles or rerenders do not desync visual state.

## Task 4: Verify and Commit

**Files:**
- Modify: `docs/开发进度.md`

**Steps:**
1. Run `npm test -- --run tests/pages/map-page.test.ts`.
2. Run `npm run type-check`.
3. Run `npm run build:h5`.
4. Run `npm run build:mp-weixin`.
5. Update `docs/开发进度.md` with branch, files, verification, and remaining manual Mini Program checks.
6. Run `git diff --check`.
7. Commit with `fix(map): improve filter menu overlay`.
