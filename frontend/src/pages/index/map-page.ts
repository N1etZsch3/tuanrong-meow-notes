export type MapDrawerState = "expanded" | "collapsed";

export type MapShellItemType =
  | "cat"
  | "supply"
  | "daily_task"
  | "emergency_task"
  | "landmark";

export type MapFilterKey = "all" | MapShellItemType;

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
  type: MapShellItemType;
  title: string;
  subtitle: string;
  description: string;
  distance_meters: number;
  status_label?: string;
  tag_label?: string;
}

export interface MapFilterOption {
  key: MapFilterKey;
  label: string;
  description: string;
}

export const DEFAULT_MAP_DRAWER_STATE: MapDrawerState = "expanded";
export const ALL_MAP_FILTER_KEY: MapFilterKey = "all";

const DRAWER_DRAG_THRESHOLD_PX = 64;

export const HBNU_CAMPUS_CORE_BOUNDS: LngLatBounds = {
  south_west: { lng: 115.0558, lat: 30.2248 },
  north_east: { lng: 115.0693, lat: 30.2342 },
};

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

export const MAP_FILTER_OPTIONS: MapFilterOption[] = [
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
];

export const MAP_SHELL_ITEMS: MapShellItem[] = [
  {
    id: "task-emergency-north-gate",
    type: "emergency_task",
    title: "北门草丛紧急救助任务",
    subtitle: "发现受伤流浪猫",
    description: "北门草丛中发现受伤流浪猫，需要紧急救助和医疗处理。",
    distance_meters: 120,
    status_label: "进行中",
    tag_label: "紧急任务",
  },
  {
    id: "task-daily-canteen",
    type: "daily_task",
    title: "食堂后方投喂清洁",
    subtitle: "日常投喂与清理",
    description: "清理食堂后方投喂点，补充少量猫粮并检查水碗。",
    distance_meters: 250,
    status_label: "可接取",
    tag_label: "日常任务",
  },
  {
    id: "cat-xiaoju",
    type: "cat",
    title: "小橘常驻点",
    subtitle: "教学楼B附近",
    description: "常驻猫咪，性格亲人，常在教学楼B右侧草坪活动。",
    distance_meters: 150,
    status_label: "健康",
    tag_label: "猫咪点",
  },
  {
    id: "supply-gym",
    type: "supply",
    title: "猫协物资点 #1",
    subtitle: "体育馆旁物资补给",
    description: "猫粮、航空箱、诱捕笼备用点。",
    distance_meters: 90,
    status_label: "可用",
    tag_label: "物资点",
  },
  {
    id: "landmark-library",
    type: "landmark",
    title: "图书馆",
    subtitle: "校园地标",
    description: "图书馆附近有常见投喂路线和临时观察点。",
    distance_meters: 210,
    status_label: "地标",
    tag_label: "地标",
  },
];

export function getMapDrawerStateAfterDrag(
  currentState: MapDrawerState,
  deltaY: number,
): MapDrawerState {
  if (deltaY >= DRAWER_DRAG_THRESHOLD_PX) {
    return "collapsed";
  }

  if (deltaY <= -DRAWER_DRAG_THRESHOLD_PX) {
    return "expanded";
  }

  return currentState;
}

export function getMapFilterLabel(filterKey: string): string {
  return (
    MAP_FILTER_OPTIONS.find((option) => option.key === filterKey)?.label ??
    MAP_FILTER_OPTIONS[0].label
  );
}

export function isMapShellItemVisibleByFilter(
  item: MapShellItem,
  filterKey: MapFilterKey,
): boolean {
  return filterKey === ALL_MAP_FILTER_KEY || item.type === filterKey;
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

export function formatDistance(distanceMeters: number): string {
  if (distanceMeters < 1000) {
    return `${Math.round(distanceMeters)}m`;
  }

  return `${(distanceMeters / 1000).toFixed(1)}km`;
}
