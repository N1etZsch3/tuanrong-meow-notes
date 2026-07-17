import { describe, expect, it } from "vitest";

import adminCreateUserSource from "../../src/pages/admin/create-user.vue?raw";
import adminIndexSource from "../../src/pages/admin/index.vue?raw";
import adminLandmarkCreateSource from "../../src/pages/admin/landmarks/create.vue?raw";
import adminLandmarkLocationSource from "../../src/pages/admin/landmarks/location.vue?raw";
import landmarkPageSource from "../../src/pages/admin/landmarks/landmark-page.ts?raw";
import adminUsersApiSource from "../../src/api/admin-users.ts?raw";
import adminUsersDetailSource from "../../src/pages/admin/users/detail.vue?raw";
import pagesJson from "../../src/pages.json?raw";
import {
  createMemberEditSnapshot,
  hasUnsavedMemberChanges,
} from "../../src/pages/admin/users/member-edit-guard";

function extractFunctionSource(source: string, functionName: string): string {
  const normalStart = source.indexOf(`function ${functionName}`);
  const asyncStart = source.indexOf(`async function ${functionName}`);
  const start = normalStart >= 0 ? normalStart : asyncStart;
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

function extractCssRule(source: string, selector: string): string {
  const start = source.lastIndexOf(`${selector} {`);
  expect(start).toBeGreaterThanOrEqual(0);
  const end = source.indexOf("}", start);
  expect(end).toBeGreaterThan(start);
  return source.slice(start, end + 1);
}

describe("admin entry pages", () => {
  it("registers admin entry, personnel, create user, and landmark routes", () => {
    expect(pagesJson).toContain("pages/admin/index");
    expect(pagesJson).toContain("pages/admin/users/index");
    expect(pagesJson).toContain("pages/admin/users/detail");
    expect(pagesJson).toContain("pages/admin/create-user");
    expect(pagesJson).toContain("pages/admin/landmarks/create");
    expect(pagesJson).toContain("pages/landmarks/detail");
  });

  it("keeps only personnel management in the admin entry page", () => {
    expect(adminIndexSource).toContain("人员管理");
    expect(adminIndexSource).toContain("/pages/admin/users/index");
    expect(adminIndexSource).not.toContain("发布喂食任务");
    expect(adminIndexSource).not.toContain("/pages/admin/tasks/create");
    expect(adminIndexSource).not.toContain("新建物资点");
    expect(adminIndexSource).not.toContain("/pages/admin/supplies/create");
    expect(adminIndexSource).not.toContain("新建地标点");
    expect(adminIndexSource).not.toContain("/pages/admin/landmarks/create");
  });

  it("keeps the personnel entry card compact with explicit text spacing", () => {
    const actionRule = extractCssRule(adminIndexSource, ".admin-action");
    const copyRule = extractCssRule(adminIndexSource, ".action-copy");
    const titleRule = extractCssRule(adminIndexSource, ".action-title");
    const subtitleRule = extractCssRule(adminIndexSource, ".action-subtitle");

    expect(actionRule).toContain("min-height: 118rpx");
    expect(actionRule).toContain("line-height: 1");
    expect(copyRule).toContain("gap: 6rpx");
    expect(titleRule).toContain("line-height: 1.1");
    expect(subtitleRule).toContain("margin-top: 0");
    expect(subtitleRule).toContain("line-height: 1.25");
  });

  it("creates member accounts through the admin users api", () => {
    expect(adminCreateUserSource).toContain("createAdminUser");
    expect(adminCreateUserSource).toContain("restoreAdminUser");
    expect(adminCreateUserSource).toContain("parseDeletedAccountConflict");
    expect(adminCreateUserSource).toContain("新增成员");
    expect(adminCreateUserSource).toContain("喵喵号");
    expect(adminCreateUserSource).toContain("initial_password");
    expect(adminCreateUserSource).toContain("must_change_password");
  });

  it("uses a designed modal to offer restoring a deleted meow account", () => {
    expect(adminCreateUserSource).toContain('v-if="restoreConflict"');
    expect(adminCreateUserSource).toContain('class="restore-modal-mask"');
    expect(adminCreateUserSource).toContain('class="restore-modal-card"');
    expect(adminCreateUserSource).toContain("这个喵喵号用过啦");
    expect(adminCreateUserSource).toContain("历史昵称");
    expect(adminCreateUserSource).toContain("重新启用原账号");
    expect(adminCreateUserSource).toContain("保留原资料和历史记录");
    expect(adminCreateUserSource).toContain("不会使用本页新填写的昵称、部门和角色");
    expect(adminCreateUserSource).toContain('@tap="confirmRestoreAccount"');
    expect(adminCreateUserSource).toContain('@tap="closeRestoreModal"');
    expect(adminCreateUserSource).toContain('class="restore-modal-confirm"');
    expect(adminCreateUserSource).toContain("backdrop-filter: blur(10rpx)");
    expect(adminCreateUserSource).toContain("animation: restore-modal-in");
  });

  it("offers summer volunteer accounts and the trmx sequence placeholder", () => {
    expect(adminCreateUserSource).toContain('"summer_volunteer"');
    expect(adminCreateUserSource).toContain("trmx+四位序号");
  });

  it("uses shared map-title metrics on admin secondary pages", () => {
    expect(adminIndexSource).toContain("var(--catmap-page-title-top, 92rpx)");
    expect(adminIndexSource).toContain("var(--catmap-page-title-font-size, 52rpx)");
    expect(adminCreateUserSource).toContain("var(--catmap-page-title-top, 92rpx)");
    expect(adminCreateUserSource).toContain("var(--catmap-page-title-font-size, 52rpx)");
  });

  it("searches nearby landmark POIs independently from the landmark point name", () => {
    const nearbySource = extractFunctionSource(adminLandmarkLocationSource, "loadNearbyPoiCandidates");

    expect(nearbySource).toContain("keyword: getLocationPickerPoiKeyword()");
    expect(nearbySource).not.toContain("keyword: selectedLocation.location_name");
  });

  it("uses one-shot location handoff storage instead of keeping landmark drafts", () => {
    const pickerReadSource = extractFunctionSource(adminLandmarkLocationSource, "readLocationTransfer");
    const formReadSource = extractFunctionSource(adminLandmarkCreateSource, "readSelectedLocation");

    expect(pickerReadSource).toContain("uni.removeStorageSync(LANDMARK_LOCATION_STORAGE_KEY)");
    expect(formReadSource).toContain("uni.removeStorageSync(LANDMARK_LOCATION_STORAGE_KEY)");
  });

  it("starts and resets landmark point selection at the current user location", () => {
    const resetSource = extractFunctionSource(adminLandmarkLocationSource, "resetLocation");

    expect(adminLandmarkLocationSource).toContain("getCachedUserLocation");
    expect(adminLandmarkLocationSource).toContain("refreshUserLocation");
    expect(adminLandmarkLocationSource).toContain("void placeAtCurrentUserLocation()");
    expect(adminLandmarkLocationSource).toContain(':show-location="true"');
    expect(resetSource).toContain("void placeAtCurrentUserLocation({ silent: false })");
    expect(resetSource).not.toContain("HBNU_DEFAULT_LANDMARK_LOCATION");
  });

  it("lets admins drag landmark photos to change the cover order", () => {
    expect(adminLandmarkCreateSource).toContain("SortableImageGrid");
    expect(adminLandmarkCreateSource).toContain('@reorder="reorderPhoto"');
    expect(adminLandmarkCreateSource).toContain("moveArrayItem(form.photos");
    expect(landmarkPageSource).toContain("sort_order: index");
    expect(landmarkPageSource).toContain("is_cover: index === 0");
  });

  it("groups editable member account operations beside the save action", () => {
    expect(adminUsersApiSource).toContain("deleteAdminUser");
    expect(adminUsersApiSource).toContain('method: "DELETE"');
    expect(adminUsersDetailSource).toContain("deleteAdminUser");
    expect(adminUsersDetailSource).toContain("openAccountActions");
    expect(adminUsersDetailSource).toContain("uni.showActionSheet");
    expect(adminUsersDetailSource).toContain(
      '["重置密码", "重置微信绑定", "删除账号"]',
    );
    expect(adminUsersDetailSource).toContain("confirmDeleteAccount");
    expect(adminUsersDetailSource).toContain('v-if="!readonlyMode"');
    expect(adminUsersDetailSource).toContain('class="detail-actions"');
    expect(adminUsersDetailSource).toContain('class="account-actions-button"');
    expect(adminUsersDetailSource).toContain("账号操作");
    expect(adminUsersDetailSource).toContain("保存资料");
    expect(adminUsersDetailSource).toContain("删除账号");
    expect(adminUsersDetailSource).not.toContain("成员退出");
    expect(adminUsersDetailSource).not.toContain('class="reset-button"');
    expect(adminUsersDetailSource).not.toContain('class="wechat-unbind-button"');
    expect(adminUsersDetailSource).not.toContain('class="exit-button"');
  });

  it("keeps member WeChat reset discoverable and reports an unbound account", () => {
    expect(adminUsersDetailSource).toContain("clearAdminUserWechatBinding");
    expect(adminUsersDetailSource).toContain("confirmClearWechatBinding");
    expect(adminUsersDetailSource).toContain("userDetail.value?.wechat_bound");
    expect(adminUsersDetailSource).toContain("重置微信绑定");
    expect(adminUsersDetailSource).toContain("当前成员尚未绑定微信");
    expect(adminUsersDetailSource).toContain("解绑后，该成员下次需要使用喵喵号和密码重新登录并绑定微信");
  });

  it("guards unsaved member fields and avatar for both button and native swipe-back", () => {
    const saved = createMemberEditSnapshot({
      nickname: "小林",
      real_name: "林同学",
      departments: ["宣传部"],
      grade: "2025",
      contact_info: "13800138000",
      role: "member",
      status: "active",
      avatar_url: "https://example.com/avatar-a.jpg",
    });

    expect(hasUnsavedMemberChanges(saved, { ...saved })).toBe(false);
    expect(
      hasUnsavedMemberChanges(saved, { ...saved, role: "summer_volunteer" }),
    ).toBe(true);
    expect(
      hasUnsavedMemberChanges(saved, { ...saved, avatar_url: "https://example.com/avatar-b.jpg" }),
    ).toBe(true);
    expect(
      hasUnsavedMemberChanges(saved, { ...saved, departments: ["宣传部", "秘书部"] }),
    ).toBe(true);
    expect(adminUsersDetailSource).toContain("createMemberEditSnapshot");
    expect(adminUsersDetailSource).toContain("hasUnsavedMemberChanges");
    expect(adminUsersDetailSource).toContain("createPageLeaveGuard");
    expect(adminUsersDetailSource).toContain("<page-container");
    expect(adminUsersDetailSource).toContain('@beforeleave="handleNativePageLeave"');
    expect(adminUsersDetailSource).toContain('@afterleave="handleGuardContainerAfterLeave"');
    expect(adminUsersDetailSource).toContain("createPageContainerLeaveCoordinator");
    expect(adminUsersDetailSource).toContain(
      "if (isSaving.value || !hasPendingMemberChanges())",
    );
    expect(adminUsersDetailSource).toContain("修改尚未保存，是否放弃？");
    expect(adminUsersDetailSource).toContain("preservePendingAvatar");
  });

  it("does not put a clean member detail page behind a permanent intermediate container", () => {
    const pageRootIndex = adminUsersDetailSource.indexOf('<view class="member-detail-page">');
    const guardIndex = adminUsersDetailSource.indexOf("<page-container");

    expect(pageRootIndex).toBeGreaterThanOrEqual(0);
    expect(guardIndex).toBeGreaterThan(pageRootIndex);
    expect(adminUsersDetailSource).toContain("const pageLeaveGuardArmed = computed(");
    expect(adminUsersDetailSource).not.toContain("const pageLeaveGuardArmed = ref(true)");
    expect(adminUsersDetailSource).toMatch(
      /function goBack\(\)\s*{[\s\S]*if \(!hasPendingMemberChanges\(\)\)[\s\S]*uni\.navigateBack\(\)/,
    );
  });
});
