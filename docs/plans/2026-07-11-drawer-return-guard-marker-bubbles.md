# 抽屉动画、资料返回确认与 Marker 气泡 Implementation Plan

> **For Claude:** REQUIRED SUB-SKILL: Use superpowers:executing-plans to implement this plan task-by-task.

**Goal:** 在不改变定位权限与地图接口参数的前提下，使地图抽屉拖动更平滑、筛选菜单向下展开、资料编辑能拦截微信右滑退出，并让 Marker 气泡只在低密度当前视口中以缩放效果出现。

**Architecture:** 保留 WXS 驱动的抽屉触摸路径，减少无意义样式写入并放慢进度和抽屉回弹；原生地图仍采用预铺尺寸，避免重现瓦片重载。新增纯 Marker 视口/气泡策略函数，在地图稳定后由原生地图 region 与 `toScreenLocation` 计算最多六个业务 Marker 的覆盖层气泡。两个资料页共享脏表单返回守卫，微信端用 `page-container` 捕获原生返回和右滑，其他端保留显式返回按钮回退。

**Tech Stack:** uni-app Vue 3、TypeScript、WXS、微信小程序原生 `map`/`cover-view`/`page-container`、Vitest。

---

### Task 1: 抽屉与筛选菜单的 WXS 动画回归测试

**Files:**
- Modify: `frontend/tests/pages/map-page.test.ts:230-320`
- Modify: `frontend/src/pages/index/drawer.wxs:1-220`
- Modify: `frontend/src/pages/index/filter-menu.wxs:1-100`

**Step 1: Write the failing test**

在 `map-page.test.ts` 增加源码级断言：WXS 触摸进度使用更大的拖动距离、缓存上一次应用进度以跳过细微变化、抽屉释放动画不短于 `0.4s`，而原生地图 transition 仍为 `none`；筛选菜单打开时 `chipWidth` 与关闭时相同，菜单只做向下位移/透明度变化。

**Step 2: Run test to verify it fails**

Run: `cd frontend && npm run test -- --run tests/pages/map-page.test.ts`

Expected: FAIL，当前 WXS 的进度距离为 `368`、没有进度缓存、抽屉回弹为 `0.3s`，筛选 chip 在打开时为 `336`。

**Step 3: Write minimal implementation**

在 `drawer.wxs`：

```js
var DRAG_PROGRESS_DISTANCE_RPX = 560;
var MIN_PROGRESS_DELTA = 0.002;
var lastAppliedProgress = -1;
var DRAWER_SNAP_TRANSITION = 'all 0.42s cubic-bezier(0.25, 1, 0.5, 1)';

function applyProgress(progress, ownerInstance, transition) {
  if (Math.abs(progress - lastAppliedProgress) < MIN_PROGRESS_DELTA) return;
  lastAppliedProgress = progress;
  // 保留已有 selectorQuery setStyle；原生地图 transition 仍为 none。
}

deltaProgress = -deltaY / px(DRAG_PROGRESS_DISTANCE_RPX);
```

在触摸开始和最终吸附前重置缓存，确保点击/吸附总能写入最终样式。`filter-menu.wxs` 把 chip/hit 宽度固定为关闭状态宽度，并继续仅改变菜单的 `opacity`、`translateY` 与箭头旋转。

**Step 4: Run test to verify it passes**

Run: `cd frontend && npm run test -- --run tests/pages/map-page.test.ts`

Expected: PASS。

**Step 5: Commit**

```powershell
git add -- frontend/src/pages/index/drawer.wxs frontend/src/pages/index/filter-menu.wxs frontend/tests/pages/map-page.test.ts
git commit -m "fix: smooth map drawer interactions"
```

### Task 2: 可测试的 Marker 视口与气泡可见性策略

**Files:**
- Modify: `frontend/src/pages/index/map-page.ts:1-390`
- Modify: `frontend/tests/pages/map-page.test.ts:1-225`

**Step 1: Write the failing test**

为纯函数写入以下用例：缩放 `<18`、拖动中、筛选未就绪、无标记时均不展示；缩放足够且视口业务点 `<=6` 时展示；`>=8` 时隐藏；`7` 保留上次稳定状态；选择中的业务 Marker 只允许自己的原生标题；外部 POI 不允许自动气泡。再为经纬度边界函数写入边界内、边界外和跨越顺序测试。

**Step 2: Run test to verify it fails**

Run: `cd frontend && npm run test -- --run tests/pages/map-page.test.ts`

Expected: FAIL，纯策略和视口函数尚不存在，旧 `getMarkerDisplayMode` 忽略可见点数。

**Step 3: Write minimal implementation**

在 `map-page.ts` 导出明确的无副作用 API：

```ts
export interface MapViewportBounds { southwest: MapCoordinate; northeast: MapCoordinate }
export function isMarkerInsideViewport(marker: MapPointMarker, bounds: MapViewportBounds): boolean
export function getMarkerBubbleVisibility(input: MarkerBubbleVisibilityInput): boolean
```

`getMarkerBubbleVisibility` 依照 `zoom >= 18`、`stable`、`filterReady`、非无标记、实际视口内业务点数，以及 6/8/7 滞回返回布尔值；现有 `getMarkerDisplayMode` 调整为“只有 selected 才可使用原生 title label”，不再把全量 Marker 转成 `ALWAYS` callout。

**Step 4: Run test to verify it passes**

Run: `cd frontend && npm run test -- --run tests/pages/map-page.test.ts`

Expected: PASS。

**Step 5: Commit**

```powershell
git add -- frontend/src/pages/index/map-page.ts frontend/tests/pages/map-page.test.ts
git commit -m "fix: add marker bubble visibility policy"
```

### Task 3: 当前视口的 Marker 覆盖层气泡

**Files:**
- Modify: `frontend/src/pages/index/index.vue:1-2700`
- Modify: `frontend/src/shime-uni.d.ts:1-120`
- Modify: `frontend/tests/pages/map-page.test.ts:700-1040`

**Step 1: Write the failing test**

新增测试断言：地图稳定后调用 `getRegion`，按当前筛选的 `nativeMarkerSourceMarkers` 计算视口内业务点；只为策略允许的最多六个点调用 `toScreenLocation` 并渲染 `cover-view` 气泡；`begin` 阶段、筛选切换和无标记都会清空覆盖层；原生 marker 的未选中 callout 始终是空 `BYCLICK`，不再由“选中后切换筛选”的临时布尔状态驱动。

**Step 2: Run test to verify it fails**

Run: `cd frontend && npm run test -- --run tests/pages/map-page.test.ts`

Expected: FAIL，当前代码没有 region/screen-location 气泡状态，且 `selectFilter` 使用 `hadSelectedPoint`。

**Step 3: Write minimal implementation**

在 `NativeMapContext` 加上可选的 `getRegion`、`toScreenLocation` 类型；在页面维护递增请求序列、稳定 region、`viewportMarkerBubbles` 和滞回状态。只在 `regionchange` 的 `end` 且筛选请求结束时刷新：

```ts
const visibleMarkers = nativeMarkerSourceMarkers.value.filter(isBusinessMarker).filter(inViewport);
const shouldShow = getMarkerBubbleVisibility({ zoom, stable: true, filterReady, activeFilter, visibleMarkerCount: visibleMarkers.length, previousVisible });
const bubbles = shouldShow ? await Promise.all(visibleMarkers.slice(0, 6).map(toScreenLocation)) : [];
```

模板把气泡放入 map 覆盖层，使用 key 变化的 CSS `opacity + transform: scale()` 动画；气泡 `pointer-events: none`，不截获点位点击。地图开始拖动/缩放、筛选改变、组件卸载和过期异步结果均清空或丢弃。保留选中业务点的原生 `BYCLICK/ALWAYS` 标题作为即时兜底，外部 POI 不显示自动气泡。

**Step 4: Run test to verify it passes**

Run: `cd frontend && npm run test -- --run tests/pages/map-page.test.ts`

Expected: PASS。

**Step 5: Commit**

```powershell
git add -- frontend/src/pages/index/index.vue frontend/src/shime-uni.d.ts frontend/tests/pages/map-page.test.ts
git commit -m "fix: show marker bubbles only in sparse viewports"
```

### Task 4: 个人资料页的统一未保存返回守卫

**Files:**
- Create: `frontend/src/utils/page-leave-guard.ts`
- Modify: `frontend/src/pages/profile/detail.vue:1-330`
- Modify: `frontend/tests/pages/profile-page.test.ts:1-320`

**Step 1: Write the failing test**

为返回守卫纯状态机写入：干净表单立即离开；脏表单先取消本次返回再请求确认；确认后只允许一次程序化 `navigateBack`；取消后守卫重新生效。页面源码测试应验证 `page-container` 使用 `@beforeleave`，自定义返回按钮也复用同一个返回请求函数。

**Step 2: Run test to verify it fails**

Run: `cd frontend && npm run test -- --run tests/pages/profile-page.test.ts`

Expected: FAIL，新守卫工具和 `page-container` 尚不存在。

**Step 3: Write minimal implementation**

实现不依赖 Vue 的 guard 控制器：

```ts
export function createPageLeaveGuard(hasUnsavedChanges: () => boolean) {
  // requestLeave / cancelNativeLeave / confirmDiscard / reset
}
```

资料页以它包裹已有的确认弹窗：`page-container` 的 `beforeleave` 先消费微信原生返回/右滑，脏表单调用既有 `confirmDiscardChanges`，确认后临时解除容器并在 `nextTick` 中只执行一次 `uni.navigateBack()`；取消则重新武装。非微信编译目标不渲染 `page-container`，保留左上角按钮的相同确认路径。

**Step 4: Run test to verify it passes**

Run: `cd frontend && npm run test -- --run tests/pages/profile-page.test.ts`

Expected: PASS。

**Step 5: Commit**

```powershell
git add -- frontend/src/utils/page-leave-guard.ts frontend/src/pages/profile/detail.vue frontend/tests/pages/profile-page.test.ts
git commit -m "fix: guard profile changes before leaving"
```

### Task 5: 管理员成员编辑页复用返回守卫

**Files:**
- Modify: `frontend/src/pages/admin/users/detail.vue:1-620`
- Modify: `frontend/tests/pages/admin-page.test.ts:1-360`

**Step 1: Write the failing test**

新增用例验证管理员资料加载成功后保存初始快照，昵称、部门、年级、联系方式、角色、状态或头像变化会判脏；左上角返回与 `page-container` 的 `beforeleave` 使用共用 guard；保存成功后更新初始快照。

**Step 2: Run test to verify it fails**

Run: `cd frontend && npm run test -- --run tests/pages/admin-page.test.ts`

Expected: FAIL，当前 `goBack` 直接 `navigateBack()`，没有快照与微信退出守卫。

**Step 3: Write minimal implementation**

为成员资料构造可比较快照（头像 URL 和所有可编辑字段）；`applyUser` 与保存成功后更新快照；复用 `createPageLeaveGuard` 和相同的确认文案。不可编辑字段和加载失败不标记为脏，保存中不允许重复离开动作。

**Step 4: Run test to verify it passes**

Run: `cd frontend && npm run test -- --run tests/pages/admin-page.test.ts`

Expected: PASS。

**Step 5: Commit**

```powershell
git add -- frontend/src/pages/admin/users/detail.vue frontend/tests/pages/admin-page.test.ts
git commit -m "fix: guard unsaved member edits"
```

### Task 6: 集成验证、文档与手工微信验收

**Files:**
- Modify: `docs/开发进度.md`
- Modify: relevant current module docs only if public behavior is documented there

**Step 1: Run focused automated verification**

Run: `cd frontend && npm run test -- --run tests/pages/map-page.test.ts tests/pages/profile-page.test.ts tests/pages/admin-page.test.ts`

Expected: PASS。

**Step 2: Run broad frontend verification**

Run:

```powershell
cd frontend
npm run test -- --run
npm run type-check
npm run build:mp-weixin
```

Expected: all commands PASS; the mini-program build accepts `page-container`, `cover-view`, WXS and map-context typings.

**Step 3: Manually verify in WeChat DevTools**

1. Slowly drag the drawer through every snap state and verify its move/release is smooth, while the map tile/center does not flicker or reset.
2. Open every filter and verify the button width never grows rightward; the menu expands directly below it.
3. Change profile/member fields, use both top-left return and right-edge swipe, then verify cancel stays and confirm exits once; verify clean pages exit directly.
4. In a wide map view, verify no unselected bubbles. Zoom in until six or fewer filtered business markers are in view and verify only those bubbles scale/fade in; pan to a different sparse viewport and verify labels migrate. Test the selected → 无标记 → 任意有标记 sequence and verify no mass bubbles appear.

**Step 4: Update progress note**

Append a `+08:00` entry to `docs/开发进度.md` documenting branch, behavior, no API/schema changes, verification commands, and remaining DevTools checks.

**Step 5: Commit**

```powershell
git add -- docs/开发进度.md docs/模块功能/<only-if-updated>
git commit -m "docs: record map interaction verification"
```
