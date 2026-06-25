import { describe, expect, it, vi } from "vitest";

import {
  getFavoriteCats,
  getMeDashboard,
  getMyCheckins,
  getMyObservations,
  getMyTasks,
} from "@/api/me";

function mockSuccessfulRequest(data: unknown) {
  return vi.fn((options: UniNamespace.RequestOptions) => {
    options.success?.({
      statusCode: 200,
      data: {
        code: 0,
        message: "success",
        data,
        trace_id: "trace-me",
      },
      header: {},
      cookies: [],
    } as UniNamespace.RequestSuccessCallbackResult);
  });
}

describe("me api", () => {
  it("gets the personal center dashboard", async () => {
    const requestMock = mockSuccessfulRequest({
      profile: {
        user_id: "u1",
        student_no: "trmx0001",
        meow_no: "trmx0001",
        nickname: "Nietzsche",
        avatar_url: null,
        department: "宣传部",
        role: "admin",
        show_admin_entry: true,
      },
      stats: {
        total_completed_tasks: 0,
        monthly_completed_tasks: 0,
        current_in_progress_tasks: 0,
        total_observation_records: 0,
        favorite_cats: 0,
      },
      todo: {
        unread_notifications: 0,
        pending_assignments: 0,
        today_duty_count: 0,
        in_progress_task_count: 0,
      },
      recent_tasks: [],
      recent_notifications: [],
    });
    vi.stubGlobal("uni", { request: requestMock });

    await expect(getMeDashboard("token-1")).resolves.toMatchObject({
      profile: { meow_no: "trmx0001", show_admin_entry: true },
    });
    expect(requestMock).toHaveBeenCalledWith(
      expect.objectContaining({
        method: "GET",
        url: expect.stringContaining("/me/dashboard"),
        header: expect.objectContaining({ Authorization: "Bearer token-1" }),
      }),
    );
  });

  it("gets empty record pages through stable endpoints", async () => {
    const page = {
      items: [],
      page: 1,
      page_size: 20,
      total: 0,
      has_more: false,
    };
    const requestMock = mockSuccessfulRequest(page);
    vi.stubGlobal("uni", { request: requestMock });

    await expect(getMyTasks("token-1")).resolves.toEqual(page);
    await expect(getMyCheckins("token-1")).resolves.toEqual(page);
    await expect(getMyObservations("token-1")).resolves.toEqual(page);
    await expect(getFavoriteCats("token-1")).resolves.toEqual(page);

    expect(requestMock).toHaveBeenNthCalledWith(
      1,
      expect.objectContaining({ url: expect.stringContaining("/me/tasks") }),
    );
    expect(requestMock).toHaveBeenNthCalledWith(
      4,
      expect.objectContaining({ url: expect.stringContaining("/me/favorite-cats") }),
    );
  });
});
