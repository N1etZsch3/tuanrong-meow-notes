import { describe, expect, it, vi } from "vitest";

import {
  checkinTask,
  deleteTaskCheckinPhoto,
  deleteSummerFeedingTask,
  getAdminTaskDetail,
  getTaskDetail,
  getTasks,
  publishSummerFeedingTask,
  updateSummerFeedingTaskStatus,
  updateSummerFeedingTask,
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

  it("requests task detail scoped to a child execution date", async () => {
    const requestMock = mockSuccess({ task_id: "task-1", detail_scope: "execution" });
    vi.stubGlobal("uni", { request: requestMock });

    await expect(
      getTaskDetail("token-1", "task-1", { execution_date_id: "execution-1" }),
    ).resolves.toMatchObject({
      task_id: "task-1",
      detail_scope: "execution",
    });

    expect(requestMock).toHaveBeenCalledWith(
      expect.objectContaining({
        method: "GET",
        url: expect.stringContaining("/tasks/task-1"),
        data: {
          execution_date_id: "execution-1",
        },
      }),
    );
  });

  it("requests admin editable task detail by task id", async () => {
    const requestMock = mockSuccess({ task_id: "task-1", title: "北区投喂" });
    vi.stubGlobal("uni", { request: requestMock });

    await expect(getAdminTaskDetail("admin-token", "task-1")).resolves.toMatchObject({
      task_id: "task-1",
    });

    expect(requestMock).toHaveBeenCalledWith(
      expect.objectContaining({
        method: "GET",
        url: expect.stringContaining("/admin/tasks/task-1"),
        header: expect.objectContaining({
          Authorization: "Bearer admin-token",
        }),
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
          tencent_poi_id: "7554185223751732838",
          tencent_poi_name: "湖北师范大学教育大楼",
          tencent_poi_address: "湖北省黄石市黄石港区",
          tencent_poi_category: "教育学校:大学",
          tencent_poi_lng: 115.0617,
          tencent_poi_lat: 30.2311,
          tencent_poi_distance_meters: 42,
          tencent_poi_match_method: "admin_selected",
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
            tencent_poi_id: "7554185223751732838",
            tencent_poi_name: "湖北师范大学教育大楼",
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

  it("updates a summer feeding task with edited dates, location and photos", async () => {
    const requestMock = mockSuccess({
      task_id: "task-1",
      updated_at: "2026-07-02T12:00:00+08:00",
    });
    vi.stubGlobal("uni", { request: requestMock });

    await updateSummerFeedingTask(
      "admin-token",
      "task-1",
      {
        title: "学生宿舍区北侧喂食点",
        description: "补粮、换水并观察食盆状态",
        required_items: "猫粮、水",
        execute_dates: ["2026-07-02", "2026-07-09"],
        map_point: {
          location_name: "学生宿舍区北侧喂食点",
          location_detail: "靠近教学楼B",
          lng: 115.061742,
          lat: 30.22532684,
          route_instruction: "从教学楼B后方小路进入",
          tencent_poi_id: "7554185223751732838",
          tencent_poi_name: "湖北师范大学教育大楼",
          tencent_poi_address: "湖北省黄石市黄石港区",
          tencent_poi_category: "教育学校:大学",
          tencent_poi_lng: 115.0617,
          tencent_poi_lat: 30.2311,
          tencent_poi_distance_meters: 42,
          tencent_poi_match_method: "admin_selected",
        },
        photos: [
          {
            file_id: "asset-1",
            file_url: "/uploads/task/asset-1.jpg",
            thumbnail_url: "/uploads/task/asset-1-thumb.jpg",
            is_cover: true,
          },
        ],
      },
    );

    expect(requestMock).toHaveBeenCalledWith(
      expect.objectContaining({
        method: "PATCH",
        url: expect.stringContaining("/admin/tasks/task-1"),
        data: expect.objectContaining({
          execute_dates: ["2026-07-02", "2026-07-09"],
          map_point: expect.objectContaining({
            tencent_poi_id: "7554185223751732838",
          }),
          photos: [expect.objectContaining({ file_id: "asset-1" })],
        }),
      }),
    );
  });

  it("updates a summer feeding task status from the admin edit flow", async () => {
    const requestMock = mockSuccess({
      task_id: "task-1",
      status: "completed",
      updated_at: "2026-07-02T12:30:00+08:00",
    });
    vi.stubGlobal("uni", { request: requestMock });

    await updateSummerFeedingTaskStatus("admin-token", "task-1", {
      status: "completed",
      reason: "管理员在任务编辑页手动调整完成状态",
    });

    expect(requestMock).toHaveBeenCalledWith(
      expect.objectContaining({
        method: "PATCH",
        url: expect.stringContaining("/admin/tasks/task-1/status"),
        data: {
          status: "completed",
          reason: "管理员在任务编辑页手动调整完成状态",
        },
      }),
    );
  });

  it("soft deletes a summer feeding task from the admin edit flow", async () => {
    const requestMock = mockSuccess({
      task_id: "task-1",
      deleted_at: "2026-07-02T12:30:00+08:00",
    });
    vi.stubGlobal("uni", { request: requestMock });

    await deleteSummerFeedingTask("admin-token", "task-1");

    expect(requestMock).toHaveBeenCalledWith(
      expect.objectContaining({
        method: "DELETE",
        url: expect.stringContaining("/admin/tasks/task-1"),
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

  it("soft deletes a task checkin photo through the task business API", async () => {
    const requestMock = mockSuccess({
      photo_id: "photo-1",
      deleted_at: "2026-07-02T12:30:00+08:00",
    });
    vi.stubGlobal("uni", { request: requestMock });

    await deleteTaskCheckinPhoto("token-1", "task-1", "photo-1");

    expect(requestMock).toHaveBeenCalledWith(
      expect.objectContaining({
        method: "DELETE",
        url: expect.stringContaining("/tasks/task-1/checkin-photos/photo-1"),
        header: expect.objectContaining({
          Authorization: "Bearer token-1",
        }),
      }),
    );
  });
});
