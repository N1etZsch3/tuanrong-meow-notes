<template>
  <view class="detail-page">
    <image class="page-bg" :src="loadingBackground" mode="aspectFill" />
    <scroll-view class="detail-scroll" scroll-y :show-scrollbar="false">
      <view class="detail-inner">
        <view class="nav-row">
          <button class="back-button" hover-class="button-hover" @tap="goBack">‹</button>
          <view>
            <text class="nav-title">地标详情</text>
            <text class="nav-subtitle">查看地标位置和路线说明</text>
          </view>
        </view>

        <view v-if="loadState === 'loading'" class="state-box">
          <text class="state-title">正在加载地标详情</text>
        </view>

        <view v-else-if="loadState === 'error'" class="state-box">
          <text class="state-title">地标详情加载失败</text>
          <text class="state-copy">{{ errorMessage }}</text>
          <button class="retry-button" hover-class="button-hover" @tap="loadLandmarkDetail">
            重新加载
          </button>
        </view>

        <view v-else-if="landmark" class="detail-content">
          <view class="hero-card">
            <swiper
              v-if="heroPhotos.length"
              class="hero-swiper"
              :autoplay="true"
              :interval="5000"
              :duration="400"
              :circular="true"
            >
              <swiper-item
                v-for="photo in heroPhotos"
                :key="photo.photo_id"
                class="hero-slide"
              >
                <image
                  class="hero-image"
                  :src="photo.url"
                  mode="aspectFill"
                  @tap="openImagePreview(heroPhotoUrls, photo.url)"
                />
              </swiper-item>
            </swiper>
            <view v-else class="hero-placeholder">
              <image class="hero-placeholder-icon" :src="landmarkIcon" mode="aspectFit" />
            </view>
          </view>

          <view class="title-block">
            <text class="eyebrow">地标名称</text>
            <view class="title-row">
              <text class="page-title-text">{{ landmark.name }}</text>
              <button
                v-if="canAdminEdit"
                class="edit-button"
                hover-class="button-hover"
                @tap="goEditLandmark"
              >
                编辑
              </button>
            </view>
            <text class="desc-text">{{ landmark.description || "暂无补充说明" }}</text>
          </view>

          <view class="info-panel">
            <view class="info-section address-section">
              <view class="info-section-head">
                <text class="info-label">地址</text>
                <view class="address-pin" />
              </view>
              <text class="address-title">{{ landmark.map_point.location_name || landmark.name }}</text>
              <text class="address-detail">
                {{ landmark.map_point.location_detail || "暂无详细地址" }}
              </text>
            </view>
          </view>

          <view v-if="associatedPoi" class="section-card poi-section">
            <view class="section-head">
              <text class="section-title">附近地标</text>
              <button class="small-button" hover-class="button-hover" @tap="goViewAssociatedPoiOnMap">
                地图查看
              </button>
            </view>
            <view class="section-line">
              <text class="section-line-label">名称</text>
              <text class="section-line-value">{{ associatedPoi.name }}</text>
            </view>
            <view class="section-line">
              <text class="section-line-label">类别</text>
              <text class="section-line-value">{{ associatedPoi.category || "腾讯地图点位" }}</text>
            </view>
            <view class="section-line">
              <text class="section-line-label">地址</text>
              <text class="section-line-value">{{ associatedPoi.address || "暂无地址" }}</text>
            </view>
          </view>

          <view class="section-card">
            <view class="section-head">
              <text class="section-title">路线说明</text>
            </view>
            <text class="route-text">
              {{ landmark.map_point.route_instruction || landmark.description || "暂无路线说明" }}
            </text>
          </view>
        </view>
      </view>
    </scroll-view>

    <view v-if="landmark" class="bottom-actions">
      <button class="primary-action" hover-class="button-hover" @tap="goNavigateToLandmark">
        导航前往
      </button>
    </view>

  </view>
</template>

<script setup lang="ts">
import { onLoad } from "@dcloudio/uni-app";
import { computed, ref } from "vue";

import { getLandmarkDetail, type LandmarkDetailDto } from "@/api/landmarks";
import { LOGIN_ROUTE } from "@/services/app-startup";
import { ApiBusinessError } from "@/services/request";
import { useUserStore } from "@/stores/user";
import { MAP_PENDING_NAVIGATION_STORAGE_KEY } from "@/pages/index/map-page";
import { getLandmarkPhotoDisplayUrl } from "@/pages/admin/landmarks/landmark-page";

import landmarkIcon from "../../../素材/png/地图点/地标.png";
import loadingBackground from "../../../素材/加载页素材/背景.jpg";

type LoadState = "idle" | "loading" | "ready" | "error";

const userStore = useUserStore();
const landmarkId = ref("");
const landmark = ref<LandmarkDetailDto | null>(null);
const loadState = ref<LoadState>("idle");
const errorMessage = ref("");
const heroPhotos = computed(() =>
  (landmark.value?.photos || [])
    .map((photo) => ({ photo_id: photo.photo_id, url: getLandmarkPhotoDisplayUrl(photo) }))
    .filter((photo) => photo.url),
);
const heroPhotoUrls = computed(() => heroPhotos.value.map((photo) => photo.url));
const associatedPoi = computed(() => landmark.value?.map_point.associated_poi || null);
const canAdminEdit = computed(() => userStore.isAdmin);

async function getAccessToken(): Promise<string | null> {
  const accessToken = await userStore.ensureFreshAccessToken();
  if (accessToken) {
    return accessToken;
  }
  uni.reLaunch({ url: LOGIN_ROUTE });
  return null;
}

async function loadLandmarkDetail() {
  const token = await getAccessToken();
  if (!token || !landmarkId.value) {
    loadState.value = "error";
    errorMessage.value = "缺少地标 ID";
    return;
  }
  loadState.value = "loading";
  try {
    landmark.value = await getLandmarkDetail(token, landmarkId.value);
    loadState.value = "ready";
  } catch (error) {
    loadState.value = "error";
    errorMessage.value =
      error instanceof ApiBusinessError || error instanceof Error
        ? error.message
        : "请稍后重试";
  }
}

function openImagePreview(urls: string[], current: string) {
  if (!current) {
    return;
  }
  const uniqueUrls = Array.from(new Set(urls.filter((url) => url)));
  const resolvedUrls = uniqueUrls.includes(current)
    ? uniqueUrls
    : [current, ...uniqueUrls];
  uni.previewImage({
    current,
    urls: resolvedUrls,
  });
}

function goNavigateToLandmark() {
  if (!landmark.value) {
    return;
  }
  uni.setStorageSync(MAP_PENDING_NAVIGATION_STORAGE_KEY, {
    source: "landmark_detail",
    map_point_id: landmark.value.map_point_id,
    shell_item: {
      id: landmark.value.landmark_id,
      map_point_id: landmark.value.map_point_id,
      type: "landmark",
      title: landmark.value.name,
      subtitle: landmark.value.map_point.location_name,
      description: landmark.value.map_point.location_detail,
      distance_meters: null,
      status_label: "查看",
      status_key: landmark.value.status,
      tag_label: "地标",
      lng: landmark.value.map_point.lng,
      lat: landmark.value.map_point.lat,
      cover_photo_url: landmark.value.photos[0]?.thumbnail_url || landmark.value.photos[0]?.file_url || null,
      icon_key: "landmark",
      associated_poi: landmark.value.map_point.associated_poi || null,
    },
  });
  uni.switchTab({ url: "/pages/index/index" });
}

function goViewAssociatedPoiOnMap() {
  const poi = associatedPoi.value;
  if (!poi) {
    return;
  }
  uni.setStorageSync(MAP_PENDING_NAVIGATION_STORAGE_KEY, {
    source: "landmark_detail_poi",
    poi,
  });
  uni.switchTab({ url: "/pages/index/index" });
}

function goEditLandmark() {
  if (!landmark.value) {
    return;
  }
  uni.navigateTo({
    url: `/pages/admin/landmarks/create?mode=edit&landmark_id=${landmark.value.landmark_id}`,
  });
}

function goBack() {
  uni.navigateBack();
}

onLoad((query) => {
  landmarkId.value =
    typeof query?.landmark_id === "string" ? query.landmark_id : "";
  void loadLandmarkDetail();
});
</script>

<style scoped>
.detail-page {
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

.detail-scroll {
  position: relative;
  z-index: 1;
  height: 100vh;
}

.detail-inner {
  box-sizing: border-box;
  min-height: 100vh;
  padding: var(--catmap-page-title-top, 92rpx) var(--catmap-page-title-side, 42rpx)
    calc(env(safe-area-inset-bottom) + 150rpx);
}

.nav-row {
  display: flex;
  align-items: center;
  gap: 24rpx;
}

.back-button,
.retry-button,
.small-button,
.edit-button,
.primary-action {
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
.retry-button::after,
.small-button::after,
.edit-button::after,
.primary-action::after {
  border: 0;
}

.nav-title,
.nav-subtitle,
.state-title,
.state-copy,
.eyebrow,
.page-title-text,
.desc-text,
.info-label,
.section-title,
.section-line,
.section-line-label,
.section-line-value,
.route-text,
.address-title,
.address-detail {
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
  color: #526070;
  font-size: var(--catmap-page-title-subtitle-size, 24rpx);
  font-weight: 700;
}

.detail-content {
  margin-top: 38rpx;
}

.hero-card,
.hero-swiper,
.hero-slide,
.hero-image,
.hero-placeholder {
  width: 100%;
  height: 418rpx;
  border-radius: 28rpx;
  overflow: hidden;
}

.hero-card {
  box-shadow: 0 18rpx 42rpx rgba(27, 54, 30, 0.12);
}

.hero-placeholder {
  background: #edf8e8;
  display: flex;
  align-items: center;
  justify-content: center;
}

.hero-placeholder-icon {
  width: 150rpx;
  height: 150rpx;
}

.title-block {
  margin-top: 34rpx;
}

.eyebrow {
  color: #6f7a65;
  font-size: 24rpx;
  font-weight: 800;
}

.title-row {
  margin-top: 12rpx;
  display: grid;
  grid-template-columns: minmax(0, 1fr) 104rpx;
  align-items: center;
  gap: 18rpx;
}

.page-title-text {
  color: #111827;
  font-size: 52rpx;
  font-weight: 900;
  line-height: 1.12;
}

.edit-button,
.retry-button,
.small-button {
  background: #e8f5e6;
  color: #287c31;
  font-weight: 900;
}

.edit-button {
  width: 104rpx;
  height: 56rpx;
  border-radius: 18rpx;
  font-size: 24rpx;
  line-height: 56rpx;
}

.retry-button {
  width: 168rpx;
  height: 64rpx;
  margin-top: 22rpx;
  border-radius: 20rpx;
  font-size: 25rpx;
  line-height: 64rpx;
}

.desc-text {
  margin-top: 18rpx;
  color: #465160;
  font-size: 26rpx;
  font-weight: 700;
  line-height: 1.5;
}

.info-panel,
.section-card,
.state-box {
  box-sizing: border-box;
  border-radius: 26rpx;
  background: rgba(255, 255, 255, 0.92);
  box-shadow: 0 14rpx 34rpx rgba(27, 54, 30, 0.09);
}

.state-box {
  margin-top: 42rpx;
  padding: 46rpx 34rpx;
}

.state-title {
  color: #111827;
  font-size: 30rpx;
  font-weight: 900;
}

.state-copy {
  margin-top: 12rpx;
  color: #6b7280;
  font-size: 24rpx;
}

.info-panel {
  margin-top: 34rpx;
  overflow: hidden;
  border: 2rpx solid rgba(212, 237, 208, 0.72);
}

.info-section {
  padding: 28rpx;
  background: rgba(255, 255, 255, 0.68);
}

.info-section-head,
.section-head {
  display: flex;
  align-items: center;
  justify-content: space-between;
  gap: 16rpx;
}

.info-label {
  color: #6b7280;
  font-size: 22rpx;
  font-weight: 700;
}

.address-title {
  margin-top: 18rpx;
  color: #111827;
  font-size: 30rpx;
  font-weight: 900;
  line-height: 1.35;
}

.address-detail {
  margin-top: 10rpx;
  color: #4b5563;
  font-size: 25rpx;
  font-weight: 800;
  line-height: 1.5;
}

.address-pin {
  position: relative;
  width: 26rpx;
  height: 26rpx;
  border: 5rpx solid #63b95d;
  border-radius: 50% 50% 50% 0;
  transform: rotate(-45deg);
  background: #ffffff;
}

.address-pin::after {
  position: absolute;
  left: 50%;
  top: 50%;
  width: 8rpx;
  height: 8rpx;
  border-radius: 50%;
  background: #63b95d;
  content: "";
  transform: translate(-50%, -50%);
}

.section-card {
  margin-top: 24rpx;
  padding: 30rpx;
}

.section-title {
  color: #111827;
  font-size: 32rpx;
  font-weight: 900;
}

.small-button {
  width: 126rpx;
  height: 56rpx;
  border-radius: 18rpx;
  font-size: 23rpx;
  line-height: 56rpx;
}

.section-line {
  margin-top: 16rpx;
  display: flex;
  align-items: flex-start;
  gap: 10rpx;
  line-height: 1.55;
}

.section-line-label {
  flex: 0 0 70rpx;
  color: #788293;
  font-size: 24rpx;
  font-weight: 800;
}

.section-line-value,
.route-text {
  color: #273040;
  font-size: 25rpx;
  font-weight: 900;
  line-height: 1.55;
}

.section-line-value {
  flex: 1;
  min-width: 0;
}

.route-text {
  margin-top: 18rpx;
}

.bottom-actions {
  position: fixed;
  z-index: 4;
  left: 32rpx;
  right: 32rpx;
  bottom: calc(env(safe-area-inset-bottom) + 24rpx);
}

.primary-action {
  width: 100%;
  height: 92rpx;
  border-radius: 30rpx;
  background: #287c31;
  color: #ffffff;
  font-size: 29rpx;
  font-weight: 900;
  line-height: 92rpx;
  box-shadow: 0 14rpx 34rpx rgba(40, 124, 49, 0.24);
}

.button-hover {
  opacity: 0.9;
  transform: translateY(2rpx);
}
</style>
