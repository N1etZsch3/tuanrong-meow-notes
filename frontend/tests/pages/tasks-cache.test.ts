import { describe, expect, it } from "vitest";

import type { TaskListQuery, TaskListResponse } from "@/api/tasks";
import {
  TASK_LIST_CACHE_TTL_MS,
  buildTaskListCacheKey,
  clearTaskListCache,
  getCachedTaskList,
  setCachedTaskList,
} from "@/pages/tasks/task-list-cache";

function response(total: number): TaskListResponse {
  return {
    items: [],
    page: 1,
    page_size: 50,
    total,
    has_more: false,
  };
}

describe("task list frontend cache", () => {
  it("keys task list cache by query fields and ignores empty values", () => {
    const first: TaskListQuery = {
      task_type: "feeding",
      status: "in_progress,completed",
      only_today: undefined,
      page: 1,
      page_size: 50,
    };
    const second: TaskListQuery = {
      page_size: 50,
      page: 1,
      status: "in_progress,completed",
      task_type: "feeding",
    };

    expect(buildTaskListCacheKey(first)).toBe(buildTaskListCacheKey(second));
  });

  it("returns cached task lists until the ttl expires", () => {
    const query: TaskListQuery = {
      task_type: "feeding",
      status: "in_progress,completed",
      page: 1,
      page_size: 50,
    };

    clearTaskListCache();
    setCachedTaskList(query, response(1), 1_000);

    expect(getCachedTaskList(query, 1_000 + TASK_LIST_CACHE_TTL_MS - 1)?.total).toBe(1);
    expect(getCachedTaskList(query, 1_000 + TASK_LIST_CACHE_TTL_MS + 1)).toBeNull();
  });
});
