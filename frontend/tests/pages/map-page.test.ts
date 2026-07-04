import { describe, expect, it } from "vitest";

import drawerWxsSource from "../../src/pages/index/drawer.wxs?raw";
import mapApiSource from "../../src/api/map.ts?raw";
import appSource from "../../src/App.vue?raw";
import filterMenuWxsSource from "../../src/pages/index/filter-menu.wxs?raw";
import indexPageSource from "../../src/pages/index/index.vue?raw";
import mapPageSource from "../../src/pages/index/map-page.ts?raw";
import userLocationServiceSource from "../../src/services/user-location.ts?raw";
import {
  ALL_MAP_FILTER_KEY,
  HBNU_CAMPUS,
  NO_MAP_FILTER_KEY,
  clampLngLatToBounds,
  expandLngLatBounds,
  filterCampusExternalPoiResults,
  getMapPointQueryByFilter,
  getMarkerDisplayMode,
  getMapFilterLabel,
  isFiniteLngLat,
  mapBottomContentItemToShellItem,
  mapMarkerToShellItem,
  mapSearchResultToShellItem,
  normalizeMapFilterOptions,
  searchMapShellItems,
  shouldSyncMapScaleFromRegionChange,
  shouldQueryMapScaleFromRegionChange,
  toNativeMapPoint,
  type MapShellItem,
} from "@/pages/index/map-page";

const shellItems: MapShellItem[] = [
  {
    id: "task-1",
    type: "emergency_task",
    title: "北门草丛紧急救助任务",
    subtitle: "紧急任务 · 进行中",
    description: "北门草丛中发现受伤流浪猫",
    distance_meters: 120,
  },
  {
    id: "cat-1",
    type: "cat",
    title: "小橘常驻点",
    subtitle: "教学楼B附近",
    description: "常驻猫咪，性格亲人",
    distance_meters: 150,
  },
  {
    id: "supply-1",
    type: "supply",
    title: "猫协物资点 #1",
    subtitle: "体育馆旁",
    description: "猫粮、航空箱、诱捕笼备用点",
    distance_meters: 90,
  },
];

function extractFunctionSource(functionName: string): string {
  const normalStart = indexPageSource.indexOf(`function ${functionName}`);
  const asyncStart = indexPageSource.indexOf(`async function ${functionName}`);
  const start = normalStart >= 0 ? normalStart : asyncStart;
  expect(start).toBeGreaterThanOrEqual(0);
  const bodyStart = indexPageSource.indexOf("{", start);
  expect(bodyStart).toBeGreaterThan(start);

  let depth = 0;
  for (let index = bodyStart; index < indexPageSource.length; index += 1) {
    const char = indexPageSource[index];
    if (char === "{") {
      depth += 1;
    } else if (char === "}") {
      depth -= 1;
      if (depth === 0) {
        return indexPageSource.slice(start, index + 1);
      }
    }
  }

  return indexPageSource.slice(start);
}

describe("map page shell behavior", () => {
  it("does not keep static frontend task point fixtures", () => {
    expect(mapPageSource).not.toContain("MAP_SHELL_ITEMS");
    expect(mapPageSource).not.toContain("task-emergency-north-gate");
    expect(mapPageSource).not.toContain("task-daily-canteen");
  });

  it("uses the renewable access token provider before map api calls", () => {
    expect(indexPageSource).toContain("userStore.ensureFreshAccessToken()");
  });

  it("uses the WeChat mini program native map path only", () => {
    expect(indexPageSource).toContain('<map');
    expect(indexPageSource).toContain('class="native-map"');
    expect(indexPageSource).toContain(':show-location="Boolean(userLocation)"');
    expect(userLocationServiceSource).toContain("getWechatMiniProgramLocation");
    expect(userLocationServiceSource).toContain("wx.getLocation");
    expect(indexPageSource).not.toContain("uni.openLocation");
    expect(indexPageSource).not.toContain("supportsAmapWeb");
    expect(indexPageSource).not.toContain("window.AMap");
    expect(indexPageSource).not.toContain("appEnv");
    expect(indexPageSource).not.toContain("campus-amap");
    expect(indexPageSource).not.toContain("amap-host");
  });

  it("ignores canceled map requests instead of treating them as page errors", () => {
    expect(indexPageSource).toContain("isRequestCanceledError");
  });

  it("does not load map point markers before the user selects a marker layer", () => {
    expect(indexPageSource).not.toContain(
      "const activeFilter = ref<MapFilterKey>(ALL_MAP_FILTER_KEY)",
    );
    expect(indexPageSource).not.toContain(
      "Promise.all([refreshMapPoints(), loadBottomContent()])",
    );
  });

  it("uses backend-driven filter options with a no-marker default state", () => {
    expect(indexPageSource).toContain("filterOptions");
    expect(indexPageSource).toContain("applyMapFilterOptions");
    expect(indexPageSource).toContain("NO_MAP_FILTER_LABEL");
    expect(indexPageSource).not.toContain('v-for="option in MAP_FILTER_OPTIONS"');
    expect(indexPageSource).toContain("getMapPointQueryByFilter(activeFilter.value");
  });

  it("selects marker display modes from zoom while keeping the selected marker labeled", () => {
    expect(
      getMarkerDisplayMode({
        zoom: 17.8,
        visibleMarkerCount: 40,
        previewEnabled: true,
        labelMinZoom: 16,
        previewMinZoom: 18,
      }),
    ).toBe("icon");
    expect(
      getMarkerDisplayMode({
        zoom: 18,
        visibleMarkerCount: 5,
        previewEnabled: true,
        labelMinZoom: 16,
        previewMinZoom: 18,
      }),
    ).toBe("label");
    expect(
      getMarkerDisplayMode({
        zoom: 19,
        visibleMarkerCount: 40,
        previewEnabled: true,
        labelMinZoom: 16,
        previewMinZoom: 18,
      }),
    ).toBe("label");
    expect(
      getMarkerDisplayMode({
        zoom: 17.9,
        visibleMarkerCount: 1,
        selected: true,
        previewEnabled: true,
        labelMinZoom: 16,
        previewMinZoom: 18,
      }),
    ).toBe("label");
    expect(
      getMarkerDisplayMode({
        zoom: 18.8,
        visibleMarkerCount: 1,
        previewEnabled: true,
        labelMinZoom: 19,
        previewMinZoom: 19,
      }),
    ).toBe("label");
    expect(
      getMarkerDisplayMode({
        zoom: 19,
        visibleMarkerCount: 1,
        previewEnabled: true,
        labelMinZoom: 19,
        previewMinZoom: 19,
      }),
    ).toBe("label");
  });

  it("keeps drawer state native-map friendly without missing WXS callbacks", () => {
    expect(indexPageSource).not.toContain("function onDrawerProgressChange");
    expect(indexPageSource).not.toContain("currentDrawerProgress");
    expect(drawerWxsSource).not.toContain("callMethod('onDrawerProgressChange'");
    expect(indexPageSource).not.toContain("scheduleMapResizeAfterDrawerChange");
    expect(indexPageSource).not.toContain("amapInstance.resize");
  });

  it("does not call missing Vue methods from the filter menu WXS module", () => {
    expect(indexPageSource).toContain('@tap="toggleFilterMenu"');
    expect(indexPageSource).not.toContain('@tap="filterMenu.toggle"');
    expect(filterMenuWxsSource).not.toContain("callMethod");
    expect(filterMenuWxsSource).not.toContain("setFilterMenuOpen");
  });

  it("lets the drawer expand near full screen while keeping a top gap", () => {
    expect(drawerWxsSource).toContain("MAX_DRAWER_PROGRESS");
    expect(drawerWxsSource).toContain("MAX_DRAWER_TOP_GAP_RPX");
    expect(drawerWxsSource).toContain("config.windowHeight / config.rpxRatio - MAX_DRAWER_TOP_GAP_RPX");
    expect(drawerWxsSource).toContain("clamp(progress, 0, MAX_DRAWER_PROGRESS)");
  });

  it("keeps map task rows compact without duplicate middle tags", () => {
    expect(indexPageSource).not.toContain('class="item-tag"');
    expect(indexPageSource).toContain('class="item-status"');
    expect(indexPageSource).toMatch(/\.content-row\s*{[^}]*text-align: left;[^}]*}/s);
    expect(indexPageSource).toMatch(/\.content-row\s*{[^}]*gap: 12rpx;[^}]*}/s);
  });

  it("renders task rows with uploaded cover thumbnails, location detail, and status tones", () => {
    expect(indexPageSource).toContain("getShellItemMetaText(item)");
    expect(indexPageSource).toContain("getShellItemStatusTone(item)");
    expect(indexPageSource).toContain("item.cover_photo_url");
    expect(indexPageSource).toContain('class="item-cover"');
    expect(mapPageSource).toContain("location_detail");
    expect(mapPageSource).toContain("task_status_label");
    expect(indexPageSource).toContain("status-completed");
    expect(indexPageSource).toContain("status-in_progress");
    expect(indexPageSource).toContain("status-cancelled");
    expect(indexPageSource).toContain("status-archived");
    expect(indexPageSource).not.toContain("· 距离 {{ formatDistance(item.distance_meters) }}");
  });

  it("maps cancelled and archived task statuses into task list status tones", () => {
    const baseMarker = {
      point_id: "point-1",
      point_type: "task",
      point_scope: "long_term",
      business_type: "feeding",
      business_id: "task-1",
      name: "娘子坡喂食任务",
      subtitle: "暑假喂食任务",
      lng: 115.06321,
      lat: 30.23108,
      area_id: null,
      area_name: null,
      marker_key: "task_feeding",
      icon_key: "task_feeding",
      display_level: 85,
      visibility: "public",
      status: "active",
      cover_photo_url: null,
      preview_enabled: true,
      preview_min_zoom: 16,
      label_min_zoom: 16,
      distance_meters: null,
    };

    expect(
      mapMarkerToShellItem({
        ...baseMarker,
        extra: { task_status: "cancelled", task_status_label: "已取消" },
      }).status_key,
    ).toBe("cancelled");
    expect(
      mapMarkerToShellItem({
        ...baseMarker,
        extra: { task_status: "archived", task_status_label: "已归档" },
      }).status_key,
    ).toBe("archived");
    const completedTodayMarker = mapMarkerToShellItem({
      ...baseMarker,
      extra: {
        task_status: "in_progress",
        task_status_label: "进行中",
        feeding_status: "completed",
      },
    });
    expect(completedTodayMarker.status_key).toBe("in_progress");
    expect(completedTodayMarker.status_label).toBe("进行中");
    expect(mapSearchResultToShellItem({
      result_type: "task",
      map_point_id: "point-1",
      business_id: "task-1",
      point_type: "task",
      business_type: "feeding",
      title: "归档喂食任务",
      subtitle: "暑假喂食任务",
      description: "屋檐下",
      icon_key: "task_feeding",
      cover_photo_url: null,
      lng: 115.06321,
      lat: 30.23108,
      distance_meters: null,
      status_label: "已归档",
      highlight_text: "",
      sort_score: 0,
    }).status_key).toBe("archived");
    expect(mapBottomContentItemToShellItem({
      id: "task-1",
      type: "daily_task",
      title: "取消喂食任务",
      subtitle: "暑假喂食任务",
      description: "屋檐下",
      distance_meters: null,
      status_label: "已取消",
      tag_label: "喂食任务",
      cover_photo_url: null,
      map_point_id: "point-1",
      lng: 115.06321,
      lat: 30.23108,
    }).status_key).toBe("cancelled");
  });

  it("lets the drawer drag start from the handle and search box only", () => {
    expect(indexPageSource).toContain('class="drawer-grip-area"');
    expect(indexPageSource).toContain('@touchstart="drawer.touchstart"');
    expect(indexPageSource).toContain('class="search-box"');
    expect(indexPageSource).toContain('@touchstart="drawer.touchstart"');
    expect(indexPageSource).toContain('@touchmove="drawer.touchmove"');
    expect(indexPageSource).toContain('@touchend="drawer.touchend"');
    expect(indexPageSource).not.toContain('@touchstart.stop="drawer.touchstart"');
    expect(indexPageSource).not.toContain('@touchmove.stop="drawer.touchmove"');
    expect(indexPageSource).not.toContain('@touchend.stop="drawer.touchend"');
    expect(indexPageSource).toContain('class="search-input"');
    expect(indexPageSource).toContain('@focus="focusSearch"');
  });

  it("shows only the title-side summary type badge in selected point detail cards", () => {
    expect(indexPageSource).toContain("summaryTypeTag");
    expect(indexPageSource).toContain('class="summary-type-badge"');
    expect(indexPageSource).not.toContain('class="summary-tags"');
  });

  it("upserts a marker when a bottom task row is selected from the no-marker state", () => {
    const selectSource = extractFunctionSource("selectShellItem");
    expect(indexPageSource).toContain("function upsertShellItemMapMarker");
    expect(selectSource).toContain("upsertShellItemMapMarker(item)");
  });

  it("keeps the selected point detail paired with a visible native marker", () => {
    const loadSource = extractFunctionSource("loadPointSummary");
    const refreshSource = extractFunctionSource("refreshMapPoints");

    expect(indexPageSource).toContain("function ensureFocusedMarkerFromSummary");
    expect(loadSource).toContain("ensureFocusedMarkerFromSummary(selectedSummary.value)");
    expect(refreshSource).toContain("ensureFocusedMarkerFromSummary(selectedSummary.value)");
  });

  it("clears selected point state when the native map blank area is tapped", () => {
    const tapSource = extractFunctionSource("handleNativeMapTap");
    const clearSource = extractFunctionSource("clearSelectedMapPointState");

    expect(indexPageSource).toContain('@tap="handleNativeMapTap"');
    expect(tapSource).toContain("shouldIgnoreNativeMapTap()");
    expect(tapSource).toContain("clearSelectedMapPointState()");
    expect(clearSource).toContain("selectedSummary.value = null");
    expect(clearSource).toContain("selectedPoiMarker.value = null");
    expect(clearSource).toContain("filterMenuOpen.value = false");
    expect(clearSource).not.toContain("activeFilter.value = null");
    expect(clearSource).not.toContain("searchKeyword.value = \"\"");
    expect(clearSource).not.toContain("clearNativeRoute()");
  });

  it("guards native map blank taps immediately after marker or poi taps", () => {
    const markerTapSource = extractFunctionSource("handleNativeMarkerTap");
    const poiTapSource = extractFunctionSource("handleNativePoiTap");
    const guardSource = extractFunctionSource("shouldIgnoreNativeMapTap");

    expect(indexPageSource).toContain("lastPointTapAt");
    expect(indexPageSource).toContain("MAP_BLANK_TAP_GUARD_MS");
    expect(markerTapSource).toContain("markPointTapInteraction()");
    expect(poiTapSource).toContain("markPointTapInteraction()");
    expect(guardSource).toContain("Date.now() - lastPointTapAt.value");
  });

  it("deduplicates the selected point detail card before rendering text blocks", () => {
    expect(indexPageSource).toContain("summarySubtitleText");
    expect(indexPageSource).toContain("summaryDescriptionText");
    expect(indexPageSource).toContain("summaryLocationText");
    expect(indexPageSource).toContain("summaryPoiTitleText");
    expect(indexPageSource).not.toContain('v-if="selectedSummary.description" class="summary-desc"');
    expect(indexPageSource).not.toContain("公共地点：{{ associatedPoi.name }}");
  });

  it("renders selected task point thumbnails after the avatar image and opens an in-app preview modal", () => {
    expect(indexPageSource).toContain("summaryAvatarUrl");
    expect(indexPageSource).toContain("summaryPreviewPhotos");
    expect(indexPageSource).toContain('class="summary-avatar-image"');
    expect(indexPageSource).toContain('class="summary-photo-strip"');
    expect(indexPageSource).toContain('class="summary-photo-grid"');
    expect(indexPageSource).toContain("@tap=\"previewSummaryPhoto(photo)\"");
    expect(indexPageSource).toContain("ImagePreviewModal");
    expect(indexPageSource).toContain(":visible=\"imagePreviewVisible\"");
    expect(indexPageSource).toContain("openImagePreview");
    expect(indexPageSource).toContain(".slice(1, 4)");
    expect(indexPageSource).not.toContain("uni.previewImage");
  });

  it("keeps navigation in the mini program map APIs", () => {
    expect(indexPageSource).not.toContain("window.open");
    expect(indexPageSource).toContain("renderNativeRoute");
    expect(indexPageSource).toContain("renderInAppRoute");
    expect(indexPageSource).toContain("if (navigation.route.fallback)");
    expect(indexPageSource).toContain("points: []");
    expect(indexPageSource).not.toContain("uni.openLocation");
    expect(indexPageSource).toContain(':polyline="nativeMapPolylines"');
    expect(indexPageSource).not.toContain("renderAmapWalkingRoute");
  });

  it("draws native walking routes with visible mini program polyline settings", () => {
    expect(indexPageSource).toContain('color: "#267b2f"');
    expect(indexPageSource).not.toContain("#267b2fCC");
    expect(indexPageSource).toContain("fitNativeMapToRoute");
    expect(indexPageSource).toContain("includePoints({");
    expect(indexPageSource).toContain("fitNativeMapToRoute(nativeRoutePoints.value)");
  });

  it("keeps provider route coordinates unchanged instead of clamping them into a fake campus edge", () => {
    expect(indexPageSource).toContain("const safeRoutePoints = routePoints.filter(isFiniteLngLat);");
    expect(indexPageSource).toContain(
      "const displayRoutePoints = buildDisplayRoutePoints(from, destination, safeRoutePoints);",
    );
    expect(indexPageSource).toContain("points: displayRoutePoints");
    expect(indexPageSource).not.toContain(
      "routePoints\n    .filter(isFiniteLngLat)\n    .map((point) => clampLngLatToBounds",
    );
    expect(indexPageSource).not.toContain(
      "(routePoints && routePoints.length >= 2 ? routePoints : [from, destination])\n    .filter(isFiniteLngLat)\n    .map((point) => clampLngLatToBounds",
    );
  });

  it("does not bind include-points because empty arrays crash tencent fitBounds", () => {
    expect(indexPageSource).not.toContain(':include-points="nativeMapIncludePoints"');
    expect(indexPageSource).not.toContain("nativeMapIncludePoints");
  });

  it("renders a static navigation route without dynamic navigation markers", () => {
    expect(indexPageSource).not.toContain('class="navigation-panel"');
    expect(indexPageSource).toContain('class="navigation-route-card"');
    expect(indexPageSource).toContain("navigationRoute");
    expect(indexPageSource).toContain("navigationRouteDistance");
    expect(indexPageSource).not.toContain("startNavigationTracking");
    expect(indexPageSource).not.toContain("stopNavigationTracking");
    expect(indexPageSource).not.toContain("simulatedNavigationMarker");
    expect(indexPageSource).not.toContain("navigationSimulationTimer");
    expect(indexPageSource).not.toContain("navigationSimulationRunning");
    expect(indexPageSource).not.toContain("setInterval(");
    expect(indexPageSource).not.toContain('content: "当前位置"');
    expect(indexPageSource).not.toContain("模拟导航");
    expect(indexPageSource).not.toContain("停止模拟");
  });

  it("requests backend merged internal and tencent poi search results", () => {
    expect(indexPageSource).toContain("include_external: true");
    expect(indexPageSource).not.toContain("searchCampusExternalPoisByRest");
    expect(indexPageSource).not.toContain("https://restapi.amap.com/v3/place/text");
  });

  it("starts admin point editing from a long-pressed marker instead of drawer buttons", () => {
    expect(indexPageSource).toContain("userStore.isAdmin");
    expect(indexPageSource).not.toContain('action.key === "edit_point"');
    expect(indexPageSource).not.toContain("/pages/admin/map-point/edit?point_id=");
    expect(indexPageSource).toContain("@longpress");
    expect(indexPageSource).toContain("handleMarkerLongPress");
    expect(indexPageSource).toContain("findNearestEditableMarker");
    expect(indexPageSource).toContain('id="campus-map"');
    expect(indexPageSource).toContain('class="editable-marker-handle"');
    expect(indexPageSource).toContain("dragEditedPoint");
    expect(indexPageSource).toContain("fromScreenLocation");
    expect(indexPageSource).toContain("mapPointEditMode");
    expect(indexPageSource).toContain("saveEditedPointLocation");
    expect(indexPageSource).toContain("updateAdminMapPointLocation");
  });

  it("preloads realtime user location and keeps the location button as a viewport recenter control", () => {
    const locateMeSource = extractFunctionSource("locateMe");

    expect(appSource).toContain("startUserLocationPreload");
    expect(indexPageSource).toContain("subscribeUserLocation");
    expect(indexPageSource).toContain("preloadUserLocation");
    expect(indexPageSource).toContain(':scale="mapScale"');
    expect(indexPageSource).toContain(':show-location="Boolean(userLocation)"');
    expect(locateMeSource).toContain("getCachedUserLocation()");
    expect(locateMeSource).toContain("mapScale.value = getUserLocationFocusScale()");
    expect(locateMeSource).toContain("centerMapToPoint(point, { smooth: true })");
    expect(locateMeSource).not.toContain("getLocationWithFallback");
    expect(locateMeSource).not.toContain("getWechatMiniProgramLocation");
    expect(locateMeSource).not.toContain("requestUserLocation");
    expect(locateMeSource).not.toContain("userLocation.value = null");
    expect(locateMeSource).not.toContain("refreshMapPoints");
    expect(userLocationServiceSource).toContain("scope.userLocation");
    expect(userLocationServiceSource).toContain("wx.startLocationUpdate");
    expect(userLocationServiceSource).toContain("wx.onLocationChange");
    expect(userLocationServiceSource).toContain("subscribeUserLocation");
    expect(userLocationServiceSource).not.toContain("getCampusFallbackLocation");
    expect(indexPageSource).not.toContain("当前位置 ${point.lat");
    expect(indexPageSource).not.toContain("当前位置信息");
    expect(indexPageSource).not.toContain("simulatedNavigationMarker.value = point");
  });

  it("enables native tencent poi tap and resolves tapped poi details through the backend", () => {
    const poiTapSource = extractFunctionSource("handleNativePoiTap");

    expect(indexPageSource).toContain(":enable-poi=\"true\"");
    expect(indexPageSource).toContain("@poitap=\"handleNativePoiTap\"");
    expect(indexPageSource).toContain("resolveMapPoi");
    expect(indexPageSource).toContain("handleNativePoiTap");
    expect(indexPageSource).toContain("matched_poi");
    expect(poiTapSource).toContain("const summary = buildExternalSummaryFromItem(item)");
    expect(poiTapSource).toContain("selectedSummary.value = summary");
    expect(poiTapSource).not.toContain("mapPointMarkers.value");
    expect(poiTapSource).not.toContain("buildExternalSummaryFromMarker");
    expect(poiTapSource).not.toContain("locationIcon");
  });

  it("pins tapped and searched tencent POIs with the landmark svg at the POI coordinate", () => {
    const poiTapSource = extractFunctionSource("handleNativePoiTap");
    const searchMarkerSource = extractFunctionSource("mapSearchShellItemToMarker");

    expect(indexPageSource).toContain("selectedPoiMarker");
    expect(indexPageSource).toContain("buildSelectedPoiMarker(summary)");
    expect(poiTapSource).toContain("selectedPoiMarker.value = buildSelectedPoiMarker(summary)");
    expect(searchMarkerSource).toContain('businessType === "tencent_poi"');
    expect(searchMarkerSource).toContain('icon_key: isExternalPoi ? "landmark"');
    expect(indexPageSource).toContain("landmarkPointIcon");
    expect(indexPageSource).toContain("anchor: { x: 0.5, y: 1 }");
  });

  it("deduplicates native tencent poi taps so repeated native events do not flood resolve requests", () => {
    const poiTapSource = extractFunctionSource("handleNativePoiTap");

    expect(indexPageSource).toContain("pendingPoiResolveKey");
    expect(indexPageSource).toContain("lastResolvedPoiTapKey");
    expect(indexPageSource).toContain("nativePoiTapSuppressedUntil");
    expect(indexPageSource).toContain("function getPoiTapKey");
    expect(indexPageSource).toContain("function shouldSkipPoiResolve");
    expect(indexPageSource).toContain("function isSameSelectedPoiTap");
    expect(indexPageSource).toContain("function suppressNativePoiTaps");
    expect(indexPageSource).toContain("function isNativePoiTapSuppressed");
    expect(indexPageSource).toContain("function startPoiResolve");
    expect(indexPageSource).toContain("function isCurrentPoiResolve");
    expect(indexPageSource).toContain("function finishPoiResolve");
    expect(indexPageSource).toContain("pendingPoiResolveKey.value !== null");
    expect(poiTapSource).toContain("const poiTapKey = getPoiTapKey");
    expect(poiTapSource).toContain("if (isNativePoiTapSuppressed())");
    expect(poiTapSource).toContain("if (shouldSkipPoiResolve(poiTapKey, { lng, lat, keyword }))");
    expect(poiTapSource).toContain("const resolveRequestId = startPoiResolve(poiTapKey)");
    expect(poiTapSource).toContain("if (!isCurrentPoiResolve(resolveRequestId))");
    expect(poiTapSource).toContain("lastResolvedPoiTapKey.value = poiTapKey");
    expect(poiTapSource).toContain("suppressNativePoiTaps()");
    expect(poiTapSource).toContain("finishPoiResolve(resolveRequestId, poiTapKey)");
  });

  it("clears pending native poi state before locating the user so stale resolves cannot pull the map back", () => {
    const locateMeSource = extractFunctionSource("locateMe");

    expect(indexPageSource).toContain("function clearNativePoiSelection");
    expect(indexPageSource).toContain("poiResolveRequestSeq += 1");
    expect(indexPageSource).toContain("pendingPoiResolveKey.value = null");
    expect(indexPageSource).toContain("lastResolvedPoiTapKey.value = null");
    expect(locateMeSource).toContain("clearNativePoiSelection()");
    expect(locateMeSource).toContain("suppressNativePoiTaps()");
    expect(locateMeSource).toContain("centerMapToPoint(point, { smooth: true })");
  });

  it("uses native marker callouts for title labels without slot custom callout fan-out", () => {
    const regionChangeSource = extractFunctionSource("handleMapRegionChange");
    const displayModeSource = extractFunctionSource("getNativeMarkerDisplayMode");

    expect(indexPageSource).not.toContain('slot="callout"');
    expect(indexPageSource).not.toContain(":marker-id=\"callout.markerId\"");
    expect(indexPageSource).not.toContain("nativeMarkerCallouts");
    expect(indexPageSource).toContain("getNativeMarkerDisplayMode(marker)");
    expect(indexPageSource).toContain("buildNativeMarkerTitleCallout(marker.name)");
    expect(indexPageSource).not.toContain("customCallout");
    expect(indexPageSource).not.toContain("marker-callout-thumb");
    expect(indexPageSource).not.toContain("marker-callout-preview");
    expect(regionChangeSource).toContain("shouldSyncMapScaleFromRegionChange(detail)");
    expect(regionChangeSource).toContain("syncMapScaleFromNative(Number(detail.scale))");
    expect(regionChangeSource).toContain("shouldQueryMapScaleFromRegionChange(detail)");
    expect(regionChangeSource).toContain("syncMapScaleFromContext()");
    expect(displayModeSource).toContain(
      "const selectedPointId = selectedSummary.value?.point_id;",
    );
    expect(displayModeSource).toContain(
      'if (selectedPointId && selectedPointId !== marker.point_id) return "icon";',
    );
  });

  it("uses animated focused map movement for poi and marker recentering", () => {
    const poiTapSource = extractFunctionSource("handleNativePoiTap");
    const markerTapSource = extractFunctionSource("handleNativeMarkerTap");

    expect(indexPageSource).toContain("const MAP_POINT_FOCUS_SCALE");
    expect(indexPageSource).toContain("function animateMapCenterToPoint");
    expect(indexPageSource).toContain("function focusMapToPoint");
    expect(indexPageSource).toContain("mapScale.value = getMapPointFocusScale()");
    expect(poiTapSource).toContain("focusMapToPoint({ lng: summary.lng, lat: summary.lat })");
    expect(markerTapSource).toContain("focusMapToPoint({ lng: marker.lng, lat: marker.lat })");
    expect(indexPageSource).not.toContain("moveToLocation({");
  });

  it("syncs manual map drags so the location button can recenter repeatedly", () => {
    const regionChangeSource = extractFunctionSource("handleMapRegionChange");
    const locateMeSource = extractFunctionSource("locateMe");

    expect(regionChangeSource).toContain("stopMapCenterAnimation()");
    expect(regionChangeSource).toContain("syncMapCenterFromNative(nextCenter)");
    expect(locateMeSource).toContain("centerMapToPoint(point, { smooth: true })");
    expect(indexPageSource).toContain(
      "const point = userLocation.value || getCachedUserLocation()",
    );
  });

  it("does not echo programmatic native map updates back into the bound center", () => {
    const regionChangeSource = extractFunctionSource("handleMapRegionChange");

    expect(indexPageSource).toContain("function syncMapCenterFromNative");
    expect(indexPageSource).toContain("function isSameMapCenter");
    expect(regionChangeSource).toContain('if (detail.causedBy === "update")');
    expect(regionChangeSource).toContain("syncMapCenterFromNative(nextCenter)");
    expect(regionChangeSource).not.toContain("mapCenter.value = nextCenter");
  });

  it("syncs native map scale whenever native regionchange provides a scale", () => {
    const regionChangeSource = extractFunctionSource("handleMapRegionChange");

    expect(indexPageSource).toContain("function syncMapScaleFromNative");
    expect(indexPageSource).toContain("function syncMapScaleFromContext");
    expect(indexPageSource).toContain("mapContext.getScale");
    expect(regionChangeSource).toContain("shouldSyncMapScaleFromRegionChange(detail)");
    expect(regionChangeSource).toContain("syncMapScaleFromNative(Number(detail.scale))");
    expect(regionChangeSource).toContain("shouldQueryMapScaleFromRegionChange(detail)");
    expect(regionChangeSource).toContain("syncMapScaleFromContext()");
    expect(regionChangeSource).not.toContain("mapScale.value = detail.scale");

    expect(
      shouldSyncMapScaleFromRegionChange({
        type: "end",
        causedBy: "scale",
        scale: 15,
      }),
    ).toBe(true);
    expect(
      shouldSyncMapScaleFromRegionChange({
        type: "end",
        scale: 15,
      }),
    ).toBe(true);
    expect(
      shouldSyncMapScaleFromRegionChange({
        type: "end",
        causedBy: "drag",
        scale: 15,
      }),
    ).toBe(true);
    expect(
      shouldSyncMapScaleFromRegionChange({
        type: "end",
        causedBy: "update",
        scale: 15,
      }),
    ).toBe(false);
    expect(
      shouldQueryMapScaleFromRegionChange({
        type: "end",
        causedBy: "scale",
      }),
    ).toBe(true);
    expect(
      shouldQueryMapScaleFromRegionChange({
        type: "end",
      }),
    ).toBe(true);
    expect(
      shouldQueryMapScaleFromRegionChange({
        type: "end",
        causedBy: "scale",
        scale: 18,
      }),
    ).toBe(false);
    expect(
      shouldQueryMapScaleFromRegionChange({
        type: "end",
        causedBy: "drag",
      }),
    ).toBe(false);
    expect(
      shouldQueryMapScaleFromRegionChange({
        type: "end",
        causedBy: "update",
      }),
    ).toBe(false);
  });

  it("lowers and compacts the map title, map viewport, filter, and content drawer", () => {
    expect(indexPageSource).toContain("top: var(--catmap-page-title-top, 92rpx)");
    expect(indexPageSource).toContain("font-size: var(--catmap-page-title-font-size, 52rpx)");
    expect(indexPageSource).toContain("font-size: var(--catmap-page-title-subtitle-size, 24rpx)");
    expect(indexPageSource).toContain("top: 218rpx");
    expect(indexPageSource).toContain("bottom: 664rpx");
    expect(indexPageSource).toContain("top: 380rpx");
    expect(indexPageSource).toContain("height: 460rpx");
    expect(drawerWxsSource).toContain("FILTER_LAYER_MIN_TOP_RPX");
    expect(drawerWxsSource).toContain("Math.max(mapT + 34, FILTER_LAYER_MIN_TOP_RPX)");
  });

  it("keeps the native map from auto-fitting marker filters while allowing the native location dot", () => {
    expect(indexPageSource).toContain(':show-location="Boolean(userLocation)"');
    expect(indexPageSource).toContain("nativeRoutePoints.value.length");
    expect(indexPageSource).toContain("return [];");
    expect(indexPageSource).not.toContain("return nativeMarkerSourceMarkers.value");
  });

  it("ignores tapped native POIs outside the campus bounds before resolving them", () => {
    expect(indexPageSource).toContain(
      "if (!isLngLatInsideBounds({ lng, lat }, campusMapConfig.value.limit_bounds))",
    );
    expect(indexPageSource).toContain("return;");
  });

  it("renders mini-program-safe png marker icons and arrow in the filter menu", () => {
    expect(indexPageSource).toContain("MAP_FILTER_ICON_SRC");
    expect(indexPageSource).toContain("filter-option-icon");
    expect(indexPageSource).toContain("filterArrowIcon");
    expect(indexPageSource).toContain("filter-arrow-icon");
    expect(indexPageSource).toContain("../../../素材/png/地图点/全部.png");
    expect(indexPageSource).toContain("../../../素材/png/地图点/紧急任务.png");
    expect(indexPageSource).toContain("../../../素材/png/地图点/日常任务.png");
    expect(indexPageSource).toContain("../../../素材/png/地图点/猫咪点.png");
    expect(indexPageSource).toContain("../../../素材/png/地图点/物资点.png");
    expect(indexPageSource).toContain("../../../素材/png/地图点/地标.png");
    expect(indexPageSource).toContain("../../../素材/png/地图点/箭头.png");
    expect(indexPageSource).toContain("../../../素材/png/地图点/完成任务.png");
    expect(indexPageSource).toContain("../../../素材/png/地图点/失败任务.png");
    expect(indexPageSource).not.toContain("素材/svg/地图点");
    expect(indexPageSource).not.toContain("filter-chevron-mark");
    expect(indexPageSource).not.toContain("⌄");
  });

  it("uses completion and failure task pngs for feeding task map markers", () => {
    expect(indexPageSource).toContain("getFeedingMarkerIcon");
    expect(indexPageSource).toContain("marker.business_type === \"feeding\"");
    expect(indexPageSource).toContain("marker.extra.feeding_status === \"completed\"");
  });

  it("keeps the filter menu in a native-map-safe cover layer", () => {
    expect(indexPageSource).toContain('class="map-filter-layer"');
    expect(indexPageSource).toContain('class="filter-panel-hit-layer"');
    expect(indexPageSource).toContain('@tap="toggleFilterMenu"');
    expect(indexPageSource).toContain(
      '<script module="filterMenu" lang="wxs" src="./filter-menu.wxs"></script>',
    );
    expect(indexPageSource).not.toContain('class="filter-wrap"');

    const viewportIndex = indexPageSource.indexOf('class="map-viewport"');
    const layerIndex = indexPageSource.indexOf('class="map-filter-layer"');
    const drawerIndex = indexPageSource.indexOf('class="content-drawer"');

    expect(viewportIndex).toBeGreaterThan(-1);
    expect(layerIndex).toBeGreaterThan(viewportIndex);
    expect(layerIndex).toBeLessThan(drawerIndex);
  });

  it("hides the native filter cover layer while the image preview mask is open", () => {
    const previewSource = extractFunctionSource("openImagePreview");

    expect(indexPageSource).toContain('<cover-view v-if="!imagePreviewVisible" class="map-filter-layer"');
    expect(previewSource).toContain("filterMenuOpen.value = false");
  });

  it("keeps native marker size aligned with main branch", () => {
    expect(indexPageSource).toContain("const NATIVE_MARKER_HIT_SIZE = 34");
    expect(indexPageSource).toContain("width: NATIVE_MARKER_HIT_SIZE");
    expect(indexPageSource).toContain("height: NATIVE_MARKER_HIT_SIZE");
  });

  it("does not resize native markers on selection because native map marker size is not animatable", () => {
    const nativeMarkerSource = indexPageSource.slice(
      indexPageSource.indexOf("const nativeMapMarkers = computed"),
      indexPageSource.indexOf("const nativeMapPolylines = computed"),
    );

    expect(indexPageSource).not.toContain("ACTIVE_NATIVE_MARKER_SIZE");
    expect(indexPageSource).not.toContain("activeMapPointId");
    expect(indexPageSource).not.toContain("function getNativeMarkerSize");
    expect(nativeMarkerSource).not.toContain("markerSize");
  });

  it("keeps the filter menu animation native-map-safe on iOS", () => {
    expect(filterMenuWxsSource).toContain("filter-chip");
    expect(filterMenuWxsSource).toContain("filter-menu");
    expect(filterMenuWxsSource).toContain("filter-arrow-icon");
    expect(filterMenuWxsSource).toContain("rotate(180deg)");
    expect(filterMenuWxsSource).toContain("rotate(0deg)");
    expect(indexPageSource).toContain(
      '<cover-view class="filter-menu" :class="{ \'is-open\': filterMenuOpen }">',
    );
    expect(indexPageSource).toContain(".filter-menu.is-open");
    expect(filterMenuWxsSource).toContain("opacity 0.18s ease");
    expect(filterMenuWxsSource).toContain("transform 0.18s ease");
    expect(filterMenuWxsSource).not.toContain("transition: trans");
    expect(filterMenuWxsSource).not.toContain("transition || 'none'");
    expect(filterMenuWxsSource).not.toContain("pointerEvents");
    expect(filterMenuWxsSource).not.toContain("scaleY");
  });

  it("navigates summary card view-detail actions to the task detail page", () => {
    expect(indexPageSource).toContain('action.key === "view_detail"');
    expect(indexPageSource).toContain("appendExecutionDateQuery(action.path");
    expect(indexPageSource).toContain("/pages/tasks/detail?task_id=");
  });

  it("filters external poi search results to the campus bounds", () => {
    const results = filterCampusExternalPoiResults(
      [
        {
          id: "inside",
          title: "问山居",
          address: "湖北师范大学校内",
          lng: 115.0612,
          lat: 30.2301,
        },
        {
          id: "outside",
          title: "校外商圈",
          address: "校园外",
          lng: 115.09,
          lat: 30.25,
        },
      ],
      HBNU_CAMPUS.limit_bounds,
    );

    expect(results).toHaveLength(1);
    expect(results[0].id).toBe("inside");
  });

  it("validates coordinates before passing poi or route points to the native map", () => {
    expect(isFiniteLngLat({ lng: 115.0612, lat: 30.2301 })).toBe(true);
    expect(isFiniteLngLat({ lng: Number.NaN, lat: 30.2301 })).toBe(false);
    expect(toNativeMapPoint({ lng: 115.0612, lat: 30.2301 })).toEqual({
      longitude: 115.0612,
      latitude: 30.2301,
    });
    expect(toNativeMapPoint({ lng: Number.NaN, lat: 30.2301 })).toBeNull();

    const clamped = clampLngLatToBounds(
      { lng: 115.2, lat: 30.5 },
      HBNU_CAMPUS.limit_bounds,
    );
    expect(clamped.lng).toBeLessThanOrEqual(HBNU_CAMPUS.limit_bounds.north_east.lng);
    expect(clamped.lat).toBeLessThanOrEqual(HBNU_CAMPUS.limit_bounds.north_east.lat);

    expect(indexPageSource).toContain("toNativeMapPoint");
    expect(indexPageSource).toContain("clampLngLatToBounds");
  });

  it("consumes pending task-detail navigation on the map tab", () => {
    expect(indexPageSource).toContain("MAP_PENDING_NAVIGATION_STORAGE_KEY");
    expect(indexPageSource).toContain("consumePendingNavigation");
    expect(indexPageSource).toContain("loadPendingNavigationSummary");
    expect(indexPageSource).toContain("await loadPointSummary(pending.map_point_id)");
    expect(indexPageSource).not.toContain("buildPendingNavigationSummary");
    expect(indexPageSource).not.toContain("focusPendingMapPoint");
    expect(indexPageSource).not.toContain("summaryToFocusedMarker");
    expect(indexPageSource).not.toContain("mapPointMarkers.value = [marker]");
    expect(indexPageSource).not.toContain("void handleSummaryAction");
  });

  it("does not retain amap web sdk or rest poi search paths in the mini program page", () => {
    expect(indexPageSource).not.toContain("searchCampusExternalPoisByRest");
    expect(indexPageSource).not.toContain("searchCampusExternalPoisByAmapJs");
    expect(indexPageSource).not.toContain("https://restapi.amap.com/v3/place/text");
    expect(indexPageSource).not.toContain("parseAmapRestLocation");
  });

  it("renders searched backend results as temporary native map markers", () => {
    expect(indexPageSource).toContain("mapSearchShellItemToMarker");
    expect(indexPageSource).toContain("search_result");
    expect(indexPageSource).not.toContain("selectedExternalTarget");
    expect(indexPageSource).not.toContain("search_external");
  });

  it("keeps a readable label for each map filter", () => {
    expect(getMapFilterLabel(ALL_MAP_FILTER_KEY)).toBe("全部标记");
    expect(getMapFilterLabel("none")).toBe("无标记");
    expect(getMapFilterLabel("cat")).toBe("猫咪点");
    expect(getMapFilterLabel("unknown")).toBe("全部标记");
  });

  it("adds all marker filter when two or more marker categories exist", () => {
    const twoOptions = normalizeMapFilterOptions([
      { key: "feeding_pending", label: "未完成任务", point_types: ["task"] },
      { key: "feeding_completed", label: "完成任务", point_types: ["task"] },
    ]);

    expect(twoOptions.map((option) => option.key)).toEqual([
      NO_MAP_FILTER_KEY,
      ALL_MAP_FILTER_KEY,
      "feeding_pending",
      "feeding_completed",
    ]);

    const threeOptions = normalizeMapFilterOptions([
      { key: "task", label: "任务", point_types: ["task"] },
      { key: "cat", label: "猫咪点", point_types: ["cat"] },
      { key: "supply", label: "物资点", point_types: ["supply"] },
    ]);

    expect(threeOptions.map((option) => option.key)).toEqual([
      NO_MAP_FILTER_KEY,
      ALL_MAP_FILTER_KEY,
      "task",
      "cat",
      "supply",
    ]);
  });

  it("searches shell items by title, subtitle, and description", () => {
    expect(searchMapShellItems(shellItems, "北门", ALL_MAP_FILTER_KEY)).toHaveLength(
      1,
    );
    expect(searchMapShellItems(shellItems, "猫粮", ALL_MAP_FILTER_KEY)).toEqual([
      shellItems[2],
    ]);
    expect(searchMapShellItems(shellItems, "教学楼", "cat")).toEqual([
      shellItems[1],
    ]);
    expect(searchMapShellItems(shellItems, "教学楼", "supply")).toEqual([]);
  });

  it("expands the campus limit bounds beyond the visible school boundary", () => {
    const expandedBounds = expandLngLatBounds(HBNU_CAMPUS.core_bounds, 0.35);

    expect(expandedBounds.south_west.lng).toBeLessThan(
      HBNU_CAMPUS.core_bounds.south_west.lng,
    );
    expect(expandedBounds.south_west.lat).toBeLessThan(
      HBNU_CAMPUS.core_bounds.south_west.lat,
    );
    expect(expandedBounds.north_east.lng).toBeGreaterThan(
      HBNU_CAMPUS.core_bounds.north_east.lng,
    );
    expect(expandedBounds.north_east.lat).toBeGreaterThan(
      HBNU_CAMPUS.core_bounds.north_east.lat,
    );
  });

  it("uses backend campus bounds and smoothly restores drags outside the campus limit", () => {
    expect(mapApiSource).toContain("core_bounds");
    expect(mapApiSource).toContain("limit_bounds");
    expect(mapPageSource).toContain("isFiniteLngLatBounds");
    expect(indexPageSource).toContain("data.campus.core_bounds");
    expect(indexPageSource).toContain("data.campus.limit_bounds");
    expect(indexPageSource).toContain("centerMapToPoint(nextCenter, { smooth: true })");
  });

  it("maps backend task markers to frontend shell items", () => {
    const item = mapMarkerToShellItem({
      point_id: "point-1",
      point_type: "task",
      point_scope: "temporary",
      business_type: "emergency",
      business_id: "task-1",
      name: "北门草丛紧急救助任务",
      subtitle: "发现受伤流浪猫",
      lng: 115.0609,
      lat: 30.233,
      area_id: null,
      area_name: "北门",
      marker_key: "task_emergency",
      icon_key: "task_emergency",
      display_level: 100,
      visibility: "public",
      status: "active",
      cover_photo_url: null,
      preview_enabled: true,
      preview_min_zoom: 16,
      label_min_zoom: 16,
      distance_meters: 120,
      extra: {},
    });

    expect(item).toMatchObject({
      id: "point-1",
      map_point_id: "point-1",
      type: "emergency_task",
      title: "北门草丛紧急救助任务",
      tag_label: "紧急任务",
      status_label: "进行中",
    });
  });

  it("maps backend search and bottom content items to the same list shape", () => {
    expect(
      mapSearchResultToShellItem({
        result_type: "external_poi",
        map_point_id: null,
        business_id: "tencent:7554185223751732838",
        point_type: "landmark",
        business_type: "tencent_poi",
        title: "湖北师范大学教育大楼",
        subtitle: "教育学校:大学",
        description: "湖北省黄石市黄石港区",
        icon_key: "landmark",
        cover_photo_url: null,
        lng: 115.0617,
        lat: 30.2311,
        distance_meters: null,
        status_label: "地图点位",
        highlight_text: "教学楼",
        sort_score: 50,
      }),
    ).toMatchObject({
      id: "tencent:7554185223751732838",
      type: "landmark",
      map_point_id: undefined,
      distance_meters: null,
    });

    expect(
      mapBottomContentItemToShellItem({
        id: "task-point",
        map_point_id: "task-point",
        type: "daily_task",
        title: "食堂后方投喂清洁",
        subtitle: "日常投喂与清理",
        description: "补粮并检查水碗。",
        distance_meters: null,
        status_label: "日常任务",
        active_execution: {
          execution_date_id: "execution-1",
          execute_date: "2026-07-15",
          display_status: "completed",
          display_status_label: "已完成",
        },
        tag_label: "日常任务",
        cover_photo_url: null,
      }),
    ).toMatchObject({
      map_point_id: "task-point",
      type: "daily_task",
      status_label: "已完成",
      status_key: "completed",
      active_execution: {
        execution_date_id: "execution-1",
        execute_date: "2026-07-15",
      },
    });
  });

  it("carries active child execution state from task markers into map task cards", () => {
    const item = mapMarkerToShellItem({
      point_id: "point-1",
      point_type: "task",
      point_scope: "campus",
      business_type: "feeding",
      business_id: "task-1",
      name: "猫哥喂食任务",
      subtitle: "屋檐下",
      lng: 115.0617,
      lat: 30.2311,
      area_id: null,
      area_name: null,
      marker_key: "feeding",
      icon_key: "task_feeding",
      display_level: 80,
      visibility: "public",
      status: "active",
      cover_photo_url: null,
      preview_enabled: true,
      preview_min_zoom: 18,
      label_min_zoom: 16,
      distance_meters: null,
      extra: {
        task_status: "in_progress",
        task_status_label: "进行中",
        feeding_status: "pending",
        active_execution: {
          execution_date_id: "execution-1",
          execute_date: "2026-07-15",
          display_status: "completed",
          display_status_label: "已完成",
        },
      },
    });

    expect(item).toMatchObject({
      id: "point-1",
      type: "daily_task",
      status_key: "completed",
      active_execution: {
        execution_date_id: "execution-1",
        execute_date: "2026-07-15",
        display_status: "completed",
      },
    });
    expect(mapPageSource).toContain("active_execution");
    expect(indexPageSource).toContain("appendExecutionDateQuery");
    expect(indexPageSource).toContain("execution_date_id");
  });

  it("uses selected map markers as drawer list content for active marker filters", () => {
    expect(indexPageSource).toContain("if (activeFilter.value && !isSearchMode.value)");
    expect(indexPageSource).toContain(
      "bottomContentItems.value = mapPointMarkers.value.map(mapMarkerToShellItem)",
    );
    expect(indexPageSource).toContain("return activeFilterLabel.value");
  });

  it("builds backend point filters from frontend filter keys", () => {
    expect(getMapPointQueryByFilter("emergency_task")).toEqual({
      point_types: "task",
      business_types: "emergency",
    });
    expect(getMapPointQueryByFilter("daily_task")).toEqual({
      point_types: "task",
      business_types: "daily,feeding",
    });
    expect(getMapPointQueryByFilter("feeding_pending")).toEqual({
      point_types: "task",
      business_types: "feeding",
      filter_key: "feeding_pending",
    });
    expect(getMapPointQueryByFilter("feeding_completed")).toEqual({
      point_types: "task",
      business_types: "feeding",
      filter_key: "feeding_completed",
    });
    expect(getMapPointQueryByFilter("cat")).toEqual({ point_types: "cat" });
    expect(getMapPointQueryByFilter("all")).toEqual({});
  });
});
