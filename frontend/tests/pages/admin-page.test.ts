import { describe, expect, it } from "vitest";

import adminCreateUserSource from "../../src/pages/admin/create-user.vue?raw";
import adminIndexSource from "../../src/pages/admin/index.vue?raw";
import pagesJson from "../../src/pages.json?raw";

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
});
