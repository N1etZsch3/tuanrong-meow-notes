import { describe, expect, it } from "vitest";

import adminCreateUserSource from "../../src/pages/admin/create-user.vue?raw";
import adminIndexSource from "../../src/pages/admin/index.vue?raw";
import adminLandmarkCreateSource from "../../src/pages/admin/landmarks/create.vue?raw";
import adminLandmarkLocationSource from "../../src/pages/admin/landmarks/location.vue?raw";
import adminUsersApiSource from "../../src/api/admin-users.ts?raw";
import adminUsersDetailSource from "../../src/pages/admin/users/detail.vue?raw";
import pagesJson from "../../src/pages.json?raw";

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

describe("admin entry pages", () => {
  it("registers admin entry, personnel, create user, and landmark routes", () => {
    expect(pagesJson).toContain("pages/admin/index");
    expect(pagesJson).toContain("pages/admin/users/index");
    expect(pagesJson).toContain("pages/admin/users/detail");
    expect(pagesJson).toContain("pages/admin/create-user");
    expect(pagesJson).toContain("pages/admin/landmarks/create");
    expect(pagesJson).toContain("pages/landmarks/detail");
  });

  it("shows personnel management, summer feeding, supply, and landmark actions", () => {
    expect(adminIndexSource).toContain("人员管理");
    expect(adminIndexSource).toContain("/pages/admin/users/index");
    expect(adminIndexSource).toContain("发布喂食任务");
    expect(adminIndexSource).toContain("/pages/admin/tasks/create");
    expect(adminIndexSource).toContain("新建物资点");
    expect(adminIndexSource).toContain("/pages/admin/supplies/create");
    expect(adminIndexSource).toContain("新建地标点");
    expect(adminIndexSource).toContain("/pages/admin/landmarks/create");
  });

  it("creates member accounts through the admin users api", () => {
    expect(adminCreateUserSource).toContain("createAdminUser");
    expect(adminCreateUserSource).toContain("新增成员");
    expect(adminCreateUserSource).toContain("喵喵号");
    expect(adminCreateUserSource).toContain("initial_password");
    expect(adminCreateUserSource).toContain("must_change_password");
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

  it("lets admins soft delete editable members from member detail", () => {
    expect(adminUsersApiSource).toContain("deleteAdminUser");
    expect(adminUsersApiSource).toContain('method: "DELETE"');
    expect(adminUsersDetailSource).toContain("deleteAdminUser");
    expect(adminUsersDetailSource).toContain("confirmMemberExit");
    expect(adminUsersDetailSource).toContain('v-if="!readonlyMode"');
    expect(adminUsersDetailSource).toContain("exit-button");
  });
});
