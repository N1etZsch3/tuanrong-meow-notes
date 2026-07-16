<template>
  <view class="records-page">
    <view class="records-inner">
      <view class="nav-row">
        <button class="back-button" @tap="goBack">‹</button>
        <text class="nav-title">{{ recordMeta.title }}</text>
      </view>

      <scroll-view
        v-if="isCompletedTaskRecordPage && completedTaskRecords.length"
        class="record-list"
        scroll-y
        :show-scrollbar="false"
        lower-threshold="140"
        @scrolltolower="loadMoreRecords"
      >
        <button
          v-for="record in completedTaskRecords"
          :key="record.checkin_id"
          class="record-card"
          hover-class="record-card-hover"
          @tap="goTaskRecord(record)"
        >
          <view class="record-main">
            <text class="record-title">{{ record.task_title }}</text>
            <text class="record-meta">
              {{ formatRecordDate(record.execute_date) }} · {{ record.map_point?.location_name || "投喂点" }}
            </text>
            <text class="record-copy">{{ record.process_result || record.remark || "已完成本次投喂" }}</text>
          </view>
          <text class="record-arrow">›</text>
        </button>

        <view class="list-footer">
          <text v-if="isLoadingMore" class="list-footer-text">正在加载更多记录...</text>
          <text v-else-if="!hasMore" class="list-footer-text">已展示全部 {{ totalRecords }} 条记录</text>
        </view>
      </scroll-view>

      <view v-else class="empty-card">
        <image class="empty-image" :src="emptyImage" mode="aspectFit" />
        <text class="empty-title">{{ recordMeta.empty_title }}</text>
        <text class="empty-description">{{ recordMeta.empty_description }}</text>
        <button class="refresh-button" :loading="isLoading" @tap="loadRecords">刷新</button>
      </view>
    </view>
  </view>
</template>

<script setup lang="ts">
import { computed, ref } from "vue";
import { onLoad } from "@dcloudio/uni-app";

import {
  getFavoriteCats,
  getMyCheckins,
  getMyObservations,
  getMyTasks,
  type EmptyRecordPage,
  type MyCheckinRecordDto,
} from "@/api/me";
import { LOGIN_ROUTE } from "@/services/app-startup";
import { useUserStore } from "@/stores/user";

import {
  PROFILE_RECORD_TYPES,
  type ProfileRecordType,
} from "./profile-page";
import emptyImage from "../../../素材/svg/缺省页/记录空空的.svg";

const userStore = useUserStore();
const recordType = ref<ProfileRecordType>("total_tasks");
const records = ref<EmptyRecordPage | null>(null);
const isLoading = ref(false);
const isLoadingMore = ref(false);
const currentPage = ref(0);
const totalRecords = ref(0);
const hasMore = ref(false);
const PAGE_SIZE = 10;

const recordMeta = computed(() => PROFILE_RECORD_TYPES[recordType.value]);
const isCompletedTaskRecordPage = computed(
  () => recordType.value === "total_tasks" || recordType.value === "monthly_completed",
);
const completedTaskRecords = computed<MyCheckinRecordDto[]>(() => {
  if (!isCompletedTaskRecordPage.value) {
    return [];
  }
  return (records.value?.items || []) as MyCheckinRecordDto[];
});

function formatRecordDate(value: string | null): string {
  if (!value) {
    return "未记录日期";
  }
  const [year, month, day] = value.split("-");
  if (!year || !month || !day) {
    return value;
  }
  return `${year}年${Number(month)}月${Number(day)}日`;
}

async function loadCompletedTaskRecords(accessToken: string) {
  const page = await getMyCheckins(accessToken, { page: 1, page_size: PAGE_SIZE });
  records.value = page;
  currentPage.value = page.page;
  totalRecords.value = page.total;
  hasMore.value = page.has_more;
}

async function loadRecords() {
  const accessToken = await userStore.ensureFreshAccessToken();
  if (!accessToken) {
    uni.reLaunch({ url: LOGIN_ROUTE });
    return;
  }

  isLoading.value = true;
  try {
    if (isCompletedTaskRecordPage.value) {
      await loadCompletedTaskRecords(accessToken);
    } else if (recordType.value === "observations") {
      records.value = await getMyObservations(accessToken);
    } else if (recordType.value === "favorite_cats") {
      records.value = await getFavoriteCats(accessToken);
    } else {
      records.value = await getMyTasks(accessToken);
    }
  } catch (error) {
    const message = error instanceof Error ? error.message : "记录加载失败";
    uni.showToast({ title: message, icon: "none" });
  } finally {
    isLoading.value = false;
  }
}

async function loadMoreRecords() {
  if (
    !isCompletedTaskRecordPage.value ||
    isLoadingMore.value ||
    isLoading.value ||
    !hasMore.value
  ) {
    return;
  }
  const accessToken = await userStore.ensureFreshAccessToken();
  if (!accessToken) {
    return;
  }
  isLoadingMore.value = true;
  try {
    const page = await getMyCheckins(accessToken, {
      page: currentPage.value + 1,
      page_size: PAGE_SIZE,
    });
    const existing = (records.value?.items || []) as MyCheckinRecordDto[];
    const existingIds = new Set(existing.map((item) => item.checkin_id));
    const merged = [
      ...existing,
      ...(page.items as MyCheckinRecordDto[]).filter(
        (item) => !existingIds.has(item.checkin_id),
      ),
    ];
    records.value = { ...page, items: merged };
    currentPage.value = page.page;
    totalRecords.value = page.total;
    hasMore.value = page.has_more;
  } catch {
    // 加载更多失败保持已加载内容，静默处理。
  } finally {
    isLoadingMore.value = false;
  }
}

function goBack() {
  uni.navigateBack();
}

function goTaskRecord(record: MyCheckinRecordDto) {
  const executionQuery = record.execution_date_id
    ? `&execution_date_id=${record.execution_date_id}`
    : "";
  uni.navigateTo({
    url: `/pages/tasks/detail?task_id=${record.task_id}${executionQuery}`,
  });
}

onLoad((options) => {
  const type = String(options?.type || "");
  if (type in PROFILE_RECORD_TYPES) {
    recordType.value = type as ProfileRecordType;
  }
  void loadRecords();
});
</script>

<style scoped>
.records-page {
  height: 100vh;
  overflow: hidden;
  background: linear-gradient(180deg, #fbfcfb 0%, #f5faef 100%);
  color: #20242a;
  font-family: "Songti SC", "STSong", "SimSun", "Noto Serif CJK SC", serif;
}

.records-inner {
  box-sizing: border-box;
  min-height: 100vh;
  padding: var(--catmap-page-title-top, 92rpx) var(--catmap-page-title-side, 42rpx)
    calc(env(safe-area-inset-bottom) + 48rpx);
}

.nav-row {
  display: flex;
  align-items: center;
  gap: var(--catmap-page-title-gap, 14rpx);
}

.back-button {
  width: 64rpx;
  height: 64rpx;
  margin: 0;
  padding: 0;
  border-radius: 50%;
  background: #ffffff;
  color: #2f8037;
  font-size: 58rpx;
  line-height: 54rpx;
  box-shadow: 0 10rpx 28rpx rgba(42, 63, 43, 0.1);
}

.back-button::after,
.refresh-button::after {
  border: 0;
}

.nav-title {
  color: #171b22;
  font-size: var(--catmap-page-title-font-size, 52rpx);
  font-weight: 900;
  line-height: 1;
}

.empty-card {
  margin-top: 48rpx;
  border-radius: 30rpx;
  background: rgba(255, 255, 255, 0.96);
  box-shadow: 0 16rpx 42rpx rgba(42, 63, 43, 0.1);
  padding: 56rpx 36rpx 44rpx;
  display: flex;
  flex-direction: column;
  align-items: center;
  text-align: center;
}

.record-list {
  height: calc(100vh - 220rpx);
  margin-top: 42rpx;
}

.record-card {
  box-sizing: border-box;
  width: 100%;
  min-height: 148rpx;
  margin: 0 0 20rpx;
  padding: 26rpx 28rpx;
  border: 0;
  border-radius: 26rpx;
  background: rgba(255, 255, 255, 0.96);
  box-shadow: 0 14rpx 36rpx rgba(42, 63, 43, 0.1);
  color: #20242a;
  display: flex;
  align-items: center;
  gap: 18rpx;
  text-align: left;
}

.record-card::after {
  border: 0;
}

.record-card-hover {
  opacity: 0.9;
  transform: translateY(2rpx);
}

.record-main {
  flex: 1;
  min-width: 0;
}

.record-title,
.record-meta,
.record-copy {
  display: block;
  overflow: hidden;
  text-overflow: ellipsis;
  white-space: nowrap;
}

.record-title {
  color: #171b22;
  font-size: 30rpx;
  font-weight: 900;
}

.record-meta {
  margin-top: 12rpx;
  color: #2f8037;
  font-size: 24rpx;
  font-weight: 900;
}

.record-copy {
  margin-top: 8rpx;
  color: #6f7780;
  font-size: 23rpx;
  font-weight: 700;
}

.record-arrow {
  color: #8a929c;
  font-size: 48rpx;
  font-weight: 300;
}

.list-footer {
  padding: 20rpx 0 32rpx;
  text-align: center;
}

.list-footer-text {
  color: #8b929a;
  font-size: 22rpx;
  font-weight: 700;
}

.empty-image {
  width: 220rpx;
  height: 180rpx;
}

.empty-title {
  margin-top: 26rpx;
  color: #23272e;
  font-size: 32rpx;
  font-weight: 900;
}

.empty-description {
  margin-top: 16rpx;
  color: #6f7780;
  font-size: 25rpx;
  line-height: 1.5;
}

.refresh-button {
  height: 78rpx;
  margin-top: 34rpx;
  padding: 0 52rpx;
  border-radius: 24rpx;
  background: #2f8037;
  color: #ffffff;
  font-size: 27rpx;
  font-weight: 900;
  line-height: 78rpx;
}
</style>
