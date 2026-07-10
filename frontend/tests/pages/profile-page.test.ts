import { describe, expect, it } from "vitest";

import pagesJson from "../../src/pages.json?raw";
import profileDetailSource from "../../src/pages/profile/detail.vue?raw";
import profileIndexSource from "../../src/pages/profile/index.vue?raw";
import profileRecordsSource from "../../src/pages/profile/records.vue?raw";
import profileResetPasswordSource from "../../src/pages/profile/reset-password.vue?raw";
import profileSettingsSource from "../../src/pages/profile/settings.vue?raw";
import {
  PROFILE_RECORD_TYPES,
  PROFILE_STAT_ENTRIES,
  getRoleLabel,
  getRolePillClass,
} from "../../src/pages/profile/profile-page";

function extractCssRule(source: string, selector: string): string {
  const start = source.lastIndexOf(`${selector} {`);
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

describe("profile center pages", () => {
  it("registers personal center detail and record routes", () => {
    expect(pagesJson).toContain("pages/profile/detail");
    expect(pagesJson).toContain("pages/profile/records");
  });

  it("renders the real dashboard instead of the under-development placeholder", () => {
    expect(profileIndexSource).toContain("getMeDashboard");
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
    const titleRule = extractCssRule(profileIndexSource, ".hero-title");
    const subtitleRule = extractCssRule(profileIndexSource, ".hero-subtitle");
    const iconRule = extractCssRule(profileIndexSource, ".hero-cat");

    expect(profileIndexSource).toContain("hero-title-row");
    expect(profileIndexSource).toContain('<image class="hero-cat"');
    expect(profileIndexSource).toContain("var(--catmap-page-title-top, 92rpx)");
    expect(titleRule).toContain("color: #111827");
    expect(titleRule).toContain("font-size: var(--catmap-page-title-font-size, 52rpx)");
    expect(titleRule).toContain("font-weight: 900");
    expect(iconRule).toContain("width: var(--catmap-page-title-icon-size, 48rpx)");
    expect(iconRule).toContain("height: var(--catmap-page-title-icon-size, 48rpx)");
    expect(subtitleRule).toContain("color: #6b7280");
    expect(subtitleRule).toContain("font-size: var(--catmap-page-title-subtitle-size, 24rpx)");
    expect(subtitleRule).toContain("font-weight: 700");
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


  it("uses the provided profile svg assets for dashboard and menu icons", () => {
    expect(profileIndexSource).toContain("素材/svg/用户页/任务.svg");
    expect(profileIndexSource).toContain("素材/svg/用户页/进行中.svg");
    expect(profileIndexSource).toContain("素材/svg/用户页/设置.svg");
    expect(profileIndexSource).toContain("素材/svg/用户页/通知.svg");
    expect(profileIndexSource).toContain("素材/svg/用户页/帮助和反馈.svg");
    expect(profileIndexSource).toContain("profileStatIconMap");
    expect(profileIndexSource).toContain("profileMenuIconMap");
    expect(profileIndexSource).toContain('class="stat-icon-image"');
    expect(profileIndexSource).toContain('class="menu-icon-image"');
    expect(profileIndexSource).not.toContain("{{ item.icon }}");
  });

  it("keeps profile detail editable with the profile update api", () => {
    expect(profileDetailSource).toContain("getMyProfile");
    expect(profileDetailSource).toContain("updateMyProfile");
    expect(profileDetailSource).toContain("联系方式");
  });

  it("routes account settings to a dedicated settings page with logout and reset password actions", () => {
    expect(pagesJson).toContain("pages/profile/settings");
    expect(pagesJson).toContain("pages/profile/reset-password");
    expect(profileIndexSource).toContain("/pages/profile/settings");
    expect(profileIndexSource).not.toContain('class="logout-button"');
    expect(profileSettingsSource).toContain("/pages/profile/reset-password");
    expect(profileSettingsSource).toContain("logoutFromServer");
    expect(profileResetPasswordSource).toContain("changeCurrentPassword");
    expect(profileResetPasswordSource).toContain("重设密码");
  });

  it("uses compact grouped account settings with a confirmed WeChat self-unbind action", () => {
    const settingsRowRule = extractCssRule(profileSettingsSource, ".settings-row");
    const rowTitleRule = extractCssRule(profileSettingsSource, ".row-title");
    const unbindCall = profileSettingsSource.indexOf(
      "await userStore.unbindCurrentWechat()",
    );
    const loginRedirect = profileSettingsSource.indexOf(
      "uni.reLaunch({ url: LOGIN_ROUTE })",
      unbindCall,
    );

    expect(profileSettingsSource).toContain("账号与安全");
    expect(profileSettingsSource).toContain("重设密码");
    expect(profileSettingsSource).toContain("微信解绑");
    expect(profileSettingsSource).toContain("退出登录");
    expect(profileSettingsSource).toContain("解绑后将立即退出登录");
    expect(profileSettingsSource).toContain("userStore.unbindCurrentWechat");
    expect(profileSettingsSource).not.toContain('class="row-desc"');
    expect(profileSettingsSource).toContain("素材/svg/登录页/修改密码.svg");
    expect(profileSettingsSource).toContain("素材/svg/用户页/设置.svg");
    expect(settingsRowRule).toContain("line-height: 1");
    expect(rowTitleRule).toContain("line-height: 1");
    expect(unbindCall).toBeGreaterThan(-1);
    expect(loginRedirect).toBeGreaterThan(unbindCall);
  });

  it("uses role-specific labels and badge classes", () => {
    expect(getRoleLabel("admin")).toBe("猫协管理员");
    expect(getRoleLabel("member")).toBe("猫协成员");
    expect(getRoleLabel("summer_volunteer")).toBe("暑期志愿者");
    expect(getRolePillClass("admin")).toBe("role-pill--admin");
    expect(getRolePillClass("member")).toBe("role-pill--member");
    expect(getRolePillClass("summer_volunteer")).toBe("role-pill--volunteer");
    expect(profileIndexSource).toContain(":class=\"rolePillClass\"");
  });

  it("uses shared map-title metrics on profile secondary pages", () => {
    for (const source of [
      profileDetailSource,
      profileRecordsSource,
      profileSettingsSource,
      profileResetPasswordSource,
    ]) {
      expect(source).toContain("var(--catmap-page-title-top, 92rpx)");
      expect(source).toContain("var(--catmap-page-title-font-size, 52rpx)");
    }
  });

  it("loads record pages through the corresponding me endpoints", () => {
    expect(profileRecordsSource).toContain("getMyTasks");
    expect(profileRecordsSource).toContain("getMyCheckins");
    expect(profileRecordsSource).toContain("getMyObservations");
    expect(profileRecordsSource).toContain("getFavoriteCats");
  });

  it("uses completed child task checkins for cumulative and monthly task records", () => {
    expect(profileRecordsSource).toContain("loadCompletedTaskRecords");
    expect(profileRecordsSource).toContain(
      'recordType.value === "total_tasks" || recordType.value === "monthly_completed"',
    );
    expect(profileRecordsSource).toContain("records.value = await getMyCheckins(accessToken");
    expect(profileRecordsSource).toContain('class="record-card"');
    expect(profileRecordsSource).toContain("record.execute_date");
  });
});
