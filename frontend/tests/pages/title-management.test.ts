import { describe, expect, it } from "vitest";

import createUserSource from "../../src/pages/admin/create-user.vue?raw";
import memberDetailSource from "../../src/pages/admin/users/detail.vue?raw";
import profileIndexSource from "../../src/pages/profile/index.vue?raw";
import settingsSource from "../../src/pages/profile/settings.vue?raw";
import titleModalSource from "../../src/components/MemberTitleActionsModal.vue?raw";
import {
  availableAssignableTitles,
  canManageMemberTitles,
} from "../../src/pages/admin/users/title-actions";
import type { TitleCatalogItem } from "../../src/api/titles";

describe("title management pages", () => {
  const catalog: TitleCatalogItem[] = [
    { key: "president", label: "会长", shield: "gold", is_available: false, holder: null },
    { key: "vice_president", label: "副会长", shield: "purple", is_available: false, holder: { user_id: "u1", meow_no: "trmx0001", nickname: "甲" } },
    { key: "care_head", label: "部部长", shield: "green", is_available: true, holder: null },
  ];

  it("only offers available non-president slots plus the target's current slot", () => {
    expect(availableAssignableTitles(catalog, "u1").map((item) => item.key)).toEqual([
      "vice_president",
      "care_head",
    ]);
    expect(availableAssignableTitles(catalog, "u2").map((item) => item.key)).toEqual([
      "care_head",
    ]);
  });

  it("keeps title management exclusive to the president and excludes self", () => {
    expect(
      canManageMemberTitles("super_admin", "president", "president-id", "member-id"),
    ).toBe(true);
    expect(
      canManageMemberTitles("admin", "president", "president-id", "member-id"),
    ).toBe(false);
    expect(
      canManageMemberTitles("admin", "vice_president", "vice-id", "member-id"),
    ).toBe(false);
    expect(
      canManageMemberTitles("super_admin", "president", "same-id", "same-id"),
    ).toBe(false);
  });

  it("integrates title identity, creation, resignation, grant, and transfer flows", () => {
    expect(profileIndexSource).toContain("TitleBadge");
    expect(createUserSource).toContain("getTitleCatalog");
    expect(createUserSource).toContain("form.title");
    expect(settingsSource).toContain("resignMyTitle");
    expect(settingsSource).toContain("退出头衔");
    expect(memberDetailSource).toContain("setMemberTitle");
    expect(memberDetailSource).toContain("transferPresident");
    expect(memberDetailSource).toContain("uni.showModal");
    expect(memberDetailSource).toContain("MemberTitleActionsModal");
    expect(memberDetailSource).not.toContain("当前头衔</text>");
    expect(memberDetailSource).not.toContain('class="title-actions-card"');
    expect(titleModalSource).toContain("授予或变更头衔");
    expect(titleModalSource).toContain("同时转移超级管理员权限");
  });
});
