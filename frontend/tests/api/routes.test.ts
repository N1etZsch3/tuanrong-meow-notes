import { describe, expect, it } from "vitest";

import {
  API_ENDPOINTS,
  compactApiParams,
  compactDefinedApiParams,
} from "@/api/routes";

describe("api routes", () => {
  it("keeps static endpoints in one registry", () => {
    expect(API_ENDPOINTS.auth.login).toBe("/auth/login");
    expect(API_ENDPOINTS.map.points).toBe("/map/points");
    expect(API_ENDPOINTS.admin.users).toBe("/admin/users");
  });

  it("builds encoded endpoints for resource ids", () => {
    expect(API_ENDPOINTS.tasks.detail("task 1/2")).toBe("/tasks/task%201%2F2");
    expect(API_ENDPOINTS.tasks.checkins("task 1/2")).toBe(
      "/tasks/task%201%2F2/checkins",
    );
    expect(API_ENDPOINTS.admin.mapPoint("point 1/2")).toBe(
      "/admin/map/points/point%201%2F2",
    );
  });

  it("builds asset content paths with compact query parameters", () => {
    expect(
      API_ENDPOINTS.files.assetContent("asset 1/2", {
        scene: "task detail full",
        variant_key: undefined,
      }),
    ).toBe(
      "/files/assets/asset%201%2F2/content?scene=task%20detail%20full",
    );
  });

  it("compacts request params without dropping falsy business values", () => {
    expect(
      compactApiParams({
        keyword: "",
        page: 1,
        has_more: false,
        optional: null,
      }),
    ).toEqual({
      page: 1,
      has_more: false,
    });
  });

  it("compacts payload params while keeping explicit empty values", () => {
    expect(
      compactDefinedApiParams({
        area_id: null,
        subtitle: "",
        name: undefined,
      }),
    ).toEqual({
      area_id: null,
      subtitle: "",
    });
  });
});
