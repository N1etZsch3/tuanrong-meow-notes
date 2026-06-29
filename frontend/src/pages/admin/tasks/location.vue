<template>
  <view class="location-page">
    <image class="page-bg" :src="loadingBackground" mode="aspectFill" />
    <view class="location-inner">
      <view class="nav-row">
        <button class="back-button" hover-class="button-hover" @tap="goBack">‹</button>
        <view class="nav-copy">
          <text class="nav-title">选择任务位置</text>
          <text class="nav-subtitle">点击地图即可插入喂食点</text>
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

      <view class="selected-card">
        <text class="card-label">已选位置</text>
        <input
          v-model.trim="selectedLocation.location_name"
          class="location-input"
          maxlength="30"
          placeholder="请输入喂食点名称"
          placeholder-class="placeholder"
        />
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
        <text class="info-line">该位置将用于后续喂食任务</text>
      </view>
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
import { computed, reactive } from "vue";

import {
  HBNU_DEFAULT_TASK_LOCATION,
  TASK_PUBLISH_LOCATION_STORAGE_KEY,
  type SelectedTaskLocation,
} from "@/pages/tasks/task-page";

import feedingPendingIcon from "../../../../素材/svg/地图点/失败任务.svg";
import loadingBackground from "../../../../素材/加载页素材/加载页背景.jpg";

const selectedLocation = reactive<SelectedTaskLocation>({
  ...HBNU_DEFAULT_TASK_LOCATION,
});
const markers = computed(() => [
  {
    id: 1,
    longitude: selectedLocation.lng,
    latitude: selectedLocation.lat,
    iconPath: feedingPendingIcon,
    width: 42,
    height: 42,
    callout: {
      content: selectedLocation.location_name,
      color: "#111827",
      fontSize: 12,
      borderRadius: 8,
      bgColor: "#ffffff",
      padding: 8,
      display: "ALWAYS",
    },
  },
]);

function selectLocationFromMap(event: any) {
  const lng = Number(event.detail?.longitude);
  const lat = Number(event.detail?.latitude);
  if (!Number.isFinite(lng) || !Number.isFinite(lat)) {
    return;
  }

  selectedLocation.lng = Number(lng.toFixed(7));
  selectedLocation.lat = Number(lat.toFixed(7));
  if (!selectedLocation.location_name || selectedLocation.location_name === "学生宿舍区北侧喂食点") {
    selectedLocation.location_name = "自选喂食点";
  }
  selectedLocation.location_detail = "请补充具体参照物";
}

function resetLocation() {
  Object.assign(selectedLocation, HBNU_DEFAULT_TASK_LOCATION);
}

function confirmLocation() {
  if (!selectedLocation.location_name.trim()) {
    uni.showToast({ title: "请输入喂食点名称", icon: "none" });
    return;
  }

  uni.setStorageSync(TASK_PUBLISH_LOCATION_STORAGE_KEY, {
    ...selectedLocation,
    route_instruction: selectedLocation.route_instruction || "",
  });
  uni.navigateBack();
}

function goBack() {
  uni.navigateBack();
}
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
.map-control::after {
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
  font-size: 44rpx;
  font-weight: 900;
}

.nav-subtitle {
  margin-top: 8rpx;
  color: #6b7280;
  font-size: 24rpx;
  font-weight: 700;
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

.location-input {
  box-sizing: border-box;
  width: 100%;
  height: 76rpx;
  margin-top: 18rpx;
  padding: 0 20rpx;
  border: 2rpx solid rgba(40, 124, 49, 0.25);
  border-radius: 20rpx;
  background: #ffffff;
  color: #111827;
  font-size: 26rpx;
  font-weight: 800;
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
