import type {
  SupplyItemDto,
  SupplyItemPayload,
  SupplyPhotoDto,
  SupplyPhotoPayload,
  SupplyPointCreatePayload,
  UploadedFileRef,
} from "@/api/supplies";
import { buildFileAssetContentUrl, type ApprovedImageAsset } from "@/api/files";

export const SUPPLY_LOCATION_STORAGE_KEY = "catmap_supply_publish_location";
export const HBNU_DEFAULT_SUPPLY_LOCATION = {
  location_name: "",
  location_detail: "",
  lng: 115.061742,
  lat: 30.22532684,
  route_instruction: "",
};

export interface SelectedSupplyLocation {
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

export interface SupplyDraftItem {
  local_id: string;
  item_name: string;
  item_type: string;
  quantity: number;
  unit: string;
  icon_key: string | null;
  color_key: string;
  is_custom: boolean;
}

export interface SupplyPointDraft {
  name: string;
  description: string;
  items: SupplyDraftItem[];
  location: SelectedSupplyLocation | null;
  photos: UploadedFileRef[];
  route_instruction: string;
}

export interface ValidationResult {
  valid: boolean;
  message?: string;
}

export const SYSTEM_SUPPLY_ITEMS: SupplyDraftItem[] = [
  {
    local_id: "cat_food",
    item_name: "猫粮",
    item_type: "cat_food",
    quantity: 1,
    unit: "份",
    icon_key: "cat_food",
    color_key: "green",
    is_custom: false,
  },
  {
    local_id: "water",
    item_name: "水",
    item_type: "water",
    quantity: 1,
    unit: "瓶",
    icon_key: "water",
    color_key: "blue",
    is_custom: false,
  },
  {
    local_id: "gloves",
    item_name: "手套",
    item_type: "gloves",
    quantity: 1,
    unit: "副",
    icon_key: "gloves",
    color_key: "purple",
    is_custom: false,
  },
  {
    local_id: "net",
    item_name: "网兜",
    item_type: "net",
    quantity: 1,
    unit: "个",
    icon_key: "net",
    color_key: "teal",
    is_custom: false,
  },
  {
    local_id: "carrier",
    item_name: "航空箱",
    item_type: "carrier",
    quantity: 1,
    unit: "个",
    icon_key: "carrier",
    color_key: "orange",
    is_custom: false,
  },
  {
    local_id: "trap",
    item_name: "诱捕笼",
    item_type: "trap",
    quantity: 1,
    unit: "个",
    icon_key: "trap",
    color_key: "red",
    is_custom: false,
  },
];

export function createDefaultSupplyDraft(): SupplyPointDraft {
  return {
    name: "",
    description: "",
    items: [],
    location: null,
    photos: [],
    route_instruction: "",
  };
}

export function cloneSystemSupplyItem(item: SupplyDraftItem): SupplyDraftItem {
  return { ...item, local_id: `${item.local_id}-${Date.now()}-${Math.random()}` };
}

export function buildCustomSupplyItem(name: string): SupplyDraftItem {
  const normalized = name.trim();
  return {
    local_id: `custom-${Date.now()}-${Math.random()}`,
    item_name: normalized,
    item_type: "custom",
    quantity: 1,
    unit: "件",
    icon_key: null,
    color_key: "gray",
    is_custom: true,
  };
}

export function supplyItemLabel(item: Pick<SupplyDraftItem | SupplyItemDto, "item_name" | "quantity" | "unit">): string {
  return `${item.item_name} x${item.quantity}${item.unit || ""}`;
}

export function validateSupplyDraft(draft: SupplyPointDraft): ValidationResult {
  if (!draft.name.trim()) {
    return { valid: false, message: "请填写物资点名称" };
  }

  if (!draft.location) {
    return { valid: false, message: "请选择物资点位置" };
  }

  if (!draft.location.location_detail?.trim()) {
    return { valid: false, message: "请填写位置补充说明" };
  }

  if (!draft.items.length) {
    return { valid: false, message: "请至少添加一种物资" };
  }

  if (draft.items.some((item) => !item.item_name.trim() || item.quantity < 0)) {
    return { valid: false, message: "请检查物资名称和数量" };
  }

  if (!draft.photos.length) {
    return { valid: false, message: "请上传物资点照片" };
  }

  return { valid: true };
}

export function buildUploadedSupplyPhoto(asset: ApprovedImageAsset): UploadedFileRef {
  return {
    file_id: asset.asset_id,
    file_url: asset.default_url,
    thumbnail_url: asset.default_thumb_url,
  };
}

export function buildSupplyPayload(draft: SupplyPointDraft): SupplyPointCreatePayload {
  const location = draft.location;
  if (!location) {
    throw new Error("请选择物资点位置");
  }

  return {
    name: draft.name.trim(),
    description: draft.description.trim() || null,
    access_instruction: draft.route_instruction.trim() || location.route_instruction || null,
    map_point: {
      ...location,
      location_name: draft.name.trim(),
      route_instruction: draft.route_instruction.trim() || location.route_instruction || null,
    },
    items: draft.items.map<SupplyItemPayload>((item, index) => ({
      item_name: item.item_name.trim(),
      item_type: item.item_type || "custom",
      quantity: Number(item.quantity) || 0,
      unit: item.unit.trim() || null,
      icon_key: item.icon_key,
      color_key: item.color_key,
      is_custom: item.is_custom,
      sort_order: index,
    })),
    photos: draft.photos.map<SupplyPhotoPayload>((photo, index) => ({
      ...photo,
      photo_type: index === 0 ? "cover" : "scene",
      sort_order: index,
      is_cover: index === 0,
    })),
    is_public: true,
  };
}

export function supplyPhotoToUploadedRef(photo: SupplyPhotoDto): UploadedFileRef {
  return {
    file_id: null,
    file_url: photo.file_url,
    thumbnail_url: photo.thumbnail_url,
  };
}

export function dtoItemToDraftItem(item: SupplyItemDto): SupplyDraftItem {
  return {
    local_id: item.item_id || `${item.item_type}-${item.sort_order}`,
    item_name: item.item_name,
    item_type: item.item_type,
    quantity: item.quantity,
    unit: item.unit || "",
    icon_key: item.icon_key,
    color_key: item.color_key || "gray",
    is_custom: item.is_custom,
  };
}

function isImageUploadEndpointUrl(url: string): boolean {
  const pathname = url.trim().split(/[?#]/)[0].replace(/\/+$/, "");
  return pathname.endsWith("/files/images");
}

export function normalizeSupplyImageDisplayUrl(url?: string | null): string {
  const normalizedUrl = url?.trim() ?? "";
  if (!normalizedUrl || isImageUploadEndpointUrl(normalizedUrl)) {
    return "";
  }
  return normalizedUrl;
}

export function getSupplyPhotoDisplayUrl(photo?: UploadedFileRef | SupplyPhotoDto | null): string {
  if (!photo) {
    return "";
  }
  const fallbackUrl = photo.thumbnail_url || photo.file_url;
  const displayUrl = normalizeSupplyImageDisplayUrl(fallbackUrl);
  if (displayUrl) {
    return displayUrl;
  }
  return "file_id" in photo && photo.file_id
    ? buildFileAssetContentUrl(photo.file_id, "task_detail_full")
    : "";
}

function padDatePart(value: number): string {
  return String(value).padStart(2, "0");
}

export function formatLocalDate(value: Date): string {
  return `${value.getFullYear()}-${padDatePart(value.getMonth() + 1)}-${padDatePart(
    value.getDate(),
  )}`;
}

export function formatRecordTime(value: string | null | undefined): string {
  return value ? value.replace("T", " ").slice(0, 16) : "";
}

export type SupplyRecordFilterValue = "all" | "month" | "week" | "day";

export function buildSupplyRecordFilterQuery(filter: SupplyRecordFilterValue, baseDate = new Date()) {
  if (filter === "day") {
    return { record_date: formatLocalDate(baseDate) };
  }
  if (filter === "week") {
    const weekday = baseDate.getDay();
    const mondayOffset = weekday === 0 ? -6 : 1 - weekday;
    const monday = new Date(baseDate.getFullYear(), baseDate.getMonth(), baseDate.getDate() + mondayOffset);
    return { record_week_start: formatLocalDate(monday) };
  }
  if (filter === "month") {
    return {
      record_month: `${baseDate.getFullYear()}-${padDatePart(baseDate.getMonth() + 1)}`,
    };
  }
  return {};
}
