import { describe, expect, it } from "vitest";

import pickerSource from "../../src/components/DepartmentTagPicker.vue?raw";
import profileIndexSource from "../../src/pages/profile/index.vue?raw";
import profileDetailSource from "../../src/pages/profile/detail.vue?raw";
import profileCompleteSource from "../../src/pages/profile/complete.vue?raw";
import adminCreateUserSource from "../../src/pages/admin/create-user.vue?raw";
import adminUsersDetailSource from "../../src/pages/admin/users/detail.vue?raw";
import adminUsersIndexSource from "../../src/pages/admin/users/index.vue?raw";
import { DEPARTMENTS, isKnownDepartment } from "../../src/constants/departments";

describe("department tag picker component", () => {
  it("renders removable tags and adds via native action sheet", () => {
    expect(pickerSource).toContain('emit("update:modelValue"');
    expect(pickerSource).toContain("removeDepartment");
    expect(pickerSource).toContain("uni.showActionSheet");
    expect(pickerSource).toContain("＋ 添加部门");
    expect(pickerSource).toContain('class="dept-tag-remove"');
    expect(pickerSource).toContain("×");
    expect(pickerSource).toContain('from "@/constants/departments"');
  });

  it("exposes the five fixed departments as the shared constant", () => {
    expect(DEPARTMENTS).toEqual([
      "生存保障部",
      "活动部",
      "宣传部",
      "秘书部",
      "养护部",
    ]);
    expect(isKnownDepartment("活动部")).toBe(true);
    expect(isKnownDepartment("计算机学院")).toBe(false);
  });
});

describe("multi-department forms", () => {
  it("replaces the single-select department picker in all four forms", () => {
    for (const source of [
      profileDetailSource,
      profileCompleteSource,
      adminCreateUserSource,
      adminUsersDetailSource,
    ]) {
      expect(source).toContain("DepartmentTagPicker");
      expect(source).toContain('v-model="form.departments"');
      expect(source).not.toContain("onDepartmentChange");
      expect(source).not.toContain("selectDepartment(event");
    }
    expect(profileDetailSource).toContain("departments: form.departments");
    expect(adminUsersDetailSource).toContain("departments: form.departments");
  });

  it("keeps the member edit control disabled in readonly mode", () => {
    expect(adminUsersDetailSource).toContain(':disabled="readonlyMode"');
  });

  it("renders the profile card departments as a horizontally scrollable tag row", () => {
    expect(profileIndexSource).toContain('class="dept-scroll"');
    expect(profileIndexSource).toContain("scroll-x");
    expect(profileIndexSource).toContain("departmentTags");
    expect(profileIndexSource).toContain('class="dept-chip"');
    expect(profileIndexSource).not.toContain("部门：{{");
  });

  it("shows every department of a member on the admin list card", () => {
    expect(adminUsersIndexSource).toContain("memberDepartments");
    expect(adminUsersIndexSource).toContain('v-for="dept in memberDepartments(user)"');
    expect(adminUsersIndexSource).toContain('from "@/constants/departments"');
  });
});
