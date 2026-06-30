import type {
  MapBottomContentItemDto,
  MapFilterOptionDto,
  MapPointMarkerDto,
  MapPointQuery,
  MapSearchResultDto,
  TencentPoiDto,
} from "@/api/map";


export type MapShellItemType =
  | "cat"
  | "supply"
  | "daily_task"
  | "emergency_task"
  | "landmark";

export type MapFilterKey = string;

export interface LngLat {
  lng: number;
  lat: number;
}

export interface LngLatBounds {
  south_west: LngLat;
  north_east: LngLat;
}

export interface CampusMapConfig {
  id: string;
  name: string;
  center: LngLat;
  default_zoom: number;
  min_zoom: number;
  max_zoom: number;
  core_bounds: LngLatBounds;
  limit_bounds: LngLatBounds;
}

export interface MapShellItem {
  id: string;
  map_point_id?: string;
  type: MapShellItemType;
  title: string;
  subtitle: string | null;
  description: string | null;
  distance_meters: number | null;
  status_label?: string;
  tag_label?: string;
  lng?: number;
  lat?: number;
  cover_photo_url?: string | null;
  icon_key?: string | null;
  associated_poi?: TencentPoiDto | null;
}

export interface CampusExternalPoiResult {
  id: string;
  title: string;
  address: string | null;
  lng: number;
  lat: number;
}

export interface MapFilterOption {
  key: MapFilterKey;
  label: string;
  description: string;
  icon_key?: string | null;
  point_types?: string[];
  business_types?: string[];
}

export type MapMarkerDisplayMode = "icon" | "label" | "preview";

export interface MapMarkerDisplayModeInput {
  zoom: number;
  visibleMarkerCount: number;
  previewEnabled?: boolean;
  labelMinZoom?: number | null;
  previewMinZoom?: number | null;
  selected?: boolean;
}

export const ALL_MAP_FILTER_KEY: MapFilterKey = "all";
export const NO_MAP_FILTER_KEY: MapFilterKey = "none";
export const MAP_PENDING_NAVIGATION_STORAGE_KEY = "catmap_pending_navigation";
export const NO_MAP_FILTER_LABEL = "无标记";

export const HBNU_CAMPUS_CORE_BOUNDS: LngLatBounds = {
  south_west: { lng: 115.0558, lat: 30.2248 },
  north_east: { lng: 115.0693, lat: 30.2342 },
};

export function isFiniteLngLat(
  point: Partial<LngLat> | null | undefined,
): point is LngLat {
  return (
    typeof point?.lng === "number" &&
    typeof point?.lat === "number" &&
    Number.isFinite(point.lng) &&
    Number.isFinite(point.lat)
  );
}

export function clampLngLatToBounds(point: LngLat, bounds: LngLatBounds): LngLat {
  return {
    lng: Math.min(Math.max(point.lng, bounds.south_west.lng), bounds.north_east.lng),
    lat: Math.min(Math.max(point.lat, bounds.south_west.lat), bounds.north_east.lat),
  };
}

export function toNativeMapPoint(
  point: Partial<LngLat> | null | undefined,
): { longitude: number; latitude: number } | null {
  return isFiniteLngLat(point)
    ? {
        longitude: point.lng,
        latitude: point.lat,
      }
    : null;
}

export function expandLngLatBounds(
  bounds: LngLatBounds,
  paddingRatio: number,
): LngLatBounds {
  const lngSpan = bounds.north_east.lng - bounds.south_west.lng;
  const latSpan = bounds.north_east.lat - bounds.south_west.lat;
  const safeRatio = Math.max(0, paddingRatio);

  return {
    south_west: {
      lng: Number((bounds.south_west.lng - lngSpan * safeRatio).toFixed(7)),
      lat: Number((bounds.south_west.lat - latSpan * safeRatio).toFixed(7)),
    },
    north_east: {
      lng: Number((bounds.north_east.lng + lngSpan * safeRatio).toFixed(7)),
      lat: Number((bounds.north_east.lat + latSpan * safeRatio).toFixed(7)),
    },
  };
}

export const HBNU_CAMPUS: CampusMapConfig = {
  id: "hbnu-main",
  name: "湖北师范大学",
  center: { lng: 115.062202, lat: 30.22991 },
  default_zoom: 17.1,
  min_zoom: 15,
  max_zoom: 20,
  core_bounds: HBNU_CAMPUS_CORE_BOUNDS,
  limit_bounds: expandLngLatBounds(HBNU_CAMPUS_CORE_BOUNDS, 0.35),
};

export const NO_MAP_FILTER_OPTION: MapFilterOption = {
  key: NO_MAP_FILTER_KEY,
  label: NO_MAP_FILTER_LABEL,
  description: "暂不显示地图点位",
  icon_key: "filter_none",
  point_types: [],
  business_types: [],
};

export const MAP_FILTER_OPTIONS: MapFilterOption[] = [
  NO_MAP_FILTER_OPTION,
  {
    key: "all",
    label: "全部标记",
    description: "展示任务、猫咪、物资和地标入口",
  },
  {
    key: "emergency_task",
    label: "紧急任务",
    description: "需要快速响应的任务点",
  },
  {
    key: "daily_task",
    label: "日常任务",
    description: "巡查、投喂、清洁等任务",
  },
  {
    key: "cat",
    label: "猫咪点",
    description: "常驻猫咪和高频出现点",
  },
  {
    key: "supply",
    label: "物资点",
    description: "猫粮、航空箱、诱捕笼等物资点",
  },
  {
    key: "landmark",
    label: "地标",
    description: "校门、图书馆、食堂等位置",
  },
  {
    key: "feeding_pending",
    label: "未完成任务",
    description: "尚未完成的暑假投喂点",
    icon_key: "feeding_pending",
    point_types: ["task"],
    business_types: ["feeding"],
  },
  {
    key: "feeding_completed",
    label: "完成任务",
    description: "已完成投喂的任务点",
    icon_key: "feeding_completed",
    point_types: ["task"],
    business_types: ["feeding"],
  },
];

export function getMapFilterLabel(filterKey: string): string {
  return (
    MAP_FILTER_OPTIONS.find((option) => option.key === filterKey)?.label ??
    MAP_FILTER_OPTIONS.find((option) => option.key === ALL_MAP_FILTER_KEY)?.label ??
    "全部标记"
  );
}

export function normalizeMapFilterOptions(
  options: MapFilterOptionDto[] | undefined,
): MapFilterOption[] {
  const normalized = (options || [])
    .filter((option) => option.key && option.label)
    .map<MapFilterOption>((option) => ({
      key: option.key,
      label: option.label,
      description: option.description || "",
      icon_key: option.icon_key,
      point_types: option.point_types || [],
      business_types: option.business_types || [],
    }));

  if (!normalized.some((option) => option.key === NO_MAP_FILTER_KEY)) {
    normalized.unshift(NO_MAP_FILTER_OPTION);
  }

  return normalized.length ? normalized : [NO_MAP_FILTER_OPTION];
}

export function isMapShellItemVisibleByFilter(
  item: MapShellItem,
  filterKey: MapFilterKey,
): boolean {
  if (filterKey === NO_MAP_FILTER_KEY) {
    return false;
  }
  if (filterKey === "feeding_pending" || filterKey === "feeding_completed") {
    return item.type === "daily_task";
  }
  return filterKey === ALL_MAP_FILTER_KEY || item.type === filterKey;
}

export function getMarkerDisplayMode(
  input: MapMarkerDisplayModeInput,
): MapMarkerDisplayMode {
  const previewEnabled = input.previewEnabled !== false;
  const labelMinZoom = input.labelMinZoom ?? 16;
  const previewMinZoom = input.previewMinZoom ?? 15;

  if (previewEnabled && (input.selected || input.visibleMarkerCount <= 2)) {
    return "preview";
  }

  if (input.visibleMarkerCount >= 8 || input.zoom >= labelMinZoom + 2) {
    return "icon";
  }

  if (input.zoom >= labelMinZoom || input.zoom >= previewMinZoom) {
    return "label";
  }

  return "icon";
}

export function isLngLatInsideBounds(
  point: LngLat,
  bounds: LngLatBounds,
): boolean {
  return (
    point.lng >= bounds.south_west.lng &&
    point.lng <= bounds.north_east.lng &&
    point.lat >= bounds.south_west.lat &&
    point.lat <= bounds.north_east.lat
  );
}

export function filterCampusExternalPoiResults(
  results: CampusExternalPoiResult[],
  bounds: LngLatBounds,
): CampusExternalPoiResult[] {
  return results.filter((result) =>
    isLngLatInsideBounds({ lng: result.lng, lat: result.lat }, bounds),
  );
}

export function searchMapShellItems(
  items: MapShellItem[],
  keyword: string,
  filterKey: MapFilterKey,
): MapShellItem[] {
  const normalizedKeyword = keyword.trim().toLowerCase();

  return items.filter((item) => {
    if (!isMapShellItemVisibleByFilter(item, filterKey)) {
      return false;
    }

    if (!normalizedKeyword) {
      return true;
    }

    return [item.title, item.subtitle, item.description, item.tag_label]
      .filter(Boolean)
      .some((text) => text?.toLowerCase().includes(normalizedKeyword));
  });
}

export function formatDistance(distanceMeters: number | null): string {
  if (distanceMeters === null || Number.isNaN(distanceMeters)) {
    return "未知";
  }

  if (distanceMeters < 1000) {
    return `${Math.round(distanceMeters)}m`;
  }

  return `${(distanceMeters / 1000).toFixed(1)}km`;
}

export function resolveMapShellItemType(
  pointType: string,
  businessType?: string | null,
): MapShellItemType {
  if (pointType === "task") {
    return businessType === "emergency" ? "emergency_task" : "daily_task";
  }

  if (pointType === "cat" || pointType === "supply" || pointType === "landmark") {
    return pointType;
  }

  return "landmark";
}

export function getDefaultStatusLabel(type: MapShellItemType): string {
  const labels: Record<MapShellItemType, string> = {
    emergency_task: "进行中",
    daily_task: "可接取",
    cat: "查看",
    supply: "查看",
    landmark: "查看",
  };

  return labels[type];
}

export function mapMarkerToShellItem(marker: MapPointMarkerDto): MapShellItem {
  const type = resolveMapShellItemType(marker.point_type, marker.business_type);

  return {
    id: marker.point_id,
    map_point_id: marker.point_id,
    type,
    title: marker.name,
    subtitle: marker.subtitle,
    description: marker.subtitle,
    distance_meters: marker.distance_meters,
    status_label: getDefaultStatusLabel(type),
    tag_label: getMapFilterLabel(type),
    lng: marker.lng,
    lat: marker.lat,
    cover_photo_url: marker.cover_photo_url,
    icon_key: marker.icon_key,
  };
}

export function mapSearchResultToShellItem(
  result: MapSearchResultDto,
): MapShellItem {
  const type = resolveMapShellItemType(result.point_type, result.business_type);
  const id = result.map_point_id || result.business_id || result.title;

  return {
    id,
    map_point_id: result.map_point_id || undefined,
    type,
    title: result.title,
    subtitle: result.subtitle,
    description: result.description,
    distance_meters: result.distance_meters,
    status_label: result.status_label || getDefaultStatusLabel(type),
    tag_label: getMapFilterLabel(type),
    lng: result.lng,
    lat: result.lat,
    cover_photo_url: result.cover_photo_url,
    icon_key: result.icon_key,
    associated_poi: result.poi || null,
  };
}

export function mapBottomContentItemToShellItem(
  item: MapBottomContentItemDto,
): MapShellItem {
  const type = item.type as MapShellItemType;

  return {
    id: item.map_point_id || item.id,
    map_point_id: item.map_point_id || item.id,
    type,
    title: item.title,
    subtitle: item.subtitle,
    description: item.description,
    distance_meters: item.distance_meters,
    status_label: item.status_label || getDefaultStatusLabel(type),
    tag_label: item.tag_label || getMapFilterLabel(type),
    lng: item.lng ?? undefined,
    lat: item.lat ?? undefined,
  };
}

export function getMapPointQueryByFilter(
  filterKey: MapFilterKey,
  option?: MapFilterOption | null,
): Pick<MapPointQuery, "filter_key" | "point_types" | "business_types"> {
  if (option) {
    return {
      ...(option.key !== NO_MAP_FILTER_KEY ? { filter_key: option.key } : {}),
      ...(option.point_types?.length ? { point_types: option.point_types.join(",") } : {}),
      ...(option.business_types?.length
        ? { business_types: option.business_types.join(",") }
        : {}),
    };
  }

  if (filterKey === "feeding_pending" || filterKey === "feeding_completed") {
    return {
      point_types: "task",
      business_types: "feeding",
      filter_key: filterKey,
    };
  }

  if (filterKey === NO_MAP_FILTER_KEY) {
    return { filter_key: NO_MAP_FILTER_KEY };
  }

  if (filterKey === "emergency_task") {
    return { point_types: "task", business_types: "emergency" };
  }

  if (filterKey === "daily_task") {
    return { point_types: "task", business_types: "daily,feeding" };
  }

  if (filterKey === "cat" || filterKey === "supply" || filterKey === "landmark") {
    return { point_types: filterKey };
  }

  return {};
}
