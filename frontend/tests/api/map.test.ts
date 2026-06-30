import { describe, expect, it, vi } from "vitest";

import {
  getAdminMapPoint,
  updateAdminMapPoint,
  updateAdminMapPointLocation,
} from "@/api/admin-map";
import { getMapInit, getMapPointNavigation, getMapPoints, searchMap } from "@/api/map";

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
      filter_options: [{ key: "none", label: "无标记" }],
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
      filter_key: "feeding_pending",
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
          filter_key: "feeding_pending",
        },
      }),
    );
  });

  it("searches map content with keyword, pagination, and external poi flag", async () => {
    const requestMock = mockSuccess({ items: [], total: 0 });
    vi.stubGlobal("uni", { request: requestMock });

    await searchMap("token-1", {
      keyword: "北门",
      include_external: true,
      page: 1,
      page_size: 20,
    });

    expect(requestMock).toHaveBeenCalledWith(
      expect.objectContaining({
        method: "GET",
        url: expect.stringContaining("/map/search"),
        data: {
          keyword: "北门",
          include_external: true,
          page: 1,
          page_size: 20,
        },
      }),
    );
  });

  it("requests point navigation with current location and in-app mode", async () => {
    const requestMock = mockSuccess({
      point_id: "point-1",
      title: "北门草丛",
      destination: {
        lng: 115.0609,
        lat: 30.233,
        location_name: "北门草丛",
        amap_poi_id: null,
        amap_address: null,
      },
      route_instruction: null,
      landmark_hint: null,
      entrance_hint: null,
      photos: [],
      amap_navigation: {
        mode: "walking",
        open_url: "",
        web_url: "",
      },
      route: {
        provider: "amap",
        fallback: false,
        distance_meters: 450,
        duration_seconds: 360,
        points: [
          { lng: 115.0622, lat: 30.2299 },
          { lng: 115.0609, lat: 30.233 },
        ],
        steps: [],
      },
    });
    vi.stubGlobal("uni", { request: requestMock });

    await getMapPointNavigation("token-1", "point-1", {
      from_lng: 115.0622,
      from_lat: 30.2299,
      mode: "walking",
    });

    expect(requestMock).toHaveBeenCalledWith(
      expect.objectContaining({
        method: "GET",
        url: expect.stringContaining("/map/points/point-1/navigation"),
        data: {
          from_lng: 115.0622,
          from_lat: 30.2299,
          mode: "walking",
        },
      }),
    );
  });

  it("requests admin map point edit endpoints", async () => {
    const requestMock = mockSuccess({ point_id: "point-1" });
    vi.stubGlobal("uni", { request: requestMock });

    await getAdminMapPoint("token-1", "point-1");
    await updateAdminMapPoint("token-1", "point-1", {
      name: "北门草丛救助点",
      route_instruction: "从北门进来后沿右侧围栏走。",
    });
    await updateAdminMapPointLocation("token-1", "point-1", {
      lng: 115.0611,
      lat: 30.2332,
    });

    expect(requestMock).toHaveBeenNthCalledWith(
      1,
      expect.objectContaining({
        method: "GET",
        url: expect.stringContaining("/admin/map/points/point-1"),
      }),
    );
    expect(requestMock).toHaveBeenNthCalledWith(
      2,
      expect.objectContaining({
        method: "PATCH",
        url: expect.stringContaining("/admin/map/points/point-1"),
        data: {
          name: "北门草丛救助点",
          route_instruction: "从北门进来后沿右侧围栏走。",
        },
      }),
    );
    expect(requestMock).toHaveBeenNthCalledWith(
      3,
      expect.objectContaining({
        method: "PATCH",
        url: expect.stringContaining("/admin/map/points/point-1/location"),
        data: {
          lng: 115.0611,
          lat: 30.2332,
        },
      }),
    );
  });
});
