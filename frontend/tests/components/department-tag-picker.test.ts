import { describe, expect, it } from "vitest";

import pickerSource from "../../src/components/DepartmentTagPicker.vue?raw";
import profileIndexSource from "../../src/pages/profile/index.vue?raw";
import profileDetailSource from "../../src/pages/profile/detail.vue?raw";
import profileCompleteSource from "../../src/pages/profile/complete.vue?raw";
import adminCreateUserSource from "../../src/pages/admin/create-user.vue?raw";
import adminUsersDetailSource from "../../src/pages/admin/users/detail.vue?raw";
import adminUsersIndexSource from "../../src/pages/admin/users/index.vue?raw";
import {
  DEPARTMENTS,
  DEPARTMENT_THEMES,
  getDepartmentTagColors,
  getDepartmentTagStyle,
  isKnownDepartment,
} from "../../src/constants/departments";

describe("department tag picker component", () => {
  it("renders removable tags and adds via native action sheet", () => {
    expect(pickerSource).toContain('emit("update:modelValue"');
    expect(pickerSource).toContain("removeDepartment");
    expect(pickerSource).toContain("uni.showActionSheet");
    expect(pickerSource).toContain('class="dept-picker-header"');
    expect(pickerSource).toContain("暂无部门");
    expect(pickerSource).toContain("width: 46rpx");
    expect(pickerSource).toContain('aria-label="添加部门"');
    expect(pickerSource).toContain('class="dept-add-icon"');
    expect(pickerSource).not.toContain("＋ 添加部门");
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
    expect(new Set(DEPARTMENTS.map((department) => getDepartmentTagColors(department).background)).size).toBe(5);
    expect(getDepartmentTagStyle("宣传部")).toEqual({
      backgroundColor: "#f4dfed",
      color: "#963b7a",
    });
    expect(DEPARTMENT_THEMES.养护部.head_title).toBe("#24786c");
    expect(DEPARTMENT_THEMES.养护部.deputy_title).toBe("#607c77");
    expect(getDepartmentTagStyle("未分部")).toEqual({
      backgroundColor: "#edf0f3",
      color: "#526070",
    });
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
    expect(adminUsersDetailSource).toContain('size="large"');
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
    expect(adminUsersIndexSource).toContain('v-for="dept in page"');
    expect(adminUsersIndexSource).toContain('from "@/constants/departments"');
    expect(adminUsersIndexSource).toContain("getDepartmentTagStyle(dept)");
    expect(adminUsersIndexSource).toContain("memberDepartmentPages");
    expect(adminUsersIndexSource).toContain('class="department-swiper"');
    expect(adminUsersIndexSource).toContain("vertical");
    expect(adminUsersIndexSource).toContain('@touchmove.stop="stopDepartmentGesture"');
    expect(adminUsersIndexSource).toContain("departments.slice(index, index + 2)");
    expect(adminUsersIndexSource).toContain("'is-single': memberDepartments(user).length === 1");
  });

  it("uses the shared identity avatar instead of role tags", () => {
    expect(adminUsersIndexSource).toContain("IdentityAvatar");
    expect(adminUsersIndexSource).toContain(':role="user.role"');
    expect(adminUsersIndexSource).not.toContain('class="role-tag"');
    expect(adminUsersIndexSource).not.toContain("function roleLabel(");
  });

  it("renders title identity as a shield and colored nickname without a title tag", () => {
    expect(adminUsersIndexSource).toContain("TitleIdentityName");
    expect(adminUsersIndexSource).toContain(':name="user.profile.nickname"');
    expect(adminUsersIndexSource).toContain(':title="user.profile.title"');
    expect(adminUsersIndexSource).not.toContain("TitleBadge");
  });

  it("keeps personnel cards uniform and places the raw member number near the name", () => {
    expect(adminUsersIndexSource).toContain("height: 168rpx");
    expect(adminUsersIndexSource).toContain('class="member-no">{{ user.meow_no }}</text>');
    expect(adminUsersIndexSource).toContain("margin-top: 7rpx");
    expect(adminUsersIndexSource).not.toContain("喵喵号 {{ user.meow_no }}");
  });
});
