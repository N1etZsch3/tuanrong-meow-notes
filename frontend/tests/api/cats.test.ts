import { describe, expect, it, vi } from "vitest";

import { getCatFilterOptions, getCatStats, getCats } from "@/api/cats";

function mockSuccess(data: unknown) {
  return vi.fn((options: UniNamespace.RequestOptions) => {
    options.success?.({
      statusCode: 200,
      data: {
        code: 0,
        message: "success",
        data,
        trace_id: "trace-cats",
      },
      header: {},
      cookies: [],
    } as UniNamespace.RequestSuccessCallbackResult);
  });
}

describe("cats api", () => {
  it("requests cat stats with bearer token", async () => {
    const requestMock = mockSuccess({
      total_cats: 0,
      active_cats: 0,
      waiting_adoption_cats: 0,
      watching_cats: 0,
      neutered_cats: 0,
      neuter_rate: 0,
    });
    vi.stubGlobal("uni", { request: requestMock });

    await expect(getCatStats("token-1")).resolves.toMatchObject({
      total_cats: 0,
      neuter_rate: 0,
    });

    expect(requestMock).toHaveBeenCalledWith(
      expect.objectContaining({
        method: "GET",
        url: expect.stringContaining("/cats/stats"),
        header: expect.objectContaining({
          Authorization: "Bearer token-1",
        }),
      }),
    );
  });

  it("requests filter options", async () => {
    const requestMock = mockSuccess({
      filter_options: [],
      sort_options: [{ value: "last_seen_desc", label: "最近出现" }],
    });
    vi.stubGlobal("uni", { request: requestMock });

    await expect(getCatFilterOptions("token-1")).resolves.toMatchObject({
      sort_options: [{ value: "last_seen_desc", label: "最近出现" }],
    });

    expect(requestMock).toHaveBeenCalledWith(
      expect.objectContaining({
        method: "GET",
        url: expect.stringContaining("/cats/filter-options"),
      }),
    );
  });

  it("requests cat list with search filters and pagination", async () => {
    const requestMock = mockSuccess({
      items: [],
      page: 1,
      page_size: 20,
      total: 0,
      has_more: false,
    });
    vi.stubGlobal("uni", { request: requestMock });

    await getCats("token-1", {
      keyword: "小橘",
      filter_key: "health_status",
      filter_value: "watching",
      sort: "last_seen_desc",
      page: 1,
      page_size: 20,
      unused: "",
    });

    expect(requestMock).toHaveBeenCalledWith(
      expect.objectContaining({
        method: "GET",
        url: expect.stringContaining("/cats"),
        data: {
          keyword: "小橘",
          filter_key: "health_status",
          filter_value: "watching",
          sort: "last_seen_desc",
          page: 1,
          page_size: 20,
        },
      }),
    );
  });
});
