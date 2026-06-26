import { describe, expect, it } from "vitest";

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

  it("resizes the amap instance after WXS drawer layout changes", () => {
    expect(indexPageSource).toContain("scheduleMapResizeAfterDrawerChange");
    expect(indexPageSource).toContain("amapInstance.resize");
  });

  it("keeps navigation inside the app instead of opening external amap urls", () => {
    expect(indexPageSource).not.toContain("window.open");
    expect(indexPageSource).toContain("renderAmapWalkingRoute");
    expect(indexPageSource).toContain("renderNativeRoute");
    expect(indexPageSource).toContain("renderInAppRoute");
    expect(indexPageSource).toContain(':polyline="nativeMapPolylines"');
  });

  it("renders the filter menu with the updated named map point svg assets", () => {
    expect(indexPageSource).toContain("MAP_FILTER_ICON_SRC");
    expect(indexPageSource).toContain("全部.svg");
    expect(indexPageSource).toContain("紧急任务.svg");
    expect(indexPageSource).toContain("日常任务.svg");
    expect(indexPageSource).toContain("猫咪点.svg");
    expect(indexPageSource).toContain("物资点.svg");
    expect(indexPageSource).toContain("地标.svg");
    expect(indexPageSource).toContain("筛选.svg");
    expect(indexPageSource).toContain("箭头.svg");
    expect(indexPageSource).toContain("filter-option-icon");
  });

  it("keeps the filter overlay outside the native map gesture layer", () => {
    expect(indexPageSource).toContain("map-filter-layer");
    expect(indexPageSource).toContain("filter-panel-hit-layer");
    expect(indexPageSource.indexOf('class="map-filter-layer"')).toBeGreaterThan(
      indexPageSource.indexOf('class="map-viewport"'),
    );
    expect(indexPageSource.indexOf('class="map-filter-layer"')).toBeLessThan(
      indexPageSource.indexOf('class="content-drawer"'),
    );
  });

  it("animates the filter menu and arrow through WXS instead of css-only state", () => {
    expect(indexPageSource).toContain('module="filterMenu"');
    expect(indexPageSource).toContain('src="./filter-menu.wxs"');
    expect(indexPageSource).toContain("@tap=\"filterMenu.toggle\"");
    expect(indexPageSource).toContain("filter-arrow-icon");
    expect(indexPageSource).not.toContain("filter-chevron-mark");
    expect(indexPageSource).not.toContain("⌄");
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

  it("keeps a non-web amap rest fallback for mini program poi search", () => {
    expect(indexPageSource).toContain("searchCampusExternalPoisByRest");
    expect(indexPageSource).toContain("https://restapi.amap.com/v3/place/text");
    expect(indexPageSource).toContain("parseAmapRestLocation");
  });

  it("renders searched internal and external results as temporary map markers", () => {
    expect(indexPageSource).toContain("mapSearchShellItemToMarker");
    expect(indexPageSource).toContain("createSearchPointSummary");
    expect(indexPageSource).toContain("selectedExternalTarget");
    expect(indexPageSource).toContain("search_external");
  });

  it("keeps a readable label for each map filter", () => {
    expect(getMapFilterLabel(ALL_MAP_FILTER_KEY)).toBe("全部标记");
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
      business_types: "daily",
    });
    expect(getMapPointQueryByFilter("cat")).toEqual({ point_types: "cat" });
    expect(getMapPointQueryByFilter("all")).toEqual({});
  });
});
