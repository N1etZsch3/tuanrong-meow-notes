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

  it("logs in with password and stores returned session", async () => {
    const requestMock = vi.fn((options: UniNamespace.RequestOptions) => {
      options.success?.({
        statusCode: 200,
        data: {
          code: 0,
          message: "login success",
          data: {
            access_token: "token-1",
            token_type: "Bearer",
            expires_in: 7200,
            must_change_password: false,
            user: {
              id: "u1",
              student_no: "20252160A1010",
              nickname: "小林",
              avatar_url: null,
              role: "admin",
              status: "active",
            },
          },
          trace_id: "trace-1",
        },
        header: {},
        cookies: [],
      } as UniNamespace.RequestSuccessCallbackResult);
    });
    vi.stubGlobal("uni", {
      getStorageSync: vi.fn(),
      setStorageSync: vi.fn(),
      removeStorageSync: vi.fn(),
      request: requestMock,
    });

    const store = useUserStore();
    await store.loginWithPassword({
      student_no: "20252160A1010",
      password: "123456",
      captcha_id: "captcha-1",
      captcha_code: "A7KD",
      agree_terms: true,
    });

    expect(store.accessToken).toBe("token-1");
    expect(store.currentUser?.must_change_password).toBe(false);
    expect(store.isAdmin).toBe(true);
  });
});
