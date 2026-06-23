import { describe, expect, it } from "vitest";

import {
  APP_TAB_ITEMS,
  getActiveTabKey,
  getTabTarget,
  shouldNavigateTab,
} from "@/components/app-tab-bar";

describe("app tab bar navigation", () => {
  it("keeps the four primary tabs in product order", () => {
    expect(APP_TAB_ITEMS.map((item) => item.label)).toEqual([
      "地图",
      "猫咪库",
      "任务",
      "我的",
    ]);
    expect(APP_TAB_ITEMS.map((item) => item.route)).toEqual([
      "/pages/index/index",
      "/pages/cats/index",
      "/pages/tasks/index",
      "/pages/profile/index",
    ]);
  });

  it("matches active tab by exact page route", () => {
    expect(getActiveTabKey("/pages/index/index")).toBe("map");
    expect(getActiveTabKey("pages/cats/index")).toBe("cats");
    expect(getActiveTabKey("/pages/tasks/index?status=pending")).toBe("tasks");
    expect(getActiveTabKey("/pages/profile/index")).toBe("profile");
  });

  it("falls back to map when route is outside the primary tabs", () => {
    expect(getActiveTabKey("/pages/login/index")).toBe("map");
    expect(getActiveTabKey("")).toBe("map");
  });

  it("returns the selected tab route and avoids duplicate navigation", () => {
    expect(getTabTarget("tasks")).toBe("/pages/tasks/index");
    expect(shouldNavigateTab("tasks", "/pages/index/index")).toBe(true);
    expect(shouldNavigateTab("tasks", "/pages/tasks/index")).toBe(false);
  });

  it("keeps the map icon in its original colors when active", () => {
    const mapItem = APP_TAB_ITEMS.find((item) => item.key === "map");
    const otherItems = APP_TAB_ITEMS.filter((item) => item.key !== "map");

    expect(mapItem?.preserveActiveIconColor).toBe(true);
    expect(otherItems.every((item) => !item.preserveActiveIconColor)).toBe(
      true,
    );
  });
});
