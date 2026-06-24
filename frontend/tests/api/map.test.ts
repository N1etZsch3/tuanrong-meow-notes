import { describe, expect, it, vi } from "vitest";

import { getMapInit, getMapPoints, searchMap } from "@/api/map";

function mockSuccess(data: unknown) {
  return vi.fn((options: UniNamespace.RequestOptions) => {
    options.success?.({
      statusCode: 200,
      data: {
        code: 0,
        message: "success",
        data,
        trace_id: "trace-map",
      },
      header: {},
      cookies: [],
    } as UniNamespace.RequestSuccessCallbackResult);
  });
}

describe("map api", () => {
  it("requests map init with bearer token", async () => {
    const requestMock = mockSuccess({
      campus: { name: "湖北师范大学" },
      areas: [],
      marker_configs: [],
      default_filters: {},
      ui_config: {},
      amap_config: { web_key: "web-key", security_js_code: "security" },
    });
    vi.stubGlobal("uni", { request: requestMock });

    await expect(getMapInit("token-1")).resolves.toMatchObject({
      campus: { name: "湖北师范大学" },
    });

    expect(requestMock).toHaveBeenCalledWith(
      expect.objectContaining({
        method: "GET",
        url: expect.stringContaining("/map/init"),
        header: expect.objectContaining({
          Authorization: "Bearer token-1",
        }),
      }),
    );
  });

  it("requests points with filters and viewport params", async () => {
    const requestMock = mockSuccess({ items: [], total: 0 });
    vi.stubGlobal("uni", { request: requestMock });

    await getMapPoints("token-1", {
      point_types: "task",
      business_types: "emergency",
      min_lng: 115,
      min_lat: 30,
      max_lng: 116,
      max_lat: 31,
      user_lng: undefined,
    });

    expect(requestMock).toHaveBeenCalledWith(
      expect.objectContaining({
        method: "GET",
        url: expect.stringContaining("/map/points"),
        data: {
          point_types: "task",
          business_types: "emergency",
          min_lng: 115,
          min_lat: 30,
          max_lng: 116,
          max_lat: 31,
        },
      }),
    );
  });

  it("searches map content with keyword and pagination", async () => {
    const requestMock = mockSuccess({ items: [], total: 0 });
    vi.stubGlobal("uni", { request: requestMock });

    await searchMap("token-1", {
      keyword: "北门",
      page: 1,
      page_size: 20,
    });

    expect(requestMock).toHaveBeenCalledWith(
      expect.objectContaining({
        method: "GET",
        url: expect.stringContaining("/map/search"),
        data: {
          keyword: "北门",
          page: 1,
          page_size: 20,
        },
      }),
    );
  });
});
