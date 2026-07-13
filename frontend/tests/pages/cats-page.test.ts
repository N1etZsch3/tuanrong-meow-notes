import { describe, expect, it } from "vitest";

import catsPageSource from "../../src/pages/cats/index.vue?raw";
import {
  buildCatStatsDisplayItems,
  buildCatListQuery,
  formatCatSeenTime,
  getCatTagTone,
  normalizeCatStats,
} from "@/pages/cats/cats-page";

function extractCssRule(source: string, selector: string): string {
  const start = source.indexOf(`${selector} {`);
  expect(start).toBeGreaterThanOrEqual(0);
  const bodyStart = source.indexOf("{", start);
  expect(bodyStart).toBeGreaterThan(start);

  let depth = 0;
  for (let index = bodyStart; index < source.length; index += 1) {
    const char = source[index];
    if (char === "{") {
      depth += 1;
    } else if (char === "}") {
      depth -= 1;
      if (depth === 0) {
        return source.slice(start, index + 1);
      }
    }
  }

  return source.slice(start);
}

describe("cats page behavior", () => {
  it("loads stats filters and cat list from backend APIs", () => {
    expect(catsPageSource).toContain("getCatStats");
    expect(catsPageSource).toContain("getCatFilterOptions");
    expect(catsPageSource).toContain("getCats");
    expect(catsPageSource).toContain("userStore.ensureFreshAccessToken()");
    expect(catsPageSource).not.toContain('state="under_development"');
  });

  it("keeps expected page states as a bookshelf sub-page with a back control", () => {
    expect(catsPageSource).not.toContain("AppTabBar");
    expect(catsPageSource).not.toContain('active-key="cats"');
    expect(catsPageSource).toContain('class="back-button"');
    expect(catsPageSource).toContain("uni.navigateBack()");
    expect(catsPageSource).toContain("isLoading");
    expect(catsPageSource).toContain("errorMessage");
    expect(catsPageSource).toContain("empty-list");
    expect(catsPageSource).toContain("markImageFailed");
  });

  it("uses the shared app background and map-page title treatment", () => {
    const titleRule = extractCssRule(catsPageSource, ".page-title-text");
    const iconRule = extractCssRule(catsPageSource, ".page-title-icon");
    const subtitleRule = extractCssRule(catsPageSource, ".page-title-subtitle");

    expect(catsPageSource).toContain("背景.jpg");
    expect(catsPageSource).toContain("萌猫/寿司.svg");
    expect(catsPageSource).toContain("page-title-row");
    expect(catsPageSource).toContain("page-title-icon");
    expect(catsPageSource).toContain("var(--catmap-page-title-top, 92rpx)");
    expect(titleRule).toContain("color: #111827");
    expect(titleRule).toContain("font-size: var(--catmap-page-title-font-size, 52rpx)");
    expect(titleRule).toContain("font-weight: 900");
    expect(titleRule).not.toContain("letter-spacing");
    expect(iconRule).toContain("width: var(--catmap-page-title-icon-size, 48rpx)");
    expect(iconRule).toContain("height: var(--catmap-page-title-icon-size, 48rpx)");
    expect(iconRule).toContain("transform: scale(1.55)");
    expect(subtitleRule).toContain("color: #6b7280");
    expect(subtitleRule).toContain("font-size: var(--catmap-page-title-subtitle-size, 24rpx)");
    expect(subtitleRule).toContain("font-weight: 700");
    expect(catsPageSource).not.toContain("hero-icon-shell");
  });

  it("uses mini-program-safe filter controls and lazy list loading", () => {
    expect(catsPageSource).toContain("地图点/箭头.png");
    expect(catsPageSource).not.toContain("地图点/箭头.svg");
    expect(catsPageSource).toContain("picker-arrow-icon");
    expect(catsPageSource).toContain("activePicker");
    expect(catsPageSource).toContain("clear-filter-icon");
    expect(catsPageSource).toContain("@scrolltolower=\"loadMoreCats\"");
    expect(catsPageSource).toContain("isLoadingMore");
    expect(catsPageSource).toContain("hasMore");
  });

  it("uses the planet svg for the graduated stats icon", () => {
    expect(catsPageSource).toContain("素材/svg/猫咪库/星球.svg");
    expect(catsPageSource).toContain("graduated: graduatedStatsIcon");
    expect(catsPageSource).not.toContain('graduated: ""');
  });

  it("builds the stat card items from the new archive counts", () => {
    expect(
      buildCatStatsDisplayItems({
        total_cats: 100,
        active_cats: 55,
        waiting_adoption_cats: 10,
        adopted_cats: 20,
        deceased_cats: 5,
        watching_cats: 7,
        neutered_cats: 48,
        neuter_rate: 48,
      }),
    ).toEqual([
      { key: "total", label: "在档猫咪", value: 100, tone: "green", has_icon: true },
      { key: "active", label: "正常在校", value: 55, tone: "green", has_icon: true },
      { key: "waiting_adoption", label: "待领养", value: 10, tone: "orange" },
      { key: "adopted", label: "已领养", value: 20, tone: "blue" },
      { key: "graduated", label: "毕业", value: 5, tone: "purple", has_icon: true },
    ]);
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
      adopted_cats: 0,
      deceased_cats: 0,
      neuter_rate: 0,
    });
  });
});
