<template>
  <view class="location-page">
    <image class="page-bg" :src="loadingBackground" mode="aspectFill" />
    <view class="location-inner">
      <view class="nav-row">
        <button class="back-button" hover-class="button-hover" @tap="goBack">‹</button>
        <view class="nav-copy">
          <text class="nav-title">选择物资点位置</text>
          <text class="nav-subtitle">点击地图即可插入物资点</text>
        </view>
        <button class="top-confirm" hover-class="button-hover" @tap="confirmLocation">
          确认
        </button>
      </view>

      <view class="map-shell">
        <map
          class="native-map"
          :longitude="selectedLocation.lng"
          :latitude="selectedLocation.lat"
          :scale="17"
          :markers="markers"
          :show-location="true"
          :enable-zoom="true"
          :enable-scroll="true"
          @tap="selectLocationFromMap"
        />
        <view class="map-tip">点击地图可重新选点</view>
        <button class="map-control reset-control" hover-class="button-hover" @tap="resetLocation">
          重置
        </button>
      </view>

      <scroll-view class="selected-card" scroll-y :show-scrollbar="false">
        <text class="card-label">已选位置</text>
        <view class="readonly-name">
          <text>{{ selectedLocation.location_name || "物资点名称来自创建表单" }}</text>
        </view>
        <input
          v-model.trim="selectedLocation.location_detail"
          class="location-input"
          maxlength="40"
          placeholder="位置补充说明"
          placeholder-class="placeholder"
        />
        <view class="coord-grid">
          <view>
            <text class="coord-label">经度</text>
            <text class="coord-value">{{ selectedLocation.lng.toFixed(6) }}</text>
          </view>
          <view>
            <text class="coord-label">纬度</text>
            <text class="coord-value">{{ selectedLocation.lat.toFixed(6) }}</text>
          </view>
        </view>
        <view v-if="currentAssociatedPoi" class="poi-card is-linked">
          <text class="poi-title">已关联公共地点：{{ currentAssociatedPoi.name }}</text>
          <text class="poi-desc">
            {{ currentAssociatedPoi.category || "腾讯地图点位" }} · {{ currentAssociatedPoi.address || "暂无地址" }}
          </text>
          <button class="poi-ghost-button" hover-class="button-hover" @tap="clearAssociatedPoi">
            取消关联
          </button>
        </view>
        <view v-else-if="poiLoadState === 'loading'" class="poi-card">
          <text class="poi-title">正在查找附近公共地点</text>
          <text class="poi-desc">请稍候</text>
        </view>
        <view v-else-if="associatedPoiCandidates.length" class="poi-card">
          <text class="poi-title">附近公共地点</text>
          <view class="poi-list">
            <button
              v-for="poi in associatedPoiCandidates"
              :key="poi.poi_id || `${poi.name}-${poi.lng}-${poi.lat}`"
              class="poi-option"
              hover-class="button-hover"
              @tap="selectAssociatedPoi(poi)"
            >
              <view class="poi-option-copy">
                <text class="poi-option-name">{{ poi.name }}</text>
                <text class="poi-option-desc">
                  {{ poi.category || "腾讯地图点位" }} · 距离 {{ poi.distance_meters ?? "未知" }}m
                </text>
              </view>
              <text class="poi-option-action">关联</text>
            </button>
          </view>
          <button class="poi-ghost-button poi-clear-button" hover-class="button-hover" @tap="clearAssociatedPoi">
            不关联公共点
          </button>
        </view>
        <view v-else-if="poiLoadState === 'ready'" class="poi-card">
          <text class="poi-title">附近暂无公共地点</text>
          <text class="poi-desc">可以直接使用当前选点创建物资点。</text>
        </view>
        <text class="info-line">该位置将用于地图中的物资点</text>
      </scroll-view>
    </view>

    <view class="bottom-actions">
      <button class="cancel-button" hover-class="button-hover" @tap="goBack">取消</button>
      <button class="confirm-button" hover-class="button-hover" @tap="confirmLocation">
        确认此位置
      </button>
    </view>
  </view>
</template>

<script setup lang="ts">
import { onLoad } from "@dcloudio/uni-app";
import { computed, reactive, ref } from "vue";

import { getNearbyMapPois, type TencentPoiDto } from "@/api/map";
import {
  getCachedUserLocation,
  refreshUserLocation,
  type UserLocationPoint,
} from "@/services/user-location";
import {
  HBNU_DEFAULT_SUPPLY_LOCATION,
  SUPPLY_LOCATION_STORAGE_KEY,
  type SelectedSupplyLocation,
} from "@/pages/admin/supplies/supply-page";
import { useUserStore } from "@/stores/user";

import supplyMarkerIcon from "../../../../素材/png/地图点/物资点.png";
import loadingBackground from "../../../../素材/加载页素材/背景.jpg";

type PoiLoadState = "idle" | "loading" | "ready" | "error";
const LOCATION_PICKER_POI_KEYWORD = "\u6e56\u5317\u5e08\u8303\u5927\u5b66";

const userStore = useUserStore();
const initialUserLocation = getCachedUserLocation();
const selectedLocation = reactive<SelectedSupplyLocation>({
  ...HBNU_DEFAULT_SUPPLY_LOCATION,
  ...(initialUserLocation ? toSelectedCoordinates(initialUserLocation) : {}),
});
const associatedPoiCandidates = ref<TencentPoiDto[]>([]);
const poiLoadState = ref<PoiLoadState>("idle");
const initialName = ref("");
let currentLocationRequestId = 0;
const currentAssociatedPoi = computed<TencentPoiDto | null>(() => {
  if (!selectedLocation.tencent_poi_id && !selectedLocation.tencent_poi_name) {
    return null;
  }
  return {
    provider: "tencent",
    poi_id: selectedLocation.tencent_poi_id || null,
    name: selectedLocation.tencent_poi_name || "",
    address: selectedLocation.tencent_poi_address || null,
    category: selectedLocation.tencent_poi_category || null,
    lng: selectedLocation.tencent_poi_lng || selectedLocation.lng,
    lat: selectedLocation.tencent_poi_lat || selectedLocation.lat,
    distance_meters: selectedLocation.tencent_poi_distance_meters ?? null,
    match_method: selectedLocation.tencent_poi_match_method || "admin_selected",
  };
});
const markers = computed(() => [
  {
    id: 1,
    longitude: selectedLocation.lng,
    latitude: selectedLocation.lat,
    iconPath: supplyMarkerIcon,
    width: 42,
    height: 42,
    callout: {
      content: selectedLocation.location_name || "物资点坐标",
      color: "#111827",
      fontSize: 12,
      borderRadius: 8,
      bgColor: "#ffffff",
      padding: 8,
      display: "ALWAYS",
    },
  },
]);

function getLocationPickerPoiKeyword(): string {
  return LOCATION_PICKER_POI_KEYWORD;
}

function toSelectedCoordinates(point: UserLocationPoint): Pick<SelectedSupplyLocation, "lng" | "lat"> {
  return {
    lng: Number(point.lng.toFixed(7)),
    lat: Number(point.lat.toFixed(7)),
  };
}

function applyUserLocationToSelection(point: UserLocationPoint | null): boolean {
  if (!point) {
    return false;
  }

  Object.assign(selectedLocation, toSelectedCoordinates(point), {
    location_name: initialName.value,
  });
  clearAssociatedPoi({ keepCandidates: false });
  poiLoadState.value = "idle";
  return true;
}

async function placeAtCurrentUserLocation(options: { silent?: boolean } = { silent: true }) {
  const requestId = ++currentLocationRequestId;
  const silent = options.silent ?? true;
  const usedCached = applyUserLocationToSelection(getCachedUserLocation());
  const refreshed = await refreshUserLocation({ silent: silent || usedCached });
  if (requestId !== currentLocationRequestId) {
    return;
  }

  const usedRefreshed = applyUserLocationToSelection(refreshed);
  if (usedCached || usedRefreshed) {
    void loadNearbyPoiCandidates();
  }
}

function readLocationTransfer() {
  const value = uni.getStorageSync(SUPPLY_LOCATION_STORAGE_KEY);
  if (value && typeof value === "object") {
    Object.assign(selectedLocation, value as SelectedSupplyLocation);
    uni.removeStorageSync(SUPPLY_LOCATION_STORAGE_KEY);
  }
  initialName.value = selectedLocation.location_name || "";
}

function selectLocationFromMap(event: any) {
  const lng = Number(event.detail?.longitude);
  const lat = Number(event.detail?.latitude);
  if (!Number.isFinite(lng) || !Number.isFinite(lat)) {
    return;
  }
  currentLocationRequestId += 1;
  selectedLocation.lng = Number(lng.toFixed(7));
  selectedLocation.lat = Number(lat.toFixed(7));
  selectedLocation.location_name = initialName.value;
  clearAssociatedPoi({ keepCandidates: false });
  void loadNearbyPoiCandidates();
}

function resetLocation() {
  void placeAtCurrentUserLocation({ silent: false });
}

async function loadNearbyPoiCandidates() {
  const token = await userStore.ensureFreshAccessToken();
  if (!token) {
    poiLoadState.value = "error";
    return;
  }
  poiLoadState.value = "loading";
  try {
    const response = await getNearbyMapPois(token, {
      lng: selectedLocation.lng,
      lat: selectedLocation.lat,
      keyword: getLocationPickerPoiKeyword(),
      radius: 180,
      limit: 6,
    });
    associatedPoiCandidates.value = response.candidates;
    poiLoadState.value = "ready";
  } catch {
    associatedPoiCandidates.value = [];
    poiLoadState.value = "error";
  }
}

function selectAssociatedPoi(poi: TencentPoiDto) {
  selectedLocation.tencent_poi_id = poi.poi_id;
  selectedLocation.tencent_poi_name = poi.name;
  selectedLocation.tencent_poi_address = poi.address;
  selectedLocation.tencent_poi_category = poi.category;
  selectedLocation.tencent_poi_lng = poi.lng;
  selectedLocation.tencent_poi_lat = poi.lat;
  selectedLocation.tencent_poi_distance_meters = poi.distance_meters;
  selectedLocation.tencent_poi_match_method = "admin_selected";
  selectedLocation.location_detail = poi.name || poi.address || "";
  selectedLocation.location_name = initialName.value;
}

function clearAssociatedPoi(options: { keepCandidates?: boolean } = {}) {
  selectedLocation.tencent_poi_id = null;
  selectedLocation.tencent_poi_name = null;
  selectedLocation.tencent_poi_address = null;
  selectedLocation.tencent_poi_category = null;
  selectedLocation.tencent_poi_lng = null;
  selectedLocation.tencent_poi_lat = null;
  selectedLocation.tencent_poi_distance_meters = null;
  selectedLocation.tencent_poi_match_method = null;
  if (!options.keepCandidates) {
    associatedPoiCandidates.value = [];
  }
}

function confirmLocation() {
  selectedLocation.location_name = initialName.value;
  if (!selectedLocation.location_name.trim()) {
    uni.showToast({ title: "请先在表单填写物资点名称", icon: "none" });
    return;
  }
  if (!selectedLocation.location_detail?.trim()) {
    uni.showToast({ title: "请输入位置补充说明", icon: "none" });
    return;
  }
  uni.setStorageSync(SUPPLY_LOCATION_STORAGE_KEY, {
    ...selectedLocation,
    route_instruction: selectedLocation.route_instruction || "",
  });
  uni.navigateBack();
}

function goBack() {
  uni.navigateBack();
}

onLoad(() => {
  readLocationTransfer();
  void placeAtCurrentUserLocation();
});
</script>

<style scoped>
.location-page {
  position: relative;
  height: 100vh;
  overflow: hidden;
  color: #111827;
  font-family: "Songti SC", "STSong", "SimSun", "Noto Serif CJK SC", serif;
}

.page-bg {
  position: fixed;
  inset: 0;
  width: 100%;
  height: 100%;
  z-index: 0;
}

.location-inner {
  position: relative;
  z-index: 1;
  box-sizing: border-box;
  height: 100vh;
  padding: var(--catmap-page-title-top, 92rpx) var(--catmap-page-title-side, 42rpx)
    calc(env(safe-area-inset-bottom) + 160rpx);
  display: flex;
  flex-direction: column;
}

.nav-row {
  display: grid;
  grid-template-columns: 72rpx minmax(0, 1fr) 96rpx;
  align-items: center;
  gap: 22rpx;
}

.back-button,
.top-confirm,
.cancel-button,
.confirm-button,
.map-control {
  margin: 0;
  padding: 0;
  border: 0;
}

.back-button {
  width: 72rpx;
  height: 72rpx;
  border-radius: 50%;
  background: rgba(255, 255, 255, 0.94);
  color: #111827;
  font-size: 58rpx;
  line-height: 62rpx;
  box-shadow: 0 12rpx 28rpx rgba(26, 52, 30, 0.12);
}

.back-button::after,
.top-confirm::after,
.cancel-button::after,
.confirm-button::after,
.map-control::after,
.poi-ghost-button::after,
.poi-option::after {
  border: 0;
}

.nav-title,
.nav-subtitle,
.card-label,
.coord-label,
.coord-value,
.info-line {
  display: block;
}

.nav-title {
  color: #111827;
  font-size: var(--catmap-page-title-font-size, 52rpx);
  font-weight: 900;
  line-height: 1;
}

.nav-subtitle {
  margin-top: var(--catmap-page-title-subtitle-margin, 14rpx);
  color: #6b7280;
  font-size: var(--catmap-page-title-subtitle-size, 24rpx);
  font-weight: 700;
  line-height: 1.2;
}

.top-confirm {
  height: 62rpx;
  border-radius: 20rpx;
  background: transparent;
  color: #287c31;
  font-size: 28rpx;
  font-weight: 900;
  line-height: 62rpx;
}

.map-shell {
  position: relative;
  flex-shrink: 0;
  height: 640rpx;
  margin-top: 34rpx;
  border-radius: 30rpx;
  overflow: hidden;
  background: #dff2d2;
  box-shadow: 0 16rpx 40rpx rgba(27, 54, 30, 0.12);
}

.native-map {
  width: 100%;
  height: 100%;
}

.map-tip {
  position: absolute;
  top: 26rpx;
  left: 50%;
  transform: translateX(-50%);
  padding: 14rpx 24rpx;
  border-radius: 999rpx;
  background: rgba(255, 255, 255, 0.92);
  color: #263324;
  font-size: 24rpx;
  font-weight: 900;
  box-shadow: 0 8rpx 20rpx rgba(26, 52, 30, 0.1);
}

.map-control {
  position: absolute;
  right: 22rpx;
  bottom: 28rpx;
  width: 96rpx;
  height: 84rpx;
  border-radius: 24rpx;
  background: rgba(255, 255, 255, 0.94);
  color: #287c31;
  font-size: 24rpx;
  font-weight: 900;
  line-height: 84rpx;
  box-shadow: 0 8rpx 20rpx rgba(26, 52, 30, 0.1);
}

.selected-card {
  box-sizing: border-box;
  flex: 1;
  min-height: 0;
  margin-top: 28rpx;
  padding: 30rpx;
  border-radius: 28rpx;
  background: rgba(255, 255, 255, 0.94);
  box-shadow: 0 14rpx 34rpx rgba(27, 54, 30, 0.09);
}

.card-label {
  color: #287c31;
  font-size: 24rpx;
  font-weight: 900;
}

.readonly-name,
.location-input {
  box-sizing: border-box;
  width: 100%;
  height: 76rpx;
  margin-top: 18rpx;
  padding: 0 20rpx;
  border-radius: 20rpx;
  color: #111827;
  font-size: 26rpx;
  font-weight: 800;
}

.readonly-name {
  background: #edf8e8;
  color: #287c31;
  line-height: 76rpx;
}

.location-input {
  border: 2rpx solid rgba(40, 124, 49, 0.25);
  background: #ffffff;
}

.placeholder {
  color: #8b919b;
}

.coord-grid {
  margin-top: 24rpx;
  display: grid;
  grid-template-columns: repeat(2, minmax(0, 1fr));
  gap: 18rpx;
}

.coord-label {
  color: #6b7280;
  font-size: 22rpx;
  font-weight: 700;
}

.coord-value {
  margin-top: 8rpx;
  color: #111827;
  font-size: 25rpx;
  font-weight: 900;
}

.poi-card {
  margin-top: 22rpx;
  padding: 18rpx;
  border-radius: 20rpx;
  background: #f6fbf2;
  border: 2rpx solid rgba(40, 124, 49, 0.14);
}

.poi-card.is-linked {
  background: #edf8e8;
}

.poi-title,
.poi-desc {
  display: block;
}

.poi-title {
  color: #1f6f29;
  font-size: 24rpx;
  font-weight: 900;
  line-height: 1.3;
}

.poi-desc {
  margin-top: 8rpx;
  color: #65705f;
  font-size: 21rpx;
  font-weight: 800;
  line-height: 1.35;
}

.poi-ghost-button {
  height: 58rpx;
  margin: 14rpx 0 0;
  padding: 0 10rpx;
  border: 0;
  border-radius: 18rpx;
  background: #ffffff;
  color: #287c31;
  font-size: 22rpx;
  font-weight: 900;
  line-height: 58rpx;
}

.poi-list {
  margin-top: 16rpx;
  display: flex;
  flex-direction: column;
  gap: 12rpx;
}

.poi-option {
  width: 100%;
  min-height: 74rpx;
  margin: 0;
  padding: 14rpx 16rpx;
  border: 0;
  border-radius: 18rpx;
  background: #ffffff;
  color: #111827;
  display: grid;
  grid-template-columns: minmax(0, 1fr) 70rpx;
  align-items: center;
  gap: 14rpx;
  text-align: left;
}

.poi-option-name,
.poi-option-desc {
  display: block;
}

.poi-option-name {
  color: #1f6f29;
  font-size: 23rpx;
  font-weight: 900;
  line-height: 1.25;
}

.poi-option-desc {
  margin-top: 6rpx;
  color: #65705f;
  font-size: 20rpx;
  font-weight: 800;
  line-height: 1.3;
}

.poi-option-action {
  color: #287c31;
  font-size: 22rpx;
  font-weight: 900;
  text-align: right;
}

.poi-clear-button {
  width: 100%;
}

.info-line {
  margin-top: 24rpx;
  padding: 16rpx 18rpx;
  border-radius: 18rpx;
  background: #edf8e8;
  color: #287c31;
  font-size: 23rpx;
  font-weight: 900;
}

.bottom-actions {
  position: fixed;
  z-index: 4;
  left: 32rpx;
  right: 32rpx;
  bottom: calc(env(safe-area-inset-bottom) + 24rpx);
  display: grid;
  grid-template-columns: minmax(0, 1fr) minmax(0, 1.18fr);
  gap: 22rpx;
}

.cancel-button,
.confirm-button {
  height: 92rpx;
  border-radius: 30rpx;
  font-size: 30rpx;
  font-weight: 900;
  line-height: 92rpx;
}

.cancel-button {
  border: 2rpx solid #287c31;
  background: rgba(255, 255, 255, 0.96);
  color: #287c31;
}

.confirm-button {
  background: #287c31;
  color: #ffffff;
  box-shadow: 0 14rpx 34rpx rgba(40, 124, 49, 0.22);
}

.button-hover {
  opacity: 0.9;
  transform: translateY(2rpx);
}
</style>
