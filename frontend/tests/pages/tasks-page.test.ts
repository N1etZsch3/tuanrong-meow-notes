import { describe, expect, it } from "vitest";

import adminCreateTaskSource from "../../src/pages/admin/tasks/create.vue?raw";
import adminTaskLocationSource from "../../src/pages/admin/tasks/location.vue?raw";
import taskDetailSource from "../../src/pages/tasks/detail.vue?raw";
import taskIndexSource from "../../src/pages/tasks/index.vue?raw";
import pagesJson from "../../src/pages.json?raw";
import {
  DEFAULT_REQUIRED_ITEMS,
  buildSummerFeedingTaskPayload,
  buildUploadedTaskPhoto,
  createDefaultFeedingTaskDraft,
  formatExecutionDateSummary,
  getTaskListStatusLabel,
  validatePublishDraft,
} from "@/pages/tasks/task-page";

describe("summer feeding task pages", () => {
  it("registers task list, task detail, publish and map location pages", () => {
    expect(pagesJson).toContain("pages/tasks/index");
    expect(pagesJson).toContain("pages/tasks/detail");
    expect(pagesJson).toContain("pages/admin/tasks/create");
    expect(pagesJson).toContain("pages/admin/tasks/location");
  });

  it("uses real task list and detail pages instead of the development placeholder", () => {
    expect(taskIndexSource).toContain("getTasks");
    expect(taskIndexSource).toContain("/pages/tasks/detail?task_id=");
    expect(taskIndexSource).not.toContain("任务模块建设中");
    expect(taskDetailSource).toContain("getTaskDetail");
    expect(taskDetailSource).toContain("完成投喂");
  });

  it("renders task detail photos in a five-second swipeable carousel", () => {
    expect(taskDetailSource).toContain("<swiper");
    expect(taskDetailSource).toContain("<swiper-item");
    expect(taskDetailSource).toContain("heroPhotos");
    expect(taskDetailSource).toContain(":autoplay=\"true\"");
    expect(taskDetailSource).toContain(":interval=\"5000\"");
    expect(taskDetailSource).toContain(":circular=\"true\"");
  });

  it("shows an admin edit shortcut beside the task detail title", () => {
    expect(taskDetailSource).toContain("canAdminEditTask");
    expect(taskDetailSource).toContain('class="task-edit-button"');
    expect(taskDetailSource).toContain("goEditTask");
    expect(taskDetailSource).toContain("/pages/admin/tasks/create?mode=edit&task_id=");
  });

  it("retries transient task detail loading failures and exposes manual retry", () => {
    expect(taskDetailSource).toContain("loadTaskDetail({ retry: true })");
    expect(taskDetailSource).toContain("retryTaskDetail");
    expect(taskDetailSource).toContain("重新加载");
  });

  it("uses cached task list data on tab re-entry and invalidates after checkin", () => {
    expect(taskIndexSource).toContain("getCachedTaskList");
    expect(taskIndexSource).toContain("setCachedTaskList");
    expect(taskIndexSource).toContain("silent: true");
    expect(taskDetailSource).toContain("clearTaskListCache");
  });

  it("keeps the publish form fields requested for summer feeding tasks", () => {
    for (const label of [
      "任务标题",
      "任务说明",
      "时间",
      "位置",
      "所需物资",
      "任务点图片",
      "路线说明",
    ]) {
      expect(adminCreateTaskSource).toContain(label);
    }
    expect(adminCreateTaskSource).toContain("publishSummerFeedingTask");
    expect(adminCreateTaskSource).toContain("updateSummerFeedingTask");
    expect(adminCreateTaskSource).toContain("getAdminTaskDetail");
    expect(adminCreateTaskSource).toContain("编辑喂食任务");
    expect(adminCreateTaskSource).toContain("uploadImage");
    expect(adminCreateTaskSource).toContain("map_point_scene");
  });

  it("reuses the publish form as an admin edit form with existing task data", () => {
    expect(adminCreateTaskSource).toContain("editTaskId");
    expect(adminCreateTaskSource).toContain("applyTaskDetailToForm");
    expect(adminCreateTaskSource).toContain("task.execution_dates.map");
    expect(adminCreateTaskSource).toContain("task.photos.map");
    expect(adminCreateTaskSource).toContain("removeTaskPhoto");
    expect(adminCreateTaskSource).toContain("mode=edit");
  });

  it("lets admins update task completion status from the reused edit form", () => {
    expect(adminCreateTaskSource).toContain("任务完成状态");
    expect(adminCreateTaskSource).toContain("statusOptions");
    expect(adminCreateTaskSource).toContain("form.status");
    expect(adminCreateTaskSource).toContain("updateSummerFeedingTaskStatus");
    expect(adminCreateTaskSource).toContain("submitStatusChangeIfNeeded");
  });

  it("starts map-page navigation from the task detail navigation button", () => {
    expect(taskDetailSource).toContain("goNavigateToTaskPoint");
    expect(taskDetailSource).toContain("MAP_PENDING_NAVIGATION_STORAGE_KEY");
    expect(taskDetailSource).toContain("uni.setStorageSync");
    expect(taskDetailSource).toContain('uni.switchTab({ url: "/pages/index/index" })');
    expect(taskDetailSource).not.toContain("导航后续接入");
  });

  it("shows associated tencent poi metadata on task detail when available", () => {
    expect(taskDetailSource).toContain("associatedPoi");
    expect(taskDetailSource).toContain("公共地点");
    expect(taskDetailSource).toContain("associatedPoi.category");
    expect(taskDetailSource).toContain("associatedPoi.address");
  });

  it("uses a custom multi-select calendar instead of the native date picker", () => {
    expect(adminCreateTaskSource).not.toContain('<picker mode="date"');
    expect(adminCreateTaskSource).toContain('class="calendar-overlay"');
    expect(adminCreateTaskSource).toContain('class="calendar-grid"');
    expect(adminCreateTaskSource).toContain("toggleCalendarDate");
    expect(adminCreateTaskSource).toContain("confirmCalendarDates");
    expect(adminCreateTaskSource).toContain("calendarDraftDates");
  });

  it("does not expose task publishing from the task tab", () => {
    expect(taskIndexSource).not.toContain('class="publish-toolbar"');
    expect(taskIndexSource).not.toContain('class="publish-button"');
    expect(taskIndexSource).not.toContain("function goPublish");
    expect(taskIndexSource).not.toContain("/pages/admin/tasks/create");
  });

  it("uses a native mini program map for publish-time task point selection", () => {
    expect(adminTaskLocationSource).toContain("<map");
    expect(adminTaskLocationSource).toContain("@tap=\"selectLocationFromMap\"");
    expect(adminTaskLocationSource).toContain("uni.setStorageSync");
    expect(adminTaskLocationSource).toContain("确认此位置");
    expect(adminTaskLocationSource).toContain("getNearbyMapPois");
    expect(adminTaskLocationSource).toContain("associatedPoiCandidates");
    expect(adminTaskLocationSource).toContain("associateSelectedPoi");
    expect(adminTaskLocationSource).toContain("clearAssociatedPoi");
    expect(adminTaskLocationSource).not.toContain("自选喂食点");
    expect(adminTaskLocationSource).not.toContain("请补充具体参照物");
  });

  it("defaults materials to cat food and water and builds the publish payload", () => {
    const draft = createDefaultFeedingTaskDraft();
    draft.title = "学生宿舍区北侧喂食点";
    draft.description = "补粮、换水并观察食盆状态";
    draft.execute_dates = ["2026-07-02", "2026-07-05"];
    draft.location = {
      location_name: "学生宿舍区北侧喂食点",
      location_detail: "靠近教学楼B",
      lng: 115.061742,
      lat: 30.22532684,
      route_instruction: "",
    };
    draft.photos = [
      {
        file_id: "asset-1",
        file_url: "/uploads/task/asset-1.jpg",
        thumbnail_url: "/uploads/task/asset-1-thumb.jpg",
      },
    ];

    expect(DEFAULT_REQUIRED_ITEMS).toBe("猫粮、水");
    expect(validatePublishDraft(draft)).toEqual({ valid: true });
    expect(buildSummerFeedingTaskPayload(draft)).toMatchObject({
      title: "学生宿舍区北侧喂食点",
      required_items: "猫粮、水",
      execute_dates: ["2026-07-02", "2026-07-05"],
      map_point: {
        location_name: "学生宿舍区北侧喂食点",
        route_instruction: "",
      },
      photos: [
        {
          file_id: "asset-1",
          photo_type: "cover",
          is_cover: true,
        },
      ],
    });
  });

  it("validates missing publish fields before submit", () => {
    expect(validatePublishDraft(createDefaultFeedingTaskDraft())).toEqual({
      valid: false,
      message: "请输入任务标题",
    });

    const draft = createDefaultFeedingTaskDraft();
    draft.title = "学生宿舍区北侧喂食点";
    draft.description = "补粮、换水并观察食盆状态";
    draft.execute_dates = ["2026-07-02"];
    draft.photos = [
      {
        file_id: "asset-1",
        file_url: "/uploads/task/asset-1.jpg",
        thumbnail_url: "/uploads/task/asset-1-thumb.jpg",
      },
    ];
    draft.location = {
      location_name: "",
      location_detail: "",
      lng: 115.061742,
      lat: 30.22532684,
      route_instruction: "",
    };

    expect(validatePublishDraft(draft)).toEqual({
      valid: false,
      message: "请填写喂食点名称",
    });

    draft.location.location_name = "学生宿舍区北侧喂食点";
    expect(validatePublishDraft(draft)).toEqual({
      valid: false,
      message: "请填写位置补充说明",
    });
  });

  it("formats execution date summaries for the publish card", () => {
    expect(formatExecutionDateSummary([])).toBe("请选择日期");
    expect(formatExecutionDateSummary(["2026-07-02", "2026-07-05"])).toBe(
      "已选 2 个日期 | 7月2日、7月5日",
    );
  });

  it("maps uploaded assets into task photo refs", () => {
    expect(
      buildUploadedTaskPhoto({
        asset_id: "asset-1",
        default_url: "/uploads/task/asset-1.jpg",
        default_thumb_url: "/uploads/task/asset-1-thumb.jpg",
      }),
    ).toEqual({
      file_id: "asset-1",
      file_url:
        "http://localhost:8000/api/v1/files/assets/asset-1/content?scene=task_detail_full",
      thumbnail_url:
        "http://localhost:8000/api/v1/files/assets/asset-1/content?scene=task_list_cover",
    });
  });

  it("shows completed execution status in the task list status pill", () => {
    expect(
      getTaskListStatusLabel({
        status_label: "进行中",
        current_execution: {
          status: "completed",
        },
      }),
    ).toBe("已完成");

    expect(
      getTaskListStatusLabel({
        status_label: "进行中",
        current_execution: {
          status: "pending",
        },
      }),
    ).toBe("进行中");
  });
});
