import { describe, expect, it, vi } from "vitest";

import {
  changePassword,
  getCaptcha,
  login,
  renewAccessToken,
  wechatLogin,
} from "@/api/auth";

describe("auth api", () => {
  it("requests captcha from /auth/captcha", async () => {
    const requestMock = vi.fn((options: UniNamespace.RequestOptions) => {
      options.success?.({
        statusCode: 200,
        data: {
          code: 0,
          message: "success",
          data: {
            captcha_id: "captcha-1",
            captcha_image: "data:image/svg+xml;base64,abc",
            expires_in: 300,
          },
          trace_id: "trace-1",
        },
        header: {},
        cookies: [],
      } as UniNamespace.RequestSuccessCallbackResult);
    });
    vi.stubGlobal("uni", { request: requestMock });

    await expect(getCaptcha()).resolves.toEqual({
      captcha_id: "captcha-1",
      captcha_image: "data:image/svg+xml;base64,abc",
      expires_in: 300,
    });
    expect(requestMock).toHaveBeenCalledWith(
      expect.objectContaining({
        method: "GET",
        url: expect.stringContaining("/auth/captcha"),
      }),
    );
  });

  it("posts meow number login payload to /auth/login", async () => {
    const requestMock = vi.fn((options: UniNamespace.RequestOptions) => {
      options.success?.({
        statusCode: 200,
        data: {
          code: 0,
          message: "login success",
          data: {
            access_token: "token-1",
            token_type: "Bearer",
            expires_in: 604800,
            must_change_password: true,
            next_action: "change_password",
            user: {
              id: "u1",
              student_no: "trmx0001",
              meow_no: "trmx0001",
              nickname: "小林",
              avatar_url: null,
              role: "member",
              status: "active",
              profile_completed: false,
            },
          },
          trace_id: "trace-2",
        },
        header: {},
        cookies: [],
      } as UniNamespace.RequestSuccessCallbackResult);
    });
    vi.stubGlobal("uni", { request: requestMock });

    const result = await login({
      meow_no: "trmx0001",
      password: "123456",
      captcha_id: "captcha-1",
      captcha_code: "A7KD",
      agree_terms: true,
      wechat_code: "wechat-code-1",
      agree_wechat_bind: true,
    });

    expect(result.access_token).toBe("token-1");
    expect(result.next_action).toBe("change_password");
    expect(result.user.meow_no).toBe("trmx0001");
    expect(requestMock).toHaveBeenCalledWith(
      expect.objectContaining({
        method: "POST",
        url: expect.stringContaining("/auth/login"),
        data: expect.objectContaining({
          meow_no: "trmx0001",
          agree_terms: true,
          wechat_code: "wechat-code-1",
          agree_wechat_bind: true,
        }),
      }),
    );
  });

  it("posts a WeChat code to /auth/wechat/login", async () => {
    const requestMock = vi.fn((options: UniNamespace.RequestOptions) => {
      options.success?.({
        statusCode: 200,
        data: {
          code: 0,
          message: "login success",
          data: {
            access_token: "wechat-token",
            token_type: "Bearer",
            expires_in: 604800,
            must_change_password: false,
            profile_completed: true,
            next_action: "enter_app",
            user: {
              id: "u1",
              student_no: "trmx0001",
              meow_no: "trmx0001",
              nickname: "小林",
              avatar_url: null,
              role: "member",
              status: "active",
              profile_completed: true,
            },
          },
          trace_id: "trace-wechat",
        },
        header: {},
        cookies: [],
      } as UniNamespace.RequestSuccessCallbackResult);
    });
    vi.stubGlobal("uni", { request: requestMock });

    await expect(wechatLogin("wechat-code-1")).resolves.toMatchObject({
      access_token: "wechat-token",
      next_action: "enter_app",
    });
    expect(requestMock).toHaveBeenCalledWith(
      expect.objectContaining({
        method: "POST",
        url: expect.stringContaining("/auth/wechat/login"),
        data: { code: "wechat-code-1" },
      }),
    );
  });

  it("renews access token through /auth/renew", async () => {
    const requestMock = vi.fn((options: UniNamespace.RequestOptions) => {
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
          trace_id: "trace-3",
        },
        header: {},
        cookies: [],
      } as UniNamespace.RequestSuccessCallbackResult);
    });
    vi.stubGlobal("uni", { request: requestMock });

    await expect(renewAccessToken("token-1")).resolves.toEqual({
      access_token: "token-2",
      token_type: "Bearer",
      expires_in: 604800,
    });
    expect(requestMock).toHaveBeenCalledWith(
      expect.objectContaining({
        method: "POST",
        url: expect.stringContaining("/auth/renew"),
        header: expect.objectContaining({
          Authorization: "Bearer token-1",
        }),
      }),
    );
  });

  it("changes password and receives a fresh token for onboarding", async () => {
    const requestMock = vi.fn((options: UniNamespace.RequestOptions) => {
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
          trace_id: "trace-4",
        },
        header: {},
        cookies: [],
      } as UniNamespace.RequestSuccessCallbackResult);
    });
    vi.stubGlobal("uni", { request: requestMock });

    await expect(
      changePassword(
        {
          old_password: "trmx0001",
          new_password: "Catmap2026",
          confirm_password: "Catmap2026",
        },
        "token-1",
      ),
    ).resolves.toEqual({
      access_token: "token-2",
      token_type: "Bearer",
      expires_in: 604800,
      must_change_password: false,
      profile_completed: false,
      next_action: "complete_profile",
    });
    expect(requestMock).toHaveBeenCalledWith(
      expect.objectContaining({
        method: "PATCH",
        url: expect.stringContaining("/auth/password"),
        header: expect.objectContaining({
          Authorization: "Bearer token-1",
        }),
      }),
    );
  });
});
