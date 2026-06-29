import { describe, expect, it } from "vitest";

import adminCreateUserSource from "../../src/pages/admin/create-user.vue?raw";
import adminIndexSource from "../../src/pages/admin/index.vue?raw";
import pagesJson from "../../src/pages.json?raw";

describe("admin entry pages", () => {
  it("registers admin entry and create user routes", () => {
    expect(pagesJson).toContain("pages/admin/index");
    expect(pagesJson).toContain("pages/admin/create-user");
  });

  it("shows account creation and summer feeding publish actions", () => {
    expect(adminIndexSource).toContain("添加账户");
    expect(adminIndexSource).toContain("/pages/admin/create-user");
    expect(adminIndexSource).toContain("发布喂食任务");
    expect(adminIndexSource).toContain("/pages/admin/tasks/create");
  });

  it("creates member accounts through the admin users api", () => {
    expect(adminCreateUserSource).toContain("createAdminUser");
    expect(adminCreateUserSource).toContain("喵喵号");
    expect(adminCreateUserSource).toContain("initial_password");
    expect(adminCreateUserSource).toContain("must_change_password");
  });
});
