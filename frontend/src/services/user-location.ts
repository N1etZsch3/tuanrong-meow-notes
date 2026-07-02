export interface UserLocationPoint {
  lng: number;
  lat: number;
  updated_at: number;
}

type UserLocationListener = (point: UserLocationPoint | null) => void;

type WxLocationResult = {
  longitude: number;
  latitude: number;
};

type UserLocationSetting = {
  authSetting: Record<string, boolean | undefined>;
};

type WxLike = {
  getSetting?: (options: {
    success?: (settings: UserLocationSetting) => void;
    fail?: () => void;
  }) => void;
  authorize?: (options: {
    scope: string;
    success?: () => void;
    fail?: () => void;
  }) => void;
  getLocation?: (options: {
    type?: string;
    isHighAccuracy?: boolean;
    highAccuracyExpireTime?: number;
    success?: (location: WxLocationResult) => void;
    fail?: () => void;
  }) => void;
  startLocationUpdate?: (options: {
    type?: string;
    success?: () => void;
    fail?: () => void;
  }) => void;
  onLocationChange?: (handler: (location: WxLocationResult) => void) => void;
  offLocationChange?: (handler: (location: WxLocationResult) => void) => void;
};

const USER_LOCATION_PERMISSION_SCOPE = "scope.userLocation";
const FALLBACK_REFRESH_INTERVAL_MS = 15000;

const listeners = new Set<UserLocationListener>();

let currentUserLocation: UserLocationPoint | null = null;
let preloadPromise: Promise<UserLocationPoint | null> | null = null;
let realtimeLocationStarted = false;
let fallbackRefreshTimer: ReturnType<typeof setInterval> | null = null;
let locationChangeHandler: ((location: WxLocationResult) => void) | null = null;

function getWxApi(): WxLike | null {
  return (globalThis as unknown as { wx?: WxLike }).wx || null;
}

function isFiniteUserLocation(point: Partial<UserLocationPoint> | null): point is UserLocationPoint {
  return (
    typeof point?.lng === "number" &&
    typeof point?.lat === "number" &&
    Number.isFinite(point.lng) &&
    Number.isFinite(point.lat)
  );
}

function normalizeLocation(location: WxLocationResult): UserLocationPoint | null {
  const point = {
    lng: location.longitude,
    lat: location.latitude,
    updated_at: Date.now(),
  };
  return isFiniteUserLocation(point) ? point : null;
}

function emitUserLocation(point: UserLocationPoint | null) {
  currentUserLocation = point ? { ...point } : null;
  const snapshot = getCachedUserLocation();
  listeners.forEach((listener) => listener(snapshot));
}

function startFallbackLocationRefresh() {
  if (fallbackRefreshTimer) {
    return;
  }

  fallbackRefreshTimer = setInterval(() => {
    void refreshUserLocation({ silent: true, skipRealtimeStart: true });
  }, FALLBACK_REFRESH_INTERVAL_MS);
}

function startRealtimeLocationUpdates() {
  if (realtimeLocationStarted) {
    return;
  }
  realtimeLocationStarted = true;

  const wx = getWxApi();
  if (wx?.startLocationUpdate && wx?.onLocationChange) {
    locationChangeHandler = (location: WxLocationResult) => {
      const point = normalizeLocation(location);
      if (point) {
        emitUserLocation(point);
      }
    };
    wx.onLocationChange(locationChangeHandler);
    wx.startLocationUpdate({
      type: "gcj02",
      fail: () => {
        startFallbackLocationRefresh();
      },
    });
    return;
  }

  startFallbackLocationRefresh();
}

function requestUserLocationPermission(): Promise<boolean> {
  return new Promise((resolve) => {
    const wx = getWxApi();
    const getSetting = wx?.getSetting || uni.getSetting;
    const authorize = wx?.authorize || uni.authorize;

    getSetting({
      success: (settings: UserLocationSetting) => {
        if (settings.authSetting[USER_LOCATION_PERMISSION_SCOPE]) {
          resolve(true);
          return;
        }
        authorize({
          scope: USER_LOCATION_PERMISSION_SCOPE,
          success: () => resolve(true),
          fail: () => resolve(false),
        });
      },
      fail: () => resolve(true),
    });
  });
}

function getWechatMiniProgramLocation(): Promise<UserLocationPoint | null> {
  return new Promise((resolve) => {
    const wx = getWxApi();
    const handleSuccess = (location: WxLocationResult) => {
      resolve(normalizeLocation(location));
    };
    const locationOptions = {
      type: "gcj02",
      isHighAccuracy: true,
      highAccuracyExpireTime: 4000,
      success: handleSuccess,
      fail: () => resolve(null),
    };

    if (wx?.getLocation) {
      wx.getLocation(locationOptions);
      return;
    }

    uni.getLocation(locationOptions as unknown as UniNamespace.GetLocationOptions);
  });
}

export function getCachedUserLocation(): UserLocationPoint | null {
  return currentUserLocation ? { ...currentUserLocation } : null;
}

export function subscribeUserLocation(listener: UserLocationListener): () => void {
  listeners.add(listener);
  listener(getCachedUserLocation());

  return () => {
    listeners.delete(listener);
  };
}

export async function refreshUserLocation(
  options: { silent?: boolean; skipRealtimeStart?: boolean } = {},
): Promise<UserLocationPoint | null> {
  const authorized = await requestUserLocationPermission();
  if (!authorized) {
    if (!options.silent) {
      uni.showToast({ title: "无法获取当前位置", icon: "none" });
    }
    return null;
  }

  if (!options.skipRealtimeStart) {
    startRealtimeLocationUpdates();
  }

  const point = await getWechatMiniProgramLocation();
  if (point) {
    emitUserLocation(point);
    return point;
  }

  if (!options.silent) {
    uni.showToast({ title: "无法获取当前位置", icon: "none" });
  }
  return null;
}

export function preloadUserLocation(
  options: { silent?: boolean } = { silent: true },
): Promise<UserLocationPoint | null> {
  if (!preloadPromise) {
    preloadPromise = refreshUserLocation(options).finally(() => {
      preloadPromise = null;
    });
  }
  return preloadPromise;
}

export function startUserLocationPreload() {
  void preloadUserLocation({ silent: true });
}

export function stopUserLocationUpdates() {
  const wx = getWxApi();
  if (locationChangeHandler && wx?.offLocationChange) {
    wx.offLocationChange(locationChangeHandler);
  }
  locationChangeHandler = null;
  realtimeLocationStarted = false;

  if (fallbackRefreshTimer) {
    clearInterval(fallbackRefreshTimer);
    fallbackRefreshTimer = null;
  }
}
