import { describe, expect, it } from "vitest";

import {
  ALL_MAP_FILTER_KEY,
  DEFAULT_MAP_DRAWER_STATE,
  HBNU_CAMPUS,
  expandLngLatBounds,
  getMapPointQueryByFilter,
  getMapDrawerStateAfterDrag,
  getMapFilterLabel,
  mapBottomContentItemToShellItem,
  mapMarkerToShellItem,
  mapSearchResultToShellItem,
  searchMapShellItems,
  type MapDrawerState,
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
  it("starts with the dynamic content drawer expanded", () => {
    expect(DEFAULT_MAP_DRAWER_STATE).toBe("expanded");
  });

  it("collapses and expands the drawer by vertical drag distance", () => {
    const expanded: MapDrawerState = "expanded";
    const collapsed: MapDrawerState = "collapsed";

    expect(getMapDrawerStateAfterDrag(expanded, 86)).toBe("collapsed");
    expect(getMapDrawerStateAfterDrag(collapsed, -86)).toBe("expanded");
    expect(getMapDrawerStateAfterDrag(expanded, 18)).toBe("expanded");
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
