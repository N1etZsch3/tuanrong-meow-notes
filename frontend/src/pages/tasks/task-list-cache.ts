import type { TaskListQuery, TaskListResponse } from "@/api/tasks";

export const TASK_LIST_CACHE_TTL_MS = 60_000;

interface TaskListCacheEntry {
  key: string;
  data: TaskListResponse;
  cachedAt: number;
}

let taskListCache: TaskListCacheEntry | null = null;

export function buildTaskListCacheKey(query: TaskListQuery): string {
  const compact = Object.entries(query)
    .filter(([, value]) => value !== undefined && value !== null && value !== "")
    .sort(([left], [right]) => left.localeCompare(right));

  return JSON.stringify(compact);
}

export function getCachedTaskList(
  query: TaskListQuery,
  now = Date.now(),
): TaskListResponse | null {
  const key = buildTaskListCacheKey(query);
  if (!taskListCache || taskListCache.key !== key) {
    return null;
  }

  if (now - taskListCache.cachedAt > TASK_LIST_CACHE_TTL_MS) {
    return null;
  }

  return taskListCache.data;
}

export function setCachedTaskList(
  query: TaskListQuery,
  data: TaskListResponse,
  now = Date.now(),
): void {
  taskListCache = {
    key: buildTaskListCacheKey(query),
    data,
    cachedAt: now,
  };
}

export function clearTaskListCache(): void {
  taskListCache = null;
}
