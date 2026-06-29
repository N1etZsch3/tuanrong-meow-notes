import { describe, expect, it, vi } from "vitest";

import {
  checkinTask,
  getTaskDetail,
  getTasks,
  publishSummerFeedingTask,
} from "@/api/tasks";

function mockSuccess(data: unknown) {
  return vi.fn((options: UniNamespace.RequestOptions) => {
    options.success?.({
      statusCode: 200,
      data: {
        code: 0,
        message: "success",
        data,
        trace_id: "trace-tasks",
      },
      header: {},
      cookies: [],
    } as UniNamespace.RequestSuccessCallbackResult);
  });
}

describe("tasks api", () => {
  it("requests summer feeding tasks with filters", async () => {
    const requestMock = mockSuccess({ items: [], page: 1, page_size: 20, total: 0 });
    vi.stubGlobal("uni", { request: requestMock });

    await getTasks("token-1", {
      task_type: "feeding",
      status: "in_progress",
      only_today: true,
      keyword: "",
      page: 1,
    });

    expect(requestMock).toHaveBeenCalledWith(
      expect.objectContaining({
        method: "GET",
        url: expect.stringContaining("/tasks"),
        data: {
          task_type: "feeding",
          status: "in_progress",
          only_today: true,
          page: 1,
        },
        header: expect.objectContaining({
          Authorization: "Bearer token-1",
        }),
      }),
    );
  });

  it("requests task detail by task id", async () => {
    const requestMock = mockSuccess({ task_id: "task-1", title: "北区投喂" });
    vi.stubGlobal("uni", { request: requestMock });

    await expect(getTaskDetail("token-1", "task-1")).resolves.toMatchObject({
      task_id: "task-1",
    });

    expect(requestMock).toHaveBeenCalledWith(
      expect.objectContaining({
        method: "GET",
        url: expect.stringContaining("/tasks/task-1"),
      }),
    );
  });

  it("publishes a summer feeding task with materials, route and task point photo", async () => {
    const requestMock = mockSuccess({
      task_id: "task-1",
      task_no: "TF202607020001",
      map_point_id: "point-1",
      execution_date_count: 2,
      photo_count: 1,
    });
    vi.stubGlobal("uni", { request: requestMock });

    await publishSummerFeedingTask(
      {
        title: "学生宿舍区北侧喂食点",
        description: "补粮、换水并观察食盆状态",
        required_items: "猫粮、水",
        execute_dates: ["2026-07-02", "2026-07-05"],
        map_point: {
          location_name: "学生宿舍区北侧喂食点",
          location_detail: "靠近教学楼B",
          lng: 115.061742,
          lat: 30.22532684,
          route_instruction: "",
        },
        photos: [
          {
            file_id: "asset-1",
            file_url: "/uploads/task/asset-1.jpg",
            thumbnail_url: "/uploads/task/asset-1-thumb.jpg",
            photo_type: "cover",
            is_cover: true,
          },
        ],
      },
      "admin-token",
    );

    expect(requestMock).toHaveBeenCalledWith(
      expect.objectContaining({
        method: "POST",
        url: expect.stringContaining("/admin/tasks/summer-feeding"),
        data: expect.objectContaining({
          required_items: "猫粮、水",
          map_point: expect.objectContaining({
            route_instruction: "",
          }),
          photos: [
            expect.objectContaining({
              file_id: "asset-1",
              is_cover: true,
            }),
          ],
        }),
      }),
    );
  });

  it("submits a task checkin with photos", async () => {
    const requestMock = mockSuccess({
      execution_date_id: "execution-1",
      status: "completed",
    });
    vi.stubGlobal("uni", { request: requestMock });

    await checkinTask(
      "token-1",
      "task-1",
      {
        execute_date: "2026-07-02",
        is_completed: true,
        process_result: "已补粮换水",
        remark: "猫粮余量充足",
        photos: [
          {
            file_id: "asset-2",
            file_url: "/uploads/checkin/asset-2.jpg",
            thumbnail_url: "/uploads/checkin/asset-2-thumb.jpg",
          },
        ],
      },
    );

    expect(requestMock).toHaveBeenCalledWith(
      expect.objectContaining({
        method: "POST",
        url: expect.stringContaining("/tasks/task-1/checkins"),
        data: expect.objectContaining({
          photos: [expect.objectContaining({ file_id: "asset-2" })],
        }),
      }),
    );
  });
});
