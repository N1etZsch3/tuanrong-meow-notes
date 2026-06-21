import { describe, expect, it, vi } from "vitest";

import {
  ApiBusinessError,
  buildRequestUrl,
  createAuthorizationHeader,
  request,
} from "@/services/request";

describe("request service", () => {
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
});
