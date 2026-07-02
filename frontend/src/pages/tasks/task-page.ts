import type {
  SummerFeedingTaskCreatePayload,
  TaskPhotoPayload,
  UploadedFileRef,
} from "@/api/tasks";
import { buildFileAssetContentUrl, type UploadedImageAsset } from "@/api/files";

export const DEFAULT_REQUIRED_ITEMS = "猫粮、水";
export const DEFAULT_ROUTE_INSTRUCTION = "";
export const TASK_PUBLISH_LOCATION_STORAGE_KEY = "catmap_task_publish_location";
export const HBNU_DEFAULT_TASK_LOCATION = {
  location_name: "",
  location_detail: "",
  lng: 115.061742,
  lat: 30.22532684,
  route_instruction: DEFAULT_ROUTE_INSTRUCTION,
};

export interface SelectedTaskLocation {
  campus_id?: string;
  area_id?: string | null;
  location_name: string;
  location_detail?: string | null;
  lng: number;
  lat: number;
  route_instruction?: string | null;
  landmark_hint?: string | null;
  entrance_hint?: string | null;
  amap_poi_id?: string | null;
  amap_address?: string | null;
  tencent_poi_id?: string | null;
  tencent_poi_name?: string | null;
  tencent_poi_address?: string | null;
  tencent_poi_category?: string | null;
  tencent_poi_lng?: number | null;
  tencent_poi_lat?: number | null;
  tencent_poi_distance_meters?: number | null;
  tencent_poi_match_method?: string | null;
}

export interface FeedingTaskDraft {
  title: string;
  description: string;
  required_items: string;
  execute_dates: string[];
  status: "in_progress" | "completed" | "cancelled" | "archived";
  location: SelectedTaskLocation | null;
  photos: UploadedFileRef[];
  route_instruction: string;
}

export interface ValidationResult {
  valid: boolean;
  message?: string;
}

export function createDefaultFeedingTaskDraft(): FeedingTaskDraft {
  return {
    title: "",
    description: "",
    required_items: DEFAULT_REQUIRED_ITEMS,
    execute_dates: [],
    status: "in_progress",
    location: null,
    photos: [],
    route_instruction: DEFAULT_ROUTE_INSTRUCTION,
  };
}

export function normalizeRequiredItems(value: string | null | undefined): string {
  const normalized = value?.trim();
  return normalized || DEFAULT_REQUIRED_ITEMS;
}

export function normalizeRouteInstruction(value: string | null | undefined): string {
  return value?.trim() || DEFAULT_ROUTE_INSTRUCTION;
}

export function formatDateText(value: string | null | undefined): string {
  if (!value) {
    return "";
  }

  const [, month, day] = value.split("-");
  return `${Number(month)}月${Number(day)}日`;
}

export function formatTaskDate(value: string | null | undefined): string {
  if (!value) {
    return "待定";
  }

  const [year, month, day] = value.split("-");
  return `${year}年${Number(month)}月${Number(day)}日`;
}

function padDatePart(value: number): string {
  return String(value).padStart(2, "0");
}

export function formatLocalDate(value: Date): string {
  return `${value.getFullYear()}-${padDatePart(value.getMonth() + 1)}-${padDatePart(
    value.getDate(),
  )}`;
}

function shiftDate(value: Date, days: number): Date {
  return new Date(value.getFullYear(), value.getMonth(), value.getDate() + days);
}

export type TaskDateFilterValue = "" | "today" | "week" | "month" | "specific";

export interface TaskDateFilterQuery {
  execute_date?: string;
  execute_date_start?: string;
  execute_date_end?: string;
}

export function buildTaskDateFilterQuery(
  filter: TaskDateFilterValue,
  specificDate = "",
  baseDate = new Date(),
): TaskDateFilterQuery {
  if (filter === "today") {
    return { execute_date: formatLocalDate(baseDate) };
  }

  if (filter === "week") {
    const weekday = baseDate.getDay();
    const mondayOffset = weekday === 0 ? -6 : 1 - weekday;
    const start = shiftDate(baseDate, mondayOffset);
    const end = shiftDate(start, 6);
    return {
      execute_date_start: formatLocalDate(start),
      execute_date_end: formatLocalDate(end),
    };
  }

  if (filter === "month") {
    const start = new Date(baseDate.getFullYear(), baseDate.getMonth(), 1);
    const end = new Date(baseDate.getFullYear(), baseDate.getMonth() + 1, 0);
    return {
      execute_date_start: formatLocalDate(start),
      execute_date_end: formatLocalDate(end),
    };
  }

  if (filter === "specific" && specificDate) {
    return { execute_date: specificDate };
  }

  return {};
}

export function formatExecutionDateSummary(values: string[]): string {
  if (!values.length) {
    return "请选择日期";
  }

  const sorted = [...values].sort();
  const preview = sorted.slice(0, 3).map(formatDateText).join("、");
  const suffix = sorted.length > 3 ? "..." : "";
  return `已选 ${sorted.length} 个日期 | ${preview}${suffix}`;
}

export function sortUniqueDates(values: string[]): string[] {
  return Array.from(new Set(values.filter(Boolean))).sort();
}

export function validatePublishDraft(draft: FeedingTaskDraft): ValidationResult {
  if (!draft.title.trim()) {
    return { valid: false, message: "请输入任务标题" };
  }

  if (!draft.description.trim()) {
    return { valid: false, message: "请输入任务说明" };
  }

  if (!draft.execute_dates.length) {
    return { valid: false, message: "请选择任务时间" };
  }

  if (!draft.location) {
    return { valid: false, message: "请选择任务位置" };
  }

  if (!draft.location.location_name?.trim()) {
    return { valid: false, message: "请填写喂食点名称" };
  }

  if (!draft.location.location_detail?.trim()) {
    return { valid: false, message: "请填写位置补充说明" };
  }

  if (!draft.photos.length) {
    return { valid: false, message: "请上传任务点图片" };
  }

  return { valid: true };
}

export function buildUploadedTaskPhoto(asset: UploadedImageAsset): UploadedFileRef {
  return {
    file_id: asset.asset_id,
    file_url: buildFileAssetContentUrl(asset.asset_id, "task_detail_full"),
    thumbnail_url: buildFileAssetContentUrl(asset.asset_id, "task_list_cover"),
  };
}

interface TaskListStatusSource {
  status?: string | null;
  status_label: string;
  current_execution?: {
    status?: string | null;
  } | null;
}

export type TaskStatusTone = "completed" | "in_progress" | "cancelled" | "default";

export function getTaskStatusTone(task: TaskListStatusSource): TaskStatusTone {
  if (task.current_execution?.status === "completed" || task.status === "completed") {
    return "completed";
  }
  if (task.status === "in_progress") {
    return "in_progress";
  }
  if (task.status === "cancelled") {
    return "cancelled";
  }
  return "default";
}

export function getTaskListStatusLabel(task: TaskListStatusSource): string {
  const tone = getTaskStatusTone(task);
  if (tone === "completed") {
    return "已完成";
  }
  if (tone === "in_progress") {
    return "进行中";
  }
  if (tone === "cancelled") {
    return "已取消";
  }

  return task.status_label;
}

interface TaskDetailActionStateSource {
  can_checkin: boolean;
  checkin_disabled_reason: string | null;
  current_execution?: {
    status?: string | null;
    execute_date?: string | null;
  } | null;
}

export interface TaskDetailActionState {
  label: "未开始" | "投喂" | "已完成";
  tone: "not_started" | "ready" | "completed";
  disabled: boolean;
}

export function getTaskDetailActionState(
  source: TaskDetailActionStateSource,
): TaskDetailActionState {
  if (source.current_execution?.status === "completed") {
    return {
      label: "已完成",
      tone: "completed",
      disabled: true,
    };
  }

  if (source.can_checkin) {
    return {
      label: "投喂",
      tone: "ready",
      disabled: false,
    };
  }

  return {
    label: "未开始",
    tone: "not_started",
    disabled: true,
  };
}

export function buildSummerFeedingTaskPayload(
  draft: FeedingTaskDraft,
): SummerFeedingTaskCreatePayload {
  const location = draft.location;
  if (!location) {
    throw new Error("请选择任务位置");
  }

  return {
    title: draft.title.trim(),
    description: draft.description.trim(),
    required_items: normalizeRequiredItems(draft.required_items),
    execute_dates: sortUniqueDates(draft.execute_dates),
    map_point: {
      ...location,
      route_instruction: normalizeRouteInstruction(
        draft.route_instruction || location.route_instruction,
      ),
    },
    photos: draft.photos.map<TaskPhotoPayload>((photo, index) => ({
      ...photo,
      photo_type: index === 0 ? "cover" : "scene",
      sort_order: index,
      is_cover: index === 0,
    })),
    is_public: true,
  };
}
