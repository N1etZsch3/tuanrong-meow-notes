import { describe, expect, it } from "vitest";

import adminUsersApiSource from "../../src/api/admin-users.ts?raw";
import createUserSource from "../../src/pages/admin/create-user.vue?raw";
import memberDetailSource from "../../src/pages/admin/users/detail.vue?raw";
import memberListSource from "../../src/pages/admin/users/index.vue?raw";
import profileDetailSource from "../../src/pages/profile/detail.vue?raw";
import profileIndexSource from "../../src/pages/profile/index.vue?raw";
import identityAvatarSource from "../../src/components/IdentityAvatar.vue?raw";

describe("super administrator frontend contract", () => {
  it("uses dedicated APIs for creating and managing administrators", () => {
    expect(adminUsersApiSource).toContain("createSuperAdminUser");
    expect(adminUsersApiSource).toContain("updateSuperAdminUser");
    expect(adminUsersApiSource).toContain("resetSuperAdminUserPassword");
    expect(adminUsersApiSource).toContain("clearSuperAdminUserWechatBinding");
    expect(adminUsersApiSource).toContain("deleteSuperAdminUser");
    expect(createUserSource).toContain('form.role === "admin" ? createSuperAdminUser');
    expect(memberDetailSource).toContain("usesSuperAdminApi");
    expect(memberDetailSource).toContain("updateSuperAdminUser");
  });

  it("keeps super admin non-assignable and only exposes admin assignment to the president", () => {
    expect(createUserSource).toContain('userStore.currentUser?.role === "super_admin"');
    expect(createUserSource).toContain('{ label: "管理员", value: "admin" as UserRole }');
    expect(createUserSource).not.toContain('value: "super_admin" as UserRole');
    expect(memberDetailSource).not.toContain('{ label: "超级管理员", value: "super_admin" }');
  });

  it("reuses the role-colored avatar on all requested profile surfaces", () => {
    expect(memberListSource).toContain("IdentityAvatar");
    expect(memberDetailSource).toContain("IdentityAvatar");
    expect(profileIndexSource).toContain("IdentityAvatar");
    expect(profileDetailSource).toContain("IdentityAvatar");
    expect(identityAvatarSource).toContain("超级管理员.svg");
    expect(identityAvatarSource).toContain("identity-avatar--super_admin");
    expect(identityAvatarSource).toContain("border-color: #d94343");
  });

  it("shows the title label rather than duplicating the nickname below the detail avatar", () => {
    expect(memberDetailSource).toMatch(
      /<TitleIdentityName[\s\S]*:title="userDetail\.profile\.title"[\s\S]*display="title"/,
    );
    expect(memberDetailSource).not.toMatch(
      /<TitleIdentityName[\s\S]*:name="userDetail\.profile\.nickname"[\s\S]*size="detail"/,
    );
  });

  it("removes the role pill and renders title identity through the nickname", () => {
    expect(profileIndexSource).not.toContain('class="role-pill"');
    expect(profileIndexSource).toContain("TitleIdentityName");
    expect(profileIndexSource).not.toContain("TitleBadge");
  });
});
