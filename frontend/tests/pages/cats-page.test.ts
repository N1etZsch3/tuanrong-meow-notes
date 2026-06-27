import { describe, expect, it } from "vitest";

import catsPageSource from "../../src/pages/cats/index.vue?raw";
import {
  buildCatListQuery,
  formatCatSeenTime,
  getCatTagTone,
  normalizeCatStats,
} from "@/pages/cats/cats-page";

describe("cats page behavior", () => {
  it("loads stats filters and cat list from backend APIs", () => {
    expect(catsPageSource).toContain("getCatStats");
    expect(catsPageSource).toContain("getCatFilterOptions");
    expect(catsPageSource).toContain("getCats");
    expect(catsPageSource).toContain("userStore.ensureFreshAccessToken()");
    expect(catsPageSource).not.toContain('state="under_development"');
  });

  it("keeps expected page states and bottom tab", () => {
    expect(catsPageSource).toContain('active-key="cats"');
    expect(catsPageSource).toContain("isLoading");
    expect(catsPageSource).toContain("errorMessage");
    expect(catsPageSource).toContain("empty-list");
    expect(catsPageSource).toContain("markImageFailed");
  });

  it("builds cat list query from page controls", () => {
    expect(
      buildCatListQuery({
        keyword: " 小橘 ",
        filter_key: "health_status",
        filter_value: "watching",
        sort: "last_seen_desc",
        page: 1,
        page_size: 20,
      }),
    ).toEqual({
      keyword: "小橘",
      filter_key: "health_status",
      filter_value: "watching",
      sort: "last_seen_desc",
      page: 1,
      page_size: 20,
    });

    expect(
      buildCatListQuery({
        keyword: "  ",
        filter_key: "health_status",
        filter_value: "",
        sort: "last_seen_desc",
        page: 1,
        page_size: 20,
      }),
    ).toEqual({
      sort: "last_seen_desc",
      page: 1,
      page_size: 20,
    });
  });

  it("formats recent seen time for list cards", () => {
    const now = new Date("2026-06-27T12:00:00+08:00");

    expect(formatCatSeenTime("2026-06-27T09:20:00+08:00", now)).toBe("今天 09:20");
    expect(formatCatSeenTime("2026-06-26T17:30:00+08:00", now)).toBe("昨天 17:30");
    expect(formatCatSeenTime("2026-06-22T16:10:00+08:00", now)).toBe("5天前");
    expect(formatCatSeenTime(null, now)).toBe("未知");
  });

  it("maps important tags to visual tones", () => {
    expect(getCatTagTone("健康")).toBe("green");
    expect(getCatTagTone("已绝育")).toBe("blue");
    expect(getCatTagTone("待观察")).toBe("orange");
    expect(getCatTagTone("未绝育")).toBe("red");
    expect(getCatTagTone("亲人")).toBe("purple");
  });

  it("normalizes missing stats to zeroes", () => {
    expect(normalizeCatStats(null)).toMatchObject({
      total_cats: 0,
      active_cats: 0,
      neuter_rate: 0,
    });
  });
});
