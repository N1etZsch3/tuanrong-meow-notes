import { describe, expect, it, vi } from "vitest";

import {
  getTitleCatalog,
  resignMyTitle,
  setMemberTitle,
  transferPresident,
} from "@/api/titles";

function stubSuccessfulRequest(data: unknown) {
  const requestMock = vi.fn((options: UniNamespace.RequestOptions) => {
    options.success?.({
      statusCode: 200,
      data: { code: 0, message: "ok", data, trace_id: "trace-titles" },
      header: {},
      cookies: [],
    } as UniNamespace.RequestSuccessCallbackResult);
  });
  vi.stubGlobal("uni", { request: requestMock });
  return requestMock;
}

describe("titles api", () => {
  it("loads the independent title slot catalog", async () => {
    const requestMock = stubSuccessfulRequest({ items: [] });
    await expect(getTitleCatalog("token")).resolves.toEqual({ items: [] });
    expect(requestMock).toHaveBeenCalledWith(
      expect.objectContaining({ method: "GET", url: expect.stringContaining("/admin/titles") }),
    );
  });

  it("grants, transfers, and resigns titles through dedicated endpoints", async () => {
    const requestMock = stubSuccessfulRequest({ title: null });
    await setMemberTitle("token", "member 1", "care_head");
    await transferPresident("token", "member-2");
    await resignMyTitle("token");

    expect(requestMock).toHaveBeenNthCalledWith(
      1,
      expect.objectContaining({
        method: "PATCH",
        url: expect.stringContaining("/admin/users/member%201/title"),
        data: { title: "care_head" },
      }),
    );
    expect(requestMock).toHaveBeenNthCalledWith(
      2,
      expect.objectContaining({
        method: "POST",
        url: expect.stringContaining("/admin/titles/transfer"),
        data: { successor_id: "member-2" },
      }),
    );
    expect(requestMock).toHaveBeenNthCalledWith(
      3,
      expect.objectContaining({
        method: "POST",
        url: expect.stringContaining("/profile/me/title/resign"),
      }),
    );
  });
});
