import { describe, expect, it } from "vitest";

import pagesJson from "../../src/pages.json?raw";
import profileDetailSource from "../../src/pages/profile/detail.vue?raw";
import profileIndexSource from "../../src/pages/profile/index.vue?raw";
import profileRecordsSource from "../../src/pages/profile/records.vue?raw";
import { PROFILE_RECORD_TYPES, PROFILE_STAT_ENTRIES } from "../../src/pages/profile/profile-page";

describe("profile center pages", () => {
  it("registers personal center detail and record routes", () => {
    expect(pagesJson).toContain("pages/profile/detail");
    expect(pagesJson).toContain("pages/profile/records");
  });

  it("renders the real dashboard instead of the under-development placeholder", () => {
    expect(profileIndexSource).toContain("getMeDashboard");
    expect(profileIndexSource).toContain("logoutFromServer");
    expect(profileIndexSource).toContain("AppTabBar active-key=\"profile\"");
    expect(profileIndexSource).toContain("scroll-view");
    expect(profileIndexSource).not.toContain("个人中心建设中");
  });

  it("avoids duplicate dashboard requests when switching tabs quickly", () => {
    expect(profileIndexSource).toContain("PROFILE_DASHBOARD_CACHE_MS");
    expect(profileIndexSource).toContain("lastDashboardLoadedAt");
    expect(profileIndexSource).toContain("if (isLoading.value)");
  });

  it("keeps the profile title aligned with the shared page title treatment", () => {
    expect(profileIndexSource).toContain("hero-title-row");
    expect(profileIndexSource).toContain('<image class="hero-cat"');
    expect(profileIndexSource).toContain("var(--catmap-page-title-top, 92rpx)");
    expect(profileIndexSource).toContain("var(--catmap-page-title-font-size, 52rpx)");
    expect(profileIndexSource).toContain("var(--catmap-page-title-icon-size, 48rpx)");
    expect(profileIndexSource).toContain("var(--catmap-page-title-subtitle-size, 24rpx)");
    expect(profileIndexSource).toMatch(/\.hero\s*{[^}]*align-items: flex-start;[^}]*}/s);
    expect(profileIndexSource).not.toMatch(/\.hero\s*{[^}]*justify-content: space-between/s);
  });

  it("defines clickable stats and favorite cat record entries", () => {
    expect(PROFILE_STAT_ENTRIES.map((item) => item.label)).toEqual([
      "累计任务",
      "本月完成",
      "进行中",
      "观察记录",
    ]);
    expect(PROFILE_RECORD_TYPES.favorite_cats.title).toBe("收藏猫咪");
  });

  it("keeps profile detail editable with the profile update api", () => {
    expect(profileDetailSource).toContain("getMyProfile");
    expect(profileDetailSource).toContain("updateMyProfile");
    expect(profileDetailSource).toContain("联系方式");
  });

  it("loads record pages through the corresponding me endpoints", () => {
    expect(profileRecordsSource).toContain("getMyTasks");
    expect(profileRecordsSource).toContain("getMyCheckins");
    expect(profileRecordsSource).toContain("getMyObservations");
    expect(profileRecordsSource).toContain("getFavoriteCats");
  });
});
