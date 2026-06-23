import { describe, expect, it } from "vitest";

import {
  ALL_MAP_FILTER_KEY,
  DEFAULT_MAP_DRAWER_STATE,
  HBNU_CAMPUS,
  expandLngLatBounds,
  getMapDrawerStateAfterDrag,
  getMapFilterLabel,
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
});
