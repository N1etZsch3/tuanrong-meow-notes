import { describe, expect, it, vi } from "vitest";

import { getCaptcha, login } from "@/api/auth";

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

  it("posts student number login payload to /auth/login", async () => {
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
            must_change_password: true,
            user: {
              id: "u1",
              student_no: "20252160A1010",
              nickname: "小林",
              avatar_url: null,
              role: "member",
              status: "active",
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
      student_no: "20252160A1010",
      password: "123456",
      captcha_id: "captcha-1",
      captcha_code: "A7KD",
      agree_terms: true,
    });

    expect(result.access_token).toBe("token-1");
    expect(result.user.student_no).toBe("20252160A1010");
    expect(requestMock).toHaveBeenCalledWith(
      expect.objectContaining({
        method: "POST",
        url: expect.stringContaining("/auth/login"),
        data: expect.objectContaining({
          student_no: "20252160A1010",
          agree_terms: true,
        }),
      }),
    );
  });
});
