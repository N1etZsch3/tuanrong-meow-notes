import { describe, expect, it } from "vitest";

import adminCreateTaskSource from "../../src/pages/admin/tasks/create.vue?raw";
import adminTaskLocationSource from "../../src/pages/admin/tasks/location.vue?raw";
import taskDetailSource from "../../src/pages/tasks/detail.vue?raw";
import meowNotesSource from "../../src/pages/tasks/index.vue?raw";
import taskListSource from "../../src/pages/tasks/list.vue?raw";
import pagesJson from "../../src/pages.json?raw";
import {
  DEFAULT_REQUIRED_ITEMS,
  buildSummerFeedingTaskPayload,
  buildUploadedTaskPhoto,
  buildTaskDateFilterQuery,
  createDefaultFeedingTaskDraft,
  formatChinaDateTime,
  formatExecutionDateSummary,
  getTaskPhotoDisplayUrl,
  getTaskDetailActionState,
  getTaskListStatusLabel,
  getTaskStatusTone,
  validatePublishDraft,
} from "@/pages/tasks/task-page";

function extractFunctionSource(source: string, functionName: string): string {
  const normalStart = source.indexOf(`function ${functionName}`);
  const asyncStart = source.indexOf(`async function ${functionName}`);
  const start = normalStart >= 0 ? normalStart : asyncStart;
  expect(start).toBeGreaterThanOrEqual(0);
  const bodyStart = source.indexOf("{", start);
  expect(bodyStart).toBeGreaterThan(start);

  let depth = 0;
  for (let index = bodyStart; index < source.length; index += 1) {
    const char = source[index];
    if (char === "{") {
      depth += 1;
    } else if (char === "}") {
      depth -= 1;
      if (depth === 0) {
        return source.slice(start, index + 1);
      }
    }
  }

  return source.slice(start);
}

function extractCssRule(source: string, selector: string): string {
  const start = source.indexOf(`${selector} {`);
  expect(start).toBeGreaterThanOrEqual(0);
  const bodyStart = source.indexOf("{", start);
  expect(bodyStart).toBeGreaterThan(start);

  let depth = 0;
  for (let index = bodyStart; index < source.length; index += 1) {
    const char = source[index];
    if (char === "{") {
      depth += 1;
    } else if (char === "}") {
      depth -= 1;
      if (depth === 0) {
        return source.slice(start, index + 1);
      }
    }
  }

  return source.slice(start);
}

describe("summer feeding task pages", () => {
  it("registers task list, task detail, publish and map location pages", () => {
    expect(pagesJson).toContain("pages/tasks/index");
    expect(pagesJson).toContain("pages/tasks/list");
    expect(pagesJson).toContain("pages/tasks/detail");
    expect(pagesJson).toContain("pages/admin/tasks/create");
    expect(pagesJson).toContain("pages/admin/tasks/location");
  });

  it("turns the task tab into a Meow Notes bookshelf entry page", () => {
    expect(meowNotesSource).toContain("喵记");
    expect(meowNotesSource).toContain("noteBooks");
    expect(meowNotesSource).toContain('class="shelf"');
    expect(meowNotesSource).toContain('class="shelf__inner"');
    expect(meowNotesSource).toContain('class="cell"');
    expect(meowNotesSource).toContain('class="cell__books"');
    expect(meowNotesSource).toContain('class="board"');
    expect(meowNotesSource).toContain('class="book"');
    expect(meowNotesSource).toContain("book--ribbon");
    expect(meowNotesSource).toContain("--book-w");
    expect(meowNotesSource).toContain("--frame-1");
    expect(meowNotesSource).toContain("任务");
    expect(meowNotesSource).toContain("物资");
    expect(meowNotesSource).toContain("校园地标");
    expect(meowNotesSource).toContain("药品");
    expect(meowNotesSource).toContain('/pages/tasks/list');
    expect(meowNotesSource).toContain('/pages/supplies/index');
    expect(meowNotesSource).toContain('/pages/landmarks/index');
    expect(meowNotesSource).toContain('/pages/medicines/index');
    expect(meowNotesSource).toContain("素材/svg/喵记/任务.svg");
    expect(meowNotesSource).toContain("素材/svg/喵记/物资仓库.svg");
    expect(meowNotesSource).toContain("素材/svg/喵记/地标.svg");
    expect(meowNotesSource).toContain("素材/svg/喵记/药品.svg");
    expect(meowNotesSource).not.toContain("素材/png/地图点/日常任务.png");
    expect(meowNotesSource).not.toContain("素材/png/地图点/物资点.png");
    expect(meowNotesSource).not.toContain("素材/png/地图点/地标.png");
    expect(meowNotesSource).not.toContain("素材/png/地图点/医疗任务.png");
    expect(meowNotesSource).not.toContain("药品管理暂未开放");
    expect(meowNotesSource).not.toContain("summary-strip");
    expect(meowNotesSource).not.toContain("最近新增");
    expect(meowNotesSource).not.toContain("getTasks");
  });

  it("opens Meow Notes books immediately without unused header buttons", () => {
    expect(meowNotesSource).not.toContain("head-actions");
    expect(meowNotesSource).not.toContain("round-action");
    expect(meowNotesSource).not.toContain("goSearch");
    expect(meowNotesSource).not.toContain("showMore");
    expect(meowNotesSource).not.toContain('hover-class="book--hover"');
    expect(meowNotesSource).not.toContain(".book--hover");
    expect(meowNotesSource).toContain("uni.navigateTo({ url: book.url })");
  });

  it("adds shelf pagination for future Meow Notes book pages", () => {
    const pagerRule = extractCssRule(meowNotesSource, ".shelf-pager");

    expect(meowNotesSource).toContain("bookPages");
    expect(meowNotesSource).toContain("currentBookRows");
    expect(meowNotesSource).toContain("currentShelfPageLabel");
    expect(meowNotesSource).toContain("goPreviousBookPage");
    expect(meowNotesSource).toContain("goNextBookPage");
    expect(meowNotesSource).toContain('class="shelf-pager"');
    expect(meowNotesSource).toContain('class="pager-button"');
    expect(meowNotesSource).toContain('class="pager-count"');
    expect(meowNotesSource).toContain('v-for="(row, rowIndex) in currentBookRows"');
    expect(meowNotesSource).toContain("恢复分页外框");
    expect(pagerRule).not.toContain("border:");
    expect(pagerRule).not.toContain("background:");
    expect(pagerRule).not.toContain("box-shadow:");
  });

  it("uses the task-list title treatment on the Meow Notes tab page", () => {
    const titleRule = extractCssRule(meowNotesSource, ".title-text");
    const subtitleRule = extractCssRule(meowNotesSource, ".title-subtitle");

    expect(titleRule).toContain("color: #111827");
    expect(titleRule).toContain("font-size: var(--catmap-page-title-font-size, 52rpx)");
    expect(titleRule).toContain("font-weight: 900");
    expect(subtitleRule).toContain("color: #6b7280");
    expect(subtitleRule).toContain("font-size: var(--catmap-page-title-subtitle-size, 24rpx)");
    expect(subtitleRule).toContain("font-weight: 700");
  });

  it("treats the task list as a child page without the bottom tab bar", () => {
    expect(taskListSource).toContain('class="back-button"');
    expect(taskListSource).toContain("function goBack");
    expect(taskListSource).toContain("uni.navigateBack()");
    expect(taskListSource).not.toContain("<AppTabBar");
    expect(taskListSource).not.toContain("AppTabBar from");
    expect(taskListSource).not.toContain('active-key="tasks"');
  });

  it("keeps the Meow Notes shelf and pager responsive across phone sizes", () => {
    const shelfRule = extractCssRule(meowNotesSource, ".shelf");
    const innerRule = extractCssRule(meowNotesSource, ".shelf__inner");
    const cellRule = extractCssRule(meowNotesSource, ".cell");
    const cellBooksRule = extractCssRule(meowNotesSource, ".cell__books");
    const bookRule = extractCssRule(meowNotesSource, ".book");
    const labelRule = extractCssRule(meowNotesSource, ".book__label");
    const labelTextRule = extractCssRule(meowNotesSource, ".book__label text");
    const pagerRule = extractCssRule(meowNotesSource, ".shelf-pager");

    expect(shelfRule).toContain("--shelf-w: 680rpx");
    expect(shelfRule).toContain("--book-w: 150rpx");
    expect(shelfRule).toContain("--book-h: 242rpx");
    expect(shelfRule).toContain("width: var(--shelf-w)");
    expect(shelfRule).toContain("max-width: calc(100vw - 56rpx)");
    expect(shelfRule).toContain("height: calc(100vh - 500rpx)");
    expect(shelfRule).toContain("max-height: 1064rpx");
    expect(shelfRule).not.toContain("max-width: 388px");
    expect(shelfRule).not.toContain("--book-w: 90px");
    expect(innerRule).toContain("height: 100%");
    expect(innerRule).toContain("display: flex");
    expect(cellRule).toContain("flex: 1 1 0");
    expect(cellRule).toContain("min-height: 0");
    expect(cellBooksRule).toContain("flex: 1 1 auto");
    expect(cellBooksRule).toContain("height: auto");
    expect(bookRule).toContain("max-height: calc(100% - 20rpx)");
    expect(labelRule).toContain("max-width: 128rpx");
    expect(labelRule).toContain("font-size: 25rpx");
    expect(labelTextRule).not.toContain("text-overflow: ellipsis");
    expect(pagerRule).toContain("width: var(--shelf-w)");
    expect(pagerRule).toContain("max-width: calc(100vw - 56rpx)");
  });

  it("styles the custom Meow Notes svg icons consistently on book covers", () => {
    const iconRule = extractCssRule(meowNotesSource, ".book__icon");

    expect(iconRule).toContain("width: 78rpx");
    expect(iconRule).toContain("height: 78rpx");
    expect(iconRule).toContain("object-fit: contain");
    expect(iconRule).toContain("filter:");
  });

  it("uses real task list and detail pages instead of the development placeholder", () => {
    expect(taskListSource).toContain("getTasks");
    expect(taskListSource).toContain("/pages/tasks/detail?task_id=");
    expect(taskListSource).not.toContain("任务模块建设中");
    expect(taskDetailSource).toContain("getTaskDetail");
    expect(taskDetailSource).toContain("submitTaskRecord");
  });

  it("opens a supply-style record modal from the bottom record action", () => {
    expect(taskDetailSource).toContain('@tap="openRecordForm"');
    expect(taskDetailSource).toContain("任务记录");
    expect(taskDetailSource).toContain('v-if="recordFormVisible"');
    expect(taskDetailSource).toContain('v-model.trim="recordRemark"');
    expect(taskDetailSource).toContain('placeholder="补充说明，可不填"');
    expect(taskDetailSource).toContain("完成记录");
    expect(taskDetailSource).toContain("remark: recordRemark.value || null");
    expect(taskDetailSource).not.toContain("completeFeedingTask");
  });

  it("opens a record detail modal from completed feed activities", () => {
    expect(taskDetailSource).toContain("记录详情");
    expect(taskDetailSource).toContain('v-if="viewingRecord"');
    expect(taskDetailSource).toContain('@tap="openRecordDetail(activity)"');
    expect(taskDetailSource).toContain("hasActivityRecord");
    expect(taskDetailSource).toContain("execution_completed");
    expect(taskDetailSource).toContain("task.value?.checkins");
  });

  it("renders task detail photos in a five-second swipeable carousel", () => {
    expect(taskDetailSource).toContain("<swiper");
    expect(taskDetailSource).toContain("<swiper-item");
    expect(taskDetailSource).toContain("heroPhotos");
    expect(taskDetailSource).toContain(":autoplay=\"true\"");
    expect(taskDetailSource).toContain(":interval=\"5000\"");
    expect(taskDetailSource).toContain(":circular=\"true\"");
  });

  it("lets admins drag task point photos to change the cover order", () => {
    expect(adminCreateTaskSource).toContain("SortableImageGrid");
    expect(adminCreateTaskSource).toContain('@reorder="reorderTaskPhoto"');
    expect(adminCreateTaskSource).toContain("moveArrayItem(form.photos");
  });

  it("opens task detail photos with the native image preview", () => {
    expect(taskDetailSource).toContain("@tap=\"openTaskPhotoPreview(photo.photo_id)\"");
    expect(taskDetailSource).toContain("@tap=\"openRecordDetailPhotoPreview(photo)\"");
    expect(taskDetailSource).toContain("openImagePreview");
    expect(taskDetailSource).toContain("uni.previewImage({");
    expect(taskDetailSource).toContain("urls: resolvedUrls");
    expect(taskDetailSource).not.toContain("ImagePreviewModal");
    expect(taskDetailSource).not.toContain("imagePreviewVisible");
  });

  it("uploads record photos inside the record modal and renders them in the dynamic record detail", () => {
    expect(taskDetailSource).toContain("chooseCheckinPhoto");
    expect(taskDetailSource).toContain("pendingCheckinPhotos.length < 3");
    expect(taskDetailSource).toContain("viewingRecord.photos");
    expect(taskDetailSource).not.toContain("displayCheckinPhotos");
    expect(taskDetailSource).not.toContain("confirmUploadCheckinPhotos");
  });

  it("keeps removal controls inside the unsubmitted record form", () => {
    expect(taskDetailSource).toContain("deleteImageAsset");
    expect(taskDetailSource).toContain("removeRecordPhoto");
    expect(taskDetailSource).not.toContain("deleteTaskCheckinPhoto");
    expect(taskDetailSource).not.toContain("confirmDeleteCheckinPhoto");
  });

  it("uses a mini-program-safe png arrow in task list filters", () => {
    expect(taskListSource).toContain("地图点/箭头.png");
    expect(taskListSource).not.toContain("地图点/箭头.svg");
  });

  it("uses a mini-program-safe png marker on the admin location picker map", () => {
    expect(adminTaskLocationSource).toContain("地图点/日常任务红.png");
    expect(adminTaskLocationSource).not.toContain("地图点/日常任务红.svg");
    expect(adminTaskLocationSource).not.toContain("地图点/失败任务.png");
  });

  it("shows an admin edit shortcut beside the task detail title", () => {
    expect(taskDetailSource).toContain("canAdminEditTask");
    expect(taskDetailSource).toContain('class="task-edit-button"');
    expect(taskDetailSource).toContain("goEditTask");
    expect(taskDetailSource).toContain("/pages/admin/tasks/create?mode=edit&task_id=");
    expect(taskDetailSource).toContain("&execution_date_id=${executionDateId.value}");
    expect(adminCreateTaskSource).toContain("updateSummerFeedingTaskExecutionStatus");
    expect(adminCreateTaskSource).toContain("本次子任务完成状态");
    expect(adminCreateTaskSource).toContain("execution_date_id: editExecutionDateId.value");
  });

  it("retries transient task detail loading failures and exposes manual retry", () => {
    expect(taskDetailSource).toContain("loadTaskDetail({ retry: true })");
    expect(taskDetailSource).toContain("retryTaskDetail");
    expect(taskDetailSource).toContain("重新加载");
  });

  it("uses cached task list data on tab re-entry and invalidates after checkin", () => {
    expect(taskListSource).toContain("getCachedTaskList");
    expect(taskListSource).toContain("setCachedTaskList");
    expect(taskListSource).toContain("silent: true");
    expect(taskDetailSource).toContain("clearTaskListCache");
  });

  it("adds task search and three picker filters using the cat library filter layout", () => {
    expect(taskListSource).toContain('class="search-box"');
    expect(taskListSource).toContain('placeholder="搜索任务 / 喂食点 / 位置"');
    expect(taskListSource).toContain("handleSearchConfirm");
    expect(taskListSource).toContain('class="filter-card"');
    expect(taskListSource).toContain("taskTypeOptions");
    expect(taskListSource).toContain("taskStatusOptions");
    expect(taskListSource).toContain("dateFilterOptions");
    expect(taskListSource).toContain("selectedTaskTypeLabel");
    expect(taskListSource).toContain("selectedTaskStatusLabel");
    expect(taskListSource).toContain("selectedDateFilterLabel");
    expect(taskListSource).toContain("任务类型");
    expect(taskListSource).toContain("任务状态");
    expect(taskListSource).toContain("日期");
    expect(taskListSource).toContain("本日");
    expect(taskListSource).toContain("本周");
    expect(taskListSource).toContain("本月");
    expect(taskListSource).toContain("特定日期");
    expect(taskListSource).not.toContain("全部任务类型");
    expect(taskListSource).not.toContain("全部任务状态");
    expect(taskListSource).not.toContain("今日任务");
    expect(taskListSource).not.toContain("刷新");
    expect(taskListSource).not.toContain("toggleToday");
    expect(taskListSource).not.toContain("refreshTasks");
    expect(taskListSource).not.toContain("only_today");
    expect(taskListSource).toContain("clearFilters");
    expect(taskListSource).toContain("keyword: searchKeyword.value.trim()");
    expect(taskListSource).toContain("status: DEFAULT_TASK_STATUS_QUERY");
    expect(taskListSource).toContain("execution_display_status: selectedTaskStatus.value");
  });

  it("renders recurring child execution cards inside each parent task card", () => {
    expect(taskListSource).toContain("display_executions");
    expect(taskListSource).toContain('class="execution-strip"');
    expect(taskListSource).toContain('scroll-x');
    expect(taskListSource).toContain("goExecutionDetail(task.task_id, execution.execution_date_id)");
    expect(taskListSource).toContain("getExecutionDisplayLabel(execution)");
    expect(taskListSource).toContain("getExecutionDisplayClass(execution)");
    expect(taskListSource).toContain("-webkit-line-clamp: 1");
    expect(taskListSource).not.toContain('class="task-location"');
    expect(taskListSource).not.toContain("task.required_items");
  });

  it("supports parent and child scoped task detail pages", () => {
    expect(taskDetailSource).toContain("executionDateId");
    expect(taskDetailSource).toContain("detail_scope");
    expect(taskDetailSource).toContain("isExecutionDetail");
    expect(taskDetailSource).toContain("execution_groups");
    expect(taskDetailSource).toContain("activityExecutionGroups");
    expect(taskDetailSource).toContain('v-for="group in activityExecutionGroups"');
    expect(taskDetailSource).not.toContain('v-for="group in task.execution_groups"');
    expect(taskDetailSource).toContain('class="task-info-panel"');
    expect(taskDetailSource).toContain('class="task-info-section date-section"');
    expect(taskDetailSource).toContain('class="task-info-section address-section"');
    expect(taskDetailSource).not.toContain('class="info-grid"');
    expect(taskDetailSource).toContain('class="execution-date-button"');
    expect(taskDetailSource).toContain("goExecutionDetail(execution.execution_date_id)");
    expect(taskDetailSource).toContain("getTaskDetail(token, taskId.value, {");
    expect(taskDetailSource).toContain("execution_date_id: executionDateId.value");
  });

  it("binds the parent task detail bottom action to the active child execution", () => {
    expect(taskDetailSource).toContain(
      "can_checkin: Boolean(task.value?.actions.can_checkin && currentExecution.value)",
    );
    expect(taskDetailSource).toContain(
      "const canCheckin = computed(() => !primaryActionState.value.disabled)",
    );
    expect(taskDetailSource).not.toContain(
      "isExecutionDetail.value && task.value?.actions.can_checkin",
    );
  });

  it("builds task list date filter query parameters", () => {
    const baseDate = new Date(2026, 6, 2);

    expect(buildTaskDateFilterQuery("", "", baseDate)).toEqual({});
    expect(buildTaskDateFilterQuery("today", "", baseDate)).toEqual({
      execute_date: "2026-07-02",
    });
    expect(buildTaskDateFilterQuery("week", "", baseDate)).toEqual({
      execute_date_start: "2026-06-29",
      execute_date_end: "2026-07-05",
    });
    expect(buildTaskDateFilterQuery("month", "", baseDate)).toEqual({
      execute_date_start: "2026-07-01",
      execute_date_end: "2026-07-31",
    });
    expect(buildTaskDateFilterQuery("specific", "2026-07-16", baseDate)).toEqual({
      execute_date: "2026-07-16",
    });
  });

  it("formats task activity timestamps in China Standard Time", () => {
    expect(formatChinaDateTime("2026-07-16T04:13:00Z")).toBe("2026-07-16 12:13");
    expect(formatChinaDateTime("2026-07-16T04:13:00+00:00")).toBe("2026-07-16 12:13");
    expect(formatChinaDateTime("2026-07-16T12:13:00+08:00")).toBe("2026-07-16 12:13");
    expect(formatChinaDateTime("2026-07-16T04:13:00")).toBe("2026-07-16 12:13");
    expect(taskDetailSource).toContain("formatChinaDateTime(value)");
  });

  it("uses three task detail bottom action states", () => {
    expect(
      getTaskDetailActionState({
        can_checkin: false,
        checkin_disabled_reason: "未到任务日期",
        current_execution: {
          status: "pending",
          execute_date: "2026-07-09",
        },
      }),
    ).toEqual({
      label: "未开始",
      tone: "not_started",
      disabled: true,
    });

    expect(
      getTaskDetailActionState({
        can_checkin: true,
        checkin_disabled_reason: null,
        current_execution: {
          status: "pending",
          execute_date: "2026-07-02",
        },
      }),
    ).toEqual({
      label: "记录",
      tone: "ready",
      disabled: false,
    });

    expect(
      getTaskDetailActionState({
        can_checkin: false,
        checkin_disabled_reason: "该日期已完成",
        current_execution: {
          status: "completed",
          execute_date: "2026-07-02",
        },
      }),
    ).toEqual({
      label: "已完成",
      tone: "completed",
      disabled: true,
    });
  });

  it("shows archived parent tasks as archived in the task detail action area", () => {
    expect(
      getTaskDetailActionState({
        task_status: "archived",
        can_checkin: false,
        checkin_disabled_reason: "任务当前状态不可完成",
        current_execution: {
          status: "pending",
          display_status: "not_started",
          execute_date: "2026-07-06",
        },
      }),
    ).toEqual({
      label: "已归档",
      tone: "archived",
      disabled: true,
    });
  });

  it("filters and colors task status pills by parent task status", () => {
    expect(taskListSource).toContain(":class=\"taskStatusClass(task)\"");
    expect(taskListSource).toContain("task-status-in-progress");
    expect(taskListSource).toContain("task-status-completed");
    expect(taskListSource).toContain("task-status-cancelled");
    expect(taskListSource).toContain("task-status-archived");
    expect(taskListSource).toContain('{ label: "未开始", value: "not_started" }');
    expect(taskListSource).toContain('{ label: "已取消", value: "cancelled" }');
    expect(taskListSource).toContain('{ label: "已归档", value: "archived" }');

    expect(
      getTaskStatusTone({
        status: "in_progress",
        status_label: "进行中",
        current_execution: { status: "completed" },
      }),
    ).toBe("in_progress");
    expect(
      getTaskStatusTone({
        status: "completed",
        status_label: "已结束",
      }),
    ).toBe("completed");
    expect(
      getTaskStatusTone({
        status: "cancelled",
        status_label: "已取消",
      }),
    ).toBe("cancelled");
    expect(
      getTaskStatusTone({
        status: "archived",
        status_label: "已归档",
      }),
    ).toBe("archived");
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

  it("shows a soft delete action on the admin task edit page", () => {
    expect(adminCreateTaskSource).toContain("删除任务");
    expect(adminCreateTaskSource).toContain("deleteSummerFeedingTask");
    expect(adminCreateTaskSource).toContain("confirmDeleteTask");
    expect(adminCreateTaskSource).toContain('v-if="isEditMode"');
  });

  it("starts map-page navigation from the task detail navigation button", () => {
    expect(taskDetailSource).toContain("goNavigateToTaskPoint");
    expect(taskDetailSource).toContain("MAP_PENDING_NAVIGATION_STORAGE_KEY");
    expect(taskDetailSource).toContain("uni.setStorageSync");
    expect(taskDetailSource).toContain("map_point_id: task.value.map_point.map_point_id");
    expect(taskDetailSource).toContain('uni.switchTab({ url: "/pages/index/index" })');
    expect(taskDetailSource).not.toContain("导航后续接入");
  });

  it("shows associated tencent poi metadata on task detail when available", () => {
    expect(taskDetailSource).toContain("associatedPoi");
    expect(taskDetailSource).toContain("附近地标");
    expect(taskDetailSource).toContain("associatedPoi.category");
    expect(taskDetailSource).toContain("goViewAssociatedPoiOnMap");
    expect(taskDetailSource).toContain("地图查看");
  });

  it("uses distinct label and value styles for task detail content rows", () => {
    expect(taskDetailSource).toContain("section-line-label");
    expect(taskDetailSource).toContain("section-line-value");
    expect(taskDetailSource).toContain('class="section-line-label">物资');
    expect(taskDetailSource).not.toContain("物资：{{ task.required_items }}");
  });

  it("keeps completion photos inside dynamic record details instead of a duplicate task-detail card", () => {
    expect(taskDetailSource).not.toContain('<text class="section-title">完成照片</text>');
    expect(taskDetailSource).not.toContain("displayCheckinPhotos");
    expect(taskDetailSource).toContain("viewingRecord.photos");
    expect(taskDetailSource).toContain("openRecordDetail");
  });

  it("fills selected task point detail with the associated POI name before its address", () => {
    expect(adminTaskLocationSource).toContain("selectAssociatedPoi");
    expect(adminTaskLocationSource).toContain("selectedLocation.location_detail = poi.name || poi.address");
    expect(adminTaskLocationSource).not.toContain("selectedLocation.location_detail = poi.address || poi.name");
  });

  it("uses a custom multi-select calendar instead of the native date picker", () => {
    expect(adminCreateTaskSource).not.toContain('<picker mode="date"');
    expect(adminCreateTaskSource).toContain('class="calendar-overlay"');
    expect(adminCreateTaskSource).toContain('class="calendar-grid"');
    expect(adminCreateTaskSource).toContain("toggleCalendarDate");
    expect(adminCreateTaskSource).toContain("confirmCalendarDates");
    expect(adminCreateTaskSource).toContain("calendarDraftDates");
  });

  it("exposes task publishing as an admin-only side button on the task list", () => {
    expect(taskListSource).not.toContain('class="publish-toolbar"');
    expect(taskListSource).not.toContain('class="publish-button"');
    expect(taskListSource).not.toContain("function goPublish");
    expect(taskListSource).toContain('v-if="userStore.isAdmin"');
    expect(taskListSource).toContain('class="floating-add admin-floating-add"');
    expect(taskListSource).toContain("新增任务");
    expect(taskListSource).toContain("goCreateTask");
    expect(taskListSource).toContain("/pages/admin/tasks/create");
  });

  it("uses a native mini program map for publish-time task point selection", () => {
    expect(adminTaskLocationSource).toContain("<map");
    expect(adminTaskLocationSource).toContain("@tap=\"selectLocationFromMap\"");
    expect(adminTaskLocationSource).toContain("uni.setStorageSync");
    expect(adminTaskLocationSource).toContain("确认此位置");
    expect(adminTaskLocationSource).toContain("getNearbyMapPois");
    expect(adminTaskLocationSource).toContain("associatedPoiCandidates");
    expect(adminTaskLocationSource).toContain('class="poi-list"');
    expect(adminTaskLocationSource).toContain("selectAssociatedPoi");
    expect(adminTaskLocationSource).toContain('<scroll-view class="selected-card" scroll-y');
    expect(adminTaskLocationSource).toContain("clearAssociatedPoi");
    expect(adminTaskLocationSource).not.toContain("自选喂食点");
    expect(adminTaskLocationSource).not.toContain("请补充具体参照物");
  });

  it("starts and resets task point selection at the current user location", () => {
    const resetSource = extractFunctionSource(adminTaskLocationSource, "resetLocation");

    expect(adminTaskLocationSource).toContain("getCachedUserLocation");
    expect(adminTaskLocationSource).toContain("refreshUserLocation");
    expect(adminTaskLocationSource).toContain("void placeAtCurrentUserLocation()");
    expect(adminTaskLocationSource).toContain(':show-location="true"');
    expect(resetSource).toContain("void placeAtCurrentUserLocation({ silent: false })");
    expect(resetSource).not.toContain("HBNU_DEFAULT_TASK_LOCATION");
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
        default_url: "https://cos.test/catmap/task/asset-1/display.jpg",
        default_thumb_url: "https://cos.test/catmap/task/asset-1/thumb_md.jpg",
      }),
    ).toEqual({
      file_id: "asset-1",
      file_url: "https://cos.test/catmap/task/asset-1/display.jpg",
      thumbnail_url: "https://cos.test/catmap/task/asset-1/thumb_md.jpg",
    });
  });

  it("prefers stored COS task photo urls over derived content endpoints", () => {
    expect(
      getTaskPhotoDisplayUrl(
        {
          file_id: "asset-1",
          file_url: "https://cos.test/catmap/task/asset-1/display.jpg",
          thumbnail_url: "https://cos.test/catmap/task/asset-1/thumb_md.jpg",
        },
        "task_detail_full",
      ),
    ).toBe("https://cos.test/catmap/task/asset-1/display.jpg");
  });

  it("does not use the image upload endpoint as a display image fallback", () => {
    expect(
      getTaskPhotoDisplayUrl(
        {
          file_id: null,
          file_url: "http://203.0.113.10/api/v1/files/images",
          thumbnail_url: null,
        },
        "task_detail_full",
      ),
    ).toBe("");
  });

  it("shows parent task status in the task list status pill", () => {
    expect(
      getTaskListStatusLabel({
        status_label: "进行中",
        status: "in_progress",
        current_execution: {
          status: "completed",
        },
      }),
    ).toBe("进行中");

    expect(
      getTaskListStatusLabel({
        status_label: "进行中",
        status: "in_progress",
        current_execution: {
          status: "pending",
        },
      }),
    ).toBe("进行中");

    expect(
      getTaskListStatusLabel({
        status_label: "已完成",
        status: "completed",
      }),
    ).toBe("已完成");
    expect(
      getTaskListStatusLabel({
        status_label: "已取消",
        status: "cancelled",
      }),
    ).toBe("已取消");
    expect(
      getTaskListStatusLabel({
        status_label: "已归档",
        status: "archived",
      }),
    ).toBe("已归档");
  });
});
