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
    user: (userId: ApiPathParam) => `/admin/users/${encodePathParam(userId)}`,
    userResetPassword: (userId: ApiPathParam) =>
      `/admin/users/${encodePathParam(userId)}/reset-password`,
    userWechatBinding: (userId: ApiPathParam) =>
      `/admin/users/${encodePathParam(userId)}/wechat-binding`,
    medicineCategories: "/admin/medicine-categories",
    medicineCategory: (categoryId: ApiPathParam) =>
      `/admin/medicine-categories/${encodePathParam(categoryId)}`,
    medicineCategoryStatus: (categoryId: ApiPathParam) =>
      `/admin/medicine-categories/${encodePathParam(categoryId)}/status`,
    medicine: (medicineId: ApiPathParam) =>
      `/admin/medicines/${encodePathParam(medicineId)}`,
    medicineArchive: (medicineId: ApiPathParam) =>
      `/admin/medicines/${encodePathParam(medicineId)}/archive`,
    medicineHolding: (holdingId: ApiPathParam) =>
      `/admin/medicine-holdings/${encodePathParam(holdingId)}`,
    landmarkPoints: "/admin/landmarks",
    landmarkPoint: (landmarkId: ApiPathParam) =>
      `/admin/landmarks/${encodePathParam(landmarkId)}`,
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
  landmarks: {
    detail: (landmarkId: ApiPathParam) =>
      `/landmarks/${encodePathParam(landmarkId)}`,
  },
  me: {
    dashboard: "/me/dashboard",
    tasks: "/me/tasks",
    checkins: "/me/checkins",
    observations: "/me/observations",
    favoriteCats: "/me/favorite-cats",
  },
  medicineCategories: "/medicine-categories",
  medicines: {
    list: "/medicines",
    search: "/medicines/search",
    detail: (medicineId: ApiPathParam) =>
      `/medicines/${encodePathParam(medicineId)}`,
    holdings: (medicineId: ApiPathParam) =>
      `/medicines/${encodePathParam(medicineId)}/holdings`,
    logs: (medicineId: ApiPathParam) =>
      `/medicines/${encodePathParam(medicineId)}/logs`,
  },
  medicineHoldings: {
    detail: (holdingId: ApiPathParam) =>
      `/medicine-holdings/${encodePathParam(holdingId)}`,
    logs: (holdingId: ApiPathParam) =>
      `/medicine-holdings/${encodePathParam(holdingId)}/logs`,
    purchase: (holdingId: ApiPathParam) =>
      `/medicine-holdings/${encodePathParam(holdingId)}/purchase`,
    use: (holdingId: ApiPathParam) =>
      `/medicine-holdings/${encodePathParam(holdingId)}/use`,
    scrap: (holdingId: ApiPathParam) =>
      `/medicine-holdings/${encodePathParam(holdingId)}/scrap`,
    distribute: (holdingId: ApiPathParam) =>
      `/medicine-holdings/${encodePathParam(holdingId)}/distribute`,
    transfer: (holdingId: ApiPathParam) =>
      `/medicine-holdings/${encodePathParam(holdingId)}/transfer`,
    adjust: (holdingId: ApiPathParam) =>
      `/medicine-holdings/${encodePathParam(holdingId)}/adjust`,
    applications: (holdingId: ApiPathParam) =>
      `/medicine-holdings/${encodePathParam(holdingId)}/applications`,
  },
  medicineApplications: {
    list: "/medicine-applications",
    detail: (applicationId: ApiPathParam) =>
      `/medicine-applications/${encodePathParam(applicationId)}`,
    approve: (applicationId: ApiPathParam) =>
      `/medicine-applications/${encodePathParam(applicationId)}/approve`,
    reject: (applicationId: ApiPathParam) =>
      `/medicine-applications/${encodePathParam(applicationId)}/reject`,
    cancel: (applicationId: ApiPathParam) =>
      `/medicine-applications/${encodePathParam(applicationId)}/cancel`,
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
