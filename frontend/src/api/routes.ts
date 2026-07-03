type ApiPathParam = string | number;
type ApiParamValue = string | number | boolean | null | undefined;

export type ApiParams = Record<string, ApiParamValue>;

function encodePathParam(value: ApiPathParam): string {
  return encodeURIComponent(String(value));
}

export function compactApiParams<T extends object>(
  params: T = {} as T,
): Record<string, unknown> {
  return Object.fromEntries(
    Object.entries(params as Record<string, unknown>).filter(
      ([, value]) => value !== undefined && value !== null && value !== "",
    ),
  );
}

export function compactDefinedApiParams<T extends object>(
  params: T = {} as T,
): Record<string, unknown> {
  return Object.fromEntries(
    Object.entries(params as Record<string, unknown>).filter(
      ([, value]) => value !== undefined,
    ),
  );
}

export function buildApiQueryString(params: ApiParams = {}): string {
  return Object.entries(compactApiParams(params) as ApiParams)
    .map(([key, value]) => `${encodeURIComponent(key)}=${encodeURIComponent(String(value))}`)
    .join("&");
}

function withApiQuery(path: string, params: ApiParams = {}): string {
  const queryString = buildApiQueryString(params);

  return queryString ? `${path}?${queryString}` : path;
}

export const API_ENDPOINTS = {
  auth: {
    captcha: "/auth/captcha",
    login: "/auth/login",
    renew: "/auth/renew",
    me: "/auth/me",
    password: "/auth/password",
    logout: "/auth/logout",
  },
  admin: {
    users: "/admin/users",
    supplyPoints: "/admin/supply-points",
    supplyPoint: (supplyPointId: ApiPathParam) =>
      `/admin/supply-points/${encodePathParam(supplyPointId)}`,
    summerFeedingTask: "/admin/tasks/summer-feeding",
    task: (taskId: ApiPathParam) => `/admin/tasks/${encodePathParam(taskId)}`,
    taskStatus: (taskId: ApiPathParam) =>
      `/admin/tasks/${encodePathParam(taskId)}/status`,
    mapPoint: (pointId: ApiPathParam) =>
      `/admin/map/points/${encodePathParam(pointId)}`,
    mapPointLocation: (pointId: ApiPathParam) =>
      `/admin/map/points/${encodePathParam(pointId)}/location`,
  },
  cats: {
    list: "/cats",
    stats: "/cats/stats",
    filterOptions: "/cats/filter-options",
  },
  files: {
    images: "/files/images",
    asset: (assetId: ApiPathParam) => `/files/assets/${encodePathParam(assetId)}`,
    assetContent: (assetId: ApiPathParam, params: ApiParams = {}) =>
      withApiQuery(`/files/assets/${encodePathParam(assetId)}/content`, params),
  },
  map: {
    init: "/map/init",
    points: "/map/points",
    search: "/map/search",
    bottomContent: "/map/bottom-content",
    pointSummary: (pointId: ApiPathParam) =>
      `/map/points/${encodePathParam(pointId)}/summary`,
    pointNavigation: (pointId: ApiPathParam) =>
      `/map/points/${encodePathParam(pointId)}/navigation`,
    poiResolve: "/map/poi/resolve",
    poiNearby: "/map/poi/nearby",
    walkingRoute: "/map/route/walking",
  },
  me: {
    dashboard: "/me/dashboard",
    tasks: "/me/tasks",
    checkins: "/me/checkins",
    observations: "/me/observations",
    favoriteCats: "/me/favorite-cats",
  },
  profile: {
    me: "/profile/me",
    complete: "/profile/me/complete",
  },
  tasks: {
    list: "/tasks",
    detail: (taskId: ApiPathParam) => `/tasks/${encodePathParam(taskId)}`,
    checkins: (taskId: ApiPathParam) =>
      `/tasks/${encodePathParam(taskId)}/checkins`,
    checkinPhoto: (taskId: ApiPathParam, photoId: ApiPathParam) =>
      `/tasks/${encodePathParam(taskId)}/checkin-photos/${encodePathParam(photoId)}`,
  },
  supplies: {
    detail: (supplyPointId: ApiPathParam) =>
      `/supply-points/${encodePathParam(supplyPointId)}`,
    records: (supplyPointId: ApiPathParam) =>
      `/supply-points/${encodePathParam(supplyPointId)}/records`,
  },
} as const;
