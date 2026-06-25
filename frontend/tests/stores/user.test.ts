import { createPinia, setActivePinia } from "pinia";
import { beforeEach, describe, expect, it, vi } from "vitest";

import { STORAGE_KEYS } from "@/constants/storage";
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
  profile_completed: true,
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
              profile_completed: false,
            user: {
              id: "u1",
              student_no: "trmx0001",
              meow_no: "trmx0001",
              nickname: "小林",
              avatar_url: null,
              role: "admin",
              status: "active",
              profile_completed: false,
            },
            next_action: "enter_app",
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
      meow_no: "trmx0001",
      password: "123456",
      captcha_id: "captcha-1",
      captcha_code: "A7KD",
      agree_terms: true,
    });

    expect(store.accessToken).toBe("token-1");
    expect(store.currentUser?.must_change_password).toBe(false);
    expect(store.isAdmin).toBe(true);
  });

  it("renews near-expired token before refreshing current user", async () => {
    vi.useFakeTimers();
    vi.setSystemTime(new Date("2026-06-24T00:00:00.000Z"));

    const setStorageSync = vi.fn();
    const requestMock = vi.fn((options: UniNamespace.RequestOptions) => {
      if (String(options.url).endsWith("/auth/renew")) {
        expect(options.header).toEqual(
          expect.objectContaining({ Authorization: "Bearer token-1" }),
        );
        options.success?.({
          statusCode: 200,
          data: {
            code: 0,
            message: "success",
            data: {
              access_token: "token-2",
              token_type: "Bearer",
              expires_in: 604800,
            },
            trace_id: "trace-renew",
          },
          header: {},
          cookies: [],
        } as UniNamespace.RequestSuccessCallbackResult);
        return;
      }

      expect(String(options.url)).toContain("/auth/me");
      expect(options.header).toEqual(
        expect.objectContaining({ Authorization: "Bearer token-2" }),
      );
      options.success?.({
        statusCode: 200,
        data: {
          code: 0,
          message: "success",
          data: {
            id: "u1",
            student_no: "20252160A1010",
            role: "admin",
            status: "active",
            must_change_password: false,
            profile_completed: true,
            profile: {
              nickname: "小林",
              avatar_url: null,
            },
          },
          trace_id: "trace-me",
        },
        header: {},
        cookies: [],
      } as UniNamespace.RequestSuccessCallbackResult);
    });
    vi.stubGlobal("uni", {
      getStorageSync: vi.fn(),
      setStorageSync,
      removeStorageSync: vi.fn(),
      request: requestMock,
    });

    try {
      const store = useUserStore();
      store.setSession("token-1", user, 1);

      const currentUser = await store.refreshCurrentUser();

      expect(currentUser?.student_no).toBe("20252160A1010");
      expect(store.accessToken).toBe("token-2");
      expect(requestMock).toHaveBeenCalledTimes(2);
      expect(requestMock.mock.calls[0][0].url).toContain("/auth/renew");
      expect(requestMock.mock.calls[1][0].url).toContain("/auth/me");
      expect(setStorageSync).toHaveBeenCalledWith(
        STORAGE_KEYS.accessTokenExpiresAt,
        Date.now() + 604800 * 1000,
      );
    } finally {
      vi.useRealTimers();
    }
  });

  it("changes password and replaces the invalidated token", async () => {
    const requestMock = vi.fn((options: UniNamespace.RequestOptions) => {
      expect(String(options.url)).toContain("/auth/password");
      expect(options.header).toEqual(
        expect.objectContaining({ Authorization: "Bearer token-1" }),
      );
      options.success?.({
        statusCode: 200,
        data: {
          code: 0,
          message: "success",
          data: {
            access_token: "token-2",
            token_type: "Bearer",
            expires_in: 604800,
            must_change_password: false,
            profile_completed: false,
            next_action: "complete_profile",
          },
          trace_id: "trace-password",
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
    store.setSession("token-1", { ...user, must_change_password: true, profile_completed: false });

    const result = await store.changeCurrentPassword({
      old_password: "trmx0001",
      new_password: "Catmap2026",
      confirm_password: "Catmap2026",
    });

    expect(result.next_action).toBe("complete_profile");
    expect(store.accessToken).toBe("token-2");
    expect(store.currentUser?.must_change_password).toBe(false);
    expect(store.currentUser?.profile_completed).toBe(false);
  });

  it("completes profile initialization and marks current user as ready", async () => {
    const requestMock = vi.fn((options: UniNamespace.RequestOptions) => {
      expect(String(options.url)).toContain("/profile/me/complete");
      options.success?.({
        statusCode: 200,
        data: {
          code: 0,
          message: "success",
          data: {
            profile_completed: true,
            next_action: "enter_app",
          },
          trace_id: "trace-profile",
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
    store.setSession("token-1", { ...user, profile_completed: false });

    const result = await store.completeCurrentProfile({
      nickname: "喂猫搭子🥜",
      avatar_url: null,
      department: "生存保障部",
      contact_info: "13800138000",
    });

    expect(result.next_action).toBe("enter_app");
    expect(store.currentUser?.profile_completed).toBe(true);
    expect(store.currentUser?.nickname).toBe("喂猫搭子🥜");
  });
});
