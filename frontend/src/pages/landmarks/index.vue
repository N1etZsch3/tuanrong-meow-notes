<template>
  <view class="point-list-page">
    <image class="page-bg" :src="loadingBackground" mode="aspectFill" />
    <view class="point-inner">
      <view class="point-fixed">
        <view class="page-title">
          <button class="back-button" @tap="goBack">‹</button>
          <view class="title-copy">
            <view class="title-row">
              <text class="title-text">校园地标</text>
              <image class="title-icon" :src="pawIcon" mode="aspectFit" />
            </view>
            <text class="title-subtitle">地标位置记录</text>
          </view>
        </view>

        <view class="search-box">
          <text class="search-icon">⌕</text>
          <input
            v-model="searchKeyword"
            class="search-input"
            confirm-type="search"
            placeholder="搜索校园地标 / 附近位置"
            placeholder-class="search-placeholder"
            @confirm="handleSearchConfirm"
          />
          <button class="search-button" @tap="handleSearchConfirm">搜索</button>
        </view>
      </view>

      <scroll-view
        class="point-scroll"
        scroll-y
        :show-scrollbar="false"
        lower-threshold="140"
        @scrolltolower="loadMore"
      >
        <view class="point-list-body">
          <view v-if="isLoading" class="state-box">
            <text class="state-title">正在加载校园地标</text>
            <text class="state-copy">稍等一下，地标记录马上就好。</text>
          </view>

          <view v-else-if="errorMessage" class="state-box">
            <text class="state-title">校园地标加载失败</text>
            <text class="state-copy">{{ errorMessage }}</text>
            <button class="retry-button" hover-class="button-hover" @tap="refresh">
              重新加载
            </button>
          </view>

          <view v-else-if="items.length" class="point-list">
            <button
              v-for="item in items"
              :key="item.point_id"
              class="point-card"
              hover-class="point-card-hover"
              @tap="goDetail(item)"
            >
              <view class="point-image-wrap">
                <image
                  v-if="hasCoverImage(item)"
                  class="point-image"
                  :src="item.cover_photo_url || ''"
                  mode="aspectFill"
                  @error="markImageFailed(item.point_id)"
                />
                <view v-else class="point-image-placeholder">
                  <image class="placeholder-icon" :src="landmarkIcon" mode="aspectFit" />
                </view>
              </view>
              <view class="point-main">
                <text class="point-title">{{ item.title }}</text>
                <view class="nearby-row">
                  <text class="nearby-label">附近地标</text>
                  <text class="nearby-name">{{ item.nearby_landmark_name }}</text>
                </view>
              </view>
            </button>

            <view class="list-footer">
              <text v-if="isLoadingMore" class="list-footer-text">正在加载更多地标...</text>
              <text v-else-if="!hasMore" class="list-footer-text">已展示全部 {{ total }} 个地标</text>
            </view>
          </view>

          <view v-else class="state-box">
            <text class="state-title">暂无校园地标</text>
            <text class="state-copy">新增后的地标会显示在这里和地图上。</text>
          </view>
        </view>
      </scroll-view>
    </view>
    <button
      v-if="userStore.isAdmin"
      class="floating-add admin-floating-add"
      hover-class="button-hover"
      @tap="goCreateLandmark"
    >
      新增地标
    </button>
  </view>
</template>

<script setup lang="ts">
import { onShow } from "@dcloudio/uni-app";
import { ref } from "vue";

import { getLandmarks } from "@/api/landmarks";
import { usePagedList } from "@/composables/use-paged-list";
import { LOGIN_ROUTE } from "@/services/app-startup";
import { useUserStore } from "@/stores/user";
import type { MeowPointListItem } from "@/pages/tasks/meow-list-page";

import landmarkIcon from "../../../素材/png/地图点/地标.png";
import pawIcon from "../../../素材/svg/登录页/猫爪1.svg";
import loadingBackground from "../../../素材/加载页素材/背景.jpg";

const PAGE_SIZE = 10;

const userStore = useUserStore();
const searchKeyword = ref("");
const failedImageIds = ref<Record<string, boolean>>({});

const {
  items,
  total,
  hasMore,
  isLoading,
  isLoadingMore,
  errorMessage,
  refresh: refreshList,
  loadMore,
} = usePagedList<MeowPointListItem>({
  pageSize: PAGE_SIZE,
  getItemKey: (item) => item.point_id,
  fallbackErrorMessage: "校园地标加载失败",
  fetchPage: async (page, pageSize) => {
    const token = await getAccessToken();
    if (!token) {
      throw new Error("未登录");
    }
    return getLandmarks(token, {
      keyword: searchKeyword.value.trim() || undefined,
      page,
      page_size: pageSize,
    });
  },
});

async function getAccessToken(): Promise<string | null> {
  const accessToken = await userStore.ensureFreshAccessToken();
  if (accessToken) {
    return accessToken;
  }

  uni.reLaunch({ url: LOGIN_ROUTE });
  return null;
}

async function refresh() {
  failedImageIds.value = {};
  await refreshList();
}

function handleSearchConfirm() {
  searchKeyword.value = searchKeyword.value.trim();
  void refresh();
}

function goBack() {
  uni.navigateBack();
}

function hasCoverImage(item: MeowPointListItem): boolean {
  return Boolean(item.cover_photo_url && !failedImageIds.value[item.point_id]);
}

function markImageFailed(pointId: string) {
  failedImageIds.value = {
    ...failedImageIds.value,
    [pointId]: true,
  };
}

function goDetail(item: MeowPointListItem) {
  uni.navigateTo({
    url: `/pages/landmarks/detail?landmark_id=${item.detail_id}`,
  });
}

function goCreateLandmark() {
  uni.navigateTo({ url: "/pages/admin/landmarks/create" });
}

onShow(() => {
  void refresh();
});
</script>

<style scoped>
.point-list-page {
  position: relative;
  height: 100vh;
  overflow: hidden;
  color: #111827;
  font-family: "Songti SC", "STSong", "SimSun", "Noto Serif CJK SC", serif;
}

.page-bg {
  position: fixed;
  inset: 0;
  z-index: 0;
  width: 100%;
  height: 100%;
}

.point-inner {
  position: relative;
  z-index: 1;
  box-sizing: border-box;
  height: 100vh;
  padding: var(--catmap-page-title-top, 92rpx) var(--catmap-page-title-side, 42rpx)
    calc(env(safe-area-inset-bottom) + 36rpx);
  display: flex;
  flex-direction: column;
}

.point-fixed {
  flex: 0 0 auto;
}

.point-scroll {
  flex: 1;
  min-height: 0;
  margin-top: 28rpx;
}

.point-list-body {
  padding-bottom: 24rpx;
}

.page-title {
  display: flex;
  align-items: center;
  justify-content: flex-start;
  gap: var(--catmap-page-title-gap, 14rpx);
}

.back-button {
  width: 68rpx;
  height: 68rpx;
  margin: 0;
  padding: 0;
  border-radius: 50%;
  background: rgba(255, 255, 255, 0.94);
  color: #2f8037;
  font-size: 58rpx;
  line-height: 58rpx;
  box-shadow: 0 10rpx 28rpx rgba(42, 63, 43, 0.12);
}

.title-row {
  display: flex;
  align-items: center;
  gap: var(--catmap-page-title-gap, 14rpx);
}

.title-text {
  color: #111827;
  font-size: var(--catmap-page-title-font-size, 52rpx);
  font-weight: 900;
  line-height: 1;
}

.title-icon {
  width: var(--catmap-page-title-icon-size, 48rpx);
  height: var(--catmap-page-title-icon-size, 48rpx);
}

.title-subtitle {
  display: block;
  margin-top: var(--catmap-page-title-subtitle-margin, 14rpx);
  color: #6b7280;
  font-size: var(--catmap-page-title-subtitle-size, 24rpx);
  font-weight: 700;
}

.search-box,
.point-card,
.state-box {
  box-sizing: border-box;
  border: 2rpx solid rgba(197, 230, 193, 0.78);
  background: rgba(255, 255, 255, 0.93);
  box-shadow: 0 15rpx 38rpx rgba(39, 76, 42, 0.08);
}

.search-box {
  min-height: 72rpx;
  margin-top: 30rpx;
  border: 0;
  border-radius: 24rpx;
  padding: 0 14rpx 0 24rpx;
  display: flex;
  align-items: center;
  gap: 14rpx;
}

.search-icon {
  color: #323946;
  font-size: 36rpx;
  line-height: 1;
}

.search-input {
  flex: 1;
  min-width: 0;
  height: 72rpx;
  color: #222831;
  font-size: 25rpx;
}

.search-placeholder {
  color: #969da8;
}

.search-button,
.floating-add,
.retry-button,
.point-card {
  margin: 0;
  padding: 0;
  border: 0;
  background: transparent;
}

.search-button::after,
.back-button::after,
.retry-button::after,
.floating-add::after,
.point-card::after {
  border: 0;
}

.search-button {
  width: 84rpx;
  height: 50rpx;
  border-radius: 16rpx;
  background: #2f8a38;
  color: #ffffff;
  font-size: 22rpx;
  font-weight: 900;
  line-height: 50rpx;
  text-align: center;
}

.floating-add {
  position: fixed;
  z-index: 5;
  right: 34rpx;
  bottom: calc(env(safe-area-inset-bottom) + 34rpx);
  width: 168rpx;
  height: 74rpx;
  border-radius: 26rpx;
  background: #287c31;
  color: #ffffff;
  font-size: 24rpx;
  font-weight: 900;
  line-height: 74rpx;
  text-align: center;
  box-shadow: 0 14rpx 34rpx rgba(40, 124, 49, 0.24);
}

.point-list {
  display: flex;
  flex-direction: column;
  gap: 22rpx;
}

.list-footer {
  padding: 28rpx 0 8rpx;
  text-align: center;
}

.list-footer-text {
  color: #8b929a;
  font-size: 22rpx;
  font-weight: 700;
}

.point-card {
  width: 100%;
  min-height: 176rpx;
  border-radius: 28rpx;
  padding: 20rpx;
  background: rgba(255, 255, 255, 0.94);
  color: #111827;
  display: grid;
  grid-template-columns: 136rpx minmax(0, 1fr);
  gap: 20rpx;
  text-align: left;
}

.point-card-hover,
.button-hover {
  opacity: 0.9;
  transform: translateY(2rpx);
}

.point-image-wrap,
.point-image,
.point-image-placeholder {
  width: 136rpx;
  height: 136rpx;
  border-radius: 22rpx;
  overflow: hidden;
}

.point-image-placeholder {
  background: #edf8e8;
  display: flex;
  align-items: center;
  justify-content: center;
}

.placeholder-icon {
  width: 78rpx;
  height: 78rpx;
}

.point-main {
  min-width: 0;
  display: flex;
  flex-direction: column;
  justify-content: center;
  gap: 18rpx;
}

.point-title {
  overflow: hidden;
  color: #111827;
  font-size: 30rpx;
  font-weight: 900;
  line-height: 1.25;
  text-overflow: ellipsis;
  white-space: nowrap;
}

.nearby-row {
  display: flex;
  align-items: center;
  gap: 12rpx;
  min-width: 0;
}

.nearby-label {
  flex: 0 0 auto;
  padding: 7rpx 12rpx;
  border-radius: 12rpx;
  background: #e6f6e4;
  color: #238033;
  font-size: 20rpx;
  font-weight: 900;
}

.nearby-name {
  flex: 1;
  min-width: 0;
  overflow: hidden;
  color: #6b7280;
  font-size: 23rpx;
  font-weight: 700;
  line-height: 1.3;
  text-overflow: ellipsis;
  white-space: nowrap;
}

.state-box {
  box-sizing: border-box;
  padding: 46rpx 34rpx;
  border: 0;
  border-radius: 28rpx;
  background: rgba(255, 255, 255, 0.9);
}

.state-title,
.state-copy {
  display: block;
}

.state-title {
  color: #111827;
  font-size: 30rpx;
  font-weight: 900;
}

.state-copy {
  margin-top: 14rpx;
  color: #6b7280;
  font-size: 24rpx;
  font-weight: 700;
  line-height: 1.5;
}

.retry-button {
  width: 164rpx;
  height: 56rpx;
  margin-top: 24rpx;
  border-radius: 18rpx;
  background: #2f8a38;
  color: #ffffff;
  font-size: 23rpx;
  font-weight: 900;
  line-height: 56rpx;
  text-align: center;
}
</style>
