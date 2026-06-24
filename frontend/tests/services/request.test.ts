import { beforeEach, describe, expect, it, vi } from "vitest";

import {
  ApiBusinessError,
  buildRequestUrl,
  createAuthorizationHeader,
  request,
} from "@/services/request";
import { LOGIN_ROUTE, setAuthExpiredHandler } from "@/services/auth-session";

describe("request service", () => {
  beforeEach(() => {
    setAuthExpiredHandler(null);
  });

  it("builds urls from base url and resource path", () => {
    expect(buildRequestUrl("http://localhost:8000/api/v1", "/auth/me")).toBe(
      "http://localhost:8000/api/v1/auth/me",
    );
  });

  it("creates bearer authorization header when token exists", () => {
    expect(createAuthorizationHeader("token-1")).toEqual({
      Authorization: "Bearer token-1",
    });
  });

  it("unwraps unified api response data", async () => {
    const requestMock = vi.fn((options: UniNamespace.RequestOptions) => {
      options.success?.({
        statusCode: 200,
        data: {
          code: 0,
          message: "success",
          data: { id: "u1" },
          trace_id: "trace-1",
        },
        header: {},
        cookies: [],
      } as UniNamespace.RequestSuccessCallbackResult);
    });
    vi.stubGlobal("uni", { request: requestMock });

    await expect(request<{ id: string }>({ url: "/auth/me" })).resolves.toEqual({
      id: "u1",
    });
  });

  it("throws business error when api code is not zero", async () => {
    vi.stubGlobal("uni", {
      request: (options: UniNamespace.RequestOptions) => {
        options.success?.({
          statusCode: 200,
          data: {
            code: 40301,
            message: "请先修改初始密码",
            data: null,
            trace_id: "trace-2",
          },
          header: {},
          cookies: [],
        } as UniNamespace.RequestSuccessCallbackResult);
      },
    });

    await expect(request({ url: "/tasks" })).rejects.toBeInstanceOf(
      ApiBusinessError,
    );
  });

  it("clears session and routes to login when token is expired", async () => {
    const removeStorageSync = vi.fn();
    const reLaunch = vi.fn((options: UniNamespace.ReLaunchOptions) => {
      options.complete?.({ errMsg: "reLaunch:ok" });
    });
    vi.stubGlobal("uni", {
      removeStorageSync,
      reLaunch,
      request: (options: UniNamespace.RequestOptions) => {
        options.success?.({
          statusCode: 401,
          data: {
            code: 40102,
            message: "Token 无效或已过期",
            data: null,
            trace_id: "trace-expired",
          },
          header: {},
          cookies: [],
        } as UniNamespace.RequestSuccessCallbackResult);
      },
    });

    await expect(
      request({ url: "/map/init", token: "expired-token" }),
    ).rejects.toMatchObject({
      code: 40102,
      message: "Token 无效或已过期",
    });
    expect(removeStorageSync).toHaveBeenCalledWith("cat_map_access_token");
    expect(removeStorageSync).toHaveBeenCalledWith("cat_map_current_user");
    expect(reLaunch).toHaveBeenCalledWith(
      expect.objectContaining({ url: LOGIN_ROUTE }),
    );
  });
});
