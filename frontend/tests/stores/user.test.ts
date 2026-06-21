import { createPinia, setActivePinia } from "pinia";
import { beforeEach, describe, expect, it, vi } from "vitest";

import { useUserStore } from "@/stores/user";
import type { CurrentUser } from "@/types/user";

const user: CurrentUser = {
  id: "u1",
  student_no: "20252160A1010",
  role: "admin",
  status: "active",
  nickname: "小林",
  avatar_url: "",
  must_change_password: false,
};

describe("user store", () => {
  beforeEach(() => {
    setActivePinia(createPinia());
    vi.stubGlobal("uni", {
      getStorageSync: vi.fn(),
      setStorageSync: vi.fn(),
      removeStorageSync: vi.fn(),
    });
  });

  it("sets token and current user after login", () => {
    const store = useUserStore();

    store.setSession("token-1", user);

    expect(store.accessToken).toBe("token-1");
    expect(store.currentUser?.student_no).toBe("20252160A1010");
    expect(store.isLoggedIn).toBe(true);
    expect(store.isAdmin).toBe(true);
  });

  it("clears token and current user on logout", () => {
    const store = useUserStore();
    store.setSession("token-1", user);

    store.clearSession();

    expect(store.accessToken).toBe("");
    expect(store.currentUser).toBeNull();
    expect(store.isLoggedIn).toBe(false);
  });
});
