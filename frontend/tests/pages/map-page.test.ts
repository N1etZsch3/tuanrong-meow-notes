import { describe, expect, it } from "vitest";

import drawerWxsSource from "../../src/pages/index/drawer.wxs?raw";
import filterMenuWxsSource from "../../src/pages/index/filter-menu.wxs?raw";
import indexPageSource from "../../src/pages/index/index.vue?raw";
import mapPageSource from "../../src/pages/index/map-page.ts?raw";
import {
  ALL_MAP_FILTER_KEY,
  HBNU_CAMPUS,
  expandLngLatBounds,
  filterCampusExternalPoiResults,
  getMapPointQueryByFilter,
  getMarkerDisplayMode,
  getMapFilterLabel,
  mapBottomContentItemToShellItem,
  mapMarkerToShellItem,
  mapSearchResultToShellItem,
  searchMapShellItems,
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
    expect(indexPageSource).toContain("uni.getLocation");
    expect(indexPageSource).toContain("uni.openLocation");
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

  it("selects marker display modes by zoom and visible marker density", () => {
    expect(
      getMarkerDisplayMode({
        zoom: 18.8,
        visibleMarkerCount: 16,
        previewEnabled: true,
        labelMinZoom: 16,
        previewMinZoom: 15,
      }),
    ).toBe("icon");
    expect(
      getMarkerDisplayMode({
        zoom: 16.2,
        visibleMarkerCount: 5,
        previewEnabled: true,
        labelMinZoom: 16,
        previewMinZoom: 15,
      }),
    ).toBe("label");
    expect(
      getMarkerDisplayMode({
        zoom: 14.8,
        visibleMarkerCount: 1,
        previewEnabled: true,
        labelMinZoom: 16,
        previewMinZoom: 15,
      }),
    ).toBe("preview");
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

  it("keeps navigation in the mini program map APIs", () => {
    expect(indexPageSource).not.toContain("window.open");
    expect(indexPageSource).toContain("renderNativeRoute");
    expect(indexPageSource).toContain("renderInAppRoute");
    expect(indexPageSource).toContain("uni.openLocation");
    expect(indexPageSource).toContain(':polyline="nativeMapPolylines"');
    expect(indexPageSource).not.toContain("renderAmapWalkingRoute");
  });

  it("lowers and compacts the map title, map viewport, filter, and content drawer", () => {
    expect(indexPageSource).toContain("top: var(--catmap-page-title-top, 92rpx)");
    expect(indexPageSource).toContain("font-size: var(--catmap-page-title-font-size, 52rpx)");
    expect(indexPageSource).toContain("font-size: var(--catmap-page-title-subtitle-size, 24rpx)");
    expect(indexPageSource).toContain("top: 218rpx");
    expect(indexPageSource).toContain("bottom: 664rpx");
    expect(indexPageSource).toContain("top: 300rpx");
    expect(indexPageSource).toContain("height: 460rpx");
  });

  it("renders marker svg icons and a redesigned arrow in the filter menu", () => {
    expect(indexPageSource).toContain("MAP_FILTER_ICON_SRC");
    expect(indexPageSource).toContain("filter-option-icon");
    expect(indexPageSource).toContain("filterArrowIcon");
    expect(indexPageSource).toContain("filter-arrow-icon");
    expect(indexPageSource).toContain("../../../素材/svg/地图点/全部.svg");
    expect(indexPageSource).toContain("../../../素材/svg/地图点/紧急任务.svg");
    expect(indexPageSource).toContain("../../../素材/svg/地图点/日常任务.svg");
    expect(indexPageSource).toContain("../../../素材/svg/地图点/猫咪点.svg");
    expect(indexPageSource).toContain("../../../素材/svg/地图点/物资点.svg");
    expect(indexPageSource).toContain("../../../素材/svg/地图点/地标.svg");
    expect(indexPageSource).toContain("../../../素材/svg/地图点/箭头.svg");
    expect(indexPageSource).toContain("../../../素材/svg/地图点/完成任务.svg");
    expect(indexPageSource).toContain("../../../素材/svg/地图点/失败任务.svg");
    expect(indexPageSource).not.toContain("filter-chevron-mark");
    expect(indexPageSource).not.toContain("⌄");
  });

  it("uses completion and failure task svgs for feeding task map markers", () => {
    expect(indexPageSource).toContain("getFeedingMarkerIcon");
    expect(indexPageSource).toContain("marker.business_type === \"feeding\"");
    expect(indexPageSource).toContain("marker.extra.feeding_status === \"completed\"");
  });

  it("keeps the filter menu in a native-map-safe cover layer", () => {
    expect(indexPageSource).toContain('<cover-view class="map-filter-layer"');
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

  it("animates the filter menu width and arrow direction with WXS", () => {
    expect(filterMenuWxsSource).toContain("filter-chip");
    expect(filterMenuWxsSource).toContain("filter-menu");
    expect(filterMenuWxsSource).toContain("filter-arrow-icon");
    expect(filterMenuWxsSource).toContain("rotate(180deg)");
    expect(filterMenuWxsSource).toContain("rotate(0deg)");
    expect(filterMenuWxsSource).toContain("width");
  });

  it("navigates summary card view-detail actions to the task detail page", () => {
    expect(indexPageSource).toContain('action.key === "view_detail"');
    expect(indexPageSource).toContain("uni.navigateTo({ url: action.path })");
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
        result_type: "supply",
        map_point_id: "supply-point",
        business_id: "supply-1",
        point_type: "supply",
        business_type: "food",
        title: "猫协物资点 #1",
        subtitle: "体育馆旁物资补给",
        description: "猫粮、航空箱、诱捕笼备用点。",
        icon_key: "supply_food",
        cover_photo_url: null,
        lng: 115.0642,
        lat: 30.2287,
        distance_meters: null,
        status_label: "物资点",
        highlight_text: "猫粮",
        sort_score: 50,
      }),
    ).toMatchObject({
      id: "supply-point",
      type: "supply",
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
        tag_label: "日常任务",
      }),
    ).toMatchObject({
      map_point_id: "task-point",
      type: "daily_task",
    });
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
