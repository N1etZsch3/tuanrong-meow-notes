import type {
  SummerFeedingTaskCreatePayload,
  TaskPhotoPayload,
  UploadedFileRef,
} from "@/api/tasks";
import type { UploadedImageAsset } from "@/api/files";

export const DEFAULT_REQUIRED_ITEMS = "猫粮、水";
export const DEFAULT_ROUTE_INSTRUCTION = "";
export const TASK_PUBLISH_LOCATION_STORAGE_KEY = "catmap_task_publish_location";
export const HBNU_DEFAULT_TASK_LOCATION = {
  location_name: "学生宿舍区北侧喂食点",
  location_detail: "靠近教学楼B",
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
}

export interface FeedingTaskDraft {
  title: string;
  description: string;
  required_items: string;
  execute_dates: string[];
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

  if (!draft.photos.length) {
    return { valid: false, message: "请上传任务点图片" };
  }

  return { valid: true };
}

export function buildUploadedTaskPhoto(asset: UploadedImageAsset): UploadedFileRef {
  return {
    file_id: asset.asset_id,
    file_url: asset.default_url,
    thumbnail_url: asset.default_thumb_url,
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
